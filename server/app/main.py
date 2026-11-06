import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

from . import models, ranking, schemas
from .auth import CurrentUser, get_current_user, get_optional_user
from .database import Base, SessionLocal, engine, get_db
from .django_app import django_asgi


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        ranking.rebuild(db)
    yield


app = FastAPI(title="Arena Survival API", lifespan=lifespan)


# only my landing page may read the leaderboard from a browser, and only with GET
allowed_origins = [origin for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin]
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_methods=["GET"])

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/scores", response_model=schemas.ScoreOut, status_code=201)
def submit_score(
    payload: schemas.ScoreCreate,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    score = models.Score(user_id=user.id, player_name=user.username[:20], **payload.model_dump())
    db.add(score)
    db.commit()
    db.refresh(score)
    ranking.record_score(db, user.id, score.player_name, score.score)
    return score


@app.get("/leaderboard", response_model=schemas.LeaderboardOut)
def leaderboard(
    limit: int = Query(10, ge=1, le=100),
    user: CurrentUser | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    me = ranking.get_rank(db, user.id, user.username[:20]) if user else None
    return {"entries": ranking.get_top(db, limit), "me": me}


@app.get("/me", response_model=schemas.MeOut)
def me(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    total_runs = db.scalar(select(func.count()).select_from(models.Score).where(models.Score.user_id == user.id))
    rank = ranking.get_rank(db, user.id, user.username[:20])
    return {
        "username": user.username,
        "total_runs": total_runs,
        "best_score": rank["score"] if rank else None,
        "rank": rank["rank"] if rank else None,
    }


# Django answers everything FastAPI does not: /api/register, /api/login and /admin/
app.mount("/", django_asgi)