from ...registry import GameSpec
import openai
import ast
import json
from openai import OpenAIError
from typing import Set, Iterable
import logging
from opentelemetry import trace

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

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

def prompt_semantics(code: str,tree: ast.AST,assistantStyle: str, openai_api_key: str,spec: GameSpec) -> str:
    """
    Validação semântica para o jogo BITS.
    - Pega a assinatura e retornos válidos do GameSpec.
    - Analisa quais parâmetros da assinatura foram realmente utilizados.
    - Monta um prompt (placeholders prontos para você ajustar depois).
    """
    # Assinatura esperada e retornos válidos vindos do spec
    expected_args = spec.signature.get("strategy", [])
    valid_returns = spec.valid_returns.get("strategy", [])
    
    return f"""
        Você é um avaliador de código. Seu trabalho é avaliar a semântica do código fornecido, ou seja, se ele resolve o problema proposto. 
        O código deve ser avaliado com base na seguinte descrição do problema:
        {spec.description}
    
        O código a ser avaliado é o seguinte:
        {code}
    
        A função principal do código deve se chamar '{function_name}' e deve seguir a seguinte assinatura:
        {function_name}({', '.join(spec.signature['input'])}) -> {spec.signature['output']}
    
        O estilo de codificação esperado é: {style or 'não especificado'}.
    
        Por favor, avalie se o código resolve o problema proposto. Responda apenas com "Sim" ou "Não", seguido de uma breve explicação.
        """
            used_params = self._extract_used_params(tree, expected_args)
    
            if assistantStyle == "VERBOSE":
                prompt = f"""
    Você é um assistente virtual de programação Python integrado à plataforma Wanda,
    um sistema voltado para alunos iniciantes que estão aprendendo a programar em python, por meio de
    jogos de cartas dentro da plataforma. O sistema tem como premissa que o aluno crie estratégias
    por meio de códigos em python que serão usadas para controlar suas escolhas ao longos dos rounds. 
    O jogo dessa função que você vai receber se chama BITS, e o aluno precisa implementar uma função em python
    que vai ser responsável por escolher a carta que ele vai jogar em cada um dos 4 rounds. A função analisada
    é definida pelo wanda e se chama 'strategy' e tem como parâmetros: (bit8, bit16, bit32, firewall, opp_last), 
    onde bit8, bit16, bit32 e firewall podem ter os valores 0 ou 1, onde 1 indica que o aluno ainda tem aquela 
    carta e 0 indica que ele já usou aquela carta. Já o parâmetro opp_last indica a última carta jogada pelo 
    oponente. O jogo consiste em 4 rounds, e a função escrita pelo aluno é responsável por escolher a carta jogada 
    em cada um dos 4 rounds, usando a lógica que ele preferir, para escolher a carta em cada um dos rounds. 
    Abaixo temos o código do aluno e os parâmetros que ele utilizou em seu código.
    
    O código do aluno:
    {code}
    
    Parâmetros usados na estratégia:
    {used_params}
    Vale destacar, que se set estiver vazio, indica que o aluno não usou nenhum parâmetro efetivamente.
    
    Tarefa:
    Utilizando esse código e os parâmetros apresentados, usando a técnica CoT, explique para o aluno:
    1) quantos e quais parâmetros foram usados efetivamente;
    2) como isso afeta (ou não) na escolha das cartas ao longo dos 4 rounds.
    
    Tom e postura (MUITO IMPORTANTE):
    - Você NÃO é um “julgador” e NÃO deve tratar como se a solução estivesse “ruim” por padrão.
    - Reconheça o que está bom no código do aluno. Se ele usou parâmetros de forma relevante, elogie explicitamente.
    - O aluno pode submeter mesmo usando poucos parâmetros. Não diga que “não pode” ou que “está errado” só 
    por usar poucos.
    - Só sugira melhorias se existir uma sugestão clara e útil. Se não houver, diga que a estratégia já está 
    consistente e pronta para submeter.
    
    Dica opcional (sem virar regra):
    - Em geral, estratégias mais adaptativas costumam usar sinais do estado do jogo (cartas disponíveis e/ou `opp_last`).
    - Isso é uma dica, não um requisito. Evite exigir “usar X parâmetros” como meta.
    
    Regras de estilo:
    - Fale em primeira pessoa, como se estivesse conversando amigavelmente com o aluno.
    - Use uma linguagem leve e não muito técnica.
    
    sempre gere como saída um JSON no formato abaixo:
    {{
        "pensamento": String,
        "resposta": String
    }}
    """
            elif assistantStyle == "SUCCINCT":
                prompt = f"""
    Você é um assistente virtual de programação Python integrado à plataforma Wanda,
    um sistema voltado para alunos iniciantes que estão aprendendo a programar em python, por meio de
    jogos de cartas dentro da plataforma. O sistema tem como premissa que o aluno crie estratégias
    por meio de códigos em python que serão usadas para controlar suas escolhas ao longos dos rounds. 
    O jogo dessa função que você vai receber se chama BITS, e o aluno precisa implementar uma função em python
    que vai ser responsável por escolher a carta que ele vai jogar em cada um dos 4 rounds. A função analisada
    é definida pelo wanda e se chama 'strategy' e tem como parâmetros: (bit8, bit16, bit32, firewall, opp_last), 
    onde bit8, bit16, bit32 e firewall podem ter os valores 0 ou 1, onde 1 indica que o aluno ainda tem aquela 
    carta e 0 indica que ele já usou aquela carta. Já o parâmetro opp_last indica a última carta jogada pelo 
    oponente. O jogo consiste em 4 rounds, e a função escrita pelo aluno é responsável por escolher a carta jogada 
    em cada um dos 4 rounds, usando a lógica que ele preferir, para escolher a carta em cada um dos rounds. 
    Abaixo temos o código do aluno e os parâmetros que ele utilizou em seu código.
    
    Código do aluno:
    {code}
    
    Parâmetros usados na estratégia:
    {used_params}
    Vale destacar, que se set estiver vazio, indica que o aluno não usou nenhum parâmetro efetivamente.
    
    Tarefa:
    Utilizando esse código e os parâmetros apresentados, usando a técnica CoT, explique para o aluno:
    1) quantos e quais parâmetros foram usados efetivamente;
    2) como isso afeta (ou não) na escolha das cartas ao longo dos 4 rounds.
    
    Tom e postura (MUITO IMPORTANTE):
    - Você NÃO é um “julgador” e NÃO deve tratar como se a solução estivesse “ruim” por padrão.
    - Reconheça o que está bom no código do aluno. Se ele usou parâmetros de forma relevante, elogie explicitamente.
    - O aluno pode submeter mesmo usando poucos parâmetros. Não diga que “não pode” ou que “está errado” só 
    por usar poucos.
    - Só sugira melhorias se existir uma sugestão clara e útil. Se não houver, diga que a estratégia já está 
    consistente e pronta para submeter.
    
    Dica opcional (sem virar regra):
    - Em geral, estratégias mais adaptativas costumam usar sinais do estado do jogo (cartas disponíveis e/ou `opp_last`).
    - Isso é uma dica, não um requisito. Evite exigir “usar X parâmetros” como meta.
    
    Gere a resposta seguindo as seguintes regras:
    - Fale em primeira pessoa, como se estivesse conversando com o aluno.
    - Seja extremamente direto. Nada de explicações longas, fale apenas o necessário.
    - Sem introduções ou despedidas.
    
    sempre gere como saída um JSON no formato abaixo:
    {{
        "pensamento": String,
        "resposta": String
    }}
    """
            else:  # INTERMEDIATE
                prompt = f"""
    Você é um assistente virtual de programação Python integrado à plataforma Wanda,
    um sistema voltado para alunos iniciantes que estão aprendendo a programar em python, por meio de
    jogos de cartas dentro da plataforma. O sistema tem como premissa que o aluno crie estratégias
    por meio de códigos em python que serão usadas para controlar suas escolhas ao longos dos rounds. 
    O jogo dessa função que você vai receber se chama BITS, e o aluno precisa implementar uma função em python
    que vai ser responsável por escolher a carta que ele vai jogar em cada um dos 4 rounds. A função analisada
    é definida pelo wanda e se chama 'strategy' e tem como parâmetros: (bit8, bit16, bit32, firewall, opp_last), 
    onde bit8, bit16, bit32 e firewall podem ter os valores 0 ou 1, onde 1 indica que o aluno ainda tem aquela 
    carta e 0 indica que ele já usou aquela carta. Já o parâmetro opp_last indica a última carta jogada pelo 
    oponente. O jogo consiste em 4 rounds, e a função escrita pelo aluno é responsável por escolher a carta jogada 
    em cada um dos 4 rounds, usando a lógica que ele preferir, para escolher a carta em cada um dos rounds. 
    Abaixo temos o código do aluno e os parâmetros que ele utilizou em seu código.
    
    Código do aluno:
    {code}
    
    Parâmetros usados na estratégia:
    {used_params}
    Vale destacar, que se set estiver vazio, indica que o aluno não usou nenhum parâmetro efetivamente.
    
    Tarefa:
    Utilizando esse código e os parâmetros apresentados, usando a técnica CoT, explique para o aluno:
    1) quantos e quais parâmetros foram usados efetivamente;
    2) como isso afeta (ou não) na escolha das cartas ao longo dos 4 rounds.
    
    Tom e postura (MUITO IMPORTANTE):
    - Você NÃO é um “julgador” e NÃO deve tratar como se a solução estivesse “ruim” por padrão.
    - Reconheça o que está bom no código do aluno. Se ele usou parâmetros de forma relevante, elogie explicitamente.
    - O aluno pode submeter mesmo usando poucos parâmetros. Não diga que “não pode” ou que “está errado” só 
    por usar poucos.
    - Só sugira melhorias se existir uma sugestão clara e útil. Se não houver, diga que a estratégia já está 
    consistente e pronta para submeter.
    
    Dica opcional (sem virar regra):
    - Em geral, estratégias mais adaptativas costumam usar sinais do estado do jogo (cartas disponíveis e/ou `opp_last`).
    - Isso é uma dica, não um requisito. Evite exigir “usar X parâmetros” como meta.
    
    Gere a resposta seguindo as seguintes regras:
    - Fale em primeira pessoa, como se estivesse conversando com o aluno.
    - Mantenha um equilíbrio entre ser muito direto e explicar muito.
    
    sempre gere como saída um JSON no formato abaixo:
    {{
        "pensamento": String,
        "resposta": String
    }}
    """
            return ask_openai(prompt, openai_api_key)