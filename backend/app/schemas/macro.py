from typing import Literal

from pydantic import BaseModel

MacroSentiment = Literal["POSITIVE", "NEGATIVE", "NEUTRAL"]
MacroImpact = Literal["HIGH", "MEDIUM", "LOW"]


class MacroIndicator(BaseModel):
    id: str
    label: str
    value: str
    change_label: str
    sentiment: MacroSentiment
    description: str


class MacroEvent(BaseModel):
    id: str
    title: str
    date: str
    impact: MacroImpact
    forecast: str
    previous: str
