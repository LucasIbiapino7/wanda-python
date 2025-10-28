import ast
from typing import Optional, Dict, Any

from ...validators.signature_validator import SignatureValidator
from ...validators.semantics_validator import SemanticsValidator
from ..registry import GameSpec

def _normalize_style(style: str) -> str:
    s = (style or "").strip().upper()
    if s in ("VERBOSE", "SUCCINCT", "INTERMEDIATE", "INTERMEDIARY"):
        return "INTERMEDIATE" if s == "INTERMEDIARY" else s
    return "INTERMEDIATE"

class BitsPipeline:
    def __init__(self, spec: GameSpec):
        self.spec = spec
        self._signature = SignatureValidator()
        self._semantics = SemanticsValidator()
    
    def _parse_ast(self, code: str) -> Optional[ast.AST]:
        try:
            return ast.parse(code)
        except SyntaxError:
            return None
    
    async def feedback(self, code: str, assistant_style: str,function_name: str, openai_api_key: str) -> Dict[str, Any]:
        style = _normalize_style(assistant_style)
        # 1) AST
        tree = self._parse_ast(code)
        if tree is None:
            return {
                "valid": False,
                "answer": "Erro de sintaxe: verifique indentação e vírgulas.",
                "thought": ""
            }
        
        # Assinatura
        sig_msg = self._signature.validate_bits_signature(tree=tree,assistant_style=style,spec=self.spec)
        if sig_msg:
            return {
                "valid": False,
                "answer": sig_msg,
                "thought": ""
            }
        sem_dict = self._semantics.validate_semantics_bits(
            code=code,
            tree=tree,
            assistantStyle=style,
            openai_api_key=openai_api_key,
            spec=self.spec
        )

        thought = str(sem_dict.get("pensamento", "")) if isinstance(sem_dict, dict) else ""
        answer = str(sem_dict.get("resposta", "")) if isinstance(sem_dict, dict) else ""

        return {
            "valid": True,
            "answer": answer,
            "thought": thought
        }

