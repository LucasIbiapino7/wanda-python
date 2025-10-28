import ast
from ..games.registry import GameSpec
from typing import Optional

class SignatureValidator:
    def validate_signature_and_parameters(self, tree: ast.AST, assistant_style: str, function_type: str) -> str:
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

        # Seleciona o conjunto de mensagens baseado no tipo da função
        style_dict = messages.get(function_type, messages["jokenpo1"]).get(assistant_style, messages["jokenpo1"]["SUCCINCT"])

        # Verifica a presença da função 'strategy'
        strategy_function = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "strategy":
                strategy_function = node
                break

        if not strategy_function:
            return style_dict["missing_function"]

        # Define a lista de parâmetros esperados com base no tipo de função
        if function_type == "jokenpo1":
            expected_args = ["card1", "card2", "card3"]
        elif function_type == "jokenpo2":
            expected_args = ["card1", "card2", "opponentCard1", "opponentCard2"]
        else:
            # Valor padrão, se não for reconhecido, pode-se assumir o jokenpo1
            expected_args = ["card1", "card2", "card3"]

        actual_args = [arg.arg for arg in strategy_function.args.args]
        if actual_args != expected_args:
            return style_dict["wrong_signature"]

        return ""  # Sem erros

    def validate_bits_signature(self, tree: ast.AST, assistant_style: str, spec: GameSpec) -> str:
        """
        Validação de assinatura para o jogo BITS.
        Usa a assinatura do GameSpec (spec.signature["strategy"]) e exige a função 'strategy'
        com os parâmetros exatamente na ordem indicada.
        Retorna string vazia se estiver OK; caso contrário, retorna a mensagem de erro
        de acordo com o estilo escolhido.
        """
        style = (assistant_style or "").strip().upper()
        if style not in ("VERBOSE", "SUCCINCT", "INTERMEDIATE", "INTERMEDIARY"):
            style = "INTERMEDIATE"
        if style == "INTERMEDIARY":
            style = "INTERMEDIATE"

         # Lê a assinatura esperada do GameSpec
        expected_args = spec.signature.get("strategy", [])
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