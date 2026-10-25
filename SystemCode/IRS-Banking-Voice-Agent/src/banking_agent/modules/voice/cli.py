"""Terminal-only ASR MVP entry point; it intentionally does not call the agent."""

import argparse
import asyncio
import json
from pathlib import Path

from banking_agent.schemas import AudioUpload, TranscriptionResult, TranscriptionStatus

from .asr import ASRService, AudioValidationError, MockASRBackend, WhisperCppBackend


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Transcribe a short local PCM WAV file.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--language", default=None)
    parser.add_argument("--backend", choices=("mock", "whisper_cpp"), default="mock")
    parser.add_argument("--mock-text", default="This is a synthetic ASR transcript.")
    parser.add_argument("--executable", type=Path)
    parser.add_argument("--model", type=Path)
    return parser


async def _main(args: argparse.Namespace) -> int:
    upload = AudioUpload(content_type="audio/wav", data=args.input.read_bytes())
    if args.backend == "mock":
        backend = MockASRBackend([TranscriptionResult(status=TranscriptionStatus.OK, text=args.mock_text, backend="mock")])
    else:
        if args.executable is None or args.model is None:
            raise ValueError("--executable and --model are required for whisper_cpp")
        backend = WhisperCppBackend(args.executable, args.model)
    try:
        result = await ASRService(backend).transcribe(upload, language_hint=args.language)
    except AudioValidationError as exc:
        print(json.dumps({"status": "ERROR", "error_code": exc.code}))
        return 2
    print(result.model_dump_json())
    return 0 if result.status is not TranscriptionStatus.ERROR else 1


def main() -> None:
    args = _parser().parse_args()
    try:
        raise SystemExit(asyncio.run(_main(args)))
    except (OSError, ValueError) as exc:
        raise SystemExit(str(exc)) from None


if __name__ == "__main__":
    main()
