import argparse
import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from banking_agent.modules.voice.ascend_eval import _main, edit_distance, mixed_tokens, select_clips


def row(identifier: int, language: str, speaker: int) -> dict[str, object]:
    return {
        "id": f"{identifier:05}", "audio": [{"src": f"https://example.test/{identifier}.wav"}],
        "transcription": "我想 check payment" if language == "mixed" else "hello" if language == "en" else "你好",
        "language": language, "original_speaker_id": speaker, "duration": 2.0,
    }


class AscendEvaluationTests(unittest.TestCase):
    def test_selection_is_deterministic_stratified_and_balanced_by_speaker(self):
        rows = [row(index, language, index % 4) for language, start in (("mixed", 0), ("zh", 20), ("en", 40)) for index in range(start, start + 20)]
        targets = {"mixed": 6, "zh": 3, "en": 3}
        first = select_clips(rows, seed=7, targets=targets)
        self.assertEqual(first, select_clips(rows, seed=7, targets=targets))
        self.assertEqual({language: sum(clip.language == language for clip in first) for language in targets}, targets)
        for language in targets:
            counts = [sum(clip.language == language and clip.speaker_id == speaker for clip in first) for speaker in range(4)]
            self.assertLessEqual(max(counts) - min(counts), 1)

    def test_mixed_token_error_metric_handles_chinese_and_english(self):
        self.assertEqual(mixed_tokens("我想 Check payment!"), ["我", "想", "check", "payment"])
        self.assertEqual(edit_distance(mixed_tokens("我想 check payment"), mixed_tokens("我想 payment")), 1)

    def test_merge_only_does_not_require_asr_paths(self):
        record = {
            "id": "00001", "language": "mixed", "speaker_id": 1, "duration_seconds": 1.0,
            "status": "OK", "reference": "你好", "hypothesis": "你好", "token_errors": 0,
            "reference_tokens": 2, "elapsed_seconds": 0.1,
        }
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            (output_dir / "report-shard-7.json").write_text(json.dumps({"records": [record]}), encoding="utf-8")
            result = asyncio.run(_main(argparse.Namespace(
                executable=None, model=None, output_dir=output_dir, shard_index=0, shard_count=1,
                merge_only=True, prepare_only=False,
            )))
            self.assertEqual(result, 0)
            self.assertEqual(json.loads((output_dir / "report.json").read_text(encoding="utf-8"))["summary"]["mixed"]["clips"], 1)
