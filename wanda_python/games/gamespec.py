from typing import Dict, List
from dataclasses import dataclass

@dataclass(frozen=True)
class GameSpec:
    name: str
    rulesVersion: str
    functions: List[str]
    signature: Dict[str, List[str]]
    valid_returns: Dict[str, List[str]]
    prompts_key: str
    pipeline_class: type