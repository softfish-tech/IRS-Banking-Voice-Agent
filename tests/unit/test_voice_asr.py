import asyncio
import tempfile
import unittest
import wave
from io import BytesIO
from pathlib import Path

from banking_agent.modules.voice import ASRService, AudioValidationError, MockASRBackend, WhisperCppBackend
from banking_agent.schemas import AudioUpload, TranscriptionResult, TranscriptionStatus


def pcm_wav(*, seconds: float = 0.1, rate: int = 16_000, channels: int = 1, width: int = 2) -> bytes:
    buffer = BytesIO()
    with wave.open(buffer, "wb") as writer:
        writer.setnchannels(channels)
        writer.setsampwidth(width)
        writer.setframerate(rate)
        writer.writeframes(b"\x00" * int(seconds * rate * channels * width))
    return buffer.getvalue()


class VoiceASRTests(unittest.IsolatedAsyncioTestCase):
    def upload(self, **kwargs: object) -> AudioUpload:
        values = {"content_type": "audio/wav", "data": pcm_wav()}
        values.update(kwargs)
        return AudioUpload(**values)

    def test_rejects_non_mvp_audio_before_backend(self):
        with self.assertRaisesRegex(AudioValidationError, "unsupported_content_type"):
            asyncio.run(ASRService(MockASRBackend([])).transcribe(self.upload(content_type="audio/mpeg")))
        with self.assertRaisesRegex(AudioValidationError, "unsupported_wav_format"):
            asyncio.run(ASRService(MockASRBackend([])).transcribe(self.upload(data=pcm_wav(rate=8_000))))
        with self.assertRaisesRegex(AudioValidationError, "invalid_audio_duration"):
            asyncio.run(ASRService(MockASRBackend([])).transcribe(self.upload(data=pcm_wav(seconds=61))))

    async def test_service_removes_temporary_audio_and_does_not_expose_it(self):
        backend = MockASRBackend([
            TranscriptionResult(status=TranscriptionStatus.OK, text="synthetic transfer question", backend="ignored"),
        ])
        with tempfile.TemporaryDirectory() as root:
            result = await ASRService(backend, temporary_root=Path(root)).transcribe(self.upload(), language_hint="en")
            self.assertEqual(result.status, TranscriptionStatus.OK)
            self.assertEqual(result.duration_seconds, 0.1)
            self.assertEqual(result.language, "en")
            self.assertEqual(list(Path(root).iterdir()), [])

    async def test_service_removes_temporary_audio_when_backend_raises(self):
        class FailingBackend:
            async def transcribe_file(self, audio_path, *, language_hint=None):
                raise RuntimeError("synthetic backend failure")

        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(RuntimeError, "synthetic backend failure"):
                await ASRService(FailingBackend(), temporary_root=Path(root)).transcribe(self.upload())
            self.assertEqual(list(Path(root).iterdir()), [])

    async def test_whisper_adapter_parses_local_json_output(self):
        with tempfile.TemporaryDirectory() as root:
            root_path = Path(root)
            executable, model, audio = root_path / "whisper-cli", root_path / "model.bin", root_path / "input.wav"
            executable.touch()
            model.touch()
            audio.write_bytes(pcm_wav())

            async def runner(command, cwd):
                self.assertIn("-oj", command)
                (cwd / "transcript.json").write_text('{"transcription":[{"text":" hello"},{"text":"world "}]}')
                return 0, ""

            result = await WhisperCppBackend(executable, model, runner=runner).transcribe_file(audio, language_hint="en")
            self.assertEqual(result.status, TranscriptionStatus.OK)
            self.assertEqual(result.text, "hello world")
            self.assertEqual(result.backend, "whisper.cpp")

    async def test_whisper_backend_fails_closed_when_not_installed(self):
        result = await WhisperCppBackend(Path("/not-installed/whisper-cli"), Path("/not-installed/model.bin")).transcribe_file(Path("/unused.wav"))
        self.assertEqual(result.status, TranscriptionStatus.ERROR)
        self.assertEqual(result.error_code, "backend_not_configured")
