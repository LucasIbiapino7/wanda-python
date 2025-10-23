from dataclasses import dataclass
from typing import Dict, List

@dataclass(frozen=True)
class GameSpec:
    name: str
    rulesVersion: str
    functions: List[str]
    signature: Dict[str, List[str]]
    valid_returns: Dict[str, List[str]]
    prompts_key: str

REGISTRY: Dict[str, GameSpec] = {
    "JOKENPO": GameSpec(
        name="JOKENPO",
        rulesVersion="20/10/2025",
        functions=["jokenpo1", "jokenpo2"],
        signature={
            "jokenpo1": ["colocar aqui a assinatura"],
            "jokenpo2": ["colocar aqui a assinatura"]
        },
        valid_returns={
            "jokenpo1": ["colocar aqui os retornos"],
            "jokenpo2": ["colocar aqui os retornos"]
        },
        prompts_key="jokenpo"
    )
}