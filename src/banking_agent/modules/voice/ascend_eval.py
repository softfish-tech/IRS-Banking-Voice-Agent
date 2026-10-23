"""Reproducible, local-only ASR smoke evaluation on public ASCEND test clips.

This tool downloads only the selected public clips into an ignored directory.
It intentionally never imports the banking orchestrator or persists transcripts.
"""

import argparse
import asyncio
import json
import random
import re
import time
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError

from banking_agent.schemas import AudioUpload, TranscriptionStatus

from .asr import ASRService, WhisperCppBackend

DATASET = "CAiRE/ASCEND"
CONFIG = "main"
SPLIT = "test"
SEED = 20_261_020
TARGETS = {"mixed": 60, "zh": 10, "en": 10}
ROWS_ENDPOINT = "https://datasets-server.huggingface.co/rows"


@dataclass(frozen=True)
class EvalClip:
    id: str
    audio_url: str
    reference: str
    language: str
    speaker_id: int
    duration_seconds: float


def _read_url(url: str, *, timeout: float) -> bytes:
    """Fetch a public ASCEND resource with bounded retries for transient 5xx errors."""
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310 - fixed public dataset endpoint
                return response.read()
        except (HTTPError, URLError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(1 + attempt)
    raise AssertionError("unreachable")


def _get_json(url: str) -> dict[str, Any]:
    return json.loads(_read_url(url, timeout=30))


def fetch_test_rows() -> list[dict[str, Any]]:
    """Read metadata only; audio is fetched later for the selected clips."""
    first = _get_json(f"{ROWS_ENDPOINT}?dataset={DATASET}&config={CONFIG}&split={SPLIT}&offset=0&length=100")
    total = int(first["num_rows_total"])
    pages = [first]
    for offset in range(100, total, 100):
        pages.append(_get_json(f"{ROWS_ENDPOINT}?dataset={DATASET}&config={CONFIG}&split={SPLIT}&offset={offset}&length=100"))
    return [entry["row"] for page in pages for entry in page["rows"]]


def select_clips(rows: list[dict[str, Any]], *, seed: int = SEED, targets: dict[str, int] = TARGETS) -> list[EvalClip]:
    """Stratify by source label and distribute clips evenly across available speakers.

    ASCEND's test split has only two speakers for its mixed subset, so a fixed
    global per-speaker cap would make a 60-clip mixed stratum impossible.
    """
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("language") in targets and row.get("audio"):
            grouped[str(row["language"])].append(row)
    rng = random.Random(seed)
    selected: list[EvalClip] = []
    for language, target in targets.items():
        by_speaker: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for candidate in grouped[language]:
            by_speaker[int(candidate["original_speaker_id"])].append(candidate)
        for candidates in by_speaker.values():
            rng.shuffle(candidates)
        speaker_ids = list(by_speaker)
        rng.shuffle(speaker_ids)
        chosen = 0
        while chosen < target:
            progressed = False
            for speaker_id in speaker_ids:
                if chosen == target:
                    break
                if not by_speaker[speaker_id]:
                    continue
                row = by_speaker[speaker_id].pop()
                audio = row["audio"]
                if not isinstance(audio, list) or not audio or not isinstance(audio[0], dict) or not audio[0].get("src"):
                    continue
                selected.append(EvalClip(
                    id=str(row["id"]), audio_url=str(audio[0]["src"]), reference=str(row["transcription"]),
                    language=language, speaker_id=speaker_id, duration_seconds=float(row["duration"]),
                ))
                chosen += 1
                progressed = True
            if not progressed:
                break
        if chosen != target:
            raise ValueError(f"not enough {language} clips under speaker cap")
    return selected


def mixed_tokens(text: str) -> list[str]:
    """Chinese characters are scored individually; English/number runs as words."""
    return re.findall(r"[\u3400-\u9fff]|[a-z0-9]+(?:'[a-z0-9]+)?", text.casefold())


def edit_distance(reference: list[str], hypothesis: list[str]) -> int:
    previous = list(range(len(hypothesis) + 1))
    for index, source in enumerate(reference, start=1):
        current = [index]
        for target_index, target in enumerate(hypothesis, start=1):
            current.append(min(
                previous[target_index] + 1,
                current[target_index - 1] + 1,
                previous[target_index - 1] + (source != target),
            ))
        previous = current
    return previous[-1]


def _download(url: str, destination: Path) -> None:
    destination.write_bytes(_read_url(url, timeout=60))


async def evaluate(
    clips: list[EvalClip], *, executable: Path, model: Path, output_dir: Path, language_hint: str = "auto",
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_dir = output_dir / "audio"
    audio_dir.mkdir(exist_ok=True)
    service = ASRService(WhisperCppBackend(executable, model, timeout_seconds=90))
    records: list[dict[str, Any]] = []
    for index, clip in enumerate(clips, start=1):
        audio_path = audio_dir / f"{clip.id}.wav"
        if not audio_path.exists():
            await asyncio.to_thread(_download, clip.audio_url, audio_path)
        started = time.perf_counter()
        result = await service.transcribe(AudioUpload(content_type="audio/wav", data=audio_path.read_bytes()), language_hint=language_hint)
        elapsed = round(time.perf_counter() - started, 3)
        reference = mixed_tokens(clip.reference)
        hypothesis = mixed_tokens(result.text or "")
        records.append({
            "id": clip.id, "language": clip.language, "speaker_id": clip.speaker_id,
            "duration_seconds": clip.duration_seconds, "status": result.status,
            "reference": clip.reference, "hypothesis": result.text, "token_errors": edit_distance(reference, hypothesis),
            "reference_tokens": len(reference), "elapsed_seconds": elapsed,
        })
        print(f"[{index}/{len(clips)}] {clip.id} {clip.language} {result.status}")
    return build_report(records)


def build_report(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_language: dict[str, dict[str, Any]] = {}
    for language in TARGETS:
        subset = [record for record in records if record["language"] == language]
        errors = sum(int(record["token_errors"]) for record in subset)
        tokens = sum(int(record["reference_tokens"]) for record in subset)
        by_language[language] = {
            "clips": len(subset), "successful_clips": sum(record["status"] == TranscriptionStatus.OK for record in subset),
            "mixed_token_error_rate": None if not tokens else round(errors / tokens, 4),
            "audio_seconds": round(sum(float(record["duration_seconds"]) for record in subset), 2),
        }
    return {
        "dataset": DATASET, "split": SPLIT, "seed": SEED, "selection": {"targets": TARGETS, "speaker_sampling": "balanced within each language stratum"},
        "metric_note": "Chinese characters and English/number words are tokens; this is a smoke metric, not a published benchmark.",
        "summary": by_language, "records": records,
    }


def load_or_create_selection(output_dir: Path) -> list[EvalClip]:
    """Cache the fixed public selection so evaluation shards do not re-query metadata."""
    selection_path = output_dir / "selection.json"
    if selection_path.exists():
        return [EvalClip(**entry) for entry in json.loads(selection_path.read_text(encoding="utf-8"))]
    output_dir.mkdir(parents=True, exist_ok=True)
    clips = select_clips(fetch_test_rows())
    selection_path.write_text(json.dumps([clip.__dict__ for clip in clips], ensure_ascii=False, indent=2), encoding="utf-8")
    return clips


async def _main(args: argparse.Namespace) -> int:
    if args.merge_only:
        shard_paths = sorted(
            args.output_dir.glob("report-shard-*.json"),
            key=lambda path: int(path.stem.rsplit("-", maxsplit=1)[-1]),
        )
        if not shard_paths:
            raise ValueError("no report-shard-N.json files found to merge")
        records: list[dict[str, Any]] = []
        for shard_path in shard_paths:
            records.extend(json.loads(shard_path.read_text(encoding="utf-8"))["records"])
        report = build_report(records)
        report_path = args.output_dir / "report.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
        print(f"report: {report_path}")
        return 0
    clips = load_or_create_selection(args.output_dir)
    if args.prepare_only:
        print(f"selection: {args.output_dir / 'selection.json'} ({len(clips)} clips)")
        return 0
    if args.executable is None or args.model is None:
        raise ValueError("--executable and --model are required unless --merge-only or --prepare-only is used")
    if not 0 <= args.shard_index < args.shard_count:
        raise ValueError("shard_index must be in [0, shard_count)")
    report = await evaluate(
        clips[args.shard_index::args.shard_count], executable=args.executable, model=args.model,
        output_dir=args.output_dir,
    )
    report_path = args.output_dir / f"report-shard-{args.shard_index}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print(f"report: {report_path}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the fixed ASCEND ASR smoke evaluation.")
    parser.add_argument("--executable", type=Path)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/asr/ascend_base_v1"))
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--merge-only", action="store_true")
    parser.add_argument("--prepare-only", action="store_true")
    raise SystemExit(asyncio.run(_main(parser.parse_args())))


if __name__ == "__main__":
    main()
