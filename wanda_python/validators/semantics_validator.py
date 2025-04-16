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
        Validação semântica para jokenpo1.
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

        # Definir os prompts para jokenpo1
        if assistantStyle == "VERBOSE":
            prompt = f"""
Você é um assistente virtual de programação Python integrado à plataforma Wanda,
um sistema voltado para alunos iniciantes que estão aprendendo a programar em python, por meio de um
jogo chamado Jokenpo. O jogo tem duas funções que o aluno precisa implementar o código e você está 
responsável por analisar a primeira função do aluno, responsável por escolher a carta que ele vai 
jogar no primeiro round.
Por padrão, a função que voce está analisando se chama strategy e tem como
parâmetros: (card1, card2, card3), que representam as cartas do aluno naquele round, 
e que podem ser utilizados para melhorar a estratégia da escolha da carta jogada pelo aluno.

O código do aluno:
{code}

Parâmetros usados na estratégia:
{used_params}

Utilizando esse código e os parâmetros apresentados, explique de forma amigável e detalhada quantos 
parâmetros foram efetivamente usados e como isso afeta na na escolha da sua carta do aluno no primeiro round.

sempre gere como saída um JSON no formato abaixo:
{{
    "pensamento": String,
    "resposta": String
}}
"""
        elif assistantStyle == "SUCCINCT":
            prompt = f"""
Você é um assistente virtual de programação Python integrado à plataforma Wanda,
um sistema voltado para alunos iniciantes que estão aprendendo a programar em python, por meio de um
jogo chamado Jokenpo. O jogo tem duas funções que o aluno precisa implementar o código e você está 
responsável por analisar a primeira função do aluno, responsável por escolher a carta que ele vai 
jogar no primeiro round.
Por padrão, a função que voce está analisando se chama strategy e tem como
parâmetros: (card1, card2, card3), que representam as cartas do aluno naquele round, 
e que podem ser utilizados para melhorar a estratégia da escolha da carta jogada pelo aluno.
            
código do aluno:
{code}

Parâmetros usados:
{used_params}

Utilizando esse código e os parâmetros apresentados, explique de forma extremamente direta 
quantos parâmetros foram usados e como isso afeta na na escolha da sua carta no primeiro round.

sempre gere como saída um JSON no formato abaixo:
{{
    "pensamento": String,
    "resposta": String
}}"""
        else:  # INTERMEDIATE
            prompt = f"""
Você é um assistente virtual de programação Python integrado à plataforma Wanda,
um sistema voltado para alunos iniciantes que estão aprendendo a programar em python, por meio de um
jogo chamado Jokenpo. O jogo tem duas funções que o aluno precisa implementar o código e você está 
responsável por analisar a primeira função do aluno, responsável por escolher a carta que ele vai 
jogar no primeiro round.
Por padrão, a função que voce está analisando se chama strategy e tem como
parâmetros: (card1, card2, card3), que representam as cartas do aluno naquele round, 
e que podem ser utilizados para melhorar a estratégia da escolha da carta jogada pelo aluno.

código do aluno:
{code}

Parâmetros utilizados:
{used_params}

Utilizando esse código e os parâmetros apresentados, forneça uma análise direta, mas completa, 
sobre os parâmetros utilizados, indicando se há possibilidade de melhoria.

sempre gere como saída um JSON no formato abaixo:
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

        expected_args = {"card1", "card2", "opponentCard1", "opponentCard2"}
        used_params = set()
        for node in ast.walk(strategy_function):
            if isinstance(node, ast.Name) and node.id in expected_args and isinstance(node.ctx, ast.Load):
                used_params.add(node.id)

        # prompts da jokenpo2
        if assistantStyle == "VERBOSE":
            prompt = f"""
Você é um assistente virtual de programação Python integrado à plataforma Wanda,
um sistema voltado para alunos iniciantes que estão aprendendo a programar em python, por meio de um
jogo chamado Jokenpo. O jogo tem duas funções que o aluno precisa implementar o código e você está 
responsável por analisar a segunda função do aluno, responsável por escolher a carta que ele vai 
jogar no segundo round.
Por padrão, a função que voce está analisando se chama strategy e tem como
parâmetros: (card1, card2, opponentCard1, opponentCard2), onde card1 e card2 representam as cartas do aluno e 
opponentCard1 e opponentCard2 representam as cartas do oponente naquela rodada ,
e que podem ser utilizados para melhorar a estratégia da escolha da carta jogada pelo aluno.

O código do aluno:
{code}

Parâmetros usados na estratégia:
{used_params}

Utilizando esse código e os parâmetros apresentados, explique de forma amigável e detalhada quantos 
parâmetros foram efetivamente usados e como isso afeta na na escolha da sua carta no segundo round.

sempre gere como saída um JSON no formato abaixo:
{{
    "pensamento": String,
    "resposta": String
}}
"""
        elif assistantStyle == "SUCCINCT":
            prompt = f"""
Você é um assistente virtual de programação Python integrado à plataforma Wanda,
um sistema voltado para alunos iniciantes que estão aprendendo a programar em python, por meio de um
jogo chamado Jokenpo. O jogo tem duas funções que o aluno precisa implementar o código e você está 
responsável por analisar a segunda função do aluno, responsável por escolher a carta que ele vai 
jogar no segundo round.
Por padrão, a função que voce está analisando se chama strategy e tem como
parâmetros: (card1, card2, opponentCard1, opponentCard2), onde card1 e card2 representam as cartas do aluno e 
opponentCard1 e opponentCard2 representam as cartas do oponente naquela rodada ,
e que podem ser utilizados para melhorar a estratégia da escolha da carta jogada pelo aluno.

O código do aluno:
{code}

Parâmetros usados na estratégia:
{used_params}

Utilizando esse código e os parâmetros apresentados, explique de forma extremamente direta 
quantos parâmetros foram usados e como isso afeta na na escolha da sua carta no segundo round.

sempre gere como saída um JSON no formato abaixo:
{{
    "pensamento": String,
    "resposta": String
}}
"""
        else:  # INTERMEDIATE
            prompt = f"""
Você é um assistente virtual de programação Python integrado à plataforma Wanda,
um sistema voltado para alunos iniciantes que estão aprendendo a programar em python, por meio de um
jogo chamado Jokenpo. O jogo tem duas funções que o aluno precisa implementar o código e você está 
responsável por analisar a segunda função do aluno, responsável por escolher a carta que ele vai 
jogar no segundo round.
Por padrão, a função que voce está analisando se chama strategy e tem como
parâmetros: (card1, card2, opponentCard1, opponentCard2), onde card1 e card2 representam as cartas do aluno e 
opponentCard1 e opponentCard2 representam as cartas do oponente naquela rodada ,
e que podem ser utilizados para melhorar a estratégia da escolha da carta jogada pelo aluno.

O código do aluno:
{code}

Parâmetros usados na estratégia:
{used_params}

Utilizando esse código e os parâmetros apresentados, forneça uma análise direta, mas completa, 
sobre os parâmetros utilizados, indicando se há possibilidade de melhoria.

sempre gere como saída um JSON no formato abaixo:
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
