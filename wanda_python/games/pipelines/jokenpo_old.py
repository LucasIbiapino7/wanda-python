import ast
from typing import Optional, Dict, Any

from ...validators.signature_validator import SignatureValidator
from ...validators.semantics_validator import SemanticsValidator
from ...validators.execution_validator import ExecutionValidator
from ...runner.container_runner import run_submit, run_tests

from ..registry import GameSpec

def _normalize_style(style: str) -> str:
    s = (style or "").strip().upper()
    if s in ("VERBOSE", "SUCCINCT", "INTERMEDIATE", "INTERMEDIARY"):
        return "INTERMEDIATE" if s == "INTERMEDIARY" else s
    return "INTERMEDIATE"


class JokenpoPipeline:
    """
    Pipeline única do Jokenpo contendo:
      - feedback(...): assinatura -> semântica (seu fluxo atual)
      - run(...):      assinatura -> execução de testes
    """

    def __init__(self, spec: GameSpec):
        self.spec = spec
        self._signature = SignatureValidator()
        self._semantics = SemanticsValidator()
        self._execution = ExecutionValidator()

    def _parse_ast(self, code: str) -> Optional[ast.AST]:
        try:
            return ast.parse(code)
        except SyntaxError:
            # Teoricamente nao cai aqui, apenas prevenção 
            return None

    async def feedback(
        self,
        code: str,
        assistant_style: str,
        function_name: str,#"jokenpo1" |"jokenpo2"
        openai_api_key: str
    ) -> Dict[str, Any]:

        style = _normalize_style(assistant_style)

        # 1) AST (assinatura e semântica precisam percorrer a árvore)
        tree = self._parse_ast(code)
        if tree is None:
            return {
                "valid": False,
                "answer": "Não consegui analisar a sua função por erro de sintaxe. Corrija a sintaxe e tente novamente.",
                "thought": ""
            }

        # 2) Assinatura
        sig_msg = self._signature.validate_signature_and_parameters(
            tree=tree,
            assistant_style=style,
            function_type=function_name
        )

        if sig_msg:
            return {
                "valid": False,
                "answer": sig_msg,
                "thought": ""
            }

        sem_dict = self._semantics.validator(
            code=code,
            tree=tree,
            assistantStyle=style,
            openai_api_key=openai_api_key,
            functionType=function_name
        )

        thought = str(sem_dict.get("pensamento", "")) if isinstance(sem_dict, dict) else ""
        answer = str(sem_dict.get("resposta", "")) if isinstance(sem_dict, dict) else ""

        return {
            "valid": True,
            "answer": answer,
            "thought": thought
        }
    

    #RUN 
    async def run(self, code: str, assistant_style: str, function_name: str, openai_api_key: str) -> Dict[str, Any]:
        style = _normalize_style(assistant_style)

        # 1) AST
        tree = self._parse_ast(code)
        if tree is None:
            return {
                "valid": False,
                "answer": "Não consegui analisar a sua função por erro de sintaxe. Corrija a sintaxe e tente novamente.",
                "thought": ""
            }

        # 2) Assinatura
        sig_msg = self._signature.validate_signature_and_parameters(
            tree=tree, assistant_style=style, function_type=function_name
        )
        if sig_msg:
            return {"valid": False, "answer": sig_msg, "thought": ""}

        # 3) Execução de testes via container
        test_cases_by_function = {
            "jokenpo1": [
                ["pedra", "pedra", "papel"],
                ["pedra", "papel", "tesoura"],
                ["papel", "papel", "pedra"],
                ["tesoura", "tesoura", "papel"],
                ["pedra", "papel", "papel"],
                ["tesoura", "papel", "tesoura"],
                ["papel", "pedra", "pedra"],
                ["tesoura", "papel", "papel"],
                ["papel", "tesoura", "tesoura"],
                ["pedra", "tesoura", "pedra"],
            ],
            "jokenpo2": [
                ["pedra", "papel", "tesoura", "pedra"],
                ["papel", "pedra", "papel", "tesoura"],
                ["tesoura", "tesoura", "pedra", "papel"],
                ["pedra", "pedra", "papel", "tesoura"],
                ["papel", "papel", "pedra", "tesoura"],
                ["tesoura", "tesoura", "pedra", "papel"],
                ["pedra", "papel", "pedra", "tesoura"],
                ["pedra", "tesoura", "papel", "papel"],
                ["papel", "tesoura", "pedra", "pedra"],
                ["pedra", "tesoura", "tesoura", "papel"],
            ]
        }

        valid_returns = ["pedra", "papel", "tesoura"]
        test_cases = test_cases_by_function.get(function_name, [])

        result = run_tests(code=code, test_cases=test_cases, valid_returns=valid_returns)

        if result["timed_out"]:
            return {
                "valid": False,
                "answer": "Sua função demorou demais para executar. Verifique se há loops infinitos.",
                "thought": ""
            }

        if not result["ok"]:
            error_dict = self._execution.error_execution(
                code=code, erro=result["stderr"],
                openai_api_key=openai_api_key, assistantStyle=style
            )
            return {
                "valid": False,
                "answer": str(error_dict.get("resposta", "")),
                "thought": str(error_dict.get("pensamento", ""))
            }

        # verifica se algum caso teve erro de execução
        first_error = next((r for r in result["results"] if not r["valid"]), None)
        if first_error:
            error_dict = self._execution.error_execution(
                code=code, erro=first_error.get("error", "Erro de execução"),
                openai_api_key=openai_api_key, assistantStyle=style
            )
            return {
                "valid": False,
                "answer": str(error_dict.get("resposta", "")),
                "thought": str(error_dict.get("pensamento", ""))
            }

        # 4) passa os resultados pro prompt
        param_names = {
            "jokenpo1": ["card1", "card2", "card3"],
            "jokenpo2": ["card1", "card2", "opponentCard1", "opponentCard2"]
        }
        names = param_names.get(function_name, [])
        for i, r in enumerate(result["results"]):
            if i < len(test_cases):
                r["inputs"] = dict(zip(names, test_cases[i]))

        tests = self._execution.feedback_outputs_tests_jokenpo(
            result["results"], openai_api_key, style
        )

        thought = str(tests.get("pensamento", "")) if isinstance(tests, dict) else ""
        llm_answer = str(tests.get("resposta", "")) if isinstance(tests, dict) else ""

        linhas = []
        for i, r in enumerate(result["results"], 1):
            inp = r.get("inputs", {})
            out = r.get("output")
            game_valid = r.get("gameValid", False)
            if out is None:
                retorno = "não retornou nenhuma carta ✗"
            elif not game_valid:
                retorno = f'retornou "{out}" — não é uma carta válida ✗'
            else:
                retorno = f'retornou "{out}" ✓'
            entrada = ", ".join(f'{k}="{v}"' for k, v in inp.items()) if inp else ""
            linhas.append(f"Teste {i}: {entrada} → {retorno}")

        tabela_final = "\n".join(linhas)
        validos_count = sum(1 for r in result["results"] if r.get("gameValid"))
        total_count = len(result["results"])
        cabecalho = f"Resultados dos testes ({validos_count} de {total_count} retornaram uma carta válida):\n\n"
        answer = cabecalho + tabela_final + "\n\n" + llm_answer

        return {"valid": True, "answer": answer, "thought": thought}

    async def validate(self, code: str, assistant_style: str, function_name: str, openai_api_key: str) -> Dict[str, Any]:
        style = _normalize_style(assistant_style)

        # 1) AST
        tree = self._parse_ast(code)
        if tree is None:
            return {
                "valid": False,
                "answer": "Não consegui analisar a sua função por erro de sintaxe.",
                "thought": ""
            }

        # 2) Assinatura
        sig_msg = self._signature.validate_signature_and_parameters(
            tree=tree, assistant_style=style, function_type=function_name
        )
        if sig_msg:
            return {"valid": False, "answer": sig_msg, "thought": ""}

        # 3) Execução de testes via container
        test_cases_by_function = {
            "jokenpo1": [
                ["pedra", "pedra", "papel"],
                ["pedra", "papel", "tesoura"],
                ["papel", "papel", "pedra"],
                ["tesoura", "tesoura", "papel"],
                ["pedra", "papel", "papel"],
                ["tesoura", "papel", "tesoura"],
                ["papel", "pedra", "pedra"],
                ["tesoura", "papel", "papel"],
                ["papel", "tesoura", "tesoura"],
                ["pedra", "tesoura", "pedra"],
            ],
            "jokenpo2": [
                ["pedra", "papel", "tesoura", "pedra"],
                ["papel", "pedra", "papel", "tesoura"],
                ["tesoura", "tesoura", "pedra", "papel"],
                ["pedra", "pedra", "papel", "tesoura"],
                ["papel", "papel", "pedra", "tesoura"],
                ["tesoura", "tesoura", "pedra", "papel"],
                ["pedra", "papel", "pedra", "tesoura"],
                ["pedra", "tesoura", "papel", "papel"],
                ["papel", "tesoura", "pedra", "pedra"],
                ["pedra", "tesoura", "tesoura", "papel"],
            ]
        }

        test_cases = test_cases_by_function.get(function_name, [])
        result = run_submit(code=code, test_cases=test_cases)

        # timeout — mensagem fixa
        if result["timed_out"]:
            return {
                "valid": False,
                "answer": "Sua função demorou demais para executar. Verifique se há loops infinitos.",
                "thought": ""
            }

        # erro de execução — passa pro OpenAI explicar
        if not result["ok"]:
            error_dict = self._execution.error_execution(
                code=code,
                erro=result["stderr"],
                openai_api_key=openai_api_key,
                assistantStyle=style
            )
            return {
                "valid": False,
                "answer": str(error_dict.get("resposta", "")),
                "thought": str(error_dict.get("pensamento", ""))
            }

        return {"valid": True, "answer": "aceita", "thought": ""}