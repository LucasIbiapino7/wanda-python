import openai
import json

class ExecutionValidator:

    def feedback_tests(self, code: str, assistantStyle: str, function_type: str, openai_api_key: str) -> str:
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
            input_data = {
                "card1": test_case[0],
                "card2": test_case[1],
                "card3": test_case[2],
            }

            try:
                output = strategy_function(*test_case)
                if output not in ("pedra", "papel", "tesoura"):
                    results.append({
                        "output": output,
                        "valid": False,
                        "error": "Retorno fora do esperado (não é pedra/papel/tesoura)"
                    })
                else:
                    # Tudo certo
                    results.append({
                        "output": output,
                        "valid": True
                    })
            except Exception as err:
                # Lançou exceção => interrompe
                llm_aswer = self.error_execution(code, err, openai_api_key)
                return llm_aswer
        
        tests_feedback = self.feedback_outputs_tests(results, openai_api_key)
        return tests_feedback
    
    def feedback_outputs_tests(self, results, openai_api_key: str) -> str:
        client = openai.OpenAI(api_key=openai_api_key)
        
        prompt = f"""
        Você é um assistente virtual de programação Python integrado à plataforma Wanda,
        um sistema voltado para alunos iniciantes que estão aprendendo a programar em python, por meio de um
        jogo chamado Jokenpo, e vai analisar os outputs da função escrita pelo aluno.
        O ideal, é que os retornos sejam: "pedra", "papel" ou "tesoura",  para que a sua estratégia seja a mais completa e abrangente possível, entretanto mesmo com outros retornos, o jogo funciona.
        resultados dos testes:

        {results}

        Utilizando o resultado acima e usando a técnica CoT
        Analise as saídas do aluno e explique para ele os resultados obtidos.

        Gere a resposta seguindo as seguintes regras:
        Seja extremamente direto. Nada de explicações longas.
        Sem introduções ou despedidas.

        Sempre complete o json no formato abaixo:
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


    def validator(self, code: str, assistantStyle: str) -> str:
        local_env = {}
        exec(code, {}, local_env)
        strategy_function = local_env["strategy"]
        results = self.run_outputs_tests(strategy_function, assistantStyle)
        return results
    
    def run_outputs_tests(self, code: str, assistantStyle: str) -> str:
        test_inputs = [
        ("pedra", "pedra", "papel", "papel", "tesoura", "tesoura"),
        ("pedra", "papel", "tesoura", "pedra", "papel", "tesoura"),
        ("pedra", None, "papel", "papel", None, "tesoura"),
        ("pedra", None, None, "papel", None, None),
        ("papel", "papel", "pedra", "tesoura", "tesoura", "pedra"),
        ("tesoura", "tesoura", "papel", "papel", "pedra", "pedra"),
        ("pedra", "papel", None, "papel", "tesoura", None),
        (None, "tesoura", "papel", None, "papel", "papel"),
        ("papel", "papel", "tesoura", "tesoura", "pedra", "pedra"),
        ("papel", None, "tesoura", "pedra", "papel", None),
        ]

        for i, test_case in enumerate(test_inputs):
            input_data = {"card1": test_case[0], "card2": test_case[1], "card3": test_case[2], 
                        "opponentCard1": test_case[3], "opponentCard2": test_case[4], "opponentCard3": test_case[5],
            }
            try:
                output = code(*test_case)
            except Exception as err:
                llm_answer = self.error_execution(code, err, assistantStyle)
                return llm_answer
        return ""
    
    def error_execution(self, code: str, erro: str, openai_api_key: str) -> str:
        client = openai.OpenAI(api_key=openai_api_key)
        prompt = f"""
        Você é um assistente virtual de programação Python integrado à plataforma Wanda,
        um sistema voltado para alunos iniciantes que estão aprendendo a programar em python.
        O código do aluno:

        {code}

        Erro do python durante a execução do código:

        {erro}

        Usando o código acima e o respectivo erro obtido ao executar esse código, usando a técnica CoT
        explique de forma extremamente o motivo do erro de execução. 

        Gere a resposta seguindo as seguintes regras:
        Seja extremamente direto. Nada de explicações longas.
        Sem introduções ou despedidas.
        Aponte o erro e onde ele ocorre, sempre citando a linha onde ocorreu o erro.

        complete o json abaixo:
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
            resposta_dict = json.loads(answer)
            print("Resposta da IA:")
            print("Pensamento: " + resposta_dict["pensamento"])
            print("Resposta: " + resposta_dict["resposta"])
        
        except Exception as e:
            print(f"Erro ao chamar a API da OpenAI: {e}")