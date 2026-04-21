import ast
from typing import Optional, Dict, Any
from ..base_pipeline import BasePipeline
from .prompts import prompt_semantics

import openai
import ast
import json
from openai import OpenAIError
from opentelemetry import trace
import logging

from tests import TESTS_BITS

from ...prompts.shared import prompt_error_execution, prompt_run_results

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

# from ...validators.signature_validator import SignatureValidator
# from ...validators.semantics_validator import SemanticsValidator
# from ...validators.execution_validator import ExecutionValidator
from ...registry import GameSpec

def _normalize_style(style: str) -> str:
    s = (style or "").strip().upper()
    if s in ("VERBOSE", "SUCCINCT", "INTERMEDIATE", "INTERMEDIARY"):
        return "INTERMEDIATE" if s == "INTERMEDIARY" else s
    return "INTERMEDIATE"

def ask_openai(prompt: str, api_key: str) -> dict:
    with tracer.start_as_current_span("openai.chat") as span:
        span.set_attribute("openai.model", "gpt-4o-mini")
        span.set_attribute("openai.prompt_length", len(prompt))

        client = openai.OpenAI(api_key=api_key)

        system_msg = {
            "role": "system",
            "content": (
                'Responda EXCLUSIVAMENTE com um objeto JSON contendo '
                'as chaves "pensamento" e "resposta". Nada fora das chaves.'
            )
        }

        try:
            answer = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[system_msg, {"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=300,
            )

            span.set_attribute("openai.tokens_total", answer.usage.total_tokens)
            span.set_attribute("openai.tokens_prompt", answer.usage.prompt_tokens)
            span.set_attribute("openai.tokens_completion", answer.usage.completion_tokens)

            return json.loads(answer.choices[0].message.content)

        except OpenAIError as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR)
            logger.error("Erro na chamada OpenAI", exc_info=True)
            return {"pensamento": "", "resposta": ""}

class BitsPipeline(BasePipeline):
    def __init__(self, spec: GameSpec):
        self.spec = spec
        #self._signature = SignatureValidator()
        #self._semantics = SemanticsValidator()
        #self._execution = ExecutionValidator()

    def _execute_strict(self, code: str, TESTS, assistantStyle: str, api_key: str) -> dict:
        local_env = {}
        try:
            exec(code, {}, local_env)
        except Exception as err:
            return prompt_error_execution(code, err, api_key, assistantStyle)

        strategy_fn = local_env.get("strategy")
        if not strategy_fn:
            return {
                "pensamento": "",
                "resposta": "Função 'strategy' não encontrada no seu código. "
                            "Verifique o nome da função e tente novamente."
            }

        test_inputs = TESTS

        for test_case in test_inputs:
            try:
                _ = strategy_fn(*test_case)
            except Exception as err:
                return prompt_error_execution(code, err, api_key, assistantStyle)

        return ""

    def _execute(self, code, TESTS, api_key, assistantStyle):
        test_inputs = TESTS

        results = []
        local_env = {}
        try:
            exec(code, {}, local_env)
        except Exception as err:
            prompt = prompt_error_execution(code, err, assistantStyle)
            err_message = ask_openai(prompt, api_key)
            print(err_message)
            return []

        strategy_fn = local_env.get("strategy")
        if not strategy_fn:
            err_message = ask_openai({"pensamento": "", "resposta": "Função 'strategy' não encontrada"}, api_key)
            print(err_message)
            return []
            

        for test_case in test_inputs:
            try:
                output = strategy_fn(*test_case)
                if output in ("BIT8", "BIT16", "BIT32", "FIREWALL"):
                    results.append({
                        "output": output,
                        "valid": True,
                        "gameValid": True
                })
                else:
                    results.append({
                        "output": output,
                        "valid": True,
                        "gameValid": False,
                        "fallback": "NEXT_AVAILABLE_CARD",
                        "note": (
                            "Retorno fora do esperado. O jogo ignora esse valor e "
                            "usa a próxima carta disponível na mão do jogador."
                        )
                    })
            except Exception as err:
                prompt = prompt_error_execution(code, err, assistantStyle)
                err_message = ask_openai(prompt, api_key)
                print(err_message)
                return []
            
        return results

        # return self.feedback_outputs_tests_bits(results, openai_api_key, assistantStyle)
    
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
    
    def _run_semantics(self, code, style, function_name, api_key):
        prompt = prompt_semantics(code=code, assistant_style=style, openai_api_key=api_key, spec=self.spec)
        return ask_openai(prompt, api_key)
    
    def _run_tests(self, code, style, function_name, api_key):
        results = self._execute(code, TESTS_BITS, api_key, style)
        prompt = prompt_run_results(results, self.spec.name, self.spec.valid_returns["strategy"], assistant_style=style)

        return ask_openai(prompt, api_key)

    def _run_strict_tests(self, code, style, function_name, api_key):
        error_prompt = self._execute_strict(code, TESTS_BITS, style, api_key)
        if error_prompt:
            return ask_openai(error_prompt, api_key)

        return {"valid": True, "answer": "aceita", "thought": ""}
    
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
    
