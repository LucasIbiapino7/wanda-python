import ast

class MaliciousChecker:
    def validate(self, tree: ast.AST) -> str:
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