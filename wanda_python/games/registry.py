from .gamespec import GameSpec
from typing import Dict, List
from .pipelines.bits.pipeline import BitsPipeline
from .pipelines.jokenpo.pipeline import JokenpoPipeline

REGISTRY: Dict[str, GameSpec] = {
    "JOKENPO": GameSpec(
        name="JOKENPO",
        rulesVersion="20/10/2025",
        functions=["jokenpo1", "jokenpo2"],
        signature={
            "jokenpo1": {
                "strategy": ["card1", "card2", "card3"]
            },
            "jokenpo2": {
                "strategy": ["card1", "card2", "opponentCard1", "opponentCard2"]
            }
        },
        valid_returns={
            "jokenpo1": ["pedra", "papel", "tesoura"],
            "jokenpo2": ["pedra", "papel", "tesoura"]
        },
        prompts_key="jokenpo",
        pipeline_class=JokenpoPipeline
    ),
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