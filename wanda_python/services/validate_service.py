from wanda_python.schema.validate_dto import ValidateRequest, ValidateResponse
from dotenv import load_dotenv

import os
import openai
import ast

class ValidateService:

    def __init__(self):
        load_dotenv()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

    async def validate(self, data: ValidateRequest) -> ValidateResponse:
        errors = []

        code = data.code # Pega a função

        # 1 Validação: Sintexe e indentação
        response_validate = self.validate_sintaxe_and_indentation(code)
        if response_validate:
            errors.append(response_validate)
            return ValidateResponse.create(valid=False, errors=errors)
        
        tree = ast.parse(code) # Vai ser usada nas próximas duas validações (árvore do código)

        # 2 Validação: Assinatura e argumentos
        response_validate = self.validate_signature_and_parameters(tree)
        if response_validate:
            errors.append(response_validate)
            return ValidateResponse.create(valid=False, errors=errors)

        # 3 Validação: Verificando comandos maliciosos
        malicious_errors = check_for_malicious_code_in_tree(tree)
        if malicious_errors:
            errors.append(malicious_errors)
            return ValidateResponse.create(valid=False, errors=errors)
        
        return ValidateResponse.create(valid=True, errors=errors) # Passou em todas as validações

    async def feedback(self, data: ValidateRequest) -> ValidateResponse:
        errors = []

        code = data.code # Pega a função

        # 1 Validação: Sintexe e indentação
        try:
            compile(code, "<string>", "exec")
        except (SyntaxError, IndentationError) as err:
            error_message = self.feedback_sintaxe_openai(code) # Chama a função que usa a IA
            errors.append(error_message) # Adiciona a mensagem da LLM
            return ValidateResponse.create(valid=False, errors=errors)

        # 2 Validação: Assinatura da função
        tree = ast.parse(code)
        # Verificando a presença da função strategy:
        strategy_function = None
        for node in ast.walk(tree): #percorre
            if isinstance(node, ast.FunctionDef) and node.name == "strategy":
                strategy_function = node
                break

        if not strategy_function:
            error_message = (
                "Olá! Parece que eu não consegui encontrar a função 'strategy' no seu código. "
                "Certifique-se de que ela esteja declarada assim:\n\n"
                "def strategy(card1, card2, card3, opponentCard1, opponentCard2, opponentCard3):\n"
                "    # Seu código aqui\n\n"
                "Estou aqui para ajudar, então se precisar, revise cuidadosamente o nome e a indentação!"
            )
            errors.append(error_message)
            return ValidateResponse.create(valid=False, errors=errors) # Cria e Retorna o DTO
        
        # Verificando a assinatura da função:
        expected_args = ["card1", "card2", "card3", "opponentCard1", "opponentCard2", "opponentCard3"]
        actual_args = [arg.arg for arg in strategy_function.args.args]

        if actual_args != expected_args:
            error_message = (
                f"Ei! A assinatura da sua função 'strategy' não está do jeitinho que esperamos.\n\n"
                f"Esperávamos estes parâmetros: {expected_args}\n"
                f"Mas encontramos: {actual_args}.\n\n"
                "Tente corrigir para que fique na ordem e nomes corretos, beleza?"
            )
            errors.append(error_message)

        if errors:
            return ValidateResponse.create(valid=False, errors=errors) # Cria e Retorna o DTO
        
        # 3 Validação: Verificando comandos maliciosos

        malicious_errors = check_for_malicious_code_in_tree(tree)
        if malicious_errors:
            # Constrói uma mensagem de feedback única, listando cada erro
            message_lines = [
                "Olá! Seu código parece conter alguns comandos que podem ser perigosos ou proibidos:",
                ""
            ]
            for err in malicious_errors:
                message_lines.append(f"• {err}")
            message_lines.append("")
            message_lines.append(
                "Para manter o ambiente seguro, desabilitamos o uso desses módulos/funções. "
                "Por favor, remova ou substitua esses trechos de código. "
                "Estou aqui para ajudar caso precise de sugestões!"
            )
            # Converte o array em uma string única
            final_message = "\n".join(message_lines)
            errors.append(final_message)
            return ValidateResponse.create(valid=False, errors=errors)
        # --------------------------------------------------------------

        # Caso passe em todas as validações, faz uma validação de lógica
        logic_message = self.feedback_logic_openai(code)
        errors.append(logic_message)
        return ValidateResponse.create(valid=True, errors=errors) # Cria e Retorna o DTO
    
    
    def validate_sintaxe_and_indentation(self, code: str) -> str:
        """
        Função responsável por verificar a sintaxe e indentação do código.
        Recebe o código do aluno (code) e retorna uma String vazia caso não tenha erros, ou caso tenha um erro
        Chama a função que manda o código pra LLM, retornando essa resposta        
        """
        try:
            compile(code, "<string>", "exec")
            return ""
        except (SyntaxError, IndentationError) as err:
            error_message = self.feedback_sintaxe_openai(code) # Chama a função que usa a IA
            return error_message # Resposta da LLM
    
    def validate_signature_and_parameters(tree: ast.AST) -> str:
        """
        Função responsável por validar a assinatura da função, verificando a presença da função "strategy" e 
        se os parametros são os esperados: 
        "card1", "card2", "card3", "opponentCard1", "opponentCard2", "opponentCard3"
        Caso não passe em um desses dois testes, retorna uma resposta personalizada, caso passe, retorna 
        uma String vazia
        """

        # Verificando a presença da função strategy:
        strategy_function = None
        for node in ast.walk(tree): 
            if isinstance(node, ast.FunctionDef) and node.name == "strategy":
                strategy_function = node
                break

        if not strategy_function:
            error_message = (
                "Olá! Parece que eu não consegui encontrar a função 'strategy' no seu código. "
                "Certifique-se de que ela esteja declarada assim:\n\n"
                "def strategy(card1, card2, card3, opponentCard1, opponentCard2, opponentCard3):\n"
                "    # Seu código aqui\n\n"
                "Estou aqui para ajudar, então se precisar, revise cuidadosamente o nome e a indentação!"
            )
            return error_message
        
        # Verificando a assinatura da função:
        expected_args = ["card1", "card2", "card3", "opponentCard1", "opponentCard2", "opponentCard3"]
        actual_args = [arg.arg for arg in strategy_function.args.args]

        if actual_args != expected_args:
            error_message = (
                f"Ei! A assinatura da sua função 'strategy' não está do jeitinho que esperamos.\n\n"
                f"Esperávamos estes parâmetros: {expected_args}\n"
                f"Mas encontramos: {actual_args}.\n\n"
                "Tente corrigir para que fique na ordem e nomes corretos, beleza?"
            )
            return error_message
        
        return "" # Sem erros

    def feedback_logic_openai(self, code: str) -> str:
        client = openai.OpenAI(api_key=self.openai_api_key)

        prompt = f"""
         Você é um assistente virtual de programação Python para alunos do primeiro período.
        Nesse ponto, o código do aliuno já passou pela análise de sintaxe, assinatura e indexação, parabenize ele e diga
        que o código já pode ser salvo, e que aqui vão algumas dicas sobre a lógica do código.
        Analise a lógica do código e dê dicas de possíveis melhorias, principalmente sobre estes pontos:

        1) A função leva em consideração as cartas do oponente (opponentCard1, opponentCard2, opponentCard3)?
        2) A função retorna as strings: pedra, papel e tesoura? falta alguma delas ou estão todas no código?

        {code}

        Fale em primeira pessoa, como se estivesse conversando amigavelmente com o aluno.
        Use uma linguagem leve e não muito técnica.

        Não apresente o código corrigido por completo. Ao invés disso, explique o que houve e como corrigir, 
        dando pistas específicas (por exemplo, “você pode verificar se no seu if...”), mas sem reescrever todo o código.
        """

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300 
            )
            answer = response.choices[0].message.content
            return answer
        except Exception as e:
            print(f"Erro ao chamar a API da OpenAI: {e}")

    def feedback_sintaxe_openai(self, code: str) -> str:
        client = openai.OpenAI(api_key=self.openai_api_key)

        prompt = f"""
        Você é um assistente virtual de programação Python para alunos do primeiro período.
        O código abaixo possui erros de sintaxe ou indentação — concentre-se exclusivamente neles.

        {code}

        Fale em primeira pessoa, como se estivesse conversando amigavelmente com o aluno.
        Use uma linguagem leve e não muito técnica.
        Não apresente o código corrigido por completo. Ao invés disso, explique o que houve e como corrigir, dando pistas específicas (por exemplo, “na linha X precisa de dois-pontos”), mas sem reescrever todo o código.
        Não comente sobre lógica ou melhorias que não sejam estritamente relacionadas a sintaxe/indentação.
        """

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300 
            )
            
            answer = response.choices[0].message.content
            return answer
        except Exception as e:
            print(f"Erro ao chamar a API da OpenAI: {e}")

