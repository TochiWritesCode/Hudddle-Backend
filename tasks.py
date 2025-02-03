from fastapi import APIRouter, HTTPException, status
from database import tasks_collection, users_collection, task_serializer, users_serializer
from schemas import TaskCreate, TaskUpdate, UserCreate, UserUpdate
from passlib.context import CryptContext
from bson import ObjectId
from typing import List

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash password
def hash_password(password: str):
    return pwd_context.hash(password)

# Create a New User
@router.post("/users/", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    user_dict = user.model_dump()
    user_dict["password"] = hash_password(user_dict["password"])  # Encrypt password

    new_user = await users_collection.insert_one(user_dict)
    created_user = await users_collection.find_one({"_id": new_user.inserted_id})

    return {"message": "User created successfully", "user": users_serializer(created_user)}

# Get All Users
@router.get("/users/", response_model=List[dict])
async def get_users():
    users = await users_collection.find().to_list(length=100)
    return [users_serializer(user) for user in users]

# Get User by ID
@router.get("/users/{user_id}/")
async def get_user(user_id: str):
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return users_serializer(user)

# Update User
@router.put("/users/{user_id}/", status_code=status.HTTP_200_OK)
async def update_user(user_id: str, user_update: UserUpdate):
    update_data = {k: v for k, v in user_update.model_dump(exclude_unset=True).items() if v is not None}

    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
    updated_user = await users_collection.find_one({"_id": ObjectId(user_id)})

    return {"message": "User updated successfully", "user": users_serializer(updated_user)}

# Delete User
@router.delete("/users/{user_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str):
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await users_collection.delete_one({"_id": ObjectId(user_id)})
    return {"message": "User deleted successfully"}



# Create a New Task
@router.post("/tasks/", status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate):
    task_dict = task.model_dump()
    task_dict["status"] = "not_started"
    task_dict["points"] = 10  # Default points

    # Validate assigned user (if provided)
    if task_dict.get("assigned_to"):
        user = await users_collection.find_one({"_id": ObjectId(task_dict["assigned_to"])})
        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assigned user not found")

    new_task = await tasks_collection.insert_one(task_dict)
    created_task = await tasks_collection.find_one({"_id": new_task.inserted_id})

    return {"message": "Task created successfully", "task": task_serializer(created_task)}

# Get All Tasks
@router.get("/tasks/", response_model=List[dict])
async def get_tasks():
    tasks = await tasks_collection.find().to_list(length=100)
    return [task_serializer(task) for task in tasks]

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

