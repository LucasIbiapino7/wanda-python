from typing import Protocol, Dict, Any, Tuple
from .registry import REGISTRY, GameSpec
from .pipelines.jokenpo.pipeline import JokenpoPipeline
from .pipelines.bits.pipeline import BitsPipeline
import logging

from pathlib import Path

import json
from .pipelines.base_pipeline import BasePipeline

logger = logging.getLogger(__name__)

# 1. Get the directory of the current file (router.py)
CURRENT_DIR = Path(__file__).parent

# 2. Join it with the JSON filename
JSON_PATH = CURRENT_DIR / "game_conf.json"

class GameFeedbackPipeline(Protocol):
    async def feedback(self, code: str, assistant_style: str, function_name: str, openai_api_key: str) -> dict:
        """
        Retorna dict padronizado:
        {
          "valid": bool,
          "answer": str,
          "thought": str
        }
        """
    async def run(self, code: str, assistant_style: str, function_name: str, openai_api_key: str) -> Dict[str, Any]:
        """
        Execução de testes do jogo (assinatura + testes).
        Retorna:
        {
          "valid": bool,
          "answer": str,
          "thought": str
        }
        """
    async def validate(self, code: str, assistant_style: str, function_name: str, openai_api_key: str) -> Dict[str, Any]:
        """
        Validação completa do jogo (assinatura + testes finais).
        Retorna:
        {
          "valid": bool,
          "answer": str,
          "thought": str
        }
        """

def resolve_pipeline(game_name: str, function_name: str) -> BasePipeline: # Tuple[GameSpec, GameFeedbackPipeline]:
    with open(JSON_PATH, "r") as games:
        games_conf: Dict[ str, Dict[str, Any] ] = json.load(games)

    # spec = REGISTRY.get(game_name)
    spec = games_conf.get(game_name) # Dados vêm do JSON em vez do REGISTRY

    if not spec:
        logger.error('Jogo nao suportado. game=%s', game_name)
        raise ValueError(f"Jogo não suportado: {game_name}")

    # print(f"DEBUG: Especificação do jogo {game_name}: {spec}")
    if function_name not in spec.get("functions", []):
        logger.error('Funcao invalida para o jogo. game=%s function=%s', game_name, function_name)
        raise ValueError(f"Função '{function_name}' não é válida para {game_name}")

    # Fábricas para cada jogo
    return BasePipeline.from_dict(spec)
    # return spec, spec.pipeline_class(spec) # No lugar de "pipeline_class", colocar "BasePipeline" ou algo assim, já que "spec" vem de um JSON

    # logger.error('Pipeline nao encontrado. game=%s', game_name)
    # raise ValueError(f"Pipeline não encontrado para {game_name}")