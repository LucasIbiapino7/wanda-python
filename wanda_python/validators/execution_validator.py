import openai
import json

class ExecutionValidator:

    def feedback_tests(self, code: str, assistantStyle: str, function_type: str, openai_api_key: str) -> str:
        """
        com base no type da função (jokenpo1 ou jokenpo2).
        """
        if function_type == "jokenpo1":
            return self.feedback_tests_jokenpo1(code, assistantStyle, openai_api_key)
        elif function_type == "jokenpo2":
            return self.feedback_tests_jokenpo2(code, assistantStyle, openai_api_key)
        else:
            raise ValueError("Tipo de função desconhecido. Use 'jokenpo1' ou 'jokenpo2'.")
    
    def feedback_tests_jokenpo1(self, code: str, assistantStyle: str, openai_api_key: str) -> str:
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
        
        tests_feedback = self.feedback_outputs_tests_jokenpo1(results, openai_api_key, assistantStyle)
        return tests_feedback

    def feedback_tests_jokenpo2(self, code: str, assistantStyle: str, openai_api_key: str) -> str:
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
        
        tests_feedback = self.feedback_outputs_tests_jokenpo2(results, openai_api_key, assistantStyle)
        return tests_feedback
    
    def feedback_outputs_tests_jokenpo1(self, results, openai_api_key: str, assistantStyle: str) -> str:
        client = openai.OpenAI(api_key=openai_api_key)
        
        if assistantStyle == "VERBOSE":
            prompt = f"""
            [INSIRA O PROMPT VERBOSE PARA JOKENPO1 AQUI]
            Resultados dos testes para jokenpo1:
            {results}
            
            Utilize a técnica CoT para fornecer uma análise direta e amigável.
            Complete o JSON abaixo:
            {{
                "pensamento": String,
                "resposta": String
            }}
            """
        elif assistantStyle == "SUCCINCT":
            prompt = f"""
            [INSIRA O PROMPT SUCCINCT PARA JOKENPO1 AQUI]
            Resultados:
            {results}
            
            Seja extremamente direto, sem introduções nem despedidas.
            Complete o JSON:
            {{
                "pensamento": String,
                "resposta": String
            }}
            """
        else:  # INTERMEDIATE
            prompt = f"""
            [INSIRA O PROMPT INTERMEDIARY PARA JOKENPO1 AQUI]
            Resultados dos testes:
            {results}
            
            Forneça uma análise equilibrada sobre os outputs.
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

    # Função específica para processar os outputs dos testes para jokenpo2
    def feedback_outputs_tests_jokenpo2(self, results, openai_api_key: str, assistantStyle: str) -> str:
        client = openai.OpenAI(api_key=openai_api_key)
        
        if assistantStyle == "VERBOSE":
            prompt = f"""
            [INSIRA O PROMPT VERBOSE PARA JOKENPO2 AQUI]
            Resultados dos testes para jokenpo2:
            {results}
            
            Utilize a técnica CoT para fornecer uma análise detalhada e amigável.
            Complete o JSON abaixo:
            {{
                "pensamento": String,
                "resposta": String
            }}
            """
        elif assistantStyle == "SUCCINCT":
            prompt = f"""
            [INSIRA O PROMPT SUCCINCT PARA JOKENPO2 AQUI]
            Resultados:
            {results}
            
            Seja extremamente direto.
            Complete o JSON:
            {{
                "pensamento": String,
                "resposta": String
            }}
            """
        else:  # INTERMEDIATE
            prompt = f"""
            [INSIRA O PROMPT INTERMEDIARY PARA JOKENPO2 AQUI]
            Resultados dos testes:
            {results}
            
            Forneça uma análise equilibrada sobre os outputs.
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