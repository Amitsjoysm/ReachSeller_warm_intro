from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import sys
import random
sys.path.append('/app/backend')
from models import Transaction, TransactionType
from routes.auth import get_current_user
from bson import ObjectId

router = APIRouter(prefix="/wallet", tags=["Wallet"])

def get_db():
    from server import db
    return db

class PurchaseCreditsRequest(BaseModel):
    amount: float
    payment_method: str = "credit_card_mock"

class WithdrawRequest(BaseModel):
    amount: float
    payment_method: str = "bank_account"

@router.post("/purchase-credits")
async def purchase_credits(
    request: PurchaseCreditsRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    if current_user["role"] not in ["buyer", "both"]:
        raise HTTPException(status_code=403, detail="Only buyers can purchase credits")
    
    # Calculate bonus
    bonus = 0
    if request.amount >= 100:
        bonus = request.amount * 0.05  # 5% bonus
    if request.amount >= 500:
        bonus = request.amount * 0.08  # 8% bonus
    if request.amount >= 1000:
        bonus = request.amount * 0.10  # 10% bonus
    if request.amount >= 5000:
        bonus = request.amount * 0.15  # 15% bonus
    
    credits_added = request.amount + bonus
    
    # Update buyer balance
    buyer_profile = current_user.get("buyer_profile", {})
    current_balance = buyer_profile.get("credit_balance", 0)
    new_balance = current_balance + credits_added
    
    await db.users.update_one(
        {"_id": ObjectId(current_user["_id"])},
        {"$set": {
            "buyer_profile.credit_balance": new_balance,
            "updated_at": datetime.utcnow()
        }}
    )
    
    # Create transaction record
    transaction_data = {
        "user_id": current_user["_id"],
        "transaction_type": TransactionType.CREDIT_PURCHASE.value,
        "amount": credits_added,
        "balance_before": current_balance,
        "balance_after": new_balance,
        "payment_method": request.payment_method,
        "payment_reference": f"MOCK-{random.randint(100000, 999999)}",
        "description": f"Credit purchase: ${request.amount} + ${bonus} bonus",
        "created_at": datetime.utcnow()
    }
    
    result = await db.transactions.insert_one(transaction_data)
    transaction_data["_id"] = str(result.inserted_id)
    
    return {
        "message": "Credits purchased successfully (MOCK)",
        "credits_added": credits_added,
        "bonus": bonus,
        "new_balance": new_balance,
        "transaction_id": str(result.inserted_id)
    }

@router.get("/balance")
async def get_balance(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    if current_user["role"] not in ["buyer", "both"]:
        return {"error": "Only buyers have credit balance"}
    
    buyer_profile = current_user.get("buyer_profile", {})
    available_balance = buyer_profile.get("credit_balance", 0)
    
    # Calculate in escrow
    pipeline = [
        {
            "$match": {
                "buyer_id": current_user["_id"],
                "escrow_status": {"$in": ["locked", "active", "under_review"]}
            }
        },
        {
            "$group": {
                "_id": None,
                "total_escrow": {"$sum": "$escrow_amount"}
            }
        }
    ]
    
    result = await db.orders.aggregate(pipeline).to_list(1)
    in_escrow = result[0]["total_escrow"] if result else 0
    
    return {
        "available_balance": available_balance,
        "in_escrow": in_escrow,
        "total": available_balance + in_escrow
    }

@router.get("/transactions")
async def get_transactions(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    cursor = db.transactions.find({"user_id": current_user["_id"]}).sort("created_at", -1).limit(100)
    transactions = await cursor.to_list(length=100)
    
    for transaction in transactions:
        transaction["_id"] = str(transaction["_id"])
    
    return {"transactions": transactions, "total": len(transactions)}

@router.post("/withdraw")
async def withdraw(
    request: WithdrawRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    if current_user["role"] not in ["seller", "both"]:
        raise HTTPException(status_code=403, detail="Only sellers can withdraw")
    
    seller_profile = current_user.get("seller_profile", {})
    available_balance = seller_profile.get("available_balance", 0)
    
    if request.amount > available_balance:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    if request.amount < 10:
        raise HTTPException(status_code=400, detail="Minimum withdrawal is $10")
    
    # Update seller balance
    new_balance = available_balance - request.amount
    
    await db.users.update_one(
        {"_id": ObjectId(current_user["_id"])},
        {"$set": {
            "seller_profile.available_balance": new_balance,
            "updated_at": datetime.utcnow()
        }}
    )
    
    # Create transaction record
    transaction_data = {
        "user_id": current_user["_id"],
        "transaction_type": TransactionType.WITHDRAWAL.value,
        "amount": -request.amount,
        "balance_before": available_balance,
        "balance_after": new_balance,
        "payment_method": request.payment_method,
        "payment_reference": f"WITHDRAW-{random.randint(100000, 999999)}",
        "description": f"Withdrawal to {request.payment_method}",
        "created_at": datetime.utcnow()
    }
    
    result = await db.transactions.insert_one(transaction_data)
    
    return {
        "message": "Withdrawal request submitted (MOCK)",
        "processing_time": "3-5 business days",
        "transaction_id": str(result.inserted_id)
    }
