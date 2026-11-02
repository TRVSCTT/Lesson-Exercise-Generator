"""Thin layer over the Anthropic API (easy to replace with a fake client in tests)."""
import os
from typing import Any, Protocol

from dotenv import find_dotenv, load_dotenv


class LLM(Protocol):
    def tool_call(self, system: str, user: str, tool_name: str, schema: dict, max_tokens: int = 6000) -> dict: ...


class AnthropicLLM:
    def __init__(self, model: str | None = None):
        import anthropic  # lazy import: tests don't need it
        # Reads a .env file from the current directory (or a parent). Variables already set in the
        # shell take priority over the file.
        load_dotenv(find_dotenv(usecwd=True))
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise SystemExit("ANTHROPIC_API_KEY is missing: set it in your shell or in a .env file (see .env.example).")
        self.client = anthropic.Anthropic()
        self.model = model or os.environ.get("LESSONFORGE_MODEL", "claude-sonnet-5-5")

    def tool_call(self, system, user, tool_name, schema, max_tokens=6000) -> dict[str, Any]:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            tools=[{"name": tool_name, "description": "Return the structured result.", "input_schema": schema}],
            tool_choice={"type": "tool", "name": tool_name},
        )
        if resp.stop_reason == "max_tokens":
            raise RuntimeError(f"The model's answer was cut off at {max_tokens} tokens; increase max_tokens.")
        for block in resp.content:
            if block.type == "tool_use":
                return block.input
        raise RuntimeError("The model returned no structured result.")