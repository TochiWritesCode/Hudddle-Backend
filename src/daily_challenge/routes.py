import openai
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Dict, Any
from src.db.models import User, DailyChallenge, UserDailyChallenge, Task
from src.db.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from src.auth.dependencies import get_current_user
from uuid import UUID
from pydantic import BaseModel, Field
import json

daily_challenge_router = APIRouter()

# --- LLM Integration ---

openai.api_key = "YOUR_OPENAI_API_KEY"

class ChallengeResponse(BaseModel):
    challenges: List[str] = Field(..., min_items=4, max_items=4)

async def generate_daily_challenges() -> List[str]:
    # ... (Fetch user levels)
    prompt = f"""Generate 4 unique daily challenges for a user to boost their Leader, Workaholic, Team Player, and Slacker levels in an online collaborative remote workroom. 
        The challenges should be action-oriented and achievable within a day. 
        Provide each challenge as a task description. 
        Respond with a json object that has a key called challenges and the value is a list of strings."""
    response = openai.Completion.create(
        engine="text-davinci-003",  # Or another suitable engine
        prompt=prompt,
        max_tokens=250,
    )
    try:
        # Extract the JSON part from the response.
        json_start = response.choices[0].text.find('{')
        json_str = response.choices[0].text[json_start:]
        response_data = json.loads(json_str)
        validated_response = ChallengeResponse(**response_data)
        return validated_response.challenges
    except (json.JSONDecodeError, ValueError, KeyError, TypeError) as e:
        print(f"Error parsing LLM response: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate daily challenges.")
    except Exception as e:
        print(f"unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate daily challenges.")

# --- API Endpoints ---

@daily_challenge_router.get("/users/me/daily-challenges", response_model=List[Dict[str, Any]])
async def get_user_daily_challenges(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    daily_challenges = await session.exec(select(DailyChallenge).join(UserDailyChallenge).where(UserDailyChallenge.user_id == user.id))
    return [{"id": challenge.id, "description": challenge.description, "points": challenge.points} for challenge in daily_challenges.all()]

@daily_challenge_router.post("/users/me/daily-challenges/{challenge_id}/accept")
async def accept_daily_challenge(challenge_id: UUID, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    user_challenge = await session.exec(select(UserDailyChallenge).where(UserDailyChallenge.user_id == user.id, UserDailyChallenge.daily_challenge_id == challenge_id))
    user_challenge = user_challenge.first()
    if not user_challenge:
        raise HTTPException(status_code=404, detail="Daily challenge not found")
    user_challenge.accepted = True;
    challenge = await session.get(DailyChallenge, challenge_id)
    task = Task(title = challenge.description, created_by_id = user.id, description = "Daily Challenge")
    session.add(task)
    await session.commit()
    await session.refresh(user_challenge)
    return {"message": "Daily challenge accepted"}

