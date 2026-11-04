import redis
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import cache, models

best_score = func.max(models.Score.score)


def record_score(db: Session, user_id, player_name, score):
    try:
        if cache.redis_client.zcard(cache.LEADERBOARD_KEY) == 0:
            rebuild(db)
        else:
            cache.redis_client.zadd(cache.LEADERBOARD_KEY, {f"{user_id}:{player_name}": score}, gt=True)
    except redis.RedisError:
        pass


def best_per_player(db: Session):
    query = (
        select(models.Score.user_id, models.Score.player_name, best_score)
        .group_by(models.Score.user_id, models.Score.player_name)
        .order_by(best_score.desc())
    )
    return db.execute(query).all()


def rebuild(db: Session):
    rows = best_per_player(db)
    if not rows:
        return
    members = {f"{user_id}:{player_name}": score for user_id, player_name, score in rows}
    try:
        cache.redis_client.zadd(cache.LEADERBOARD_KEY, members)
    except redis.RedisError:
        pass


def get_top(db: Session, limit: int):
    try:
        rows = cache.redis_client.zrevrange(cache.LEADERBOARD_KEY, 0, limit - 1, withscores=True)
    except redis.RedisError:
        rows = []
    if rows:
        entries = []
        for rank, (member, score) in enumerate(rows, start=1):
            player_name = member.split(":", 1)[1]
            entries.append({"rank": rank, "player_name": player_name, "score": int(score)})
        return entries
    rows = best_per_player(db)[:limit]
    return [
        {"rank": rank, "player_name": player_name, "score": score}
        for rank, (_, player_name, score) in enumerate(rows, start=1)
    ]

def get_rank(db: Session, user_id, player_name):
    member = f"{user_id}:{player_name}"
    try:
        position = cache.redis_client.zrevrank(cache.LEADERBOARD_KEY, member)
        score = cache.redis_client.zscore(cache.LEADERBOARD_KEY, member)
    except redis.RedisError:
        position = score = None
    if position is not None and score is not None:
        return {"rank": position + 1, "player_name": player_name, "score": int(score)}
    for rank, (row_user_id, row_name, row_score) in enumerate(best_per_player(db), start=1):
        if row_user_id == user_id:
            return {"rank": rank, "player_name": row_name, "score": row_score}
    return None