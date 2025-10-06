from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
import sys
sys.path.append('/app/backend')
from models import SocialAccount, Platform
from utils import generate_mock_linkedin_data, calculate_authenticity_score
from routes.auth import get_current_user
from bson import ObjectId

router = APIRouter(prefix="/linkedin", tags=["LinkedIn Integration"])

def get_db():
    from server import db
    return db

class LinkedInCallbackRequest(BaseModel):
    code: Optional[str] = None
    state: Optional[str] = None
    mock_data: Optional[bool] = True  # For testing without real OAuth

@router.get("/auth-url")
async def get_linkedin_auth_url(current_user: dict = Depends(get_current_user)):
    # In production, this would generate a real LinkedIn OAuth URL
    # For now, return a mock URL
    mock_auth_url = "https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=MOCK_CLIENT_ID&redirect_uri=MOCK_REDIRECT&state=random_state&scope=r_liteprofile%20r_emailaddress"
    
    return {
        "auth_url": mock_auth_url,
        "message": "Mock LinkedIn OAuth URL. In production, this would be a real OAuth URL."
    }

@router.post("/callback")
async def linkedin_callback(
    request: LinkedInCallbackRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    user_id = current_user["_id"]
    
    # Check if LinkedIn already connected
    existing = await db.social_accounts.find_one({
        "user_id": user_id,
        "platform": Platform.LINKEDIN.value
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="LinkedIn account already connected")
    
    # Generate mock LinkedIn data
    mock_data = generate_mock_linkedin_data()
    
    # Calculate authenticity score
    authenticity_score = calculate_authenticity_score(mock_data)
    
    # Create social account
    social_account_data = {
        "user_id": user_id,
        "platform": Platform.LINKEDIN.value,
        "platform_user_id": mock_data['username'],
        "profile_url": mock_data['profile_url'],
        "username": mock_data['username'],
        "follower_count": mock_data['follower_count'],
        "connection_count": mock_data['connection_count'],
        "engagement_rate": mock_data['engagement_rate'],
        "account_age_months": mock_data['account_age_months'],
        "posts_last_90_days": mock_data['posts_last_90_days'],
        "bot_follower_percentage": mock_data['bot_follower_percentage'],
        "authenticity_score": authenticity_score,
        "verification_method": "mock",
        "verified_at": datetime.utcnow(),
        "last_reverified": datetime.utcnow(),
        "next_reverification": datetime.utcnow() + timedelta(days=90),
        "verification_status": "verified",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.social_accounts.insert_one(social_account_data)
    social_account_data["_id"] = str(result.inserted_id)
    
    return {
        "message": "LinkedIn account linked successfully (mock data)",
        "social_account": social_account_data
    }

@router.get("/metrics/{user_id}")
async def get_linkedin_metrics(user_id: str, db = Depends(get_db)):
    # Find social account
    social_account = await db.social_accounts.find_one({
        "user_id": user_id,
        "platform": Platform.LINKEDIN.value
    })
    
    if not social_account:
        raise HTTPException(status_code=404, detail="LinkedIn account not connected")
    
    social_account["_id"] = str(social_account["_id"])
    
    return social_account

@router.get("/my-metrics")
async def get_my_linkedin_metrics(current_user: dict = Depends(get_current_user), db = Depends(get_db)):
    user_id = current_user["_id"]
    
    social_account = await db.social_accounts.find_one({
        "user_id": user_id,
        "platform": Platform.LINKEDIN.value
    })
    
    if not social_account:
        raise HTTPException(status_code=404, detail="LinkedIn account not connected")
    
    social_account["_id"] = str(social_account["_id"])
    
    return social_account

@router.post("/reverify")
async def reverify_linkedin(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    user_id = current_user["_id"]
    
    # Find social account
    social_account = await db.social_accounts.find_one({
        "user_id": user_id,
        "platform": Platform.LINKEDIN.value
    })
    
    if not social_account:
        raise HTTPException(status_code=404, detail="LinkedIn account not connected")
    
    # Generate new mock data
    mock_data = generate_mock_linkedin_data()
    authenticity_score = calculate_authenticity_score(mock_data)
    
    # Update social account
    await db.social_accounts.update_one(
        {"_id": social_account["_id"]},
        {"$set": {
            "follower_count": mock_data['follower_count'],
            "connection_count": mock_data['connection_count'],
            "engagement_rate": mock_data['engagement_rate'],
            "posts_last_90_days": mock_data['posts_last_90_days'],
            "bot_follower_percentage": mock_data['bot_follower_percentage'],
            "authenticity_score": authenticity_score,
            "last_reverified": datetime.utcnow(),
            "next_reverification": datetime.utcnow() + timedelta(days=90),
            "updated_at": datetime.utcnow()
        }}
    )
    
    return {
        "message": "Re-verification completed",
        "authenticity_score": authenticity_score
    }