def check_for_malicious_code_in_tree(tree: ast.AST) -> str:
    """
    Recebe a árvore de sintaxe (AST) já parseada e 
    verifica se há uso de módulos/funções proibidas.
    Retorna uma lista de erros (strings).
    """
    errors = []

     # 1) Módulos que não devem ser importados
    suspicious_modules = {
        "os": "Uso do módulo os é proibido",
        "sys": "Uso do módulo sys é proibido",
        "subprocess": "Uso do módulo subprocess é proibido",
        "shutil": "Uso do módulo shutil é proibido",
    }

    # 2) Funções/builtins proibidos (chamadas diretas)
    suspicious_builtins = {
        "exec": "Uso de exec() é proibido",
        "eval": "Uso de eval() é proibido",
        "compile": "Uso de compile() é proibido",
        "open": "Uso de open() é proibido",
        "__import__": "Uso de __import__() é proibido"
    }

     # 3) Chamadas em módulos que são explícitas, ex.: os.system, subprocess.Popen, etc.
    #    Cada tupla (modulo, funcao) -> mensagem de erro
    suspicious_module_calls = {
        ("os", "system"): "Chamar os.system() é proibido",
        ("os", "popen"): "Chamar os.popen() é proibido",
        ("subprocess", "Popen"): "Chamar subprocess.Popen() é proibido",
        ("subprocess", "run"): "Chamar subprocess.run() é proibido"
    }

    for node in ast.walk(tree):
        # Detectando imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in suspicious_modules:
                    errors.append(
                        f"Encontrado import proibido: 'import {alias.name}'. {suspicious_modules[alias.name]}"
                    )
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module in suspicious_modules:
                errors.append(
                    f"Encontrado import proibido: 'from {node.module} import ...'. {suspicious_modules[node.module]}"
                )
        
        # Detectando chamadas proibidas
        elif isinstance(node, ast.Call):
            # Ex.: exec(), eval()
            if isinstance(node.func, ast.Name):
                if node.func.id in suspicious_builtins:
                    errors.append(
                        f"Uso de função proibida: '{node.func.id}'. {suspicious_builtins[node.func.id]}"
                    )
            # Ex.: os.system
            elif isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    module_name = node.func.value.id
                    func_attr = node.func.attr
                    if (module_name, func_attr) in suspicious_module_calls:
                        errors.append(
                            f"Uso de chamada proibida: '{module_name}.{func_attr}'. "
                            f"{suspicious_module_calls[(module_name, func_attr)]}"
                        )
    if errors:
        # Constrói uma mensagem de feedback única, listando cada erro
        message_lines = [
            "Olá! Seu código parece conter alguns comandos que podem ser perigosos ou proibidos:",
            ""
        ]
        for err in errors:
            message_lines.append(f"• {err}")
            
        message_lines.append("")
        message_lines.append(
            "Para manter o ambiente seguro, desabilitamos o uso desses módulos/funções. "
            "Por favor, remova ou substitua esses trechos de código. "
            "Estou aqui para ajudar caso precise de sugestões!"
        )
            
        # Converte o array em uma string única
        final_message = "\n".join(message_lines)
        return final_message
    return ""
        