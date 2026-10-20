"""Local ASR MVP with a narrow, non-persistent voice boundary."""

import asyncio
import json
import tempfile
import wave
from collections.abc import Awaitable, Callable, Sequence
from io import BytesIO
from pathlib import Path
from typing import Protocol

from banking_agent.schemas import (
    ASRQuality,
    AudioUpload,
    TranscriptionResult,
    TranscriptionStatus,
)

MAX_AUDIO_BYTES = 10 * 1024 * 1024
MAX_DURATION_SECONDS = 60.0
REQUIRED_CONTENT_TYPE = "audio/wav"


class AudioValidationError(ValueError):
    """A stable, non-sensitive reason why an audio payload was not accepted."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class ASRBackend(Protocol):
    """Backend contract. Implementations receive only a short-lived local file."""

    async def transcribe_file(
        self, audio_path: Path, *, language_hint: str | None = None,
    ) -> TranscriptionResult: ...


def validate_wav(upload: AudioUpload) -> float:
    """Accept only the deliberately small MVP format: PCM WAV, 16kHz mono."""
    if upload.content_type.lower().split(";", 1)[0].strip() != REQUIRED_CONTENT_TYPE:
        raise AudioValidationError("unsupported_content_type")
    if not upload.data or len(upload.data) > MAX_AUDIO_BYTES:
        raise AudioValidationError("invalid_audio_size")
    try:
        with wave.open(BytesIO(upload.data), "rb") as reader:
            if reader.getcomptype() != "NONE":
                raise AudioValidationError("unsupported_wav_encoding")
            if reader.getnchannels() != 1 or reader.getframerate() != 16_000 or reader.getsampwidth() != 2:
                raise AudioValidationError("unsupported_wav_format")
            duration = reader.getnframes() / reader.getframerate()
    except AudioValidationError:
        raise
    except (EOFError, wave.Error):
        raise AudioValidationError("invalid_wav") from None
    if duration <= 0 or duration > MAX_DURATION_SECONDS:
        raise AudioValidationError("invalid_audio_duration")
    return duration


class ASRService:
    """Validates audio and guarantees temporary-file removal after every call."""

    def __init__(self, backend: ASRBackend, *, temporary_root: Path | None = None) -> None:
        self._backend = backend
        self._temporary_root = temporary_root

    async def transcribe(
        self, upload: AudioUpload, *, language_hint: str | None = None,
    ) -> TranscriptionResult:
        duration = validate_wav(upload)
        with tempfile.TemporaryDirectory(prefix="banking-asr-", dir=self._temporary_root) as directory:
            audio_path = Path(directory) / "input.wav"
            await asyncio.to_thread(audio_path.write_bytes, upload.data)
            result = await self._backend.transcribe_file(audio_path, language_hint=language_hint)
        # The backend is authoritative for actual duration, but no backend may omit it.
        return result if result.duration_seconds is not None else result.model_copy(update={"duration_seconds": duration})


class MockASRBackend:
    """Deterministic terminal/test backend; it never reads or retains the audio."""

    def __init__(self, results: Sequence[TranscriptionResult]) -> None:
        self._results = list(results)
        self.calls = 0

    async def transcribe_file(self, audio_path: Path, *, language_hint: str | None = None) -> TranscriptionResult:
        self.calls += 1
        if not self._results:
            return TranscriptionResult(status=TranscriptionStatus.ERROR, backend="mock", error_code="no_mock_result")
        result = self._results.pop(0)
        return result.model_copy(update={"backend": "mock", "language": result.language or language_hint})


ProcessRunner = Callable[[Sequence[str], Path], Awaitable[tuple[int, str]]]


class WhisperCppBackend:
    """Adapter for a locally installed ``whisper-cli`` executable.

    The model and executable are explicit local paths. This code never downloads a
    model or sends audio to a remote provider.
    """

    def __init__(self, executable: Path, model_path: Path, *, timeout_seconds: float = 90.0,
                 runner: ProcessRunner | None = None) -> None:
        self._executable = executable
        self._model_path = model_path
        self._timeout_seconds = timeout_seconds
        self._runner = runner or self._run

    async def transcribe_file(self, audio_path: Path, *, language_hint: str | None = None) -> TranscriptionResult:
        if not self._executable.is_file() or not self._model_path.is_file():
            return TranscriptionResult(status=TranscriptionStatus.ERROR, backend="whisper.cpp", error_code="backend_not_configured")
        output_prefix = audio_path.parent / "transcript"
        command = [str(self._executable), "-m", str(self._model_path), "-f", str(audio_path), "-oj", "-of", str(output_prefix)]
        if language_hint:
            command.extend(["-l", language_hint])
        try:
            return_code, stderr = await asyncio.wait_for(self._runner(command, audio_path.parent), timeout=self._timeout_seconds)
        except TimeoutError:
            return TranscriptionResult(status=TranscriptionStatus.ERROR, backend="whisper.cpp", error_code="timeout")
        if return_code != 0:
            return TranscriptionResult(status=TranscriptionStatus.ERROR, backend="whisper.cpp", error_code="backend_failed")
        try:
            payload = json.loads((output_prefix.with_suffix(".json")).read_text(encoding="utf-8"))
            text, quality = self._parse_output(payload)
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return TranscriptionResult(status=TranscriptionStatus.ERROR, backend="whisper.cpp", error_code="invalid_backend_output")
        if not text:
            return TranscriptionResult(status=TranscriptionStatus.EMPTY, backend="whisper.cpp")
        return TranscriptionResult(status=TranscriptionStatus.OK, text=text, language=language_hint, quality=quality, backend="whisper.cpp")

    @staticmethod
    def _parse_output(payload: object) -> tuple[str, ASRQuality | None]:
        if not isinstance(payload, dict):
            raise ValueError("expected object")
        raw_segments = payload.get("transcription", [])
        if isinstance(raw_segments, str):
            return raw_segments.strip(), None
        if not isinstance(raw_segments, list):
            raise ValueError("expected transcription list")
        segments = [entry for entry in raw_segments if isinstance(entry, dict)]
        text = " ".join(str(entry.get("text", "")).strip() for entry in segments).strip()
        return text, None

    async def _run(self, command: Sequence[str], cwd: Path) -> tuple[int, str]:
        process = await asyncio.create_subprocess_exec(
            *command, cwd=cwd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()
        return process.returncode or 0, stderr.decode("utf-8", errors="replace")
