from wanda_python.schema.validate_dto import ValidateRequest, ValidateResponse
from dotenv import load_dotenv
from wanda_python.validators.syntax_validator import SyntaxValidator
from wanda_python.validators.signature_validator import SignatureValidator
from wanda_python.validators.malicious_checker import MaliciousChecker
from wanda_python.validators.execution_validator import ExecutionValidator

import json

import os
import openai
import ast

class ValidateService:

    def __init__(self):
        load_dotenv()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.syntax_validator = SyntaxValidator()
        self.signature_validator = SignatureValidator()
        self.malicious_checker = MaliciousChecker()
        self.execution_validator = ExecutionValidator()

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
        response_validate = self.signature_validator.validate_signature_and_parameters(tree, data.assistantStyle)
        if response_validate:
            return ValidateResponse.create(valid=False, answer=response_validate, thought="")

        # 3 Validação: Verificando comandos maliciosos
        malicious_errors = self.malicious_checker.validate(tree)
        if malicious_errors:
            return ValidateResponse.create(valid=False, answer=malicious_errors, thought="")
        
        # 4 Validação: Executa uma bateria de testes
        execution_errors = self.execution_validator.validator(code, data.assistantStyle)
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
        
        tree = ast.parse(code) # Vai ser usada nas próximas duas validações (árvore do código)
        # 2 Validação: Assinatura e argumentos
        response_validate = self.signature_validator.validate_signature_and_parameters(tree, data.assistantStyle)
        if response_validate:
            return ValidateResponse.create(valid=False, answer=response_validate, thought="")

        # 3 Validação: Verificando comandos maliciosos
        malicious_errors = self.malicious_checker.validate(tree)
        if malicious_errors:
            return ValidateResponse.create(valid=False, answer=malicious_errors, thought="")

        # Caso passe em todas as validações, faz uma validação da semântica
        semantic_feedback = self.feedback_semantics(code, tree, data.assistantStyle)
        resposta_dict = json.loads(semantic_feedback)

        return ValidateResponse.create(valid=True, answer=resposta_dict["resposta"], thought=resposta_dict["pensamento"]) # Cria e Retorna o DTO
    
    def validate_sintaxe_and_indentation(self, code: str, assistantStyle: str) -> str:
        """
        Função responsável por verificar a sintaxe e indentação do código.
        Recebe o código do aluno (code) e retorna uma String vazia caso não tenha erros, ou caso tenha um erro
        Chama a função que manda o código pra LLM, retornando essa resposta        
        """
        try:
            compile(code, "<string>", "exec")
            return ""
        except (SyntaxError, IndentationError) as err:
            llm_answer = self.feedback_sintaxe_openai(code, err, assistantStyle) # Chama a função que usa a IA
            return llm_answer # Resposta da LLM
    
    def validate_signature_and_parameters(self, tree: ast.AST, assistant_style: str) -> str:
        """
        Função responsável por validar a assinatura da função, verificando a presença da função 'strategy' e 
        se os parâmetros são os esperados:
        "card1", "card2", "card3", "opponentCard1", "opponentCard2", "opponentCard3".
        
        Se houver algum problema (função inexistente ou parâmetros incorretos),
        retorna uma mensagem de erro condizente com o estilo do agente (assistant_style).
        Caso esteja tudo certo, retorna uma string vazia.
        """

        # Mapear mensagens de erro conforme o estilo
        messages = {
            "VERBOSE": {
                "missing_function": (
                    "Olá! Sabe, estou olhando seu código e não consegui achar a função 'strategy'.\n"
                    "Ela precisa estar assim:\n\n"
                    "def strategy(card1, card2, card3, opponentCard1, opponentCard2, opponentCard3):\n"
                    "    # Seu código\n\n"
                    "Verifique se o nome está correto e se não houve problemas de indentação! Estou aqui pra ajudar."
                ),
                "wrong_signature": (
                    "Ei! Parece que a sua função 'strategy' não tem os parâmetros na ordem esperada.\n"
                    "Devem ser: card1, card2, card3, opponentCard1, opponentCard2, opponentCard3.\n"
                    "Dê uma olhada e certifique-se de que eles estejam no lugar certinho, tá bom?"
                )
            },
            "SUCCINCT": {
                "missing_function": (
                    "Função 'strategy' não encontrada. Ela deve ser:\n"
                    "def strategy(card1, card2, card3, opponentCard1, opponentCard2, opponentCard3):"
                ),
                "wrong_signature": (
                    "A função 'strategy' existe, mas os parâmetros não batem.\n"
                    "Use: card1, card2, card3, opponentCard1, opponentCard2, opponentCard3."
                )
            },
            "INTERMEDIATE": {
                "missing_function": (
                    "Não achei a função 'strategy' no seu código. Ela precisa estar declarada como:\n"
                    "def strategy(card1, card2, card3, opponentCard1, opponentCard2, opponentCard3):\n"
                    "Verifique o nome e a indentação para garantir que esteja certo, ok?"
                ),
                "wrong_signature": (
                    "A função 'strategy' foi encontrada, mas os parâmetros não estão corretos.\n"
                    "Eles devem ser: card1, card2, card3, opponentCard1, opponentCard2, opponentCard3.\n"
                    "Dê uma revisada pra garantir que estejam nessa ordem."
                )
            }
        }

        # Escolher o dicionário de acordo com o estilo
        # Se vier algo inválido, use SUCCINCT como fallback, por exemplo
        style_dict = messages.get(assistant_style, messages["SUCCINCT"])

        # === Lógica de verificação ===
        
        # Verificando a presença da função strategy:
        strategy_function = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "strategy":
                strategy_function = node
                break

        if not strategy_function:
            # retorna mensagem "missing_function" conforme estilo
            return style_dict["missing_function"]

        # Verificando a assinatura da função
        expected_args = [
            "card1", "card2", "card3",
            "opponentCard1", "opponentCard2", "opponentCard3"
        ]
        actual_args = [arg.arg for arg in strategy_function.args.args]

        if actual_args != expected_args:
            return style_dict["wrong_signature"]

        return ""  # Sem erros

    def feedback_semantics(self, code: str, tree: ast.AST, assistantStyle: str) -> str:
        client = openai.OpenAI(api_key=self.openai_api_key)

        strategy_function = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "strategy":
                strategy_function = node
                break

        expected_args = {"card1", "card2", "card3", "opponentCard1", "opponentCard2","opponentCard3",}
        used_params = set()

        # Percorre todos os nós dentro do corpo da função
        for node in ast.walk(strategy_function):
            # Verifica se é um Name e se ele corresponde a um dos parâmetros
            if isinstance(node, ast.Name) and node.id in expected_args:
                if isinstance(node.ctx, ast.Load):
                    used_params.add(node.id)

        prompt_verbose = f"""
        Você é um assistente virtual de programação Python integrado à plataforma Wanda,
        um sistema voltado para alunos iniciantes que estão aprendendo a programar em python, por meio de um
        jogo chamado Jokenpo, que por padrão tem seis parâmetros sempre na função strategy: (card1, card2, card3, opponentCard1, opponentCard2,
        opponentCard3). e que podem ser usados para melhorar a estratégia do aluno

        o código do aluno:
        {code}

        parâmetros usados pelo aluno em sua estratégia:
        {used_params}

        Utilizando o código acima e usando a técnica CoT você deve fazer uma análise do código do aluno e dos parâmetros
        utilizados.

        Gere a resposta seguindo as seguintes regras:
        Fale em primeira pessoa, como se estivesse conversando amigavelmente com
        o aluno.
        Use uma linguagem leve e não muito técnica.
        sua resposta deve conter quantos parâmetros o aluno, e se é possível
        melhorar.
        fale apenas sobre os usos dos parâmetros, nada sobre a lógica.
        complete o json abaixo:
        {{
            "pensamento": String,
            "resposta": String
        }}
        """

        prompt_succint = f"""
        Você é um assistente virtual de programação Python integrado à plataforma Wanda,
        um sistema voltado para alunos iniciantes que estão aprendendo a programar em python, por meio de um
        jogo chamado Jokenpo, que por padrão tem seis parâmetros sempre na função strategy: (card1, card2, card3, opponentCard1, opponentCard2,
        opponentCard3). e que podem ser usados para melhorar a estratégia do aluno

        o código do aluno:
        {code}

        parâmetros usados pelo aluno em sua estratégia:
        {used_params}

        Utilizando o código acima e usando a técnica CoT você deve fazer uma análise do código do aluno e dos parâmetros
        utilizados.

        Gere a resposta seguindo as seguintes regras:
        Seja extremamente direto. Nada de explicações longas.
        Sem introduções ou despedidas.
        Sua resposta deve conter quantos parâmetros o aluno está usando.
        Fale apenas sobre os usos dos parâmetros, nada além disso.
        complete o json abaixo:
        {{
            "pensamento": String,
            "resposta": String
        }}
        """

        prompt_intermediary = f"""
        Você é um assistente virtual de programação Python integrado à plataforma Wanda,
        um sistema voltado para alunos iniciantes que estão aprendendo a programar em python, por meio de um
        jogo chamado Jokenpo, que por padrão tem seis parâmetros sempre na função strategy: (card1, card2, card3, opponentCard1, opponentCard2,
        opponentCard3). e que podem ser usados para melhorar a estratégia do aluno

        o código do aluno:
        {code}

        parâmetros usados pelo aluno em sua estratégia:
        {used_params}

        Utilizando o código acima e usando a técnica CoT você deve fazer uma análise do código do aluno e dos parâmetros
        utilizados.

        Gere a resposta seguindo as seguintes regras:
        Fale em primeira pessoa, sendo direto mas não muito sucinto.
        Use uma linguagem leve e não muito técnica.
        sua resposta deve conter quantos parâmetros o aluno, e se é possível
        melhorar.
        fale apenas sobre os usos dos parâmetros, nada sobre a lógica.
        complete o json abaixo:
        {{
            "pensamento": String,
            "resposta": String
        }}
        """

        if assistantStyle == "VERBOSE":
            prompt = prompt_verbose
        elif assistantStyle == "SUCCINCT":
            prompt = prompt_succint
        else:
            prompt = prompt_intermediary

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

    def feedback_sintaxe_openai(self, code: str, erro: str, assistantStyle: str) -> str:
        client = openai.OpenAI(api_key=self.openai_api_key)

        prompt_verbose = f"""
        Você é um assistente virtual de programação Python integrado à plataforma Wanda,
        um sistema voltado para alunos iniciantes que estão aprendendo a programar em python.
        
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
        Não apresente o código corrigido por completo. Ao invés disso, explique o que houve e como corrigir, 
        dando pistas específicas, mas sem reescrever todo o código.
        complete o json abaixo:
        {{
        "pensamento": String,
        "resposta": String
        }}
        """

        prompt_succint = f"""
        Você é um assistente virtual de programação Python integrado à plataforma Wanda,
        um sistema voltado para alunos iniciantes que estão aprendendo a programar em python.

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
        
        complete o json abaixo:
        {{
        "pensamento": String,
        "resposta": String
        }}
        """

        prompt_intermediary = f"""
        Você é um assistente virtual de programação Python integrado à plataforma Wanda,
        um sistema voltado para alunos iniciantes que estão aprendendo a programar em python.
        
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
        
        complete o json abaixo:
        {{
        "pensamento": String,
        "resposta": String
        }}
        """

        if assistantStyle == "VERBOSE":
            prompt = prompt_verbose
        elif assistantStyle == "SUCCINCT":
            prompt = prompt_succint
        else:
            prompt = prompt_intermediary

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
    
    def validate_execution(self, code: str, assistantStyle: str) -> str:
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
            "Seu código parece conter alguns comandos que podem ser perigosos ou proibidos:",
            ""
        ]
        for err in errors:
            message_lines.append(f"{err}")
            
        message_lines.append("")
        message_lines.append(
            "Para manter o ambiente seguro, desabilitamos o uso desses módulos/funções. "
            "Por favor, remova esses trechos de código. "
        )
            
        # Converte o array em uma string única
        final_message = "\n".join(message_lines)
        return final_message
    return ""
        