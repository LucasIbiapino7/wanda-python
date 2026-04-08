import ast
from typing import Optional, Dict, Any
from ..base_pipeline import BasePipeline

# from ...validators.signature_validator import SignatureValidator
# from ...validators.semantics_validator import SemanticsValidator
# from ...validators.execution_validator import ExecutionValidator
from ...registry import GameSpec

def _normalize_style(style: str) -> str:
    s = (style or "").strip().upper()
    if s in ("VERBOSE", "SUCCINCT", "INTERMEDIATE", "INTERMEDIARY"):
        return "INTERMEDIATE" if s == "INTERMEDIARY" else s
    return "INTERMEDIATE"

class BitsPipeline(BasePipeline):
    def __init__(self, spec: GameSpec):
        self.spec = spec
        #self._signature = SignatureValidator()
        #self._semantics = SemanticsValidator()
        #self._execution = ExecutionValidator()
    
    def _parse_ast(self, code: str) -> Optional[ast.AST]:
        try:
            return ast.parse(code)
        except SyntaxError:
            return None
        
    def _validate_signature(self, code, style, function_name) -> str:
        style = _normalize_style(style)
        # 1) AST
        tree = self._parse_ast(code)
        if tree is None:
            return {
                "valid": False,
                "answer": "Erro de sintaxe: verifique indentação e vírgulas.",
                "thought": ""
            }
        
        """
        Validação de assinatura para o jogo BITS.
        Usa a assinatura do GameSpec (spec.signature["strategy"]) e exige a função 'strategy'
        com os parâmetros exatamente na ordem indicada.
        Retorna string vazia se estiver OK; caso contrário, retorna a mensagem de erro
        de acordo com o estilo escolhido.
        """
        # style = (style or "").strip().upper()
        # if style not in ("VERBOSE", "SUCCINCT", "INTERMEDIATE", "INTERMEDIARY"):
        #     style = "INTERMEDIATE"
        # if style == "INTERMEDIARY":
        #     style = "INTERMEDIATE"

         # Lê a assinatura esperada do GameSpec
        expected_args = self.spec.signature.get("strategy", [])
        expected_sig_str = ", ".join(expected_args)

        # Mensagens por estilo
        messages = {
            "VERBOSE": {
                "missing_function": (
                    "Ei! Não encontrei a função 'strategy' no seu código.\n"
                    f"Para o jogo BITS, ela deve existir assim:\n\n"
                    f"def strategy({expected_sig_str}):\n"
                    "    # seu código aqui\n\n"
                    "Verifique se o nome está correto e se a indentação não quebrou a definição."
                ),
                "wrong_signature": (
                    "Quase lá! Achei a função 'strategy', mas a assinatura não confere.\n"
                    f"Para o BITS, a ordem correta dos parâmetros é:\n"
                    f"({expected_sig_str}).\n"
                    "Ajuste a ordem/nome dos parâmetros para seguir exatamente essa lista."
                ),
            },
            "SUCCINCT": {
                "missing_function": (
                    "Função 'strategy' ausente. Use:\n"
                    f"def strategy({expected_sig_str}):"
                ),
                "wrong_signature": (
                    "Assinatura incorreta. Esperado:\n"
                    f"({expected_sig_str})."
                ),
            },
            "INTERMEDIATE": {
                "missing_function": (
                    "Não encontrei a função 'strategy'. Para o BITS, declare assim:\n"
                    f"def strategy({expected_sig_str}):"
                ),
                "wrong_signature": (
                    "A função 'strategy' existe, mas a assinatura esperada para o BITS é:\n"
                    f"({expected_sig_str})."
                ),
            },
        }
        style_msgs = messages[style]

        # Procura a função 'strategy'
        strategy_fn: Optional[ast.FunctionDef] = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "strategy":
                strategy_fn = node
                break
        
        if not strategy_fn:
            return style_msgs["missing_function"]
        
        # Compara parâmetros
        actual_args = [arg.arg for arg in strategy_fn.args.args]
        if actual_args != expected_args:
            return style_msgs["wrong_signature"]

        return ""  # OK
    
    # async def feedback(self, code: str, assistant_style: str,function_name: str, openai_api_key: str) -> Dict[str, Any]:
    #     style = _normalize_style(assistant_style)
    #     # 1) AST
    #     tree = self._parse_ast(code)
    #     if tree is None:
    #         return {
    #             "valid": False,
    #             "answer": "Erro de sintaxe: verifique indentação e vírgulas.",
    #             "thought": ""
    #         }
        
    #     # Assinatura
    #     sig_msg = self._signature.validate_bits_signature(tree=tree,assistant_style=style,spec=self.spec)
    #     if sig_msg:
    #         return {
    #             "valid": False,
    #             "answer": sig_msg,
    #             "thought": ""
    #         }
    #     sem_dict = self._semantics.validate_semantics_bits(
    #         code=code,
    #         tree=tree,
    #         assistantStyle=style,
    #         openai_api_key=openai_api_key,
    #         spec=self.spec
    #     )

    #     thought = str(sem_dict.get("pensamento", "")) if isinstance(sem_dict, dict) else ""
    #     answer = str(sem_dict.get("resposta", "")) if isinstance(sem_dict, dict) else ""

    #     return {
    #         "valid": True,
    #         "answer": answer,
    #         "thought": thought
    #     }
    
    # def _parse_ast(self, code: str) -> Optional[ast.AST]:
    #     try:
    #         return ast.parse(code)
    #     except SyntaxError:
    #         return None

    # async def run(self, code: str, assistant_style: str, function_name: str, openai_api_key: str) -> Dict[str, Any]:
    #     style = _normalize_style(assistant_style)
        
    #     tree = self._parse_ast(code)
    #     if tree is None:
    #         return {
    #             "valid": False,
    #             "answer": "Não consegui analisar a sua função por erro de sintaxe.",
    #             "thought": ""
    #         }

    #     # Assinatura
    #     sig_msg = self._signature.validate_bits_signature(tree=tree,assistant_style=style,spec=self.spec)
    #     if sig_msg:
    #         return {"valid": False, "answer": sig_msg, "thought": ""}

    #     # testes do jogo
    #     tests = self._execution.feedback_tests_bits(code=code, assistantStyle=style, openai_api_key=openai_api_key)

    #     thought = str(tests.get("pensamento", "")) if isinstance(tests, dict) else ""
    #     answer = str(tests.get("resposta", "")) if isinstance(tests, dict) else ""

    #     return {"valid": True, "answer": answer, "thought": thought}
    
    # async def validate(self, code: str, assistant_style: str, function_name: str, openai_api_key: str) -> Dict[str, Any]:
    #     style = _normalize_style(assistant_style)

    #     # 1) AST
    #     tree = self._parse_ast(code)
    #     if tree is None:
    #         return {
    #             "valid": False,
    #             "answer": "Não consegui analisar a sua função por erro de sintaxe.",
    #             "thought": ""
    #         }

    #     # 2) Assinatura específica do BITS
    #     sig_msg = self._signature.validate_bits_signature(tree=tree, assistant_style=style, spec=self.spec)
    #     if sig_msg:
    #         return {
    #             "valid": False,
    #             "answer": sig_msg,
    #             "thought": ""
    #         }

    #     # 3) Execução de testes 
    #     exec_result = self._execution.validator_bits(code=code, assistantStyle=style, openai_api_key=openai_api_key)

    #     # Se retornou dicionário = erro 
    #     if isinstance(exec_result, dict) and (
    #         "pensamento" in exec_result or "resposta" in exec_result
    #     ):
    #         return {
    #             "valid": False,
    #             "answer": str(exec_result.get("resposta", "")),
    #             "thought": str(exec_result.get("pensamento", ""))
    #         }

    #     # 4) Se passou em tudo = aceito
    #     return {
    #         "valid": True,
    #         "answer": "aceita",
    #         "thought": ""
    #     }
    
