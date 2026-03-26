import logging
logging.basicConfig(level=logging.INFO)

from wanda_python.runner.container_runner import run_submit, run_tests

# ============================================================
# SUBMIT
# ============================================================

print("\n===== SUBMIT =====")

print("\n--- SUBMIT 1: deve passar ---")
result = run_submit(
    code="def strategy(card1, card2, card3):\n    return card1",
    test_cases=[["pedra", "papel", "tesoura"], ["papel", "pedra", "tesoura"]]
)
print("Resultado:", result)

print("\n--- SUBMIT 2: erro de execução ---")
result = run_submit(
    code="def strategy(card1, card2, card3):\n    return 1/0",
    test_cases=[["pedra", "papel", "tesoura"]]
)
print("Resultado:", result)

print("\n--- SUBMIT 3: loop infinito (timeout) ---")
result = run_submit(
    code="def strategy(card1, card2, card3):\n    while True: pass",
    test_cases=[["pedra", "papel", "tesoura"]],
    timeout=3
)
print("Resultado:", result)

print("\n--- SUBMIT 4: código malicioso ---")
result = run_submit(
    code="import os\ndef strategy(card1, card2, card3):\n    return os.system('ls')",
    test_cases=[["pedra", "papel", "tesoura"]]
)
print("Resultado:", result)

print("\n--- SUBMIT 5: retorno inválido ---")
result = run_submit(
    code="def strategy(card1, card2, card3):\n    return 'invalido'",
    test_cases=[["pedra", "papel", "tesoura"]]
)
print("Resultado:", result)

# ============================================================
# RUN
# ============================================================

print("\n===== RUN =====")

VALID_RETURNS = ["pedra", "papel", "tesoura"]
TEST_CASES = [
    ["pedra", "papel", "tesoura"],
    ["papel", "pedra", "tesoura"],
    ["tesoura", "pedra", "papel"],
]

print("\n--- RUN 1: passou em tudo ---")
result = run_tests(
    code="def strategy(card1, card2, card3):\n    return card1",
    test_cases=TEST_CASES,
    valid_returns=VALID_RETURNS
)
print("Resultado:", result)

print("\n--- RUN 2: erro em um caso, continua os outros ---")
result = run_tests(
    code="def strategy(card1, card2, card3):\n    if card1 == 'papel': raise ValueError('erro proposital')\n    return card1",
    test_cases=TEST_CASES,
    valid_returns=VALID_RETURNS
)
print("Resultado:", result)

print("\n--- RUN 3: retorno inválido ---")
result = run_tests(
    code="def strategy(card1, card2, card3):\n    return 'invalido'",
    test_cases=TEST_CASES,
    valid_returns=VALID_RETURNS
)
print("Resultado:", result)

print("\n--- RUN 4: loop infinito (timeout) ---")
result = run_tests(
    code="def strategy(card1, card2, card3):\n    while True: pass",
    test_cases=TEST_CASES,
    valid_returns=VALID_RETURNS,
    timeout=3
)
print("Resultado:", result)

print("\n--- RUN 5: código malicioso ---")
result = run_tests(
    code="import os\ndef strategy(card1, card2, card3):\n    return os.system('ls')",
    test_cases=TEST_CASES,
    valid_returns=VALID_RETURNS
)
print("Resultado:", result)

print("\n--- SUBMIT 6: erro no segundo caso, deve parar ---")
result = run_submit(
    code="def strategy(card1, card2, card3):\n    if card1 == 'papel': raise ValueError('parou aqui')\n    return card1",
    test_cases=[
        ["pedra", "papel", "tesoura"],  # passa
        ["papel", "pedra", "tesoura"],  # erro — deve parar aqui
        ["tesoura", "pedra", "papel"],  # não deve executar
    ]
)
print("Resultado:", result)