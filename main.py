from fastapi import FastAPI, Query, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from datetime import datetime, timedelta
import os

app = FastAPI(title="Discord Vouch API")

# MongoDB setup
MONGO_URL = os.getenv("MONGO_URL")
if not MONGO_URL:
    raise ValueError("MONGO_URL environment variable is required")

client = AsyncIOMotorClient(MONGO_URL)
db = client["discord_api"]
users_col = db["users"]
vouch_col = db["vouches"]  # tracks who vouched for whom and when

COOLDOWN_HOURS = 12

# Helper to get leaderboard
async def get_leaderboard():
    return await users_col.find().sort("count", -1).to_list(length=100)

# Helper to get user position
async def get_user_position(user_id: str):
    leaderboard = await get_leaderboard()
    for i, u in enumerate(leaderboard):
        if u["user_id"] == user_id:
            return i + 1
    return None

@app.get("/api")
async def api(
    user: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    from_user: Optional[str] = Query(None, alias="from"),
    username: Optional[str] = Query(None)
):
    if type == "leaderboard":
        top_users = await users_col.find().sort("count", -1).limit(10).to_list(10)
        if not top_users:
            return "No vouches yet."
        text = "\n".join(
            [f"{i+1}. <@{u['user_id']}> - **{u.get('count', 0)}** vouches" for i, u in enumerate(top_users)]
        )
        return text

    if not user:
        raise HTTPException(status_code=400, detail="Missing user ID")

    if type == "view":
        user_data = await users_col.find_one({"user_id": user})
        count = user_data["count"] if user_data else 0
        position = await get_user_position(user)
        pos_text = position if position else "unranked"
        return f"<@{user}> has {count} vouches. Leaderboard position: {pos_text}"

    if type == "add":
        if not from_user:
            raise HTTPException(status_code=400, detail="Missing from user ID")

        # Check cooldown
        twelve_hours_ago = datetime.utcnow() - timedelta(hours=COOLDOWN_HOURS)
        recent_vouch = await vouch_col.find_one({
            "from_user": from_user,
            "to_user": user,
            "timestamp": {"$gte": twelve_hours_ago}
        })

        if recent_vouch:
            next_available = recent_vouch["timestamp"] + timedelta(hours=COOLDOWN_HOURS)
            remaining = next_available - datetime.utcnow()
            hours, remainder = divmod(remaining.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"You are on cooldown! Try again in {hours}h {minutes}m {seconds}s."

        # Update user count
        await users_col.update_one(
            {"user_id": user},
            {"$inc": {"count": 1}, "$set": {"username": username if username else user}},
            upsert=True
        )

        # Record vouch
        await vouch_col.insert_one({
            "from_user": from_user,
            "to_user": user,
            "timestamp": datetime.utcnow()
        })

        return f"<@{from_user}> has added a vouch to <@{user}>. Thanks for the good work!"

    if type == "remove":
        user_data = await users_col.find_one({"user_id": user})
        if not user_data or user_data.get("count", 0) <= 0:
            return f"<@{user}> has no vouches to remove."
        await users_col.update_one({"user_id": user}, {"$inc": {"count": -1}})
        new_count = (await users_col.find_one({"user_id": user}))["count"]
        return f"Removed 1 vouch from <@{user}>. New count: {new_count}"

    raise HTTPException(status_code=400, detail="Invalid type parameter")

