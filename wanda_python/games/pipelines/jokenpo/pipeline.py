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

from .tests import TESTS_JOKENPO1, TESTS_JOKENPO2

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
            # print("EXCECAO")
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR)
            logger.error("Erro na chamada OpenAI", exc_info=True)
            return {"pensamento": "", "resposta": ""}


class JokenpoPipeline(BasePipeline):
    """
    Pipeline única do Jokenpo contendo:
      - feedback(...): assinatura -> semântica (seu fluxo atual)
      - run(...):      assinatura -> execução de testes
    """

    def __init__(self, spec: GameSpec):
        self.spec = spec
        #self._signature = SignatureValidator()
        #self._semantics = SemanticsValidator()
        #self._execution = ExecutionValidator()

    def _execute_strict(self, code: str, TESTS, assistantStyle: str) -> dict:
        local_env = {}
        try:
            exec(code, {}, local_env)
        except Exception as err:
            return prompt_error_execution(code, err, assistantStyle)

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
                return prompt_error_execution(code, err, assistantStyle)

        return ""

    def _execute(self, code, TESTS, assistantStyle):
        test_inputs = TESTS

        results = []
        local_env = {}
        try:
            exec(code, {}, local_env)
        except Exception as err:
            # print(f"Erro ao executar código: {err}")
            error_prompt = prompt_error_execution(code, err, assistantStyle)
            #err_message = ask_openai(prompt, api_key)
            #print(err_message)
            return error_prompt

        strategy_fn = local_env.get("strategy")
        if not strategy_fn:
            err_prompt = {"pensamento": "", "resposta": "Função 'strategy' não encontrada"} # ask_openai({"pensamento": "", "resposta": "Função 'strategy' não encontrada"}, api_key)
            # print(err_message)
            return err_prompt
            

        for test_case in test_inputs:
            try:
                output = strategy_fn(*test_case)
                if output in ("pedra", "papel", "tesoura"):
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
                error_prompt = prompt_error_execution(code, err, assistantStyle)
                # err_message = ask_openai(prompt, api_key)
                # print(err_message)
                return error_prompt
            
        return results

        # return self.feedback_outputs_tests_bits(results, openai_api_key, assistantStyle)

    def _parse_ast(self, code: str) -> Optional[ast.AST]:
        try:
            return ast.parse(code)
        except SyntaxError:
            # Teoricamente nao cai aqui, apenas prevenção 
            return None
        
    def _validate_signature(self, code, style, function_name) -> str:
        style = _normalize_style(style)
        # 1) AST
        tree = self._parse_ast(code)
        #print(f"AST: {tree}")
        if tree is None:
            return {
                "valid": False,
                "answer": "Erro de sintaxe: verifique indentação e vírgulas.",
                "thought": ""
            }
        
        # style = (style or "").strip().upper()
        # if style not in ("VERBOSE", "SUCCINCT", "INTERMEDIATE", "INTERMEDIARY"):
        #     style = "INTERMEDIATE"
        # if style == "INTERMEDIARY":
        #     style = "INTERMEDIATE"

        # Lê a assinatura esperada do GameSpec
        # print(f"FUNCTION NAME: {function_name}")
        # print(f"ESPEC: {self.spec.signature}")
        expected_args = self.spec.signature.get(function_name, {}).get("strategy", [])
        expected_sig_str = ", ".join(expected_args)
        # print(f"Expected args: {self.spec.signature.get(function_name, {})}")
        # print(f"Expected signature string: {expected_sig_str}")

        # Define mensagens distintas para cada tipo de função
        messages = {
            "jokenpo1": {
                "VERBOSE": {
                    "missing_function": (
                        "Olá! Sabe, estou olhando seu código e não consegui achar a função 'strategy'.\n"
                        "Ela precisa estar assim:\n"
                        "def strategy(card1, card2, card3):\n"
                        "    # Seu código\n"
                        "Verifique se o nome está correto e se não houve problemas de indentação! Estou aqui pra ajudar."
                    ),
                    "wrong_signature": (
                        "Ei! Parece que a sua função 'strategy' não tem os parâmetros na ordem esperada.\n"
                        "Devem ser: card1, card2, card3.\n"
                        "Dê uma olhada e certifique-se de que eles estejam no lugar certinho, tá bom?"
                    )
                },
                "SUCCINCT": {
                    "missing_function": (
                        "Função 'strategy' não encontrada. Ela deve ser:\n"
                        "def strategy(card1, card2, card3):"
                    ),
                    "wrong_signature": (
                        "A função 'strategy' existe, mas os parâmetros não batem.\n"
                        "Use: card1, card2, card3."
                    )
                },
                "INTERMEDIATE": {
                    "missing_function": (
                        "Não achei a função 'strategy' no seu código. Ela precisa estar declarada como:\n"
                        "def strategy(card1, card2, card3):\n"
                        "Verifique o nome e a indentação para garantir que esteja certo, ok?"
                    ),
                    "wrong_signature": (
                        "A função 'strategy' foi encontrada, mas os parâmetros não estão corretos.\n"
                        "Eles devem ser: card1, card2, card3.\n"
                        "Dê uma revisada pra garantir que estejam nessa ordem."
                    )
                }
            },
            "jokenpo2": {
                "VERBOSE": {
                    "missing_function": (
                        "Olá! Sabe, estou olhando seu código e não consegui achar a função 'strategy'.\n"
                        "Ela precisa estar assim:\n"
                        "def strategy(card1, card2, opponentCard1, opponentCard2):\n"
                        "    # Seu código\n"
                        "Verifique se o nome está correto e se não houve problemas de indentação! Estou aqui pra ajudar."
                    ),
                    "wrong_signature": (
                        "Ei! Parece que a sua função 'strategy' não tem os parâmetros na ordem esperada.\n"
                        "Devem ser: card1, card2, opponentCard1, opponentCard2.\n"
                        "Dê uma olhada e certifique-se de que eles estejam no lugar certinho, tá bom?"
                    )
                },
                "SUCCINCT": {
                    "missing_function": (
                        "Função 'strategy' não encontrada. Ela deve ser:\n"
                        "def strategy(card1, card2, opponentCard1, opponentCard2):"
                    ),
                    "wrong_signature": (
                        "A função 'strategy' existe, mas os parâmetros não batem.\n"
                        "Use: card1, card2, opponentCard1, opponentCard2."
                    )
                },
                "INTERMEDIATE": {
                    "missing_function": (
                        "Não achei a função 'strategy' no seu código. Ela precisa estar declarada como:\n"
                        "def strategy(card1, card2, opponentCard1, opponentCard2):\n"
                        "Verifique o nome e a indentação para garantir que esteja certo, ok?"
                    ),
                    "wrong_signature": (
                        "A função 'strategy' foi encontrada, mas os parâmetros não estão corretos.\n"
                        "Eles devem ser: card1, card2, opponentCard1, opponentCard2.\n"
                        "Dê uma revisada pra garantir que estejam nessa ordem."
                    )
                }
            }
        }

        # Seleciona o conjunto de mensagens baseado no tipo da função (jokenpo1 ou jokenpo2)
        style_dict = messages.get(function_name, messages["jokenpo1"]).get(style, messages["jokenpo1"]["SUCCINCT"])

        # Verifica a presença da função 'strategy'
        strategy_function = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "strategy":
                strategy_function = node
                break

        if not strategy_function:
            return style_dict["missing_function"]

        # Define a lista de parâmetros esperados com base no tipo de função
        if function_name == "jokenpo1":
            expected_args = ["card1", "card2", "card3"]
        elif function_name == "jokenpo2":
            expected_args = ["card1", "card2", "opponentCard1", "opponentCard2"]
        else:
            # Valor padrão, se não for reconhecido, pode-se assumir o jokenpo1
            expected_args = ["card1", "card2", "card3"]

        actual_args = [arg.arg for arg in strategy_function.args.args]
        if actual_args != expected_args:
            return style_dict["wrong_signature"]

        return ""  # Sem erros
    
    def _run_semantics(self, code, style, function_name, api_key):
        tree = self._parse_ast(code)
        prompt = prompt_semantics(code=code, tree=tree, assistant_style=style, function_name=function_name, spec=self.spec)

        ret = ask_openai(prompt, api_key)
        thought = str(ret.get("pensamento", "")) if isinstance(ret, dict) else ""
        answer = str(ret.get("resposta", "")) if isinstance(ret, dict) else ""

        return {"valid": True, "answer": answer, "thought": thought}
    
    def _run_tests(self, code, style, function_name, api_key):
        #print("CHEGOU AQ")
        if function_name == "jokenpo1":
            TESTS = TESTS_JOKENPO1
        elif function_name == "jokenpo2":
            TESTS = TESTS_JOKENPO2

        results = self._execute(code, TESTS, style)
        # print(f"RESULTADOS DOS TESTES: {results}")

        # Se results for uma lista, significa que a execução ocorreu e temos outputs dos testes para analisar.
        if isinstance(results, list):
            prompt = prompt_run_results(results, self.spec.name, self.spec.valid_returns[function_name], assistant_style=style)
            ret = ask_openai(prompt, api_key)
            valid = True
        else: # Se results não for uma lista, significa que ocorreu um erro na execução e o resultado é um prompt de erro a ser enviado para o OpenAI.
            ret = ask_openai(results, api_key)
            valid = False

        # print(f"RETORNO DO OPENAI APÓS TESTES: {ret}")

        # print(results)
        thought = str(ret.get("pensamento", "")) if isinstance(ret, dict) else ""
        answer = str(ret.get("resposta", "")) if isinstance(ret, dict) else ""
        # print(answer)
        return {"valid": valid, "answer": answer, "thought": thought}

    def _run_strict_tests(self, code, style, function_name, api_key):
        if function_name == "jokenpo1":
            TESTS = TESTS_JOKENPO1
        elif function_name == "jokenpo2":
            TESTS = TESTS_JOKENPO2

        error_prompt = self._execute_strict(code, TESTS, style)
        
        if error_prompt:
            ret = ask_openai(error_prompt, api_key)

            thought = str(ret.get("pensamento", "")) if isinstance(ret, dict) else ""
            answer = str(ret.get("resposta", "")) if isinstance(ret, dict) else ""

            return {"valid": False, "answer": answer, "thought": thought}

        return {"valid": True, "answer": "aceita", "thought": ""}

    # async def feedback(
    #     self,
    #     code: str,
    #     assistant_style: str,
    #     function_name: str,#"jokenpo1" |"jokenpo2"
    #     openai_api_key: str
    # ) -> Dict[str, Any]:

    #     style = _normalize_style(assistant_style)

    #     # 1) AST (assinatura e semântica precisam percorrer a árvore)
    #     tree = self._parse_ast(code)
    #     if tree is None:
    #         return {
    #             "valid": False,
    #             "answer": "Não consegui analisar a sua função por erro de sintaxe. Corrija a sintaxe e tente novamente.",
    #             "thought": ""
    #         }

    #     # 2) Assinatura
    #     sig_msg = self._signature.validate_signature_and_parameters(
    #         tree=tree,
    #         assistant_style=style,
    #         function_type=function_name
    #     )

    #     if sig_msg:
    #         return {
    #             "valid": False,
    #             "answer": sig_msg,
    #             "thought": ""
    #         }

    #     sem_dict = self._semantics.validator(
    #         code=code,
    #         tree=tree,
    #         assistantStyle=style,
    #         openai_api_key=openai_api_key,
    #         functionType=function_name
    #     )

    #     thought = str(sem_dict.get("pensamento", "")) if isinstance(sem_dict, dict) else ""
    #     answer = str(sem_dict.get("resposta", "")) if isinstance(sem_dict, dict) else ""

    #     return {
    #         "valid": True,
    #         "answer": answer,
    #         "thought": thought
    #     }
    

    # #RUN 
    # async def run(self,code: str,assistant_style: str,function_name: str, openai_api_key: str) -> Dict[str, Any]:

    #     style = _normalize_style(assistant_style)

    #     # 1) AST para assinatura
    #     tree = self._parse_ast(code)
    #     if tree is None:
    #         return {
    #             "valid": False,
    #             "answer": "Não consegui analisar a sua função por erro de sintaxe. Corrija a sintaxe e tente novamente.",
    #             "thought": ""
    #         }

    #     # 2) Assinatura
    #     sig_msg = self._signature.validate_signature_and_parameters(tree=tree,assistant_style=style,function_type=function_name)
    #     if sig_msg:
    #         return { "valid": False, "answer": sig_msg, "thought": "" }

    #     tests = self._execution.feedback_tests(code=code,assistantStyle=style, function_type=function_name,openai_api_key=openai_api_key )

    #     thought = str(tests.get("pensamento", "")) if isinstance(tests, dict) else ""
    #     answer = str(tests.get("resposta", "")) if isinstance(tests, dict) else ""

    #     return { "valid": True, "answer": answer, "thought": thought }

    # async def validate(self,code: str,assistant_style: str,function_name: str,openai_api_key: str) -> Dict[str, Any]:
    #     style = _normalize_style(assistant_style)
    #     # 1) AST
    #     tree = self._parse_ast(code)
    #     if tree is None:
    #         return {
    #             "valid": False,
    #             "answer": "Não consegui analisar a sua função por erro de sintaxe.",
    #             "thought": ""
    #         }

    #     # 2) Assinatura 
    #     sig_msg = self._signature.validate_signature_and_parameters(tree=tree, assistant_style=style,function_type=function_name
    #     )
    #     if sig_msg:
    #         return {"valid": False, "answer": sig_msg, "thought": ""}

    #     # 3) Execução de testes
    #     exec_result = self._execution.validator(code=code,assistantStyle=style,function_type=function_name,openai_api_key=openai_api_key)

    #     if isinstance(exec_result, dict) and ("pensamento" in exec_result or "resposta" in exec_result):
    #         return {
    #             "valid": False,
    #             "answer": str(exec_result.get("resposta", "")),
    #             "thought": str(exec_result.get("pensamento", ""))
    #         }

    #     return {"valid": True, "answer": "aceita", "thought": ""}