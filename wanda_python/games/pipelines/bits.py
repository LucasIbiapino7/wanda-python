import ast
from typing import Optional, Dict, Any

from ...validators.signature_validator import SignatureValidator
from ...validators.semantics_validator import SemanticsValidator
from ...validators.execution_validator import ExecutionValidator
from ..registry import GameSpec
from ...runner.container_runner import run_submit, run_tests

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
        self._execution = ExecutionValidator()
    
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
    
    def _parse_ast(self, code: str) -> Optional[ast.AST]:
        try:
            return ast.parse(code)
        except SyntaxError:
            return None

    async def run(self, code: str, assistant_style: str, function_name: str, openai_api_key: str) -> Dict[str, Any]:
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
        sig_msg = self._signature.validate_bits_signature(tree=tree, assistant_style=style, spec=self.spec)
        if sig_msg:
            return {"valid": False, "answer": sig_msg, "thought": ""}

        # 3) Execução de testes via container
        test_cases = [
            [1, 1, 1, 1, None],
            [1, 0, 1, 0, "BIT32"],
            [0, 1, 1, 1, "BIT16"],
            [1, 1, 0, 1, "FIREWALL"],
            [0, 1, 0, 1, "BIT8"],
            [1, 0, 0, 1, "BIT16"],
            [0, 0, 1, 0, "BIT32"],
            [1, 1, 0, 0, "BIT8"],
            [0, 0, 0, 1, None],
            [0, 1, 0, 0, "BIT32"],
        ]
        valid_returns = ["BIT8", "BIT16", "BIT32", "FIREWALL"]

        result = run_tests(code=code, test_cases=test_cases, valid_returns=valid_returns)

        if result["timed_out"]:
            return {
                "valid": False,
                "answer": "Sua função demorou demais para executar. Verifique se há loops infinitos.",
                "thought": ""
            }

        if not result["ok"]:
            error_dict = self._execution.error_execution(
                code=code, erro=result["stderr"],
                openai_api_key=openai_api_key, assistantStyle=style
            )
            return {
                "valid": False,
                "answer": str(error_dict.get("resposta", "")),
                "thought": str(error_dict.get("pensamento", ""))
            }

        # verifica se algum caso teve erro de execução
        first_error = next((r for r in result["results"] if not r["valid"]), None)
        if first_error:
            error_dict = self._execution.error_execution(
                code=code, erro=first_error.get("error", "Erro de execução"),
                openai_api_key=openai_api_key, assistantStyle=style
            )
            return {
                "valid": False,
                "answer": str(error_dict.get("resposta", "")),
                "thought": str(error_dict.get("pensamento", ""))
            }

        # 4) passa os resultados pro prompt
        tests = self._execution.feedback_outputs_tests_bits(
            result["results"], openai_api_key, style
        )

        thought = str(tests.get("pensamento", "")) if isinstance(tests, dict) else ""
        answer = str(tests.get("resposta", "")) if isinstance(tests, dict) else ""

        return {"valid": True, "answer": answer, "thought": thought}
    
    async def validate(self, code: str, assistant_style: str, function_name: str, openai_api_key: str) -> Dict[str, Any]:
        style = _normalize_style(assistant_style)

        # 1) AST
        tree = self._parse_ast(code)
        if tree is None:
            return {
                "valid": False,
                "answer": "Não consegui analisar a sua função por erro de sintaxe.",
                "thought": ""
            }

        # 2) Assinatura específica do BITS
        sig_msg = self._signature.validate_bits_signature(tree=tree, assistant_style=style, spec=self.spec)
        if sig_msg:
            return {
                "valid": False,
                "answer": sig_msg,
                "thought": ""
            }

        # 3) Execução de testes via container
        test_cases = [
            [1, 1, 1, 1, None],
            [1, 0, 1, 0, "BIT32"],
            [0, 1, 1, 1, "BIT16"],
            [1, 1, 0, 1, "FIREWALL"],
            [0, 1, 0, 1, "BIT8"],
            [1, 0, 0, 1, "BIT16"],
            [0, 0, 1, 0, "BIT32"],
            [1, 1, 0, 0, "BIT8"],
            [0, 0, 0, 1, None],
            [0, 1, 0, 0, "BIT32"],
        ]

        result = run_submit(code=code, test_cases=test_cases)

        # timeout — mensagem fixa, sem OpenAI
        if result["timed_out"]:
            return {
                "valid": False,
                "answer": "Sua função demorou demais para executar. Verifique se há loops infinitos.",
                "thought": ""
            }

        # erro de execução — passa pro OpenAI explicar
        if not result["ok"]:
            error_dict = self._execution.error_execution(
                code=code,
                erro=result["stderr"],
                openai_api_key=openai_api_key,
                assistantStyle=style
            )
            return {
                "valid": False,
                "answer": str(error_dict.get("resposta", "")),
                "thought": str(error_dict.get("pensamento", ""))
            }

        # 4) Se passou em tudo = aceito
        return {
            "valid": True,
            "answer": "aceita",
            "thought": ""
        }

    
