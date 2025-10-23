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


class JokenpoFeedbackPipeline:
    """
    Pipeline específico do jogo Jokenpo:
      1) valida assinatura (usando seu SignatureValidator)
      2) valida semântica (usando seu SemanticsValidator)
    Retorna sempre um dict padronizado:
      { "valid": bool, "answer": str, "thought": str }
    """

    def __init__(self, spec: GameSpec):
        self.spec = spec
        self._signature = SignatureValidator()
        self._semantics = SemanticsValidator()

    def _parse_ast(self, code: str) -> Optional[ast.AST]:
        try:
            return ast.parse(code)
        except SyntaxError:
            # Teoricamente nao cai aqui, apenas prevenção 
            return None

    async def run(
        self,
        code: str,
        assistant_style: str,
        function_name: str,#"jokenpo1" |"jokenpo2"
        openai_api_key: str
    ) -> Dict[str, Any]:

        style = _normalize_style(assistant_style)

        # 1) AST (assinatura e semântica precisam percorrer a árvore)
        tree = self._parse_ast(code)
        if tree is None:
            return {
                "valid": False,
                "answer": "Não consegui analisar a sua função por erro de sintaxe. Corrija a sintaxe e tente novamente.",
                "thought": ""
            }

        # 2) Assinatura — usa seu validador atual
        sig_msg = self._signature.validate_signature_and_parameters(
            tree=tree,
            assistant_style=style,
            function_type=function_name
        )

        if sig_msg:
            return {
                "valid": False,
                "answer": sig_msg,
                "thought": ""
            }

        sem_dict = self._semantics.validator(
            code=code,
            tree=tree,
            assistantStyle=style,
            openai_api_key=openai_api_key,
            functionType=function_name
        )

        thought = str(sem_dict.get("pensamento", "")) if isinstance(sem_dict, dict) else ""
        answer = str(sem_dict.get("resposta", "")) if isinstance(sem_dict, dict) else ""

        return {
            "valid": True,
            "answer": answer,
            "thought": thought
        }
