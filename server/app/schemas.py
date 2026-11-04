from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ScoreCreate(BaseModel):
    score: int = Field(ge=0, le=100_000)
    wave_reached: int = Field(ge=1, le=10)
    won: bool = False


class ScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    player_name: str
    score: int
    wave_reached: int
    won: bool
    created_at: datetime

class LeaderboardEntry(BaseModel):
    rank: int
    player_name: str
    score: int

class MyRank(BaseModel):
    rank: int
    player_name: str
    score: int


class LeaderboardOut(BaseModel):
    entries: list[LeaderboardEntry]
    me: MyRank | None = None


class MeOut(BaseModel):
    username: str
    total_runs: int
    best_score: int | None
    rank: int | None