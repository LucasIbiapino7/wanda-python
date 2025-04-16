from wanda_python.schema.validate_dto import ValidateRequest, ValidateResponse
from dotenv import load_dotenv
from wanda_python.validators.syntax_validator import SyntaxValidator
from wanda_python.validators.signature_validator import SignatureValidator
from wanda_python.validators.malicious_checker import MaliciousChecker
from wanda_python.validators.execution_validator import ExecutionValidator
from wanda_python.validators.semantics_validator import SemanticsValidator

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
        code = data.code # Pega a função

        # 1 Validação: Sintexe e indentação
        response_validate = self.syntax_validator.validate(code, data.assistantStyle, self.openai_api_key)
        if response_validate:
            resposta_dict = json.loads(response_validate)
            thought = resposta_dict["pensamento"]
            answer = resposta_dict["resposta"]
            return ValidateResponse.create(valid=False, answer=answer, thought=thought)
        
        tree = ast.parse(code) # Vai ser usada nas próximas duas validações (árvore do código)

        # 2 Validação: Assinatura e argumentos
        response_validate = self.signature_validator.validate_signature_and_parameters(tree, data.assistantStyle, data.functionName)
        if response_validate:
            return ValidateResponse.create(valid=False, answer=response_validate, thought="")

        # 3 Validação: Verificando comandos maliciosos
        malicious_errors = self.malicious_checker.validate(tree)
        if malicious_errors:
            return ValidateResponse.create(valid=False, answer=malicious_errors, thought="")
        
        # 4 Validação: Executa uma bateria de testes
        execution_errors = self.execution_validator.validator(code, data.assistantStyle, data.functionName, self.openai_api_key)
        if execution_errors:
            resposta_dict_execution = json.loads(execution_errors)
            thought = resposta_dict_execution["pensamento"]
            answer = resposta_dict_execution["resposta"]
            return ValidateResponse.create(valid=False, answer=answer, thought=thought)
        
        return ValidateResponse.create(valid=True, answer="aceita", thought="") # Passou em todas as validações

    # service -> Feedback
    async def feedback(self, data: ValidateRequest) -> ValidateResponse:
        code = data.code # Pega a função
        # 1 Validação: Sintaxe e indentação
        response_validate = self.syntax_validator.validate(code, data.assistantStyle, self.openai_api_key)
        if response_validate:
            resposta_dict = json.loads(response_validate)
            thought = resposta_dict["pensamento"]
            answer = resposta_dict["resposta"]
            return ValidateResponse.create(valid=False, answer=answer, thought=thought)
        
        tree = ast.parse(code) # Vai ser usada nas próximas duas validações
        # 2 Validação: Assinatura e argumentos
        response_validate = self.signature_validator.validate_signature_and_parameters(tree, data.assistantStyle, data.functionName)
        if response_validate:
            return ValidateResponse.create(valid=False, answer=response_validate, thought="")

        # 3 Validação: Verificando comandos maliciosos
        malicious_errors = self.malicious_checker.validate(tree)
        if malicious_errors:
            return ValidateResponse.create(valid=False, answer=malicious_errors, thought="")

        # Caso passe em todas as validações, faz uma validação da semântica
        semantic_feedback = self.semantics_validator.validator(code, tree, data.assistantStyle, self.openai_api_key, data.functionName)
        thought = semantic_feedback["pensamento"]
        answer = semantic_feedback["resposta"]

        return ValidateResponse.create(valid=True, answer=answer, thought=thought) 
    
    async def run (self, data: ValidateRequest) -> ValidateResponse:

        code = data.code

        response_validate = self.syntax_validator.validate(code, data.assistantStyle, self.openai_api_key)
        if response_validate:
            resposta_dict = json.loads(response_validate)
            thought = resposta_dict["pensamento"]
            answer = resposta_dict["resposta"]
            return ValidateResponse.create(valid=False, answer=answer, thought=thought)
        
        tree = ast.parse(code) # Vai ser usada nas próximas duas validações (árvore do código)
        # 2 Validação: Assinatura e argumentos
        response_validate = self.signature_validator.validate_signature_and_parameters(tree, data.assistantStyle, data.functionName)
        if response_validate:
            return ValidateResponse.create(valid=False, answer=response_validate, thought="")

        # 3 Validação: Verificando comandos maliciosos
        malicious_errors = self.malicious_checker.validate(tree)
        if malicious_errors:
            return ValidateResponse.create(valid=False, answer=malicious_errors, thought="")

        # 4 Chama a função que vai rodar os testes
        feedback_tests = self.execution_validator.feedback_tests(code, data.assistantStyle, data.functionName, self.openai_api_key)
        resposta_dict = json.loads(feedback_tests)

        return ValidateResponse.create(valid=True, answer=resposta_dict["resposta"], thought=resposta_dict["pensamento"])
    