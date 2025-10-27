import ast
from typing import Optional, Dict, Any

from ...validators.signature_validator import SignatureValidator
from ...validators.semantics_validator import SemanticsValidator
from ...validators.execution_validator import ExecutionValidator

from ..registry import GameSpec

def _normalize_style(style: str) -> str:
    s = (style or "").strip().upper()
    if s in ("VERBOSE", "SUCCINCT", "INTERMEDIATE", "INTERMEDIARY"):
        return "INTERMEDIATE" if s == "INTERMEDIARY" else s
    return "INTERMEDIATE"


class JokenpoPipeline:
    """
    Pipeline única do Jokenpo contendo:
      - feedback(...): assinatura -> semântica (seu fluxo atual)
      - run(...):      assinatura -> execução de testes
    """

    def __init__(self, spec: GameSpec):
        self.spec = spec
        self._signature = SignatureValidator()
        self._semantics = SemanticsValidator()
        self._execution = ExecutionValidator()

    def _parse_ast(self, code: str) -> Optional[ast.AST]:
        try:
            return ast.parse(code)
        except SyntaxError:
            # Teoricamente nao cai aqui, apenas prevenção 
            return None

    async def feedback(
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
    

    #RUN 
    async def run(self,code: str,assistant_style: str,function_name: str, openai_api_key: str) -> Dict[str, Any]:

        style = _normalize_style(assistant_style)

        # 1) AST para assinatura
        tree = self._parse_ast(code)
        if tree is None:
            return {
                "valid": False,
                "answer": "Não consegui analisar a sua função por erro de sintaxe. Corrija a sintaxe e tente novamente.",
                "thought": ""
            }

        # 2) Assinatura
        sig_msg = self._signature.validate_signature_and_parameters(tree=tree,assistant_style=style,function_type=function_name)
        if sig_msg:
            return { "valid": False, "answer": sig_msg, "thought": "" }

        tests = self._execution.feedback_tests(code=code,assistantStyle=style, function_type=function_name,openai_api_key=openai_api_key )

        thought = str(tests.get("pensamento", "")) if isinstance(tests, dict) else ""
        answer = str(tests.get("resposta", "")) if isinstance(tests, dict) else ""

        return { "valid": True, "answer": answer, "thought": thought }

    async def validate(self,code: str,assistant_style: str,function_name: str,openai_api_key: str) -> Dict[str, Any]:
        style = _normalize_style(assistant_style)
        # 1) AST
        tree = self._parse_ast(code)
        if tree is None:
            return {
                "valid": False,
                "answer": "Não consegui analisar a sua função por erro de sintaxe.",
                "thought": ""
            }

        # 2) Assinatura 
        sig_msg = self._signature.validate_signature_and_parameters(tree=tree, assistant_style=style,function_type=function_name
        )
        if sig_msg:
            return {"valid": False, "answer": sig_msg, "thought": ""}

        # 3) Execução de testes
        exec_result = self._execution.validator(code=code,assistantStyle=style,function_type=function_name,openai_api_key=openai_api_key)

        if isinstance(exec_result, dict) and ("pensamento" in exec_result or "resposta" in exec_result):
            return {
                "valid": False,
                "answer": str(exec_result.get("resposta", "")),
                "thought": str(exec_result.get("pensamento", ""))
            }

        return {"valid": True, "answer": "aceita", "thought": ""}