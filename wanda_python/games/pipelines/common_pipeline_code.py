import ast
from typing import Optional, Dict, Any, Iterable, Set
from ..prompts.shared import prompt_error_execution, prompt_run_results
from ..registry import GameSpec

from ...runner.container_runner import run_tests as runner_run_tests
from ...runner.container_runner import run_submit as runner_run_submit

import openai
import ast
import json
from openai import OpenAIError
from opentelemetry import trace
import logging

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

def prompt_semantics(code: str,tree: ast.AST,assistant_style: str, function_name: str, spec: GameSpec) -> str:
    """
    Validação semântica para o jogo BITS.
    - Pega a assinatura e retornos válidos do GameSpec.
    - Analisa quais parâmetros da assinatura foram realmente utilizados.
    - Monta um prompt (placeholders prontos para você ajustar depois).
    """
    # Assinatura esperada e retornos válidos vindos do spec
    expected_args = spec.get("signature", {}).get(function_name, {}).get("strategy", [])

    used_params = _extract_used_params(tree, expected_args)

    prompt_text = spec.get("prompts", {}).get(function_name, {}).get(assistant_style.lower(), "")

    formatted_prompt = prompt_text.format(code=code, used_params=used_params)

    return formatted_prompt # prompts[assistant_style]["prompt"]

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

def _execute_strict(code: str, TESTS, assistantStyle: str) -> dict:
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

# Novo parâmetro "outputs" --> ("pedra", "papel", "tesoura") se JOKENPO; ("BIT8", "BIT16", "BIT32", "FIREWALL") se BITS
def _execute(code, TESTS, assistantStyle, outputs):
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
                if output in outputs:
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

def _parse_ast(code: str) -> Optional[ast.AST]:
        try:
            return ast.parse(code)
        except SyntaxError:
            return None
        
# Novo parâmetro "selected_game_spec" para acessar a spec correta de cada jogo
def _validate_signature(code, style, function_name, selected_game_spec: Dict[str, Any]) -> str:
        style = _normalize_style(style)
        # 1) AST
        tree = _parse_ast(code)
        #print(f"AST: {tree}")
        if tree is None:
            return {
                "valid": False,
                "answer": "Erro de sintaxe: verifique indentação e vírgulas.",
                "thought": ""
            }

        # Lê a assinatura esperada do GameSpec
        expected_args = selected_game_spec.get("signature", {}).get(function_name, {}).get("strategy", [])
        expected_sig_str = ", ".join(expected_args)
        # print(f"Expected signature string: {expected_sig_str}")

        # Mensagens por estilo --> São diferentes para cada tipo de jogo (até o momento)
        # messages = select_signature_error_message(expected_sig_str, function_name)
        messages = selected_game_spec.get("error_messages", {}).get(function_name, {})
        # print(f"Mensagens {messages}")
        style_msgs = messages[style.lower()]

        # Procura a função 'strategy'
        strategy_fn: Optional[ast.FunctionDef] = None
        for node in ast.walk(tree):
            #if isinstance(node, ast.FunctionDef):
            #    print(f"AST Node name: {node.name}")
            if isinstance(node, ast.FunctionDef) and node.name == "strategy":
                # print(f"AST Node name: {node.name}")
                strategy_fn = node
                break
        
        if not strategy_fn:
            return style_msgs["missing_function"].format(expected_sig_str=expected_sig_str)
        
        # Compara parâmetros
        actual_args = [arg.arg for arg in strategy_fn.args.args]
        if actual_args != expected_args:
            return style_msgs["wrong_signature"].format(expected_sig_str=expected_sig_str)

        return ""  # OK

def _extract_used_params(tree: ast.AST, expected: Iterable[str]) -> Set[str]:
    """
    Extrai o conjunto de parâmetros (por nome) realmente usados dentro da função strategy.
    """
    expected_set = set(expected)
    used = set()

    strategy_function = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "strategy":
            strategy_function = node
            break

    if not strategy_function:
        return used

    for node in ast.walk(strategy_function):
        if isinstance(node, ast.Name) and node.id in expected_set and isinstance(node.ctx, ast.Load):
            used.add(node.id)

    return used

# Novo parâmetro "selected_game_spec" para acessar a spec correta de cada jogo
def _run_semantics(code, style, function_name, api_key, selected_game_spec: Dict[str, Any]):
        tree = _parse_ast(code)
        prompt = ""

        prompt = prompt_semantics(code=code, tree=tree, assistant_style=style, function_name=function_name, spec=selected_game_spec)

        # if(selected_game_spec.get("name") == "BITS"):
        # elif(selected_game_spec.get("name") == "JOKENPO"):
        #     prompt = prompt_semantics_jokenpo(code=code, tree=tree, assistant_style=style, function_name=function_name, spec=selected_game_spec)

        # print(f"Prompt de semântica:\n{prompt}")
        ret = ask_openai(prompt, api_key)
        # print(f"Resposta do OpenAI: {ret}")
        thought = str(ret.get("pensamento", "")) if isinstance(ret, dict) else ""
        answer = str(ret.get("resposta", "")) if isinstance(ret, dict) else ""

        return {"valid": True, "answer": answer, "thought": thought}

