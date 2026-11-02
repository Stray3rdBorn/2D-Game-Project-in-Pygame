from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models, ranking, schemas
from .database import Base, SessionLocal, engine, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        ranking.rebuild(db)
    yield


app = FastAPI(title="Arena Survival API", lifespan=lifespan)

def get_current_user(x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    if x_api_key is None:
        raise HTTPException(status_code=401, detail="Missing API key")
    api_key = db.scalar(select(models.ApiKey).where(models.ApiKey.key == x_api_key))
    if api_key is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return db.get(models.DjangoUser, api_key.user_id)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/scores", response_model=schemas.ScoreOut, status_code=201)
def submit_score(
    payload: schemas.ScoreCreate,
    user: models.DjangoUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    score = models.Score(user_id=user.id, player_name=user.username[:20], **payload.model_dump())
    db.add(score)
    db.commit()
    db.refresh(score)
    ranking.record_score(db, user.id, score.player_name, score.score)
    return score


@app.get("/leaderboard", response_model=list[schemas.LeaderboardEntry])
def leaderboard(limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    return ranking.get_top(db, limit)