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


class ExecutionValidator:

    def feedback_tests(self, code: str, assistantStyle: str, function_type: str, openai_api_key: str) -> dict:
        """
        com base no type da função (jokenpo1 ou jokenpo2).
        """
        if function_type == "jokenpo1":
            return self.feedback_tests_jokenpo1(code, assistantStyle, openai_api_key)
        elif function_type == "jokenpo2":
            return self.feedback_tests_jokenpo2(code, assistantStyle, openai_api_key)
        else:
            raise ValueError("Tipo de função desconhecido. Use 'jokenpo1' ou 'jokenpo2'.")
    


    def feedback_tests_jokenpo1(self, code: str, assistantStyle: str, openai_api_key: str) -> dict:
        """
        Executa os testes para a função jokenpo1, onde a assinatura é:
          def strategy(card1, card2, card3)
        """
        # Test inputs para jokenpo1: 3 parâmetros
        test_inputs = [
            ("pedra", "pedra", "papel"),
            ("pedra", "papel", "tesoura"),
            ("papel", "papel", "pedra"),
            ("tesoura", "tesoura", "papel"),
            ("pedra", "papel", "papel"),
            ("tesoura", "papel", "tesoura"),
            ("papel", "pedra", "pedra"),
            ("tesoura", "papel", "papel"),
            ("papel", "tesoura", "tesoura"),
            ("pedra", "tesoura", "pedra"),
        ]

        results = []
        local_env = {}
        exec(code, {}, local_env)
        strategy_function = local_env["strategy"]

        for i, test_case in enumerate(test_inputs):
            try:
                output = strategy_function(*test_case)
                if output not in ("pedra", "papel", "tesoura"):
                    results.append({
                        "output": output,
                        "valid": False,
                        "error": "Retorno fora do esperado (não é pedra/papel/tesoura)"
                    })
                else:
                    results.append({
                        "output": output,
                        "valid": True
                    })
            except Exception as err:
                llm_answer = self.error_execution(code, err, openai_api_key)
                return llm_answer
        
        tests_feedback = self.feedback_outputs_tests_jokenpo(results, openai_api_key, assistantStyle)
        return tests_feedback



    def feedback_tests_jokenpo2(self, code: str, assistantStyle: str, openai_api_key: str) -> dict:
        """
        Executa os testes para a função jokenpo2, onde a assinatura é:
        def strategy(card1, card2, opponentCard1, opponentCard2)
        Aqui você deve definir os inputs de teste apropriados.
        Atualmente, segue um exemplo placeholder.
        """
        # Test inputs para jokenpo2: 4 parâmetros
        test_inputs = [
            ("pedra", "papel", "tesoura", "pedra"),
            ("papel", "pedra", "papel", "tesoura"),
            ("tesoura", "tesoura", "pedra", "papel"),
            ("pedra", "pedra", "papel", "tesoura"),
            ("papel", "papel", "pedra", "tesoura"),
            ("tesoura", "tesoura", "pedra", "papel"),
            ("pedra", "papel", "pedra", "tesoura"), 
            ("pedra", "tesoura", "papel", "papel"),
            ("papel", "tesoura", "pedra", "pedra"),
            ("pedra", "tesoura", "tesoura", "papel")
        ]

        results = []
        local_env = {}
        exec(code, {}, local_env)
        strategy_function = local_env["strategy"]

        for i, test_case in enumerate(test_inputs):
            try:
                output = strategy_function(*test_case)
                if output not in ("pedra", "papel", "tesoura"):
                    results.append({
                        "output": output,
                        "valid": True,
                        "error": "Retorno fora do esperado pelo jogo (não é pedra/papel/tesoura)"
                    })
                else:
                    results.append({
                        "output": output,
                        "valid": True
                    })
            except Exception as err:
                llm_answer = self.error_execution(code, err, openai_api_key)
                return llm_answer
        
        tests_feedback = self.feedback_outputs_tests_jokenpo(results, openai_api_key, assistantStyle)
        return tests_feedback
    


    def feedback_outputs_tests_jokenpo(self, results, openai_api_key: str, assistantStyle: str) -> dict:
        
        if assistantStyle == "VERBOSE":
            prompt = f"""
Você é um assistente virtual de programação Python integrado à plataforma Wanda,
um sistema voltado para alunos iniciantes que estão aprendendo a programar em python, por meio de um
jogo chamado Jokenpo, onde o aluno escreve a lógica de uma função strategy para escolher a carta em um 
dos 3 rounds. Você vai analisar uma série de testes realizados com a função escrita pelo aluno
e os outputs para possíveis cenários do jogo.
O ideal, é que os retornos sejam: "pedra", "papel" ou "tesoura",  para que a sua estratégia seja a mais completa e abrangente possível, 
entretanto, caso seja um retorno fora do esperado, a escolha da carta usada na rodada passa a não depender
da lógica do aluno. Após a análise, pode sugerir que o aluno
submeta a função ou possíveis melhorias.

resultados dos testes:

{results}

Utilizando o resultado acima e usando a técnica CoT
Analise as saídas do aluno e explique para ele os resultados obtidos.

Gere a resposta seguindo as seguintes regras:
Fale em primeira pessoa, como se estivesse conversando amigavelmente com o aluno.
Use uma linguagem leve e não muito técnica.
            
complete o JSON abaixo:
{{
    "pensamento": String,
    "resposta": String
}}
"""
        elif assistantStyle == "SUCCINCT":
            prompt = f"""
Você é um assistente virtual de programação Python integrado à plataforma Wanda,
um sistema voltado para alunos iniciantes que estão aprendendo a programar em python, por meio de um
jogo chamado Jokenpo, onde o aluno escreve a lógica de uma função strategy para escolher a carta em um 
dos 3 rounds. Você vai analisar uma série de testes realizados com a função escrita pelo aluno
e os outputs para possíveis cenários do jogo.
O ideal, é que os retornos sejam: "pedra", "papel" ou "tesoura",  para que a sua estratégia seja a mais completa e abrangente possível, 
entretanto, caso seja um retorno fora do esperado, a escolha da carta usada na rodada passa a não depender
da lógica do aluno. Após a análise, pode sugerir que o aluno
submeta a função ou possíveis melhorias.

resultados dos testes:

{results}

Utilizando o resultado acima e usando a técnica CoT
Analise as saídas do aluno e explique para ele os resultados obtidos.

Gere a resposta seguindo as seguintes regras:
Seja extremamente direto. Nada de explicações longas.
Sem introduções ou despedidas.
            
complete o JSON abaixo:
{{
    "pensamento": String,
    "resposta": String
}}
"""
        else:  # INTERMEDIATE
            prompt = f"""
Você é um assistente virtual de programação Python integrado à plataforma Wanda,
um sistema voltado para alunos iniciantes que estão aprendendo a programar em python, por meio de um
jogo chamado Jokenpo, onde o aluno escreve a lógica de uma função strategy para escolher a carta em um 
dos 3 rounds. Você vai analisar uma série de testes realizados com a função escrita pelo aluno
e os outputs para possíveis cenários do jogo.
O ideal, é que os retornos sejam: "pedra", "papel" ou "tesoura",  para que a sua estratégia seja a mais completa e abrangente possível, 
entretanto, caso seja um retorno fora do esperado, a escolha da carta usada na rodada passa a não depender
da lógica do aluno. Após a análise, pode sugerir que o aluno
submeta a função ou possíveis melhorias.

resultados dos testes:

{results}

Utilizando o resultado acima e usando a técnica CoT
Analise as saídas do aluno e explique para ele os resultados obtidos.

Gere a resposta seguindo as seguintes regras:
Forneça uma resposta equilibrada, não seja muito verboso e nem muito direto.
            
complete o JSON abaixo:
{{
    "pensamento": String,
    "resposta": String
}}
"""
        answer = ask_openai(prompt, openai_api_key)
        return answer


    def validator(self, code: str, assistantStyle: str, function_type: str, openai_api_key: str) -> dict:
        """
        Recebe o código do aluno, o estilo do agente, o tipo de função (ex.: "jokenpo1" ou "jokenpo2")
        e a chave da API da OpenAI. Executa o código para obter a função 'strategy' e chama os testes
        correspondentes ao tipo da função.
        """
        local_env = {}
        exec(code, {}, local_env)
        strategy_function = local_env["strategy"]
        if function_type == "jokenpo1":
            results = self.run_outputs_tests_jokenpo1(code, strategy_function, openai_api_key, assistantStyle)
        elif function_type == "jokenpo2":
            results = self.run_outputs_tests_jokenpo2(code, strategy_function, openai_api_key, assistantStyle)
        else:
            results = "Tipo de função inválido."
        return results
    


    def run_outputs_tests_jokenpo1(self, code: str, strategy_function: callable, openai_api_key: str, assistantStyle: str) -> dict:
        """
        Executa uma série de testes para a função do tipo jokenpo1.
        Caso ocorra algum erro durante a execução de um teste, chama error_execution para obter
        uma explicação do erro.
        """
        test_inputs = [
            ("pedra", "pedra", "papel"),
            ("pedra", "papel", "tesoura"),
            ("papel", "papel", "pedra"),
            ("tesoura", "tesoura", "papel"),
            ("pedra", "papel", "papel"),
            ("tesoura", "papel", "tesoura"),
            ("papel", "pedra", "pedra"),
            ("tesoura", "papel", "papel"),
            ("papel", "tesoura", "tesoura"),
            ("pedra", "tesoura", "pedra"),
        ]

        for i, test_case in enumerate(test_inputs):
            # Input_data é opcional, mas pode ser usado para log/debug
            input_data = {
                "card1": test_case[0],
                "card2": test_case[1],
                "card3": test_case[2],
            }
            try:
                output = strategy_function(*test_case)
            except Exception as err:
                llm_answer = self.error_execution(code, err, openai_api_key, assistantStyle)
                return llm_answer
        return ""
    

    
    def run_outputs_tests_jokenpo2(self, code: str, strategy_function: callable, openai_api_key: str, assistantStyle: str) -> dict:
        """
        Implementação placeholder para testes do tipo jokenpo2.
        Caso haja uma lógica diferente para essa variante, implemente-a aqui.
        """
        # Exemplo simples (pode ser ajustado conforme as necessidades)
        test_inputs = [
            ("pedra", "papel", "tesoura", "pedra"),
            ("papel", "pedra", "papel", "tesoura"),
            ("tesoura", "tesoura", "pedra", "papel"),
            ("pedra", "pedra", "papel", "tesoura"),
            ("papel", "papel", "pedra", "tesoura"),
            ("tesoura", "tesoura", "pedra", "papel"),
            ("pedra", "papel", "pedra", "tesoura"), 
            ("pedra", "tesoura", "papel", "papel"),
            ("papel", "tesoura", "pedra", "pedra"),
            ("pedra", "tesoura", "tesoura", "papel")
        ]

        for i, test_case in enumerate(test_inputs):
            input_data = {
                "card1": test_case[0],
                "card2": test_case[1],
                "opponentCard1": test_case[2],
                "opponentCard2": test_case[3],
            }
            try:
                output = strategy_function(*test_case)
            except Exception as err:
                llm_answer = self.error_execution(code, err, openai_api_key, assistantStyle)
                return llm_answer
        return ""
    
    def feedback_tests_bits(self, code: str, assistantStyle: str, openai_api_key: str) -> dict:
        # Testes representando variáveis binárias e última jogada do oponente
        test_inputs = [
            (1, 1, 1, 1, None),
            (1, 0, 1, 0, "BIT32"),
            (0, 1, 1, 1, "BIT16"),
            (1, 1, 0, 1, "FIREWALL"),
            (0, 1, 0, 1, "BIT8"),
            (1, 0, 0, 1, "BIT16"),
            (0, 0, 1, 0, "BIT32"),
            (1, 1, 0, 0, "BIT8"),
            (0, 0, 0, 1, None),
            (0, 1, 0, 0, "BIT32"),
        ]

        results = []
        local_env = {}
        try:
            exec(code, {}, local_env)
        except Exception as err:
            return self.error_execution(code, err, openai_api_key, assistantStyle)

        strategy_fn = local_env.get("strategy")
        if not strategy_fn:
            return {"pensamento": "", "resposta": "Função 'strategy' não encontrada"}

        for test_case in test_inputs:
            try:
                output = strategy_fn(*test_case)

                if output not in ("BIT8", "BIT16", "BIT32", "FIREWALL"):
                    results.append({
                        "input": test_case,
                        "output": output,
                        "valid": False,
                        "error": "Retorno fora do esperado. Use apenas: BIT8, BIT16, BIT32 ou FIREWALL."
                    })
                else:
                    results.append({
                        "input": test_case,
                        "output": output,
                        "valid": True,
                    })

            except Exception as err:
                return self.error_execution(code, err, openai_api_key, assistantStyle)

        return self.feedback_outputs_tests_bits(results, openai_api_key, assistantStyle)
    
    # Feedbacks do jogo BITS
    def feedback_outputs_tests_bits(self, results, openai_api_key: str, assistantStyle: str) -> dict:

        if assistantStyle == "VERBOSE":
            prompt = f"""
Você é um assistente virtual de programação Python integrado à plataforma Wanda,
um sistema voltado para alunos iniciantes que estão aprendendo a programar em python,
por meio de um jogo chamado BITS. O aluno escreve a lógica de uma função strategy para escolher
uma das quatro cartas possíveis: BIT8, BIT16, BIT32 ou FIREWALL.

Nos testes abaixo, sua função foi executada com diferentes situações de cartas disponíveis
(do próprio jogador) e com o valor da última carta do oponente.

Os valores de entrada seguem este formato:
(bit8, bit16, bit32, firewall, opp_last)
onde bit8/bit16/bit32/firewall ∈ {{0,1}} e opp_last ∈ {{None, "BIT8", "BIT16", "BIT32", "FIREWALL"}}.

O objetivo é explicar ao aluno como está o desempenho da lógica da função dele.

resultados dos testes:

    {results}

    Utilizando o resultado acima e usando a técnica CoT,
    Analise as saídas do aluno e explique para ele os resultados obtidos.

    Gere a resposta seguindo as seguintes regras:
    [COLOQUE AS REGRAS VERBOSAS AQUI]

    complete o JSON abaixo:
    {{
        "pensamento": String,
        "resposta": String
    }}
    """
        elif assistantStyle == "SUCCINCT":
            prompt = f"""
    Você é um assistente virtual de programação Python integrado à plataforma Wanda,
    um sistema voltado para alunos iniciantes que estão aprendendo a programar em python,
    por meio de um jogo chamado BITS.

    Aqui estão os resultados dos testes automáticos feitos na função enviada pelo aluno:

    {results}

    Utilizando o resultado acima e usando a técnica CoT,
    Analise rapidamente se os retornos fazem sentido e informe melhorias, se necessário.

    [COLOQUE AS REGRAS SUCCINCT AQUI]

    complete o JSON abaixo:
    {{
        "pensamento": String,
        "resposta": String
    }}
    """
        else:  # INTERMEDIATE
            prompt = f"""
    Você é um assistente virtual de programação Python integrado à plataforma Wanda,
    um sistema voltado para alunos iniciantes que estão aprendendo a programar em python,
    por meio do jogo BITS.

    A seguir estão os resultados de testes aplicados à função strategy do aluno:

    {results}

    Utilizando o resultado acima e usando a técnica CoT,
    Forneça uma análise equilibrada, com orientações claras sobre oportunidades de melhoria.

    [COLOQUE AS REGRAS INTERMEDIÁRIAS AQUI]

    complete o JSON abaixo:
    {{
        "pensamento": String,
        "resposta": String
    }}
    """

        answer = ask_openai(prompt, openai_api_key)
        return answer


    def error_execution(self, code: str, erro: Exception, openai_api_key: str, assistantStyle: str) -> str:
        client = openai.OpenAI(api_key=openai_api_key)
        
        if assistantStyle == "VERBOSE":
            prompt = f"""
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
            
complete o JSON abaixo:
{{
    "pensamento": String,
    "resposta": String
}}
"""
        elif assistantStyle == "SUCCINCT":
            prompt = f"""
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
        else:  # INTERMEDIATE
            prompt = f"""
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
        answer = ask_openai(prompt, openai_api_key)
        return answer