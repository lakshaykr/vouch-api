from fastapi import FastAPI, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from pydantic import BaseModel
import os

app = FastAPI(title="Discord Counts API")

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://LAKSHAY:X3bsJLUHWSdgrC2O@vortex.2dpuzhd.mongodb.net/?retryWrites=true&w=majority&appName=VORTEX")
client = AsyncIOMotorClient(MONGO_URI)
db = client["discord_api"]
collection = db["users"]

# Helper function
async def get_user(user_id: str):
    return await collection.find_one({"user_id": user_id})

# Main endpoint
@app.get("/api")
async def api(
    user: Optional[str] = Query(None),
    type: Optional[str] = Query(None)
):
    # Leaderboard endpoint
    if user is None and type == "leaderboard":
        top_users = (
            await collection.find().sort("count", -1).limit(12).to_list(12)
        )
        if not top_users:
            return {"leaderboard": "No users yet."}

        leaderboard_text = "\n".join(
            [f"{i+1}. {u['username']} - **{u['count']}** Count"
             for i, u in enumerate(top_users)]
        )
        return {"leaderboard": leaderboard_text}

    # For other types, user param must be provided
    if not user:
        raise HTTPException(status_code=400, detail="Missing user ID")

    # View count
    if type == "view":
        user_data = await get_user(user)
        count = user_data["count"] if user_data else 0
        return {"user_id": user, "count": count}

    # Add count
    elif type == "add":
        result = await collection.update_one(
            {"user_id": user},
            {"$inc": {"count": 1}},
            upsert=True
        )
        user_data = await get_user(user)
        return {"message": "Count incremented", "count": user_data["count"]}

    # Remove count
    elif type == "remove":
        user_data = await get_user(user)
        if not user_data or user_data["count"] <= 0:
            raise HTTPException(status_code=400, detail="User has no counts to remove")
        await collection.update_one({"user_id": user}, {"$inc": {"count": -1}})
        user_data = await get_user(user)
        return {"message": "Count decremented", "count": user_data["count"]}

    else:
        raise HTTPException(status_code=400, detail="Invalid type parameter")
