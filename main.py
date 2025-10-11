from fastapi import FastAPI, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import os

app = FastAPI(title="Discord Counts API")

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URL")
if not MONGO_URI:
    raise ValueError("NO MONGO")

client = AsyncIOMotorClient(MONGO_URL)
db = client["discord_api"]
collection = db["users"]

# Helper function to get a user
async def get_user(user_id: str):
    return await collection.find_one({"user_id": user_id})

@app.get("/api")
async def api(
    user: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    username: Optional[str] = Query(None)  # optional username parameter
):
    # Leaderboard endpoint
    if type == "leaderboard":
        top_users = await collection.find().sort("count", -1).limit(12).to_list(12)
        if not top_users:
            return {"leaderboard": "No users yet."}

        leaderboard_text = "\n".join(
            [
                f"{i+1}. {u.get('username', u['user_id'])} - **{u.get('count', 0)}** Count"
                for i, u in enumerate(top_users)
            ]
        )
        return {"leaderboard": leaderboard_text}

    # Other endpoints require user ID
    if not user:
        raise HTTPException(status_code=400, detail="Missing user ID")

    # VIEW count
    if type == "view":
        user_data = await get_user(user)
        count = user_data["count"] if user_data else 0
        # Optionally update username if provided
        if username:
            await collection.update_one(
                {"user_id": user},
                {"$set": {"username": username}},
                upsert=True
            )
        return {"user_id": user, "count": count}

    # ADD count
    elif type == "add":
        await collection.update_one(
            {"user_id": user},
            {"$inc": {"count": 1}, "$set": {"username": username if username else user}},
            upsert=True
        )
        user_data = await get_user(user)
        return {"message": "Count incremented", "count": user_data["count"]}

    # REMOVE count
    elif type == "remove":
        user_data = await get_user(user)
        if not user_data or user_data["count"] <= 0:
            raise HTTPException(status_code=400, detail="User has no counts to remove")
        await collection.update_one({"user_id": user}, {"$inc": {"count": -1}})
        user_data = await get_user(user)
        return {"message": "Count decremented", "count": user_data["count"]}

    else:
        raise HTTPException(status_code=400, detail="Invalid type parameter")
