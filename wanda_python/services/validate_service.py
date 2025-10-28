from wanda_python.schema.validate_dto import ValidateRequest, ValidateResponse
from dotenv import load_dotenv
from wanda_python.validators.syntax_validator import SyntaxValidator
from wanda_python.validators.signature_validator import SignatureValidator
from wanda_python.validators.malicious_checker import MaliciousChecker
from wanda_python.validators.execution_validator import ExecutionValidator
from wanda_python.validators.semantics_validator import SemanticsValidator
from ..games.router import resolve_pipeline

import json

import os
import ast

class ValidateService:

    def __init__(self):
        load_dotenv()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.syntax_validator = SyntaxValidator()
        self.signature_validator = SignatureValidator()
        self.malicious_checker = MaliciousChecker()
        self.execution_validator = ExecutionValidator()
        self.semantics_validator = SemanticsValidator()

    async def validate(self, data: ValidateRequest) -> ValidateResponse:
        code = data.code  # Pega a função
        # 1 Validação: Sintaxe e indentação
        response_validate = self.syntax_validator.validate(code, data.assistantStyle, self.openai_api_key)
        if response_validate:
            thought = response_validate["pensamento"]
            answer = response_validate["resposta"]
            return ValidateResponse.create(valid=False, answer=answer, thought=thought)
        tree = ast.parse(code)  # Vai ser usada nas próximas duas validações (árvore do código)
        # 2 Validação: Verificando comandos maliciosos
        malicious_errors = self.malicious_checker.validate(tree)
        if malicious_errors:
            return ValidateResponse.create(valid=False, answer=malicious_errors, thought="")
        # 3 Validação: Assinatura e execução de testes via pipeline
        _, pipeline = resolve_pipeline(data.gameName, data.functionName)
        result = await pipeline.validate(
            code=code,
            assistant_style=data.assistantStyle,
            function_name=data.functionName,
            openai_api_key=self.openai_api_key
        )
        
        execution_errors = None
        if not result.get("valid", False):
            execution_errors = {
                "pensamento": str(result.get("thought", "")),
                "resposta": str(result.get("answer", ""))
            }

        # 4 Validação: erro de execução
        if execution_errors:
            thought = execution_errors["pensamento"]
            answer = execution_errors["resposta"]
            return ValidateResponse.create(valid=False, answer=answer, thought=thought)

        # Passou em todas as validações
        return ValidateResponse.create(valid=True, answer="aceita", thought="")
    # service -> Feedback
    async def feedback(self, data: ValidateRequest) -> ValidateResponse:
        code = data.code # Pega a função
        # 1 Validação: Sintaxe e indentação
        response_validate = self.syntax_validator.validate(code, data.assistantStyle, self.openai_api_key)
        if response_validate:
            thought = response_validate["pensamento"]
            answer = response_validate["resposta"]
            return ValidateResponse.create(valid=False, answer=answer, thought=thought)
        
        tree = ast.parse(code) # Vai ser usada nas próximas duas validações
        # 2 Validação: Assinatura e argumentos
        """
        response_validate = self.signature_validator.validate_signature_and_parameters(tree, data.assistantStyle, data.functionName)
        if response_validate:
            return ValidateResponse.create(valid=False, answer=response_validate, thought="")
        """

        # 3 Validação: Verificando comandos maliciosos
        malicious_errors = self.malicious_checker.validate(tree)
        if malicious_errors:
            return ValidateResponse.create(valid=False, answer=malicious_errors, thought="")

        # Caso passe em todas as validações, faz uma validação da semântica
        """
        semantic_feedback = self.semantics_validator.validator(code, tree, data.assistantStyle, self.openai_api_key, data.functionName)
        thought = semantic_feedback["pensamento"]
        answer = semantic_feedback["resposta"]
        """

        # Pega a pipeline
        spec, pipeline = resolve_pipeline(data.gameName, data.functionName)
        out = await pipeline.feedback(
            code=data.code,
            assistant_style=data.assistantStyle,
            function_name=data.functionName,
            openai_api_key=self.openai_api_key
        )
        # result: {"valid": bool, "answer": str, "thought": str}

        return ValidateResponse.create(valid=bool(out.get("valid", False)), answer=str(out.get("answer", "")),
            thought=str(out.get("thought", ""))
        )
    
    # Run 
    async def run(self, data: ValidateRequest) -> ValidateResponse:
        code = data.code

        # 1) Sintaxe
        response_validate = self.syntax_validator.validate(code, data.assistantStyle, self.openai_api_key)
        if response_validate:
            return ValidateResponse.create(
                valid=False,
                answer=response_validate.get("resposta", ""),
                thought=response_validate.get("pensamento", "")
            )

        # 2) AST para malicioso
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return ValidateResponse.create(False, "Erro de sintaxe ao analisar o código.", "")

        # 3) Malicioso
        malicious_errors = self.malicious_checker.validate(tree)
        if malicious_errors:
            return ValidateResponse.create(False, malicious_errors, "")

        # 4) Pipeline -> RUN
        spec, pipeline = resolve_pipeline(data.gameName, data.functionName)
        out = await pipeline.run(
            code=data.code,
            assistant_style=data.assistantStyle,
            function_name=data.functionName,
            openai_api_key=self.openai_api_key
        )

        return ValidateResponse.create(
            valid=bool(out.get("valid", False)),
            answer=str(out.get("answer", "")),
            thought=str(out.get("thought", ""))
        )

    