from wanda_python.schema.round_dto import RoundRequestDTO, RoundResponseDTO
from typing import List, Optional

class RoundService:

    async def round_choices(self, data: RoundRequestDTO):
        """
        Executa as funções dos dois jogadores, utilizando os parâmetros fornecidos,
        e retorna as escolhas de cada jogador.

        Args:
            data (RoundRequestDTO): Dados da rodada.

        Returns:
            RoundResponseDTO: Contém as escolhas feitas por cada jogador.
        """
        try:
            # executar dinamicamente a função do jogador 1
            player1_choice = await self.execute_player_function(
                data.player1Function, data.player1Parameters
            )

            # executar dinamicamente a função do jogador 2
            player2_choice = await self.execute_player_function(
                data.player2Function, data.player2Parameters
            )

            # Retorna as escolhas
            return RoundResponseDTO.create(player1_choice=player1_choice, player2_choice=player2_choice)
        except Exception as err:
            return RoundResponseDTO.create(player1_choice=None, player2_choice=None)
    
    async def execute_player_function(self, function_code: str, parameters: List[Optional[str]]) -> str:
         
        try:
            # Criar um ambiente local para execução segura
            local_env = {}
            exec(function_code, {}, local_env)

            # Recuperar a função 'strategy' do ambiente local
            strategy_function = local_env["strategy"]

            # Chamar a função 'strategy' com os parâmetros fornecidos
            return strategy_function(*parameters)
        except Exception as err:
            print(f"Erro ao executar a função do jogador: {err}")
            raise err