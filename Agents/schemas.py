from pydantic import BaseModel


class WolfNightDiscussOutput(BaseModel):
    message: str
    vote_target: str


class DayDiscussOutput(BaseModel):
    message: str


class DayVoteOutput(BaseModel):
    vote_target: str


class HealerOutput(BaseModel):
    healer_target: str


class InvestigatorOutput(BaseModel):
    investigator_target: str

