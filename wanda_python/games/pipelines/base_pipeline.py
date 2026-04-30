from typing import Protocol
from ..gamespec import GameSpec

class BasePipeline(Protocol):
    def __init__(self, spec: GameSpec):
        self.spec = spec

    async def feedback(self, code, assistant_style, function_name, openai_api_key):
        sig_error = self._validate_signature(code, function_name, assistant_style)
        if sig_error:
            return {"valid": False, "answer": sig_error, "thought": ""}
        return self._run_semantics(code, assistant_style, function_name, openai_api_key)
    async def run(self, code, assistant_style, function_name, openai_api_key):
        sig_error = self._validate_signature(code, function_name, assistant_style)
        # print(f"SIG_ERROR: {sig_error}")
        if sig_error:
            return {"valid": False, "answer": sig_error, "thought": ""}
        return self._run_tests(code, assistant_style, function_name, openai_api_key)
    async def validate(self, code, assistant_style, function_name, openai_api_key):
        sig_error = self._validate_signature(code, function_name, assistant_style)
        if sig_error:
            return {"valid": False, "answer": sig_error, "thought": ""}
        return self._run_strict_tests(code, assistant_style, function_name, openai_api_key)
    def _validate_signature(self, code, assistant_style, function_name) -> str: ...
    def _run_semantics(self, code, assistant_style, function_name, api_key) -> dict: ...
    def _run_tests(self, code, assistant_style, function_name, api_key) -> dict: ...
    def _run_strict_tests(self, code, assistant_style, function_name, api_key) -> dict: ...