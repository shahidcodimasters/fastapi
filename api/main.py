from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
from pydantic import BaseModel
from typing import List, Optional
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB Connection with timeout settings
MONGO_DB_URL = os.getenv("MONGO_DB_URL", "mongodb+srv://shahidcodimasters_db_user:OpKk3sWNVMFdKcLf@cluster0.ktkqngb.mongodb.net/?appName=Cluster0&serverSelectionTimeoutMS=5000&connectTimeoutMS=10000")

try:
    client = MongoClient(MONGO_DB_URL)
    client.admin.command('ping')  # Test connection
    db = client["fastapi_db"]
    collection = db["users"]
    mongo_connected = True
except (ServerSelectionTimeoutError, ConnectionFailure) as e:
    print(f"MongoDB Connection Error: {e}")
    mongo_connected = False
    client = None
    db = None
    collection = None

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class User(BaseModel):
    name: str
    email: str
    age: int
    city: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    age: int
    city: Optional[str] = None

    class Config:
        populate_by_name = True

# Routes
@app.get("/")
async def health_check():
    return {
        "message": "The health check is successful!",
        "mongodb_connected": mongo_connected
    }

# Insert User API
@app.post("/users", response_model=UserResponse)
async def create_user(user: User):
    if not mongo_connected:
        raise HTTPException(status_code=503, detail="Database connection not available")
    try:
        result = collection.insert_one(user.dict())
        user_id = str(result.inserted_id)
        return {
            "id": user_id,
            **user.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Fetch All Users API
@app.get("/users", response_model=List[UserResponse])
async def get_all_users():
    if not mongo_connected:
        raise HTTPException(status_code=503, detail="Database connection not available")
    try:
        users = []
        for user in collection.find():
            users.append({
                "id": str(user["_id"]),
                "name": user.get("name"),
                "email": user.get("email"),
                "age": user.get("age"),
                "city": user.get("city")
            })
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Fetch User by ID API
@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    if not mongo_connected:
        raise HTTPException(status_code=503, detail="Database connection not available")
    try:
        user = collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "id": str(user["_id"]),
            "name": user.get("name"),
            "email": user.get("email"),
            "age": user.get("age"),
            "city": user.get("city")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Update User API
@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user: User):
    if not mongo_connected:
        raise HTTPException(status_code=503, detail="Database connection not available")
    try:
        result = collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": user.dict()}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        updated_user = collection.find_one({"_id": ObjectId(user_id)})
        return {
            "id": str(updated_user["_id"]),
            "name": updated_user.get("name"),
            "email": updated_user.get("email"),
            "age": updated_user.get("age"),
            "city": updated_user.get("city")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Delete User API
@app.delete("/users/{user_id}")
async def delete_user(user_id: str):
    if not mongo_connected:
        raise HTTPException(status_code=503, detail="Database connection not available")
    try:
        result = collection.delete_one({"_id": ObjectId(user_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
