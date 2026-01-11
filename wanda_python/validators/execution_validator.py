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
                if output in ("pedra", "papel", "tesoura"):
                    results.append({
                        "output": output,
                        "valid": True,
                        "gameValid": True
                })
                else:
                    results.append({
                        "output": output,
                        "valid": True,
                        "gameValid": False,
                        "fallback": "NEXT_AVAILABLE_CARD",
                        "note": (
                            "Retorno fora do esperado. O jogo ignora esse valor e "
                            "usa a próxima carta disponível na mão do jogador."
                        )
                    })
            except Exception as err:
                llm_answer = self.error_execution(code, err, openai_api_key)
                return llm_answer
        
        tests_feedback = self.feedback_outputs_tests_jokenpo(results, openai_api_key, assistantStyle)
        return tests_feedback



    def feedback_tests_jokenpo2(self, code: str, assistantStyle: str, openai_api_key: str) -> dict:
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
                if output in ("pedra", "papel", "tesoura"):
                    results.append({
                        "output": output,
                        "valid": True,
                        "gameValid": True
                })
                else:
                    results.append({
                        "output": output,
                        "valid": True,
                        "gameValid": False,
                        "fallback": "NEXT_AVAILABLE_CARD",
                        "note": (
                            "Retorno fora do esperado. O jogo ignora esse valor e "
                            "usa a próxima carta disponível na mão do jogador."
                        )
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
um sistema voltado para alunos iniciantes que estão aprendendo a programar em python, por meio de
jogos de cartas dentro da plataforma. O sistema tem como premissa que o aluno crie estratégias
por meio de códigos em python que serão usadas para controlar suas escolhas ao longos dos rounds.
Você vai analisar uma série de resultados de testes realizados com a função escrita pelo aluno e os outputs para possíveis 
cenários do jogo jokenpo. O ideal, é que os retornos sejam: "pedra", "papel" ou "tesoura", para que a sua estratégia 
seja a mais completa e abrangente possível, entretanto, caso seja um retorno fora do esperado, a escolha da 
carta usada na rodada passa a não depender da lógica do aluno. Após a análise, pode sugerir que o aluno
submeta a função ou possíveis melhorias.

Você vai analisar os resultados de testes do modo RUN. Aqui vão algumas explicações sobre o resultado e o que 
isso representa no jogo:
- Cada output representa o comportamento da função do aluno para determinado conjunto de entrada.
- Se `valid` = true, significa que o código executou sem erro (não travou / não deu exceção).
- Se `gameValid` = true, significa que o retorno foi aceito pelo jogo ("pedra", "papel" ou "tesoura").
- Se `gameValid` = false, significa que o retorno NÃO é um valor esperado pelo jogo.
  Nesse caso, a engine IGNORA o retorno do aluno e aplica um fallback:
  - `fallback` = "NEXT_AVAILABLE_CARD": o jogo usa a próxima carta disponível na mão do jogador.
  Ou seja: nesses casos, a rodada não depende da lógica do aluno, e a estratégia fica menos “controlável”.

resultados dos testes:

{results}

Utilizando o resultado acima e usando a técnica CoT
Sua tarefa é:
- Resuma quantos testes tiveram `gameValid=true` e quantos tiveram `gameValid=false`(sem citar essa informação
interna: 'gameValid') e explique o seu impacto no jogo.
- Comente sobre a Diversidade das escolhas do aluno e como isso pode impactar no jogo. Por mais que não 
existam estratégias erradas, uma que retorna sempre a mesma carta pode ser previsível, diferente de uma que 
tenha uma variedade maior de retornos. 

Tom e postura (MUITO IMPORTANTE):
- Você NÃO é um “julgador” e NÃO deve tratar como se a solução estivesse “ruim” por padrão.
- Reconheça o que está bom no código do aluno. Se ele retornou valores válidos com frequência, elogie explicitamente.
- O aluno pode submeter independente do resultado dos testes. Não diga que “não pode” ou que “está errado” só 
por usar poucos.
- Só sugira melhorias se existir uma sugestão clara e útil. Se não houver, diga que a estratégia já está 
consistente e pronta para submeter.

Gere a resposta seguindo as seguintes regras:
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
Você vai analisar uma série de resultados de testes realizados com a função escrita pelo aluno e os outputs para possíveis 
cenários do jogo jokenpo. O ideal, é que os retornos sejam: "pedra", "papel" ou "tesoura", para que a sua estratégia 
seja a mais completa e abrangente possível, entretanto, caso seja um retorno fora do esperado, a escolha da 
carta usada na rodada passa a não depender da lógica do aluno. Após a análise, pode sugerir que o aluno
submeta a função ou possíveis melhorias.

Você vai analisar os resultados de testes do modo RUN. Aqui vão algumas explicações sobre o resultado e o que 
isso representa no jogo:
- Cada output representa o comportamento da função do aluno para determinado conjunto de entrada.
- Se `valid` = true, significa que o código executou sem erro (não travou / não deu exceção).
- Se `gameValid` = true, significa que o retorno foi aceito pelo jogo ("pedra", "papel" ou "tesoura").
- Se `gameValid` = false, significa que o retorno NÃO é um valor esperado pelo jogo.
  Nesse caso, a engine IGNORA o retorno do aluno e aplica um fallback:
  - `fallback` = "NEXT_AVAILABLE_CARD": o jogo usa a próxima carta disponível na mão do jogador.
  Ou seja: nesses casos, a rodada não depende da lógica do aluno, e a estratégia fica menos “controlável”.

resultados dos testes:

{results}

Utilizando o resultado acima e usando a técnica CoT
Sua tarefa é:
- Resuma quantos testes tiveram `gameValid=true` e quantos tiveram `gameValid=false`(sem citar essa informação
interna: 'gameValid') e explique o seu impacto no jogo.
- Comente sobre a Diversidade das escolhas do aluno e como isso pode impactar no jogo. Por mais que não 
existam estratégias erradas, uma que retorna sempre a mesma carta pode ser previsível, diferente de uma que 
tenha uma variedade maior de retornos. 

Tom e postura (MUITO IMPORTANTE):
- Você NÃO é um “julgador” e NÃO deve tratar como se a solução estivesse “ruim” por padrão.
- Reconheça o que está bom no código do aluno. Se ele retornou valores válidos com frequência, elogie explicitamente.
- O aluno pode submeter independente do resultado dos testes. Não diga que “não pode” ou que “está errado” só 
por usar poucos.
- Só sugira melhorias se existir uma sugestão clara e útil. Se não houver, diga que a estratégia já está 
consistente e pronta para submeter.

Gere a resposta seguindo as seguintes regras:
- Fale em primeira pessoa, como se estivesse conversando com o aluno.
- Seja extremamente direto. Nada de explicações longas.
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
Você vai analisar uma série de resultados de testes realizados com a função escrita pelo aluno e os outputs para possíveis 
cenários do jogo jokenpo. O ideal, é que os retornos sejam: "pedra", "papel" ou "tesoura", para que a sua estratégia 
seja a mais completa e abrangente possível, entretanto, caso seja um retorno fora do esperado, a escolha da 
carta usada na rodada passa a não depender da lógica do aluno. Após a análise, pode sugerir que o aluno
submeta a função ou possíveis melhorias.

Você vai analisar os resultados de testes do modo RUN. Aqui vão algumas explicações sobre o resultado e o que 
isso representa no jogo:
- Cada output representa o comportamento da função do aluno para determinado conjunto de entrada.
- Se `valid` = true, significa que o código executou sem erro (não travou / não deu exceção).
- Se `gameValid` = true, significa que o retorno foi aceito pelo jogo ("pedra", "papel" ou "tesoura").
- Se `gameValid` = false, significa que o retorno NÃO é um valor esperado pelo jogo.
  Nesse caso, a engine IGNORA o retorno do aluno e aplica um fallback:
  - `fallback` = "NEXT_AVAILABLE_CARD": o jogo usa a próxima carta disponível na mão do jogador.
  Ou seja: nesses casos, a rodada não depende da lógica do aluno, e a estratégia fica menos “controlável”.

resultados dos testes:

{results}

Utilizando o resultado acima e usando a técnica CoT
Sua tarefa é:
- Resuma quantos testes tiveram `gameValid=true` e quantos tiveram `gameValid=false`(sem citar essa informação
interna: 'gameValid') e explique o seu impacto no jogo.
- Comente sobre a Diversidade das escolhas do aluno e como isso pode impactar no jogo. Por mais que não 
existam estratégias erradas, uma que retorna sempre a mesma carta pode ser previsível, diferente de uma que 
tenha uma variedade maior de retornos. 

Tom e postura (MUITO IMPORTANTE):
- Você NÃO é um “julgador” e NÃO deve tratar como se a solução estivesse “ruim” por padrão.
- Reconheça o que está bom no código do aluno. Se ele retornou valores válidos com frequência, elogie explicitamente.
- O aluno pode submeter independente do resultado dos testes. Não diga que “não pode” ou que “está errado” só 
por usar poucos.
- Só sugira melhorias se existir uma sugestão clara e útil. Se não houver, diga que a estratégia já está 
consistente e pronta para submeter.

Gere a resposta seguindo as seguintes regras:
- Fale em primeira pessoa, como se estivesse conversando com o aluno.
- Forneça uma resposta equilibrada, não seja muito verboso e nem muito direto.
            
sempre gere como saída um JSON no formato abaixo:
{{
    "pensamento": String,
    "resposta": String
}}
"""
        answer = ask_openai(prompt, openai_api_key)
        return answer


    def validator(self, code: str, assistantStyle: str, function_type: str, openai_api_key: str) -> dict:
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
        """
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
                if output in ("BIT8", "BIT16", "BIT32", "FIREWALL"):
                    results.append({
                        "output": output,
                        "valid": True,
                        "gameValid": True
                })
                else:
                    results.append({
                        "output": output,
                        "valid": True,
                        "gameValid": False,
                        "fallback": "NEXT_AVAILABLE_CARD",
                        "note": (
                            "Retorno fora do esperado. O jogo ignora esse valor e "
                            "usa a próxima carta disponível na mão do jogador."
                        )
                    })
            except Exception as err:
                return self.error_execution(code, err, openai_api_key, assistantStyle)

        return self.feedback_outputs_tests_bits(results, openai_api_key, assistantStyle)
    
    # Feedbacks do jogo BITS
    def feedback_outputs_tests_bits(self, results, openai_api_key: str, assistantStyle: str) -> dict:

        if assistantStyle == "VERBOSE":
            prompt = f"""
Você é um assistente virtual de programação Python integrado à plataforma Wanda,
um sistema voltado para alunos iniciantes que estão aprendendo a programar em python, por meio de
jogos de cartas dentro da plataforma. O sistema tem como premissa que o aluno crie estratégias
por meio de códigos em python que serão usadas para controlar suas escolhas ao longos dos rounds. 
Você vai analisar uma série de resultados de testes realizados com a função escrita pelo aluno e os outputs para possíveis 
cenários do jogo BITS. O ideal, é que os retornos sejam: "BIT8", "BIT16", "BIT32" ou "FIREWALL", 
para que a sua estratégia seja a mais completa e abrangente possível, entretanto, caso seja um retorno fora 
do esperado, a escolha da carta usada na rodada passa a não depender da lógica do aluno. Após a análise, 
pode sugerir que o aluno submeta a função ou possíveis melhorias.

Você vai analisar os resultados de testes do modo RUN. Aqui vão algumas explicações sobre o resultado e o que 
isso representa no jogo:
- Cada output representa o comportamento da função do aluno para determinado conjunto de entrada.
- Se `valid` = true, significa que o código executou sem erro (não travou / não deu exceção).
- Se `gameValid` = true, significa que o retorno foi aceito pelo jogo ("BIT8", "BIT16", "BIT32" ou "FIREWALL").
- Se `gameValid` = false, significa que o retorno NÃO é um valor esperado pelo jogo.
  Nesse caso, a engine IGNORA o retorno do aluno e aplica um fallback:
  - `fallback` = "NEXT_AVAILABLE_CARD": o jogo usa a próxima carta disponível na mão do jogador.
  Ou seja: nesses casos, a rodada não depende da lógica do aluno, e a estratégia fica menos “controlável”.

resultados dos testes:

{results}

Utilizando o resultado acima e usando a técnica CoT
Sua tarefa é:
- Resuma quantos testes tiveram `gameValid=true` e quantos tiveram `gameValid=false`(sem citar essa informação
interna: 'gameValid') e explique o seu impacto no jogo.
- Comente sobre a Diversidade das escolhas do aluno e como isso pode impactar no jogo. Por mais que não 
existam estratégias erradas, uma que retorna sempre a mesma carta pode ser previsível, diferente de uma que 
tenha uma variedade maior de retornos. 

Tom e postura (MUITO IMPORTANTE):
- Você NÃO é um “julgador” e NÃO deve tratar como se a solução estivesse “ruim” por padrão.
- Reconheça o que está bom no código do aluno. Se ele retornou valores válidos com frequência, elogie explicitamente.
- O aluno pode submeter independente do resultado dos testes. Não diga que “não pode” ou que “está errado” só 
por usar poucos.
- Só sugira melhorias se existir uma sugestão clara e útil. Se não houver, diga que a estratégia já está 
consistente e pronta para submeter.

   Gere a resposta seguindo as seguintes regras:
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
Você vai analisar uma série de resultados de testes realizados com a função escrita pelo aluno e os outputs para possíveis 
cenários do jogo BITS. O ideal, é que os retornos sejam: "BIT8", "BIT16", "BIT32" ou "FIREWALL", 
para que a sua estratégia seja a mais completa e abrangente possível, entretanto, caso seja um retorno fora 
do esperado, a escolha da carta usada na rodada passa a não depender da lógica do aluno. Após a análise, 
pode sugerir que o aluno submeta a função ou possíveis melhorias.

Você vai analisar os resultados de testes do modo RUN. Aqui vão algumas explicações sobre o resultado e o que 
isso representa no jogo:
- Cada output representa o comportamento da função do aluno para determinado conjunto de entrada.
- Se `valid` = true, significa que o código executou sem erro (não travou / não deu exceção).
- Se `gameValid` = true, significa que o retorno foi aceito pelo jogo ("BIT8", "BIT16", "BIT32" ou "FIREWALL").
- Se `gameValid` = false, significa que o retorno NÃO é um valor esperado pelo jogo.
  Nesse caso, a engine IGNORA o retorno do aluno e aplica um fallback:
  - `fallback` = "NEXT_AVAILABLE_CARD": o jogo usa a próxima carta disponível na mão do jogador.
  Ou seja: nesses casos, a rodada não depende da lógica do aluno, e a estratégia fica menos “controlável”.

resultados dos testes:

{results}

Utilizando o resultado acima e usando a técnica CoT
Sua tarefa é:
- Resuma quantos testes tiveram `gameValid=true` e quantos tiveram `gameValid=false`(sem citar essa informação
interna: 'gameValid') e explique o seu impacto no jogo.
- Comente sobre a Diversidade das escolhas do aluno e como isso pode impactar no jogo. Por mais que não 
existam estratégias erradas, uma que retorna sempre a mesma carta pode ser previsível, diferente de uma que 
tenha uma variedade maior de retornos. 

Tom e postura (MUITO IMPORTANTE):
- Você NÃO é um “julgador” e NÃO deve tratar como se a solução estivesse “ruim” por padrão.
- Reconheça o que está bom no código do aluno. Se ele retornou valores válidos com frequência, elogie explicitamente.
- O aluno pode submeter independente do resultado dos testes. Não diga que “não pode” ou que “está errado” só 
por usar poucos.
- Só sugira melhorias se existir uma sugestão clara e útil. Se não houver, diga que a estratégia já está 
consistente e pronta para submeter.

Gere a resposta seguindo as seguintes regras:
- Fale em primeira pessoa, como se estivesse conversando com o aluno.   
- Seja extremamente direto. Nada de explicações longas.
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
Você vai analisar uma série de resultados de testes realizados com a função escrita pelo aluno e os outputs para possíveis 
cenários do jogo BITS. O ideal, é que os retornos sejam: "BIT8", "BIT16", "BIT32" ou "FIREWALL", 
para que a sua estratégia seja a mais completa e abrangente possível, entretanto, caso seja um retorno fora 
do esperado, a escolha da carta usada na rodada passa a não depender da lógica do aluno. Após a análise, 
pode sugerir que o aluno submeta a função ou possíveis melhorias.

Você vai analisar os resultados de testes do modo RUN. Aqui vão algumas explicações sobre o resultado e o que 
isso representa no jogo:
- Cada output representa o comportamento da função do aluno para determinado conjunto de entrada.
- Se `valid` = true, significa que o código executou sem erro (não travou / não deu exceção).
- Se `gameValid` = true, significa que o retorno foi aceito pelo jogo ("BIT8", "BIT16", "BIT32" ou "FIREWALL").
- Se `gameValid` = false, significa que o retorno NÃO é um valor esperado pelo jogo.
  Nesse caso, a engine IGNORA o retorno do aluno e aplica um fallback:
  - `fallback` = "NEXT_AVAILABLE_CARD": o jogo usa a próxima carta disponível na mão do jogador.
  Ou seja: nesses casos, a rodada não depende da lógica do aluno, e a estratégia fica menos “controlável”.

resultados dos testes:

{results}

Utilizando o resultado acima e usando a técnica CoT
Sua tarefa é:
- Resuma quantos testes tiveram `gameValid=true` e quantos tiveram `gameValid=false`(sem citar essa informação
interna: 'gameValid') e explique o seu impacto no jogo.
- Comente sobre a Diversidade das escolhas do aluno e como isso pode impactar no jogo. Por mais que não 
existam estratégias erradas, uma que retorna sempre a mesma carta pode ser previsível, diferente de uma que 
tenha uma variedade maior de retornos. 

Tom e postura (MUITO IMPORTANTE):
- Você NÃO é um “julgador” e NÃO deve tratar como se a solução estivesse “ruim” por padrão.
- Reconheça o que está bom no código do aluno. Se ele retornou valores válidos com frequência, elogie explicitamente.
- O aluno pode submeter independente do resultado dos testes. Não diga que “não pode” ou que “está errado” só 
por usar poucos.
- Só sugira melhorias se existir uma sugestão clara e útil. Se não houver, diga que a estratégia já está 
consistente e pronta para submeter.
Gere a resposta seguindo as seguintes regras:
- Fale em primeira pessoa, como se estivesse conversando com o aluno.
- Forneça uma resposta equilibrada, não seja muito verboso e nem muito direto.
            
sempre gere como saída um JSON no formato abaixo:
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
um sistema voltado para alunos iniciantes que estão aprendendo a programar em python, por meio de
jogos de cartas dentro da plataforma. O sistema tem como premissa que o aluno crie estratégias
por meio de códigos em python que serão usadas para controlar suas escolhas ao longos dos rounds.
Abaixo o código de um aluno que apresentou algum tipo de erro.
        
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
Abaixo o código de um aluno que apresentou algum tipo de erro.

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
Abaixo o código de um aluno que apresentou algum tipo de erro.
            
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
            
sempre gere como saída um JSON no formato abaixo:
{{
    "pensamento": String,
    "resposta": String
}}
"""
        answer = ask_openai(prompt, openai_api_key)
        return answer
    

    def validator_bits(self, code: str, assistantStyle: str, openai_api_key: str) -> dict:
        local_env = {}
        try:
            exec(code, {}, local_env)
        except Exception as err:
            return self.error_execution(code, err, openai_api_key, assistantStyle)

        strategy_fn = local_env.get("strategy")
        if not strategy_fn:
            return {
                "pensamento": "",
                "resposta": "Função 'strategy' não encontrada no seu código. "
                            "Verifique o nome da função e tente novamente."
            }

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

        for test_case in test_inputs:
            try:
                _ = strategy_fn(*test_case)
            except Exception as err:
                return self.error_execution(code, err, openai_api_key, assistantStyle)

        return ""
