from typing import Protocol, Dict, Any
from ..gamespec import GameSpec

from .common_pipeline_code import _validate_signature, _run_semantics, _run_tests, _run_strict_tests

class BasePipeline(Protocol):
    def __init__(self, spec: GameSpec):
        self.spec = spec

    @classmethod    
    def from_dict(cls, data: Dict[str, Any]):
        return cls(data)

    async def feedback(self, code, assistant_style, function_name, openai_api_key, selected_game_spec):
        # sig_error = self._validate_signature(code, assistant_style, function_name)
        sig_error = _validate_signature(code, assistant_style, function_name, self.spec) # Novo parâmetro "spec" para acessar as regras de assinatura específicas do jogo
        if sig_error:
            return {"valid": False, "answer": sig_error, "thought": ""}
        # return self._run_semantics(code, assistant_style, function_name, openai_api_key)
        return _run_semantics(code, assistant_style, function_name, openai_api_key, selected_game_spec)
    async def run(self, code, assistant_style, function_name, openai_api_key, selected_game_spec):
        # sig_error = self._validate_signature(code, assistant_style, function_name)
        sig_error = _validate_signature(code, assistant_style, function_name, self.spec) # Novo parâmetro "spec" para acessar as regras de assinatura específicas do jogo
        # print(f"SIG_ERROR: {sig_error}")
        if sig_error:
            return {"valid": False, "answer": sig_error, "thought": ""}
        # return self._run_tests(code, assistant_style, function_name, openai_api_key)
        return _run_tests(code, assistant_style, function_name, openai_api_key, selected_game_spec) 
    async def validate(self, code, assistant_style, function_name, openai_api_key, selected_game_spec):
        # sig_error = self._validate_signature(code, assistant_style, function_name)
        sig_error = _validate_signature(code, assistant_style, function_name, self.spec) # Novo parâmetro "spec" para acessar as regras de assinatura específicas do jogo
        if sig_error:
            return {"valid": False, "answer": sig_error, "thought": ""}
        # return self._run_strict_tests(code, assistant_style, function_name, openai_api_key)
        return _run_strict_tests(code, assistant_style, function_name, openai_api_key, selected_game_spec)
    
    def _validate_signature(self, code, assistant_style, function_name) -> str: ...
    def _run_semantics(self, code, assistant_style, function_name, api_key) -> dict: ...
    def _run_tests(self, code, assistant_style, function_name, api_key) -> dict: ...
    def _run_strict_tests(self, code, assistant_style, function_name, api_key) -> dict: ...