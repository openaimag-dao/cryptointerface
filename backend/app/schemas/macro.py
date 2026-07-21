from typing import Literal

from app.schemas.base import CamelModel

MacroSentiment = Literal["POSITIVE", "NEGATIVE", "NEUTRAL"]
MacroImpact = Literal["HIGH", "MEDIUM", "LOW"]


class MacroIndicator(CamelModel):
    id: str
    label: str
    value: str
    change_label: str
    sentiment: MacroSentiment
    description: str


class MacroEvent(CamelModel):
    id: str
    title: str
    date: str
    impact: MacroImpact
    forecast: str
    previous: str
