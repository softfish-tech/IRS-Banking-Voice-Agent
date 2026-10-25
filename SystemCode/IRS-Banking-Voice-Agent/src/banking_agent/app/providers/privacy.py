"""Rule-based outbound privacy guard for LLM transport.

This is deliberately a conservative baseline, not a replacement for provider
data-governance controls. It never logs the original message or matched value.
"""

import re

from .interfaces import LLMRequest


class SensitiveDataBlocked(Exception):
    """A credential-like secret was supplied and must not leave the process."""


class SensitiveDataGuard:
    _credential_patterns = (
        re.compile(r"(?i)\b(?:otp|one[ -]?time(?: password| code)?|verification code|passcode|cvv|cvc|security code)\b\s*(?:is|:|=)?\s*\d{3,8}\b"),
        re.compile(r"(?:验证码|动态码|一次性密码|安全码)\s*(?:是|为|:|：|=)?\s*\d{3,8}\b"),
        re.compile(r"(?i)\b(?:pin|password)\b\s*(?:is|:|=)?\s*[^\s]{4,}"),
        re.compile(r"(?:密码|交易密码)\s*(?:是|为|:|：|=)\s*\S{4,}"),
    )
    _email = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
    _phone = re.compile(r"(?<!\w)(?:\+65[ -]?)?[689]\d{3}[ -]?\d{4}(?!\w)")
    _nric = re.compile(r"(?i)(?<![A-Z0-9])[STFG]\d{7}[A-Z](?![A-Z0-9])")
    _account = re.compile(r"(?i)\b(?:account|acct|账户|账号)\s*(?:number|no\.?|号)?\s*[:：=#-]?\s*(\d[\d -]{6,22}\d)")
    _card_candidate = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")

    @staticmethod
    def _luhn(value: str) -> bool:
        digits = [int(char) for char in value if char.isdigit()]
        if not 13 <= len(digits) <= 19:
            return False
        total = 0
        for index, digit in enumerate(reversed(digits)):
            if index % 2:
                digit *= 2
                digit -= 9 if digit > 9 else 0
            total += digit
        return total % 10 == 0

    @staticmethod
    def _replace(pattern: re.Pattern[str], text: str, label: str) -> str:
        values: dict[str, str] = {}

        def substitute(match: re.Match[str]) -> str:
            value = match.group(0)
            if value not in values:
                values[value] = f"[{label}_{len(values) + 1}]"
            return values[value]

        return pattern.sub(substitute, text)

    def sanitize(self, request: LLMRequest) -> LLMRequest:
        replacements: dict[str, str] = {}

        def replace_value(value: str, label: str) -> str:
            if value not in replacements:
                replacements[value] = f"[{label}_{sum(item.startswith(f'[{label}_') for item in replacements.values()) + 1}]"
            return replacements[value]

        messages = []
        for message in request.messages:
            text = message.content
            if any(pattern.search(text) for pattern in self._credential_patterns):
                raise SensitiveDataBlocked
            text = self._email.sub(lambda match: replace_value(match.group(0), "EMAIL"), text)
            text = self._phone.sub(lambda match: replace_value(match.group(0), "PHONE"), text)
            text = self._nric.sub(lambda match: replace_value(match.group(0), "ID_REF"), text)
            text = self._account.sub(lambda match: match.group(0).replace(match.group(1), replace_value(match.group(1), "ACCOUNT_REF")), text)
            text = self._card_candidate.sub(
                lambda match: replace_value(match.group(0), "CARD_REF") if self._luhn(match.group(0)) else match.group(0),
                text,
            )
            messages.append(message.model_copy(update={"content": text}))
        return request.model_copy(update={"messages": tuple(messages)})
