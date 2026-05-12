import ast
from typing import Optional
from prompts.shared import prompt_error_execution, prompt_run_results
from ..registry import GameSpec

def select_signature_error_message(expected_sig_str: str, function_name: str) -> str:
    signature_error_messages = {
         "bits":
        {
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
        },
        "jokenpo1": 
            {
                "VERBOSE": {
                    "missing_function": (
                        "Olá! Sabe, estou olhando seu código e não consegui achar a função 'strategy'.\n"
                        "Ela precisa estar assim:\n"
                        f"def strategy({expected_sig_str}):\n"
                        "    # Seu código\n"
                        "Verifique se o nome está correto e se não houve problemas de indentação! Estou aqui pra ajudar."
                    ),
                    "wrong_signature": (
                        "Ei! Parece que a sua função 'strategy' não tem os parâmetros na ordem esperada.\n"
                        f"Devem ser: {expected_sig_str}.\n"
                        "Dê uma olhada e certifique-se de que eles estejam no lugar certinho, tá bom?"
                    )
                },
                "SUCCINCT": {
                    "missing_function": (
                        "Função 'strategy' não encontrada. Ela deve ser:\n"
                        f"def strategy({expected_sig_str}):"
                    ),
                    "wrong_signature": (
                        "A função 'strategy' existe, mas os parâmetros não batem.\n"
                        f"Use: {expected_sig_str}."
                    )
                },
                "INTERMEDIATE": {
                    "missing_function": (
                        "Não achei a função 'strategy' no seu código. Ela precisa estar declarada como:\n"
                        f"def strategy({expected_sig_str}):\n"
                        "Verifique o nome e a indentação para garantir que esteja certo, ok?"
                    ),
                    "wrong_signature": (
                        "A função 'strategy' foi encontrada, mas os parâmetros não estão corretos.\n"
                        f"Eles devem ser: {expected_sig_str}.\n"
                        "Dê uma revisada pra garantir que estejam nessa ordem."
                    )
                }
            },
        "jokenpo2":
            {
                    "VERBOSE": {
                        "missing_function": (
                            "Olá! Sabe, estou olhando seu código e não consegui achar a função 'strategy'.\n"
                            "Ela precisa estar assim:\n"
                            f"def strategy({expected_sig_str}):\n"
                            "    # Seu código\n"
                            "Verifique se o nome está correto e se não houve problemas de indentação! Estou aqui pra ajudar."
                        ),
                        "wrong_signature": (
                            "Ei! Parece que a sua função 'strategy' não tem os parâmetros na ordem esperada.\n"
                            f"Devem ser: {expected_sig_str}.\n"
                            "Dê uma olhada e certifique-se de que eles estejam no lugar certinho, tá bom?"
                        )
                    },
                    "SUCCINCT": {
                        "missing_function": (
                            "Função 'strategy' não encontrada. Ela deve ser:\n"
                            f"def strategy({expected_sig_str}):"
                        ),
                        "wrong_signature": (
                            "A função 'strategy' existe, mas os parâmetros não batem.\n"
                            f"Use: {expected_sig_str}."
                        )
                    },
                    "INTERMEDIATE": {
                        "missing_function": (
                            "Não achei a função 'strategy' no seu código. Ela precisa estar declarada como:\n"
                            f"def strategy({expected_sig_str}):\n"
                            "Verifique o nome e a indentação para garantir que esteja certo, ok?"
                        ),
                        "wrong_signature": (
                            "A função 'strategy' foi encontrada, mas os parâmetros não estão corretos.\n"
                            f"Eles devem ser: {expected_sig_str}.\n"
                            "Dê uma revisada pra garantir que estejam nessa ordem."
                        )
                    }
            }
    }
    
    game_msgs = signature_error_messages.get(function_name, {})
    return game_msgs

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

# Novo parâmetro "outputs" --> ("pedra", "papel", "tesoura") se JOKENPO; ("BIT8", "BIT16", "BIT32", "FIREWALL") se BITS
def _execute(self, code, TESTS, assistantStyle, outputs):
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

def _parse_ast(self, code: str) -> Optional[ast.AST]:
        try:
            return ast.parse(code)
        except SyntaxError:
            return None
        
# Novo parâmetro selected_game_spec para acessar a spec correta de cada jogo
def _validate_signature(self, code, style, function_name, selected_game_spec: GameSpec) -> str:
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

        # Lê a assinatura esperada do GameSpec
        expected_args = selected_game_spec.signature.get(function_name, {}).get("strategy", [])
        expected_sig_str = ", ".join(expected_args)
        # print(f"Expected signature string: {expected_sig_str}")

        # Mensagens por estilo --> São diferentes para cada tipo de jogo (até o momento)
        messages = select_signature_error_message(expected_sig_str, function_name)
        style_msgs = messages[style]

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
            return style_msgs["missing_function"]
        
        # Compara parâmetros
        actual_args = [arg.arg for arg in strategy_fn.args.args]
        if actual_args != expected_args:
            return style_msgs["wrong_signature"]

        return ""  # OK

def _run_semantics(self, code, style, function_name, api_key):
        tree = self._parse_ast(code)
        prompt = prompt_semantics(code=code, tree=tree, assistant_style=style, function_name=function_name, spec=self.spec)

        ret = ask_openai(prompt, api_key)
        thought = str(ret.get("pensamento", "")) if isinstance(ret, dict) else ""
        answer = str(ret.get("resposta", "")) if isinstance(ret, dict) else ""

        return {"valid": True, "answer": answer, "thought": thought}