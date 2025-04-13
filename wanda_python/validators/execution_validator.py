class ExecutionValidator:
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
                llm_answer = self.feedback_sintaxe_openai(code, err, assistantStyle)
                return llm_answer
        return ""