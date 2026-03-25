from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.enums import ActionType


@dataclass
class Action:
    type: ActionType
    payload: dict | None = None
