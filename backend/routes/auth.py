from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional
import sys
sys.path.append('/app/backend')
from models import User, UserRole, KYCStatus, SellerProfile, BuyerProfile, OTP
from utils import (
    hash_password, verify_password, generate_otp, 
    create_access_token, create_refresh_token, verify_token
)
from bson import ObjectId

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Dependency to get database
def get_db():
    from server import db
    return db

# Request models
class RegisterRequest(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    password: str
    full_name: str
    role: UserRole

class VerifyEmailRequest(BaseModel):
    email: EmailStr
    otp: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ResendOTPRequest(BaseModel):
    email: EmailStr
    otp_type: str = "email_verification"

# Helper function to get current user from token
async def get_current_user(authorization: Optional[str] = Header(None), db = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("sub")
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user["_id"] = str(user["_id"])
    return user

@router.post("/register")
async def register(request: RegisterRequest, db = Depends(get_db)):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": request.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    password_hash = hash_password(request.password)
    
    user_data = {
        "email": request.email,
        "phone": request.phone,
        "password_hash": password_hash,
        "role": request.role.value,
        "full_name": request.full_name,
        "email_verified": False,
        "phone_verified": False,
        "kyc_status": KYCStatus.PENDING.value,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Add role-specific profiles
    if request.role in [UserRole.SELLER, UserRole.BOTH]:
        user_data["seller_profile"] = SellerProfile().dict()
    
    if request.role in [UserRole.BUYER, UserRole.BOTH]:
        user_data["buyer_profile"] = BuyerProfile().dict()
    
    result = await db.users.insert_one(user_data)
    user_id = str(result.inserted_id)
    
    # Generate and send OTP
    otp_code = generate_otp()
    otp_data = {
        "email": request.email,
        "otp_code": otp_code,
        "otp_type": "email_verification",
        "verified": False,
        "expires_at": datetime.utcnow() + timedelta(minutes=10),
        "created_at": datetime.utcnow()
    }
    await db.otps.insert_one(otp_data)
    
    # In production, send email with OTP
    # For now, return it in response for testing
    return {
        "message": "Registration successful. Please verify your email.",
        "user_id": user_id,
        "email_otp_sent": True,
        "otp_code": otp_code  # Remove this in production
    }

@router.post("/verify-email")
async def verify_email(request: VerifyEmailRequest, db = Depends(get_db)):
    # Find OTP
    otp = await db.otps.find_one({
        "email": request.email,
        "otp_code": request.otp,
        "otp_type": "email_verification",
        "verified": False
    })
    
    if not otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    # Check expiration
    if otp["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP has expired")
    
    # Mark OTP as verified
    await db.otps.update_one(
        {"_id": otp["_id"]},
        {"$set": {"verified": True}}
    )
    
    # Update user
    user = await db.users.find_one_and_update(
        {"email": request.email},
        {"$set": {"email_verified": True, "updated_at": datetime.utcnow()}},
        return_document=True
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate tokens
    user_id = str(user["_id"])
    access_token = create_access_token({"sub": user_id, "email": user["email"]})
    refresh_token = create_refresh_token({"sub": user_id})
    
    # Format user response
    user["_id"] = user_id
    user.pop("password_hash", None)
    
    return {
        "message": "Email verified successfully",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user
    }

@router.post("/login")
async def login(request: LoginRequest, db = Depends(get_db)):
    # Find user
    user = await db.users.find_one({"email": request.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password
    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check email verification
    if not user.get("email_verified", False):
        raise HTTPException(status_code=403, detail="Please verify your email first")
    
    # Generate tokens
    user_id = str(user["_id"])
    access_token = create_access_token({"sub": user_id, "email": user["email"]})
    refresh_token = create_refresh_token({"sub": user_id})
    
    # Update last active
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_active": datetime.utcnow()}}
    )
    
    # Format user response
    user["_id"] = user_id
    user.pop("password_hash", None)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user
    }

@router.post("/resend-otp")
async def resend_otp(request: ResendOTPRequest, db = Depends(get_db)):
    # Check if user exists
    user = await db.users.find_one({"email": request.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate new OTP
    otp_code = generate_otp()
    otp_data = {
        "email": request.email,
        "otp_code": otp_code,
        "otp_type": request.otp_type,
        "verified": False,
        "expires_at": datetime.utcnow() + timedelta(minutes=10),
        "created_at": datetime.utcnow()
    }
    await db.otps.insert_one(otp_data)
    
    return {
        "message": "OTP sent successfully",
        "otp_code": otp_code  # Remove this in production
    }

@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return {"user": current_user}
