from fastapi import APIRouter, HTTPException, status, Depends
from firebase_admin import auth
from database import users_collection, users_serializer
from schemas import TaskCreate, TaskUpdate, UserCreate, UserUpdate
from bson import ObjectId
import firebase_admin
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# Initialize Firebase (Ensure your Firebase credentials are in the correct path)
cred = firebase_admin.credentials.Certificate(".venv/hudddle-project-firebase.json")
firebase_admin.initialize_app(cred)

# Define a Pydantic model for the request data
class GoogleUserData(BaseModel):
    id_token: str  # Firebase ID token sent from the client

# Function to verify the Firebase ID token
async def verify_google_token(id_token: str):
    try:
        # Verify the ID token using Firebase Admin SDK
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token  # Returns a dictionary containing user information
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# Create a New User with Firebase Authentication
@router.post("/users/google/", status_code=status.HTTP_201_CREATED)
async def create_user_with_google(google_data: GoogleUserData):
    # Verify the Firebase ID token
    user_data = await verify_google_token(google_data.id_token)
    
    # Check if the user already exists
    existing_user = await users_collection.find_one({"email": user_data["email"]})
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
    
    # Create a new user entry in MongoDB
    new_user = {
        "email": user_data["email"],
        "username": user_data.get("name", "Unknown"),
        "password": None,  # No password for users signed up via Google
        "preferences": {},  # You can add any default preferences here
        "user_type": "google",
        "find_us": "Google",
        "software_used": "Google Authentication",
    }
    
    # Insert the new user into MongoDB
    result = await users_collection.insert_one(new_user)
    created_user = await users_collection.find_one({"_id": result.inserted_id})

    return {"message": "User created successfully via Google authentication", "user": users_serializer(created_user)}

# Route to Get User by ID
@router.get("/users/{user_id}/")
async def get_user(user_id: str):
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return users_serializer(user)


# Get Task by ID
@router.get("/tasks/{task_id}/")
async def get_task(task_id: str):
    if not ObjectId.is_valid(task_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid task ID format")

    task = await tasks_collection.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    return task_serializer(task)

# Update a Task
@router.put("/tasks/{task_id}/", status_code=status.HTTP_200_OK)
async def update_task(task_id: str, task_update: TaskUpdate):
    if not ObjectId.is_valid(task_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid task ID format")

    update_data = {k: v for k, v in task_update.model_dump(exclude_unset=True).items() if v is not None}

    task = await tasks_collection.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    await tasks_collection.update_one({"_id": ObjectId(task_id)}, {"$set": update_data})
    updated_task = await tasks_collection.find_one({"_id": ObjectId(task_id)})

    return {"message": "Task updated successfully", "task": task_serializer(updated_task)}

# Delete a Task
@router.delete("/tasks/{task_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str):
    if not ObjectId.is_valid(task_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid task ID format")

    task = await tasks_collection.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    await tasks_collection.delete_one({"_id": ObjectId(task_id)})
    return {"message": "Task deleted successfully"}

# Reassign a Task
@router.put("/tasks/{task_id}/reassign/", status_code=status.HTTP_200_OK)
async def reassign_task(task_id: str, new_assigned_to: str):
    if not ObjectId.is_valid(task_id) or not ObjectId.is_valid(new_assigned_to):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid task or user ID format")

    # Check if the user exists
    user = await users_collection.find_one({"_id": ObjectId(new_assigned_to)})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await tasks_collection.update_one({"_id": ObjectId(task_id)}, {"$set": {"assigned_to": new_assigned_to}})
    updated_task = await tasks_collection.find_one({"_id": ObjectId(task_id)})

    return {"message": f"Task reassigned to {new_assigned_to}", "task": task_serializer(updated_task)}

