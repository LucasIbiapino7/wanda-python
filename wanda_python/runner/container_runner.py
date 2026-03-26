import subprocess
import uuid
import os
import logging

logger = logging.getLogger(__name__)

RUNNER_TMP_DIR = "/tmp/wanda_runner"
RUNNER_VOLUME_NAME = "wanda_runner_tmp"

def _execute_in_container(script: str, timeout: int = 5) -> dict:
    # nome único pro arquivo temporário
    # uuid para evitar colisoes em simultaneos
    os.makedirs(RUNNER_TMP_DIR, exist_ok=True)

    filename = f"wanda_{uuid.uuid4().hex}.py"
    tmp_path = os.path.join(RUNNER_TMP_DIR, filename)
    container_name = f"wanda_runner_{uuid.uuid4().hex}"

    logger.info("Iniciando container. nome=%s", container_name)

    try:
        # escreve o script no diretório compartilhado
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(script)

        # executa o container com protecoes
        result = subprocess.run(
            [
                "docker", "run", "--rm",  # remove o container ao terminar
                "--network", "none",  # sem acesso à internet
                "--name", container_name,  # nome
                "--memory", "128m",  # limite de memória
                "--cpus", "0.5",  # limite de CPU
                "--user", "65534:65534",  # roda como usuario sem privilegios
                "--cap-drop", "ALL",  # remove capacidades extras do container
                "--security-opt", "no-new-privileges",  # impede escalacao de privilegios
                "--pids-limit", "64",  # limita quantidade de processos
                "--read-only",
                "-v", f"{RUNNER_VOLUME_NAME}:/scripts:ro",  # monta o volume nomeado em modo leitura
                "python:3.11-alpine",  # imagem
                "python", f"/scripts/{filename}"  # executa o arquivo dentro do container
            ],
            capture_output=True,  # captura stdout e stderr
            text=True,  # retorna como string
            timeout=timeout  # mata se demorar mais que timeout segundos
        )

        logger.info(
            "Container finalizado. nome=%s returncode=%s",
            container_name, result.returncode
        )

        # retorna resultado estruturado
        return {
            "ok": result.returncode == 0,
            "timed_out": False,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode
        }

    except subprocess.TimeoutExpired:
        # timeout estourou
        # matar o container
        logger.error("Timeout. Matando container. nome=%s", container_name)
        subprocess.run(
            ["docker", "kill", container_name],
            capture_output=True,  # silencia o output
            text=True,
            check=False
        )
        return {
            "ok": False,
            "timed_out": True,
            "stdout": "",
            "stderr": "Tempo limite de execução atingido.",
            "returncode": -1
        }

    except Exception as e:
        # erro inesperado
        logger.error("Erro inesperado ao executar container. erro=%s", str(e))
        return {
            "ok": False,
            "timed_out": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }

    finally:
        # sempre deleta o arquivo, mesmo se der erro
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def _build_submit_script(code: str, test_cases: list) -> str:
    return f"""\
import sys

{code}

test_cases = {test_cases}

for i, args in enumerate(test_cases):
    try:
        result = strategy(*args)
    except Exception as e:
        print(f"Erro no caso {{i}}: {{e}}", file=sys.stderr)
        sys.exit(1)

sys.exit(0)
"""


def run_submit(code: str, test_cases: list, timeout: int = 5) -> dict:
    script = _build_submit_script(code, test_cases)
    return _execute_in_container(script, timeout)


def _build_run_script(code: str, test_cases: list, valid_returns: list) -> str:
    return f"""\
import sys
import json

{code}

test_cases = {test_cases}
valid_returns = {valid_returns}
results = []

for i, args in enumerate(test_cases):
    try:
        output = strategy(*args)
        results.append({{
            "index": i,
            "ok": True,
            "output": output,
            "gameValid": output in valid_returns
        }})
    except Exception as e:
        results.append({{
            "index": i,
            "ok": False,
            "error": str(e),
            "gameValid": False
        }})
        break

print(json.dumps(results))
sys.exit(0)
"""


def run_tests(code, test_cases, valid_returns, timeout=5):
    script = _build_run_script(code, test_cases, valid_returns)
    result = _execute_in_container(script, timeout)

    if not result["ok"]:
        return result

    import json
    # pega so a ultima linha
    last_line = result["stdout"].strip().split("\n")[-1]
    try:
        result["results"] = json.loads(last_line)
    except json.JSONDecodeError:
        logger.error("Falha ao parsear JSON do container. stdout=%s", result["stdout"])
        result["ok"] = False
        result["stderr"] = "Erro interno ao processar resultado."
        result["results"] = []

    return result