"""The local demo may load ignored configuration without overriding the shell."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from banking_agent.app.local_env import load_local_env


class LocalEnvTests(unittest.TestCase):
    def test_loads_simple_values_and_keeps_process_environment_authoritative(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / ".env"
            path.write_text(
                "# local only\n"
                "BANKING_AGENT_LLM_MODEL=deepseek-flash\n"
                "export BANKING_AGENT_RESPONSE_GENERATOR='llm'\n"
                "invalid-key=ignored\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"BANKING_AGENT_LLM_MODEL": "shell-model"}, clear=True):
                load_local_env(path)
                self.assertEqual(os.environ["BANKING_AGENT_LLM_MODEL"], "shell-model")
                self.assertEqual(os.environ["BANKING_AGENT_RESPONSE_GENERATOR"], "llm")

    def test_missing_file_is_a_noop(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            load_local_env(Path(root) / ".env")
