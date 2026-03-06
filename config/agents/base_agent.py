"""
agents/base_agent.py
--------------------
Abstract base class shared by all EDA agents.
Handles Claude API communication and structured logging.
"""

import json
import os
from abc import ABC, abstractmethod
from typing import Any

import anthropic
from config.settings import CLAUDE_MODEL, CLAUDE_MAX_TOKENS, ANTHROPIC_API_KEY


class BaseAgent(ABC):
    """Base class providing Claude API access and logging utilities."""

    def __init__(self, name: str, verbose: bool = False):
        self.name = name
        self.verbose = verbose
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.history: list[dict] = []

    # ── Claude API ─────────────────────────────────────────────────────

    def _call_claude(
        self,
        user_message: str,
        system_prompt: str,
        reset_history: bool = True,
    ) -> str:
        if reset_history:
            self.history = []
        self.history.append({"role": "user", "content": user_message})
        response = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS,
            system=system_prompt,
            messages=self.history,
        )
        text = response.content[0].text
        self.history.append({"role": "assistant", "content": text})
        return text

    def _call_claude_json(
        self,
        user_message: str,
        system_prompt: str,
    ) -> dict | list:
        raw = self._call_claude(
            user_message, system_prompt, reset_history=True
        )
        clean = raw.strip()
        if clean.startswith("```"):
            lines = clean.splitlines()
            clean = (
                "\n".join(lines[1:-1])
                if lines[-1].strip() == "```"
                else "\n".join(lines[1:])
            )
        return json.loads(clean)

    # ── Logging ────────────────────────────────────────────────────────

    def log(self, msg: str):
        if self.verbose:
            print(f"    [{self.name}] {msg}")

    def log_step(self, step: str, detail: str = ""):
        suffix = f": {detail}" if detail else ""
        print(f"  [{self.name}] ▶ {step}{suffix}")

    # ── Interface ──────────────────────────────────────────────────────

    @abstractmethod
    def run(self, context: dict) -> dict[str, Any]: ...
