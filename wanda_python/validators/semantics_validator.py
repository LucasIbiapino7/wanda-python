import openai
import ast

class SemanticsValidator:
    def validator(self, code: str, tree: ast.AST, assistantStyle: str, openai_api_key: str, functionType: str) -> str:
        """
        Método orquestrador que chama o validador específico com base no functionType.
        functionType: "jokenpo1" ou "jokenpo2"
        """
        if functionType == "jokenpo1":
            return self.validate_semantics_jokenpo1(code, tree, assistantStyle, openai_api_key)
        elif functionType == "jokenpo2":
            return self.validate_semantics_jokenpo2(code, tree, assistantStyle, openai_api_key)
        else:
            raise ValueError("Tipo de função não reconhecido. Use 'jokenpo1' ou 'jokenpo2'.")

    def validate_semantics_jokenpo1(self, code: str, tree: ast.AST, assistantStyle: str, openai_api_key: str) -> str:
        """
        Validação semântica para jokenpo1. Utiliza os prompts já existentes.
        """
        client = openai.OpenAI(api_key=openai_api_key)

        # Encontra a função strategy na árvore AST
        strategy_function = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "strategy":
                strategy_function = node
                break

        expected_args = {"card1", "card2", "card3"}
        used_params = set()
        for node in ast.walk(strategy_function):
            if isinstance(node, ast.Name) and node.id in expected_args and isinstance(node.ctx, ast.Load):
                used_params.add(node.id)

        # Definir os prompts para jokenpo1 (baseados nos atuais)
        if assistantStyle == "VERBOSE":
            prompt = f"""
            Você é um assistente virtual de programação Python integrado à plataforma Wanda,
            um sistema voltado para alunos iniciantes que estão aprendendo a programar em python, por meio de um
            jogo chamado Jokenpo. O jogo tem duas funções que o aluno precisa implementar o código e você está responsável por analisar a funçao 1.
            Por padrão, a função strategy deve utilizar os parâmetros: (card1, card2, card3), mesmo que apenas alguns sejam usados na prática.

            O código do aluno:
            {code}

            Parâmetros usados na estratégia:
            {used_params}

            Utilizando esse código e os parâmetros apresentados, explique de forma amigável e detalhada quantos 
            parâmetros foram efetivamente usados e se há espaço para melhorar o uso deles.

            Sempre Complete o JSON:
            {{
                "pensamento": String,
                "resposta": String
            }}
        """
        elif assistantStyle == "SUCCINCT":
            prompt = f"""
            Você é um assistente virtual para iniciantes em Python na plataforma Wanda.
            O código do aluno:
            {code}

            Parâmetros usados:
            {used_params}

            Explique de forma extremamente direta quantos parâmetros foram usados.
            Sempre Complete o JSON:
            {{
                "pensamento": String,
                "resposta": String
            }}
            """
        else:  # INTERMEDIATE
            prompt = f"""
            Você é um assistente virtual de programação Python integrado à plataforma Wanda.
            O código do aluno:
            {code}

            Parâmetros utilizados:
            {used_params}

            Forneça uma análise direta, mas completa, sobre os parâmetros utilizados, indicando se há possibilidade de melhoria.
            Sempre Complete o JSON:
            {{
                "pensamento": String,
                "resposta": String
            }}
            """
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300 
            )
            answer = response.choices[0].message.content
            return answer
        except Exception as e:
            print(f"Erro ao chamar a API da OpenAI: {e}")
            return ""

    def validate_semantics_jokenpo2(self, code: str, tree: ast.AST, assistantStyle: str, openai_api_key: str) -> str:
        """
        Validação semântica para jokenpo2. Aqui ainda deixam-se placeholders para os novos prompts.
        """
        client = openai.OpenAI(api_key=openai_api_key)

        # Encontra a função strategy na árvore AST
        strategy_function = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "strategy":
                strategy_function = node
                break

        expected_args = {"card1", "card2", "card3", "opponentCard1", "opponentCard2", "opponentCard3"}
        used_params = set()
        for node in ast.walk(strategy_function):
            if isinstance(node, ast.Name) and node.id in expected_args and isinstance(node.ctx, ast.Load):
                used_params.add(node.id)

        # Placeholder para os prompts da jokenpo2
        if assistantStyle == "VERBOSE":
            prompt = f"""
            [INSIRA O NOVO PROMPT VERBOSE PARA JOKENPO2 AQUI]
            O código do aluno:
            {code}

            Parâmetros utilizados:
            {used_params}

            Complete o JSON:
            {{
                "pensamento": String,
                "resposta": String
            }}
            """
        elif assistantStyle == "SUCCINCT":
            prompt = f"""
            [INSIRA O NOVO PROMPT SUCCINCT PARA JOKENPO2 AQUI]
            O código do aluno:
            {code}

            Parâmetros usados:
            {used_params}

            Complete o JSON:
            {{
                "pensamento": String,
                "resposta": String
            }}
            """
        else:  # INTERMEDIATE
            prompt = f"""
            [INSIRA O NOVO PROMPT INTERMEDIARY PARA JOKENPO2 AQUI]
            O código do aluno:
            {code}

            Parâmetros utilizados:
            {used_params}

            Complete o JSON:
            {{
                "pensamento": String,
                "resposta": String
            }}
            """
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300
            )
            answer = response.choices[0].message.content
            return answer
        except Exception as e:
            print(f"Erro ao chamar a API da OpenAI: {e}")
            return ""
