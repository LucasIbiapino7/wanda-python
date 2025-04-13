import ast

class SignatureValidator:

    def validate_signature_and_parameters(self, tree: ast.AST, assistant_style: str) -> str:
        messages = {
            "VERBOSE": {
                "missing_function": (
                    "Olá! Sabe, estou olhando seu código e não consegui achar a função 'strategy'.\n"
                    "Ela precisa estar assim:\n\n"
                    "def strategy(card1, card2, card3, opponentCard1, opponentCard2, opponentCard3):\n"
                    "    # Seu código\n\n"
                    "Verifique se o nome está correto e se não houve problemas de indentação! Estou aqui pra ajudar."
                ),
                "wrong_signature": (
                    "Ei! Parece que a sua função 'strategy' não tem os parâmetros na ordem esperada.\n"
                    "Devem ser: card1, card2, card3, opponentCard1, opponentCard2, opponentCard3.\n"
                    "Dê uma olhada e certifique-se de que eles estejam no lugar certinho, tá bom?"
                )
            },
            "SUCCINCT": {
                "missing_function": (
                    "Função 'strategy' não encontrada. Ela deve ser:\n"
                    "def strategy(card1, card2, card3, opponentCard1, opponentCard2, opponentCard3):"
                ),
                "wrong_signature": (
                    "A função 'strategy' existe, mas os parâmetros não batem.\n"
                    "Use: card1, card2, card3, opponentCard1, opponentCard2, opponentCard3."
                )
            },
            "INTERMEDIATE": {
                "missing_function": (
                    "Não achei a função 'strategy' no seu código. Ela precisa estar declarada como:\n"
                    "def strategy(card1, card2, card3, opponentCard1, opponentCard2, opponentCard3):\n"
                    "Verifique o nome e a indentação para garantir que esteja certo, ok?"
                ),
                "wrong_signature": (
                    "A função 'strategy' foi encontrada, mas os parâmetros não estão corretos.\n"
                    "Eles devem ser: card1, card2, card3, opponentCard1, opponentCard2, opponentCard3.\n"
                    "Dê uma revisada pra garantir que estejam nessa ordem."
                )
            }
        }

        # Escolher o dicionário de acordo com o estilo
        style_dict = messages.get(assistant_style, messages["SUCCINCT"])

        # Verificando a presença da função strategy:
        strategy_function = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "strategy":
                strategy_function = node
                break

        if not strategy_function:
            # retorna mensagem "missing_function" conforme estilo
            return style_dict["missing_function"]

        # Verificando a assinatura da função
        expected_args = [
            "card1", "card2", "card3",
            "opponentCard1", "opponentCard2", "opponentCard3"
        ]
        actual_args = [arg.arg for arg in strategy_function.args.args]

        if actual_args != expected_args:
            return style_dict["wrong_signature"]

        return ""  # Sem erros