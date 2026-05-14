from __future__ import annotations

from pydantic import BaseModel


class DayChannel(BaseModel):
    day: int
    round: int
    player: str
    message: str


class DaySummary(BaseModel):
    day: int
    summary: str


class WolfChannel(BaseModel):
    day: int
    round: int
    wolf: str
    message: str
    vote: str


class InvestigatorResult(BaseModel):
    day: int
    player_investigated: str
    role_revealed: str


class DayVote(BaseModel):
    voter: str
    votee: str
