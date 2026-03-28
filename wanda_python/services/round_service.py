from wanda_python.schema.round_dto import RoundRequestDTO, RoundResponseDTO
from wanda_python.runner.container_runner import (create_session as runner_create_session,
    execute_round as runner_execute_round, close_session as runner_close_session)
from typing import List, Optional, Any
import logging

logger = logging.getLogger(__name__)

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
            logger.info('Round iniciado')
            # executar dinamicamente a função do jogador 1
            player1_choice = await self.execute_player_function(
                data.player1Function, data.player1Parameters
            )

            # executar dinamicamente a função do jogador 2
            player2_choice = await self.execute_player_function(
                data.player2Function, data.player2Parameters
            )
            logger.info('Round concluido. player1=%s player2=%s', player1_choice, player2_choice)

            # Retorna as escolhas
            return RoundResponseDTO.create(player1_choice=player1_choice, player2_choice=player2_choice)
        except Exception as err:
            logger.error('Erro no round. erro=%s', str(err), exc_info=True)
            return RoundResponseDTO.create(player1_choice=None, player2_choice=None)
    
    async def execute_player_function(self, function_code: str, parameters: List[Any]) -> str:
        try:
            # Criar um ambiente local para execução segura
            local_env = {}
            exec(function_code, {}, local_env)

            # Recuperar a função 'strategy' do ambiente local
            strategy_function = local_env["strategy"]

            # Chamar a função 'strategy' com os parâmetros fornecidos
            return strategy_function(*parameters)
        except Exception as err:
            logger.error('Erro ao executar funcao do jogador. erro=%s', str(err), exc_info=True)
            raise err

    async def create_session(self, code_p1: str, code_p2: str) -> str:
        logger.info('Criando sessao de partida')
        session_id = await runner_create_session(code_p1, code_p2)
        logger.info('Sessao criada. session_id=%s', session_id)
        return session_id

    async def execute_round(self, session_id: str, params_p1: list, params_p2: list, timeout: int = 5) -> dict:
        logger.info('Executando round. session_id=%s', session_id)
        result = await runner_execute_round(session_id, params_p1, params_p2, timeout)
        return result

    async def close_session(self, session_id: str) -> None:
        logger.info('Encerrando sessao. session_id=%s', session_id)
        await runner_close_session(session_id)