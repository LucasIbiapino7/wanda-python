import openai

class SyntaxValidator:

    def validate(self, code: str, assistantStyle: str, openai_api_key: str) -> str:
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
    
    def feedback_sintaxe_openai(self, code: str, erro: str, assistantStyle: str, openai_api_key: str) -> str:
        client = openai.OpenAI(api_key=openai_api_key)

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
        sempre complete o json abaixo:
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
        
        sempre complete o json abaixo:
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
        
        sempre complete o json abaixo:
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