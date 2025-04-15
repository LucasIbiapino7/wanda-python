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
        
        tests_feedback = self.feedback_outputs_tests_jokenpo1(results, openai_api_key, assistantStyle)
        return tests_feedback
    


    def feedback_outputs_tests_jokenpo1(self, results, openai_api_key: str, assistantStyle: str) -> str:
        client = openai.OpenAI(api_key=openai_api_key)
        
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
            
            sempre complete o json abaixo:
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
            
            sempre complete o json abaixo:
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
            
            sempre complete o json abaixo:
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



    def validator(self, code: str, assistantStyle: str, function_type: str, openai_api_key: str) -> str:
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
    


    def run_outputs_tests_jokenpo1(self, code: str, strategy_function: callable, openai_api_key: str, assistantStyle: str) -> str:
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
    

    
    def run_outputs_tests_jokenpo2(self, code: str, strategy_function: callable, openai_api_key: str, assistantStyle: str) -> str:
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
            
            sempre complete o json abaixo:
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
            
            sempre complete o json abaixo:
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
            
            sempre complete o json abaixo:
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
