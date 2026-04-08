from typing import Protocol
from games.registry import GameSpec

class BasePipeline(Protocol):
    def __init__(self, spec: GameSpec):
        self.spec = spec

    async def feedback(self, code, style, function_name, api_key):
        sig_error = self._validate_signature(code, function_name, style)
        if sig_error:
            return {"valid": False, "answer": sig_error, "thought": ""}
        return self._run_semantics(code, style, function_name, api_key)

    async def run(self, code, style, function_name, api_key):
        sig_error = self._validate_signature(code, function_name, style)
        if sig_error:
            return {"valid": False, "answer": sig_error, "thought": ""}
        return self._run_tests(code, style, function_name, api_key)

    async def validate(self, code, style, function_name, api_key):
        sig_error = self._validate_signature(code, function_name, style)
        if sig_error:
            return {"valid": False, "answer": sig_error, "thought": ""}
        return self._run_strict_tests(code, style, function_name, api_key)

    def _validate_signature(self, code, style, function_name) -> str: ...
    def _run_semantics(self, code, style, function_name, api_key) -> dict: ...
    def _run_tests(self, code, style, function_name, api_key) -> dict: ...
    def _run_strict_tests(self, code, style, function_name, api_key) -> dict: ...