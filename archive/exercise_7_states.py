from typing import Annotated, TypedDict, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field
from operator import add

class DayChannel(BaseModel):
    # Chat Channels for daytime discussions, accessible to all players
    day: int
    round: int
    player: str
    message: str
    

class WolfChannel(BaseModel):
    # Chat Channels for nighttime discussions, accessible only to werewolf players
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

class OrchestratorGraph(TypedDict):
    day_channel: Annotated[list[DayChannel], add]
    wolf_channel: Annotated[list[WolfChannel], add]
    
    roles: dict[str, str] # Mapping of player names to their roles (e.g., "Alice": "Villager", "Bob": "Werewolf")
    human_player: str
    healer_player: str | None
    investigator_player: str | None
    
    wolves_kill_target: str | None
    healer_target: str | None
    investigator_target: str | None
    
    investigator_results: Annotated[list[InvestigatorResult], add]
    
    # Day votes, consumed by day resolution
    day_votes: list[DayVote] # [{'voter':player_A, 'votee':player_B}] 
    
    voted_player: str | None
    
    surviving_wolves: list[str]
    surviving_villagers: list[str]
    
    current_day: int
    
    winner: str | None
    

    
    



    