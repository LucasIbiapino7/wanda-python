import openai
import ast
import json
from openai import OpenAIError
from typing import Set, Iterable

from ..games.registry import GameSpec


def ask_openai(prompt: str, api_key: str) -> dict:
    """
    Centraliza a chamada à API OpenAI para respostas JSON.
    Retorna sempre um dict com as chaves 'pensamento' e 'resposta'.
    """
    client = openai.OpenAI(api_key=api_key)

    # Mensagem de sistema que garante saída exclusiva em JSON
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
        return json.loads(answer.choices[0].message.content)

    except OpenAIError as e:
        print(f"Erro na API OpenAI: {e}")
        return {"pensamento": "", "resposta": ""}


class SemanticsValidator:
    def validator(self, code: str, tree: ast.AST, assistantStyle: str, openai_api_key: str, functionType: str) -> dict:
        """
        Método orquestrador que chama o validador específico com base em functionType.
        functionType: "jokenpo1" ou "jokenpo2".
        """
        if functionType == "jokenpo1":
            return self.validate_semantics_jokenpo1(
                code, tree, assistantStyle, openai_api_key
            )
        elif functionType == "jokenpo2":
            return self.validate_semantics_jokenpo2(
                code, tree, assistantStyle, openai_api_key
            )
        else:
            raise ValueError(
                "Tipo de função não reconhecido. Use 'jokenpo1' ou 'jokenpo2'."
            )

    def validate_semantics_jokenpo1(self, code: str, tree: ast.AST, assistantStyle: str, openai_api_key: str) -> dict:
        """
        Validação semântica para jokenpo1.
        """
        # Mesma lógica para extrair a função e parâmetros usados
        strategy_function = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "strategy":
                strategy_function = node
                break

        expected_args = {"card1", "card2", "card3"}
        used_params = set()
        for node in ast.walk(strategy_function):
            if (
                isinstance(node, ast.Name)
                and node.id in expected_args
                and isinstance(node.ctx, ast.Load)
            ):
                used_params.add(node.id)

        # Montagem dos prompts
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
}}
"""
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
quantos parâmetros foram usados e como isso afeta na na escolha da sua carta no primeiro round.

sempre gere como saída um JSON no formato abaixo:
{{
    "pensamento": String,
    "resposta": String
}}
"""
        # Chama o centralizador que força JSON e faz parsing
        answer = ask_openai(prompt, openai_api_key)
        return answer

    def validate_semantics_jokenpo2(self, code: str, tree: ast.AST, assistantStyle: str, openai_api_key: str) -> dict:
        """
        Validação semântica para jokenpo2 (mantido igual ao seu código).
        """

        # Encontra a função strategy na árvore AST
        strategy_function = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "strategy":
                strategy_function = node
                break

        expected_args = {"card1", "card2", "opponentCard1", "opponentCard2"}
        used_params = set()
        for node in ast.walk(strategy_function):
            if (
                isinstance(node, ast.Name)
                and node.id in expected_args
                and isinstance(node.ctx, ast.Load)
            ):
                used_params.add(node.id)

        # prompts da jokenpo2 (mantido igual ao seu código)
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
        answer = ask_openai(prompt, openai_api_key)
        return answer
    
    def _extract_used_params(self, tree: ast.AST, expected: Iterable[str]) -> Set[str]:
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
    
    def validate_semantics_bits(self,code: str,tree: ast.AST,assistantStyle: str, openai_api_key: str,spec: GameSpec) -> dict:
        """
        Validação semântica para o jogo BITS.
        - Pega a assinatura e retornos válidos do GameSpec.
        - Analisa quais parâmetros da assinatura foram realmente utilizados.
        - Monta um prompt (placeholders prontos para você ajustar depois).
        """
        # Assinatura esperada e retornos válidos vindos do spec
        expected_args = spec.signature.get("strategy", [])
        valid_returns = spec.valid_returns.get("strategy", [])

        used_params = self._extract_used_params(tree, expected_args)

        if assistantStyle == "VERBOSE":
            prompt = f"""
Você é um assistente virtual de programação Python integrado à plataforma Wanda,
um sistema voltado para alunos iniciantes que estão aprendendo a programar em python, por meio de
jogos de card game. O jogo dessa função que você vai receber agora se chama BITS, e o aluno precisa
implementar uma função em python que vai ser responsável por escolher a carta que ele vai jogar em cada round.  
A função analisada é 'strategy' e tem como parâmetros: ({", ".join(expected_args)}).
Os parâmetros: bit8, bit16, bit32 e firewall podem ter os valores 0 ou 1, onde 1 indica que o aluno ainda
tem aquela carta e 0 indica que ele já usou aquela carta. Já o parâmetro opp_last indica a última carta jogada
pelo openente. O jogo consiste em 4 rounds, e a função escrita pelo aluno é responsável por escolher a carta
jogada em cada um dos 4 rounds, usando a lógica que ele preferir, para escolher a carta em cada um dos rounds.

Abaixo temos o código enviado pelo aluno e quais parâmetros ele utilizou no código.

Código do aluno:
{code}

Parâmetros efetivamente usados:
{sorted(list(used_params))}

Utilizando esse código e os parâmetros apresentados, faça uma análise semântica, explicando de forma amigável e detalhada quantos 
parâmetros foram efetivamente usados e como isso afeta na na escolha da sua carta do aluno no jogo BITS.

Sempre gere SAÍDA em JSON:
{{
  "pensamento": String,
  "resposta": String
}}
"""
        elif assistantStyle == "SUCCINCT":
            prompt = f"""
Você é um assistente virtual de programação Python integrado à plataforma Wanda,
um sistema voltado para alunos iniciantes que estão aprendendo a programar em python, por meio de
jogos de card game. O jogo dessa função que você vai receber agora se chama BITS, e o aluno precisa
implementar uma função em python que vai ser responsável por escolher a carta que ele vai jogar em cada round.  
A função analisada é 'strategy' e tem como parâmetros: ({", ".join(expected_args)}).
Os parâmetros: bit8, bit16, bit32 e firewall podem ter os valores 0 ou 1, onde 1 indica que o aluno ainda
tem aquela carta e 0 indica que ele já usou aquela carta. Já o parâmetro opp_last indica a última carta jogada
pelo openente. O jogo consiste em 4 rounds, e a função escrita pelo aluno é responsável por escolher a carta
jogada em cada um dos 4 rounds, usando a lógica que ele preferir, para escolher a carta em cada um dos rounds.

Abaixo temos o código enviado pelo aluno e quais parâmetros ele utilizou no código.

Código do aluno:
{code}

Parâmetros efetivamente usados:
{sorted(list(used_params))}

Utilizando esse código e os parâmetros apresentados, faça uma análise semântica, explicando de forma extremamente direta 
quantos parâmetros foram usados e como isso afeta na na escolha da sua carta em cada um dos rounds.

Sempre gere SAÍDA em JSON:
{{
  "pensamento": String,
  "resposta": String
}}
"""
        else:  # INTERMEDIATE
            prompt = f"""
Você é um assistente virtual de programação Python integrado à plataforma Wanda,
um sistema voltado para alunos iniciantes que estão aprendendo a programar em python, por meio de
jogos de card game. O jogo dessa função que você vai receber agora se chama BITS, e o aluno precisa
implementar uma função em python que vai ser responsável por escolher a carta que ele vai jogar em cada round.  
A função analisada é 'strategy' e tem como parâmetros: ({", ".join(expected_args)}).
Os parâmetros: bit8, bit16, bit32 e firewall podem ter os valores 0 ou 1, onde 1 indica que o aluno ainda
tem aquela carta e 0 indica que ele já usou aquela carta. Já o parâmetro opp_last indica a última carta jogada
pelo openente. O jogo consiste em 4 rounds, e a função escrita pelo aluno é responsável por escolher a carta
jogada em cada um dos 4 rounds, usando a lógica que ele preferir, para escolher a carta em cada um dos rounds.

Abaixo temos o código enviado pelo aluno e quais parâmetros ele utilizou no código.

Código do aluno:
{code}

Parâmetros efetivamente usados:
{sorted(list(used_params))}

Utilizando esse código e os parâmetros apresentados, faça uma análise semântica, fornecendo uma análise direta, 
mas completa, sobre os parâmetros utilizados, indicando se há possibilidade de melhoria.

Sempre gere SAÍDA em JSON:
{{
  "pensamento": String,
  "resposta": String
}}
"""
        return ask_openai(prompt, openai_api_key)
