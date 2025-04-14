import openai
import ast

class SemanticsValidator:
    def validator(self, code: str, tree: ast.AST, assistantStyle: str, openai_api_key: str) -> str:
        client = openai.OpenAI(api_key=openai_api_key)

        strategy_function = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "strategy":
                strategy_function = node
                break

        expected_args = {"card1", "card2", "card3", "opponentCard1", "opponentCard2","opponentCard3",}
        used_params = set()

        # Percorre todos os nós dentro do corpo da função
        for node in ast.walk(strategy_function):
            # Verifica se é um Name e se ele corresponde a um dos parâmetros
            if isinstance(node, ast.Name) and node.id in expected_args:
                if isinstance(node.ctx, ast.Load):
                    used_params.add(node.id)

        prompt_verbose = f"""
        Você é um assistente virtual de programação Python integrado à plataforma Wanda,
        um sistema voltado para alunos iniciantes que estão aprendendo a programar em python, por meio de um
        jogo chamado Jokenpo, que por padrão tem seis parâmetros sempre na função strategy: (card1, card2, card3, opponentCard1, opponentCard2,
        opponentCard3). e que podem ser usados para melhorar a estratégia do aluno

        o código do aluno:
        {code}

        parâmetros usados pelo aluno em sua estratégia:
        {used_params}

        Utilizando o código acima e usando a técnica CoT você deve fazer uma análise do código do aluno e dos parâmetros
        utilizados.

        Gere a resposta seguindo as seguintes regras:
        Fale em primeira pessoa, como se estivesse conversando amigavelmente com
        o aluno.
        Use uma linguagem leve e não muito técnica.
        sua resposta deve conter quantos parâmetros o aluno, e se é possível
        melhorar.
        fale apenas sobre os usos dos parâmetros, nada sobre a lógica.
        complete o json abaixo:
        {{
            "pensamento": String,
            "resposta": String
        }}
        """

        prompt_succint = f"""
        Você é um assistente virtual de programação Python integrado à plataforma Wanda,
        um sistema voltado para alunos iniciantes que estão aprendendo a programar em python, por meio de um
        jogo chamado Jokenpo, que por padrão tem seis parâmetros sempre na função strategy: (card1, card2, card3, opponentCard1, opponentCard2,
        opponentCard3). e que podem ser usados para melhorar a estratégia do aluno

        o código do aluno:
        {code}

        parâmetros usados pelo aluno em sua estratégia:
        {used_params}

        Utilizando o código acima e usando a técnica CoT você deve fazer uma análise do código do aluno e dos parâmetros
        utilizados.

        Gere a resposta seguindo as seguintes regras:
        Seja extremamente direto. Nada de explicações longas.
        Sem introduções ou despedidas.
        Sua resposta deve conter quantos parâmetros o aluno está usando.
        Fale apenas sobre os usos dos parâmetros, nada além disso.
        complete o json abaixo:
        {{
            "pensamento": String,
            "resposta": String
        }}
        """

        prompt_intermediary = f"""
        Você é um assistente virtual de programação Python integrado à plataforma Wanda,
        um sistema voltado para alunos iniciantes que estão aprendendo a programar em python, por meio de um
        jogo chamado Jokenpo, que por padrão tem seis parâmetros sempre na função strategy: (card1, card2, card3, opponentCard1, opponentCard2,
        opponentCard3). e que podem ser usados para melhorar a estratégia do aluno

        o código do aluno:
        {code}

        parâmetros usados pelo aluno em sua estratégia:
        {used_params}

        Utilizando o código acima e usando a técnica CoT você deve fazer uma análise do código do aluno e dos parâmetros
        utilizados.

        Gere a resposta seguindo as seguintes regras:
        Fale em primeira pessoa, sendo direto mas não muito sucinto.
        Use uma linguagem leve e não muito técnica.
        sua resposta deve conter quantos parâmetros o aluno, e se é possível
        melhorar.
        fale apenas sobre os usos dos parâmetros, nada sobre a lógica.
        complete o json abaixo:
        {{
            "pensamento": String,
            "resposta": String
        }}
        """

        if assistantStyle == "VERBOSE":
            prompt = prompt_verbose
        elif assistantStyle == "SUCCINCT":
            prompt = prompt_succint
        else:
            prompt = prompt_intermediary

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
