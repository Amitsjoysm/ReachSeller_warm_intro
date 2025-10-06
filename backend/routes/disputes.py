from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
import sys
sys.path.append('/app/backend')
from models import Dispute, DisputeType, DisputeStatus, ResolutionType, OrderStatus
from routes.auth import get_current_user
from utils import generate_dispute_number
from bson import ObjectId

router = APIRouter(prefix="/disputes", tags=["Disputes"])

def get_db():
    from server import db
    return db

class CreateDisputeRequest(BaseModel):
    order_id: str
    dispute_type: DisputeType
    reason: str
    evidence: List[str] = []
    proposed_resolution: Optional[str] = None

class RespondToDisputeRequest(BaseModel):
    response: str
    evidence: List[str] = []
    proposed_resolution: Optional[str] = None

class MediationDecisionRequest(BaseModel):
    resolution_type: ResolutionType
    refund_percentage: Optional[float] = None
    resolution_details: str

@router.post("/create")
async def create_dispute(
    request: CreateDisputeRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    # Get order
    order = await db.orders.find_one({"_id": ObjectId(request.order_id)})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check if user is part of this order
    if order["buyer_id"] != current_user["_id"] and order["seller_id"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if order can be disputed
    if order["status"] in [OrderStatus.PENDING_ACCEPTANCE.value, OrderStatus.CANCELLED.value, OrderStatus.REFUNDED.value]:
        raise HTTPException(status_code=400, detail="Order cannot be disputed")
    
    # Check if dispute already exists
    existing_dispute = await db.disputes.find_one({"order_id": request.order_id})
    if existing_dispute:
        raise HTTPException(status_code=400, detail="Dispute already exists for this order")
    
    # Determine initiator and respondent
    if order["buyer_id"] == current_user["_id"]:
        initiator_id = order["buyer_id"]
        respondent_id = order["seller_id"]
    else:
        initiator_id = order["seller_id"]
        respondent_id = order["buyer_id"]
    
    # Create dispute
    dispute_data = {
        "dispute_number": generate_dispute_number(),
        "order_id": request.order_id,
        "initiator_id": initiator_id,
        "respondent_id": respondent_id,
        "dispute_type": request.dispute_type.value,
        "initiator_reason": request.reason,
        "initiator_evidence": request.evidence,
        "initiator_proposed_resolution": request.proposed_resolution,
        "status": DisputeStatus.OPEN.value,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.disputes.insert_one(dispute_data)
    dispute_data["_id"] = str(result.inserted_id)
    
    # Update order status
    await db.orders.update_one(
        {"_id": ObjectId(request.order_id)},
        {"$set": {
            "status": OrderStatus.DISPUTED.value,
            "escrow_status": "disputed",
            "updated_at": datetime.utcnow()
        }}
    )
    
    return {
        "message": "Dispute created successfully",
        "dispute": dispute_data
    }

@router.post("/{dispute_id}/respond")
async def respond_to_dispute(
    dispute_id: str,
    request: RespondToDisputeRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    # Get dispute
    dispute = await db.disputes.find_one({"_id": ObjectId(dispute_id)})
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    
    # Check if user is respondent
    if dispute["respondent_id"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if already responded
    if dispute.get("respondent_response"):
        raise HTTPException(status_code=400, detail="Already responded to this dispute")
    
    # Update dispute
    await db.disputes.update_one(
        {"_id": ObjectId(dispute_id)},
        {"$set": {
            "respondent_response": request.response,
            "respondent_evidence": request.evidence,
            "respondent_proposed_resolution": request.proposed_resolution,
            "respondent_responded_at": datetime.utcnow(),
            "status": DisputeStatus.UNDER_MEDIATION.value,
            "updated_at": datetime.utcnow()
        }}
    )
    
    updated_dispute = await db.disputes.find_one({"_id": ObjectId(dispute_id)})
    updated_dispute["_id"] = str(updated_dispute["_id"])
    
    return {
        "message": "Response submitted. Dispute is now under mediation.",
        "dispute": updated_dispute
    }

@router.post("/{dispute_id}/mediate")
async def mediate_dispute(
    dispute_id: str,
    request: MediationDecisionRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    # In production, check if user is admin/mediator
    # For now, allowing any authenticated user for testing
    
    # Get dispute
    dispute = await db.disputes.find_one({"_id": ObjectId(dispute_id)})
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    
    # Get order
    order = await db.orders.find_one({"_id": ObjectId(dispute["order_id"])})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Update dispute
    await db.disputes.update_one(
        {"_id": ObjectId(dispute_id)},
        {"$set": {
            "resolution_type": request.resolution_type.value,
            "resolution_details": request.resolution_details,
            "refund_percentage": request.refund_percentage,
            "mediator_id": current_user["_id"],
            "mediator_assigned_at": datetime.utcnow(),
            "resolved_at": datetime.utcnow(),
            "status": DisputeStatus.RESOLVED.value,
            "updated_at": datetime.utcnow()
        }}
    )
    
    # Execute resolution
    if request.resolution_type == ResolutionType.FULL_REFUND:
        # Refund full amount to buyer
        buyer = await db.users.find_one({"_id": ObjectId(order["buyer_id"])})
        buyer_profile = buyer.get("buyer_profile", {})
        current_balance = buyer_profile.get("credit_balance", 0)
        new_balance = current_balance + order["total_cost"]
        
        await db.users.update_one(
            {"_id": ObjectId(order["buyer_id"])},
            {"$set": {"buyer_profile.credit_balance": new_balance}}
        )
        
        await db.orders.update_one(
            {"_id": ObjectId(dispute["order_id"])},
            {"$set": {
                "status": OrderStatus.REFUNDED.value,
                "escrow_status": "refunded",
                "updated_at": datetime.utcnow()
            }}
        )
    
    elif request.resolution_type == ResolutionType.PARTIAL_REFUND:
        # Refund partial amount
        refund_amount = order["total_cost"] * (request.refund_percentage / 100)
        seller_amount = order["base_cost"] - refund_amount
        
        # Refund to buyer
        buyer = await db.users.find_one({"_id": ObjectId(order["buyer_id"])})
        buyer_profile = buyer.get("buyer_profile", {})
        buyer_balance = buyer_profile.get("credit_balance", 0)
        await db.users.update_one(
            {"_id": ObjectId(order["buyer_id"])},
            {"$set": {"buyer_profile.credit_balance": buyer_balance + refund_amount}}
        )
        
        # Pay seller
        seller = await db.users.find_one({"_id": ObjectId(order["seller_id"])})
        seller_profile = seller.get("seller_profile", {})
        seller_balance = seller_profile.get("available_balance", 0)
        await db.users.update_one(
            {"_id": ObjectId(order["seller_id"])},
            {"$set": {"seller_profile.available_balance": seller_balance + seller_amount}}
        )
        
        await db.orders.update_one(
            {"_id": ObjectId(dispute["order_id"])},
            {"$set": {
                "status": OrderStatus.COMPLETED.value,
                "escrow_status": "released",
                "updated_at": datetime.utcnow()
            }}
        )
    
    elif request.resolution_type == ResolutionType.FULL_PAYMENT:
        # Pay seller full amount
        seller = await db.users.find_one({"_id": ObjectId(order["seller_id"])})
        seller_profile = seller.get("seller_profile", {})
        seller_balance = seller_profile.get("available_balance", 0)
        await db.users.update_one(
            {"_id": ObjectId(order["seller_id"])},
            {"$set": {"seller_profile.available_balance": seller_balance + order["base_cost"]}}
        )
        
        await db.orders.update_one(
            {"_id": ObjectId(dispute["order_id"])},
            {"$set": {
                "status": OrderStatus.COMPLETED.value,
                "escrow_status": "released",
                "updated_at": datetime.utcnow()
            }}
        )
    
    updated_dispute = await db.disputes.find_one({"_id": ObjectId(dispute_id)})
    updated_dispute["_id"] = str(updated_dispute["_id"])
    
    return {
        "message": "Dispute resolved",
        "dispute": updated_dispute
    }

@router.get("/user")
async def get_user_disputes(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    # Get disputes where user is either initiator or respondent
    cursor = db.disputes.find({
        "$or": [
            {"initiator_id": current_user["_id"]},
            {"respondent_id": current_user["_id"]}
        ]
    }).sort("created_at", -1)
    
    disputes = await cursor.to_list(length=100)
    
    for dispute in disputes:
        dispute["_id"] = str(dispute["_id"])
    
    return {"disputes": disputes}

@router.get("/{dispute_id}")
async def get_dispute(
    dispute_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    dispute = await db.disputes.find_one({"_id": ObjectId(dispute_id)})
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    
    # Check authorization
    if dispute["initiator_id"] != current_user["_id"] and dispute["respondent_id"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    dispute["_id"] = str(dispute["_id"])
    
    return {"dispute": dispute}