# Novo parâmetro "selected_game_spec" para acessar a spec correta de cada jogo
def _run_tests(code, style, function_name, api_key, selected_game_spec: Dict[str, Any]):
        # results = _execute(code, selected_game_spec.get("tests", []).get(function_name, []), style, selected_game_spec.get("valid_returns", {}).get(function_name, [])) # <-- "TESTS" deve ser passado como parâmetro para a função _run_tests, vindo do jogo específico. Assim, cada jogo pode ter seus próprios testes definidos na spec e passá-los para essa função genérica de execução.
        result = runner_run_tests(code, selected_game_spec.get("tests", []).get(function_name, []), selected_game_spec.get("valid_returns", {}).get(function_name, []))

        # print(f"RESULTS == {results}")

        if result["timed_out"]:
            return {
                "valid": False,
                "answer": "Sua função demorou demais para executar. Verifique se há loops infinitos.",
                "thought": ""
            }

        if not result["ok"]:
            error_prompt = prompt_error_execution(
                code, erro=result["stderr"], assistantStyle=style
            )
            error_dict = ask_openai(error_prompt, api_key)

            return {
                "valid": False,
                "answer": str(error_dict.get("resposta", "")),
                "thought": str(error_dict.get("pensamento", ""))
            }

        # verifica se algum caso teve erro de execução
        # print(f"RESULT['results'] == {result['results']}")
        first_error = next((r for r in result["results"] if not r["valid"]), None)
        if first_error:
            error_prompt = prompt_error_execution(
                code=code, erro=first_error.get("error", "Erro de execução"), assistantStyle=style
            )
            error_dict = ask_openai(error_prompt, api_key)
            return {
                "valid": False,
                "answer": str(error_dict.get("resposta", "")),
                "thought": str(error_dict.get("pensamento", ""))
            }

        # 4) passa os resultados pro prompt
        # print(f"Style == {style}")
        prompt = prompt_run_results(result["results"], selected_game_spec.get("name"), selected_game_spec.get("valid_returns", {}).get(function_name, []), style)
        # print(f"PROMPT == {prompt}")
        tests = ask_openai(prompt, api_key)
        # print(f"RESPOSTA OPENAI == {tests}")

        thought = str(tests.get("pensamento", "")) if isinstance(tests, dict) else ""
        answer = str(tests.get("resposta", "")) if isinstance(tests, dict) else ""

        return {"valid": True, "answer": answer, "thought": thought}

        # Se results for uma lista, significa que a execução ocorreu e temos outputs dos testes para analisar.
        # if isinstance(results, list):
        #     prompt = prompt_run_results(results, selected_game_spec.get("name"), selected_game_spec.get("valid_returns", {}).get(function_name, []), assistant_style=style)
        #     ret = ask_openai(prompt, api_key)
        #     valid = True
        # else: # Se results não for uma lista, significa que ocorreu um erro na execução e o resultado é um prompt de erro a ser enviado para o OpenAI.
        #     ret = ask_openai(results, api_key)
        #     valid = False

        # thought = str(ret.get("pensamento", "")) if isinstance(ret, dict) else ""
        # answer = str(ret.get("resposta", "")) if isinstance(ret, dict) else ""

        # return {"valid": valid, "answer": answer, "thought": thought}

def _run_strict_tests(code, style, function_name, api_key, selected_game_spec: Dict[str, Any]):
        # error_prompt = _execute_strict(code, selected_game_spec.get("tests", []).get(function_name, []), style) # <-- "TESTS" deve ser passado como parâmetro para a função _run_tests, vindo do jogo específico. Assim, cada jogo pode ter seus próprios testes definidos na spec e passá-los para essa função genérica de execução.
        error_prompt = runner_run_submit(code, selected_game_spec.get("tests", []).get(function_name, []))

        # print(f"Error_Prompt == {error_prompt}")

        if not error_prompt['ok']:
            ret = ask_openai(error_prompt, api_key)

            thought = str(ret.get("pensamento", "")) if isinstance(ret, dict) else ""
            answer = str(ret.get("resposta", "")) if isinstance(ret, dict) else ""

            return {"valid": False, "answer": answer, "thought": thought}

        return {"valid": True, "answer": "aceita", "thought": ""}