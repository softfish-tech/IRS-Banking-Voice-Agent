"""Shared, persistence-free contracts for the voice extension boundary."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .enums import TranscriptionStatus


class AudioUpload(BaseModel):
    """A short audio payload supplied only to the in-process ASR boundary.

    It must never be copied into ``AgentState``, persistence, or decision traces.
    """

    model_config = ConfigDict(frozen=True)

    content_type: str
    data: bytes = Field(repr=False)


class ASRQuality(BaseModel):
    """Backend-provided diagnostic signals, deliberately not a confidence score."""

    language_probability: float | None = Field(default=None, ge=0, le=1)
    no_speech_probability: float | None = Field(default=None, ge=0, le=1)
    average_log_probability: float | None = None
    compression_ratio: float | None = Field(default=None, ge=0)


class TranscriptionResult(BaseModel):
    """Sanitized ASR result for a later explicit confirmation step."""

    model_config = ConfigDict(frozen=True)

    status: TranscriptionStatus
    text: str | None = Field(default=None, max_length=4_000)
    language: str | None = Field(default=None, max_length=16)
    duration_seconds: float | None = Field(default=None, ge=0)
    quality: ASRQuality | None = None
    backend: str = Field(min_length=1, max_length=64)
    error_code: str | None = Field(default=None, max_length=64)

    @model_validator(mode="after")
    def _check_status_shape(self) -> "TranscriptionResult":
        if self.status is TranscriptionStatus.OK and not self.text:
            raise ValueError("successful transcription requires text")
        if self.status is not TranscriptionStatus.OK and self.text is not None:
            raise ValueError("non-successful transcription must not contain text")
        return self
