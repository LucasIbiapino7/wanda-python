import openai
import json
from openai import OpenAIError

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

class SyntaxValidator:

    def validate(self, code: str, assistantStyle: str, openai_api_key: str) -> dict:
        """
        Valida a sintaxe e a indentação do código.
        Retorna uma string vazia se não houver erros, 
        ou uma mensagem de erro formatada de acordo com a escolha do agente
        """
        try:
            compile(code, "<string>", "exec")
            return ""
        except (SyntaxError, IndentationError) as err:
            llm_answer = self.feedback_sintaxe_openai(code, err, assistantStyle, openai_api_key) # Chama a função que usa a IA
            return llm_answer # Resposta da LLM
    
    def feedback_sintaxe_openai(self, code: str, erro: str, assistantStyle: str, openai_api_key: str) -> dict:

        prompt_verbose = f"""
Você é um assistente virtual de programação Python integrado à plataforma Wanda,
um sistema voltado para alunos iniciantes que estão aprendendo a programar em python, por meio de um
jogo chamado Jokenpo. O jogo tem duas funções que o aluno precisa implementar o código.
        
O código do aluno:
{code}

Erro do python durante a execução do código:
{erro}
        
Usando o código acima e o respectivo erro obtido ao executar esse código, usando a técnica CoT
explique para o aluno o motivo do erro.

Gere a resposta seguindo as seguintes regras:
Fale em primeira pessoa, como se estivesse conversando amigavelmente com o aluno.
Use uma linguagem leve e não muito técnica.
Sempre identifique a linha do erro na explicação (ex: “o problema está na linha 3”).
Não apresente o código corrigido por completo. Ao invés disso, explique o que houve e como corrigir, 
dando pistas específicas, mas sem reescrever todo o código.

complete o JSON abaixo:
{{
    "pensamento": String,
    "resposta": String
}}
"""

        prompt_succint = f"""
Você é um assistente virtual de programação Python integrado à plataforma Wanda,
um sistema voltado para alunos iniciantes que estão aprendendo a programar em python, por meio de um
jogo chamado Jokenpo. O jogo tem duas funções que o aluno precisa implementar o código.

O código do aluno:
{code}

Erro do python durante a execução do código:
{erro}

Usando o código acima e o respectivo erro obtido ao executar esse código, usando a técnica CoT
explique para o aluno o motivo do erro.
        
Gere a resposta seguindo as seguintes regras:
Seja extremamente direto. Nada de explicações longas.
Sem introduções ou despedidas.
Aponte o erro e onde ele ocorre, sempre citando a linha onde ocorreu o erro.
Dê uma pista para corrigir, mas de forma sucinta.
Não apresente o código corrigido.
        
complete o JSON abaixo:
{{
    "pensamento": String,
    "resposta": String
}}
"""

        prompt_intermediary = f"""
Você é um assistente virtual de programação Python integrado à plataforma Wanda,
um sistema voltado para alunos iniciantes que estão aprendendo a programar em python, por meio de um
jogo chamado Jokenpo. O jogo tem duas funções que o aluno precisa implementar o código.
        
O código do aluno:
{code}
        
Erro do python durante a execução do código:
{erro}
        
Usando o código acima e o respectivo erro obtido ao executar esse código, usando a técnica CoT
explique para o aluno o motivo do erro.
        
Gere a resposta seguindo as seguintes regras:
Utilize snippets de código para mostrar o erro e como corrigir.
Especifique a linha onde o erro aconteceu.
O snippet deve conter apenas a correção da linha onde ocorreu o código.
        
complete o JSON abaixo:
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

        answer = ask_openai(prompt, openai_api_key)
        return answer