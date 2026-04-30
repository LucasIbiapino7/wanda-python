from .gamespec import GameSpec
from typing import Dict, List
from .pipelines.bits.pipeline import BitsPipeline
# from .pipelines.bits import JokenpoPipeline

REGISTRY: Dict[str, GameSpec] = {
    # "JOKENPO": GameSpec(
    #     name="JOKENPO",
    #     rulesVersion="20/10/2025",
    #     functions=["jokenpo1", "jokenpo2"],
    #     signature={
    #         "jokenpo1": ["colocar aqui a assinatura"],
    #         "jokenpo2": ["colocar aqui a assinatura"]
    #     },
    #     valid_returns={
    #         "jokenpo1": ["colocar aqui os retornos"],
    #         "jokenpo2": ["colocar aqui os retornos"]
    #     },
    #     prompts_key="jokenpo",
    #     pipeline_class=JokenpoPipeline()
    # ),
    "BITS": GameSpec(
        name="BITS",
        functions=["bits"],
        rulesVersion="27/10/2025",
        signature={
            "strategy": ["bit8", "bit16", "bit32", "firewall", "opp_last"]
        },
        valid_returns={
            "strategy": ["BIT8", "BIT16", "BIT32", "FIREWALL"]
        },
        prompts_key="bits",
        pipeline_class=BitsPipeline
    )
}