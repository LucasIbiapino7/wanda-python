import subprocess
import uuid
import os
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

RUNNER_TMP_DIR = "/tmp/wanda_runner"
RUNNER_VOLUME_NAME = "wanda_runner_tmp"

_sessions: dict[str, asyncio.subprocess.Process] = {}

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


def run_submit(code: str, test_cases: list, timeout: int = 30) -> dict:
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
        game_valid = output in valid_returns
        entry = {{
            "output": output,
            "valid": True,
            "gameValid": game_valid
        }}
        if not game_valid:
            entry["fallback"] = "NEXT_AVAILABLE_CARD"
            entry["note"] = "Retorno fora do esperado. O jogo ignora esse valor e usa a próxima carta disponível na mão do jogador."
        results.append(entry)
    except Exception as e:
        results.append({{
            "output": None,
            "valid": False,
            "gameValid": False,
            "error": str(e)
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
    last_line = result["stdout"].strip().split("\n")[-1]
    try:
        result["results"] = json.loads(last_line)
    except json.JSONDecodeError:
        logger.error("Falha ao parsear JSON do container. stdout=%s", result["stdout"])
        result["ok"] = False
        result["stderr"] = "Erro interno ao processar resultado."
        result["results"] = []

    return result




def _build_session_script(code_p1: str, code_p2: str) -> str:
    """
    Gera o script que roda dentro do container durante toda a partida.
    Fica em loop lendo um JSON por linha do stdin, executa as duas
    estratégias e escreve um JSON por linha no stdout.

    sys.stdout é redirecionado para /dev/null antes de carregar o código
    dos jogadores — qualquer print dentro das strategies é silenciado.
    O stdout real é preservado em _real_stdout e usado exclusivamente
    para o protocolo JSON de comunicação com o Java.
    """
    return f"""\
import json
import sys
import os

# preserva o stdout real — canal de comunicação com o Java
_real_stdout = sys.stdout

# redireciona sys.stdout para /dev/null — silencia prints dos jogadores
sys.stdout = open(os.devnull, "w")

# --- código do jogador 1 ---
{code_p1}
strategy_p1 = strategy

# --- código do jogador 2 ---
{code_p2}
strategy_p2 = strategy

# loop de partida: 1 linha de input = 1 round
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        params = json.loads(line)
        r1 = strategy_p1(*params["p1"])
        r2 = strategy_p2(*params["p2"])
        _real_stdout.write(json.dumps({{"p1": r1, "p2": r2}}) + "\\n")
        _real_stdout.flush()
    except Exception as e:
        _real_stdout.write(json.dumps({{"error": str(e)}}) + "\\n")
        _real_stdout.flush()
"""


async def create_session(code_p1: str, code_p2: str) -> str:
    session_id = uuid.uuid4().hex
    container_name = f"wanda_session_{session_id}"
    script = _build_session_script(code_p1, code_p2)

    # escreve o script no volume compartilhado
    os.makedirs(RUNNER_TMP_DIR, exist_ok=True)
    filename = f"wanda_session_{session_id}.py"
    tmp_path = os.path.join(RUNNER_TMP_DIR, filename)
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(script)

    logger.info("Criando sessao. session_id=%s", session_id)

    # sobe o container em modo interativo (stdin/stdout abertos)
    # --name garante que temos um handle pra matar o container via docker kill
    # stderr=STDOUT evita deadlock de buffer no stderr
    # -u desativa o buffering do stdout dentro do container
    process = await asyncio.create_subprocess_exec(
        "docker", "run", "--rm", "--interactive", "--init",
        "--name", container_name,
        "--network", "none",
        "--memory", "128m",
        "--cpus", "0.5",
        "--user", "65534:65534",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--pids-limit", "64",
        "--read-only",
        "-v", f"{RUNNER_VOLUME_NAME}:/scripts:ro",
        "python:3.11-alpine",
        "python", "-u", f"/scripts/{filename}",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,  # mescla stderr no stdout — evita deadlock
    )

    # guarda processo e nome do container juntos
    _sessions[session_id] = {"process": process, "container_name": container_name}
    logger.info("Sessao criada. session_id=%s pid=%s", session_id, process.pid)

    return session_id


async def execute_round(session_id: str, params_p1: list, params_p2: list, timeout: int = 5) -> dict:
    session = _sessions.get(session_id)
    process = session["process"] if session else None

    if process is None:
        logger.error("Sessao nao encontrada. session_id=%s", session_id)
        return {
            "ok": False,
            "player1Choice": None,
            "player2Choice": None,
            "error": "SESSION_NOT_FOUND",
            "errorDetail": f"Sessão '{session_id}' não existe ou já foi encerrada.",
        }

    # monta o payload do round
    payload = json.dumps({"p1": params_p1, "p2": params_p2}) + "\n"

    try:
        # escreve no stdin e aguarda 1 linha no stdout com timeout por round
        process.stdin.write(payload.encode())
        await process.stdin.drain()

        raw = await asyncio.wait_for(process.stdout.readline(), timeout=timeout)
        response = json.loads(raw.decode().strip())

        # o script pode retornar {"error": "..."} em caso de exceção interna
        if "error" in response:
            logger.error(
                "Erro de execucao no container. session_id=%s detalhe=%s",
                session_id, response["error"]
            )
            # sessão é encerrada: container em estado desconhecido após exceção
            await _kill_session(session_id)
            return {
                "ok": False,
                "player1Choice": None,
                "player2Choice": None,
                "error": "EXECUTION_ERROR",
                "errorDetail": response["error"],
            }

        logger.info(
            "Round executado. session_id=%s p1=%s p2=%s",
            session_id, response["p1"], response["p2"]
        )
        return {
            "ok": True,
            "player1Choice": response["p1"],
            "player2Choice": response["p2"],
            "error": None,
            "errorDetail": None,
        }

    except asyncio.TimeoutError:
        logger.error("Timeout no round. session_id=%s", session_id)
        # encerra a sessão — container travado não é aproveitável
        await _kill_session(session_id)
        return {
            "ok": False,
            "player1Choice": None,
            "player2Choice": None,
            "error": "TIMEOUT",
            "errorDetail": "Tempo limite do round atingido.",
        }

    except Exception as e:
        logger.error("Erro inesperado no round. session_id=%s erro=%s", session_id, str(e))
        await _kill_session(session_id)
        return {
            "ok": False,
            "player1Choice": None,
            "player2Choice": None,
            "error": "EXECUTION_ERROR",
            "errorDetail": str(e),
        }


async def close_session(session_id: str) -> None:
    if session_id not in _sessions:
        logger.warning("Tentativa de fechar sessao inexistente. session_id=%s", session_id)
        return

    await _kill_session(session_id)
    logger.info("Sessao encerrada. session_id=%s", session_id)


async def _kill_session(session_id: str) -> None:
    session = _sessions.pop(session_id, None)
    if session is None:
        return

    process = session["process"]
    container_name = session["container_name"]

    try:
        # docker kill fala direto com o daemon — garante que o container morre
        killer = await asyncio.create_subprocess_exec(
            "docker", "kill", container_name,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await killer.wait()
        process.kill()
        await process.wait()
    except Exception as e:
        logger.warning("Erro ao matar processo da sessao. session_id=%s erro=%s", session_id, str(e))