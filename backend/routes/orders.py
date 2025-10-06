from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, List
import sys
sys.path.append('/app/backend')
from models import Order, OrderStatus, EscrowStatus, ProofOfCompletion, RevisionRequest, OrderMessage, TransactionType
from routes.auth import get_current_user
from utils import generate_order_number, calculate_platform_fee
from bson import ObjectId

router = APIRouter(prefix="/orders", tags=["Orders"])

def get_db():
    from server import db
    return db

class CreateOrderRequest(BaseModel):
    service_id: str
    quantity: int = 1
    platform: str
    brief: Optional[str] = None
    hashtags: List[str] = []
    mentions: List[str] = []
    special_instructions: Optional[str] = None
    turnaround_hours: Optional[int] = None

class ProofOfCompletionRequest(BaseModel):
    url: Optional[str] = None
    screenshots: List[str] = []
    description: Optional[str] = None

class RevisionRequestModel(BaseModel):
    reason: str
    instructions: str

class DeclineOrderRequest(BaseModel):
    reason: str

@router.post("/create")
async def create_order(
    request: CreateOrderRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    if current_user["role"] not in ["buyer", "both"]:
        raise HTTPException(status_code=403, detail="Only buyers can create orders")
    
    # Get service
    service = await db.service_listings.find_one({"_id": ObjectId(request.service_id)})
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    if not service.get("active", False):
        raise HTTPException(status_code=400, detail="Service is not active")
    
    # Get seller
    seller = await db.users.find_one({"_id": ObjectId(service["seller_id"])})
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    
    # Calculate costs
    base_cost = service["base_price"] * request.quantity
    seller_tier = seller.get("seller_profile", {}).get("tier", "new")
    platform_fee = calculate_platform_fee(base_cost, seller_tier)
    total_cost = base_cost + platform_fee
    
    # Check buyer balance
    buyer_profile = current_user.get("buyer_profile", {})
    credit_balance = buyer_profile.get("credit_balance", 0)
    
    if credit_balance < total_cost:
        raise HTTPException(status_code=400, detail=f"Insufficient credits. Need {total_cost}, have {credit_balance}")
    
    # Create order
    order_data = {
        "order_number": generate_order_number(),
        "buyer_id": current_user["_id"],
        "seller_id": service["seller_id"],
        "service_id": request.service_id,
        "service_title": service["title"],
        "service_type": service["service_type"],
        "quantity": request.quantity,
        "platform": request.platform,
        "base_cost": base_cost,
        "platform_fee": platform_fee,
        "express_fee": 0.0,
        "total_cost": total_cost,
        "brief": request.brief,
        "hashtags": request.hashtags,
        "mentions": request.mentions,
        "special_instructions": request.special_instructions,
        "turnaround_hours": request.turnaround_hours or service["turnaround_hours"],
        "status": OrderStatus.PENDING_ACCEPTANCE.value,
        "escrow_status": EscrowStatus.LOCKED.value,
        "escrow_amount": total_cost,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.orders.insert_one(order_data)
    order_data["_id"] = str(result.inserted_id)
    
    # Deduct credits from buyer
    new_balance = credit_balance - total_cost
    await db.users.update_one(
        {"_id": ObjectId(current_user["_id"])},
        {"$set": {"buyer_profile.credit_balance": new_balance}}
    )
    
    # Create transaction record
    transaction_data = {
        "user_id": current_user["_id"],
        "transaction_type": TransactionType.ORDER_PAYMENT.value,
        "amount": -total_cost,
        "balance_before": credit_balance,
        "balance_after": new_balance,
        "order_id": str(result.inserted_id),
        "related_user_id": service["seller_id"],
        "description": f"Order payment for {service['title']}",
        "created_at": datetime.utcnow()
    }
    await db.transactions.insert_one(transaction_data)
    
    return {
        "message": "Order created successfully",
        "order": order_data,
        "credits_deducted": total_cost,
        "new_balance": new_balance
    }

@router.post("/{order_id}/accept")
async def accept_order(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    order = await db.orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order["seller_id"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if order["status"] != OrderStatus.PENDING_ACCEPTANCE.value:
        raise HTTPException(status_code=400, detail="Order cannot be accepted")
    
    # Calculate deadline
    deadline = datetime.utcnow() + timedelta(hours=order["turnaround_hours"])
    
    # Update order
    await db.orders.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {
            "status": OrderStatus.ACCEPTED.value,
            "escrow_status": EscrowStatus.ACTIVE.value,
            "accepted_at": datetime.utcnow(),
            "deadline": deadline,
            "updated_at": datetime.utcnow()
        }}
    )
    
    updated_order = await db.orders.find_one({"_id": ObjectId(order_id)})
    updated_order["_id"] = str(updated_order["_id"])
    
    return {
        "message": "Order accepted",
        "order": updated_order,
        "deadline": deadline.isoformat()
    }

@router.post("/{order_id}/decline")
async def decline_order(
    order_id: str,
    request: DeclineOrderRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    order = await db.orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order["seller_id"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if order["status"] != OrderStatus.PENDING_ACCEPTANCE.value:
        raise HTTPException(status_code=400, detail="Order cannot be declined")
    
    # Refund credits to buyer
    buyer = await db.users.find_one({"_id": ObjectId(order["buyer_id"])})
    buyer_profile = buyer.get("buyer_profile", {})
    current_balance = buyer_profile.get("credit_balance", 0)
    new_balance = current_balance + order["total_cost"]
    
    await db.users.update_one(
        {"_id": ObjectId(order["buyer_id"])},
        {"$set": {"buyer_profile.credit_balance": new_balance}}
    )
    
    # Update order
    await db.orders.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {
            "status": OrderStatus.CANCELLED.value,
            "escrow_status": EscrowStatus.REFUNDED.value,
            "updated_at": datetime.utcnow()
        }}
    )
    
    # Create transaction record
    transaction_data = {
        "user_id": order["buyer_id"],
        "transaction_type": TransactionType.ORDER_REFUND.value,
        "amount": order["total_cost"],
        "balance_before": current_balance,
        "balance_after": new_balance,
        "order_id": order_id,
        "description": f"Refund for declined order: {order['order_number']}",
        "notes": f"Seller declined: {request.reason}",
        "created_at": datetime.utcnow()
    }
    await db.transactions.insert_one(transaction_data)
    
    updated_order = await db.orders.find_one({"_id": ObjectId(order_id)})
    updated_order["_id"] = str(updated_order["_id"])
    
    return {
        "message": "Order declined. Credits refunded to buyer.",
        "order": updated_order
    }

@router.post("/{order_id}/deliver")
async def deliver_order(
    order_id: str,
    request: ProofOfCompletionRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    order = await db.orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order["seller_id"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if order["status"] not in [OrderStatus.ACCEPTED.value, OrderStatus.REVISION_REQUESTED.value]:
        raise HTTPException(status_code=400, detail="Order cannot be delivered")
    
    # Create proof of completion
    proof = ProofOfCompletion(
        url=request.url,
        screenshots=request.screenshots,
        description=request.description,
        submitted_at=datetime.utcnow(),
        verified=False,
        verification_method="manual"
    )
    
    # Calculate review deadline (72 hours)
    review_deadline = datetime.utcnow() + timedelta(hours=72)
    
    # Update order
    await db.orders.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {
            "status": OrderStatus.DELIVERED.value,
            "escrow_status": EscrowStatus.UNDER_REVIEW.value,
            "proof_of_completion": proof.dict(),
            "delivered_at": datetime.utcnow(),
            "review_deadline": review_deadline,
            "updated_at": datetime.utcnow()
        }}
    )
    
    updated_order = await db.orders.find_one({"_id": ObjectId(order_id)})
    updated_order["_id"] = str(updated_order["_id"])
    
    return {
        "message": "Proof submitted. Awaiting buyer approval.",
        "order": updated_order
    }

@router.post("/{order_id}/approve")
async def approve_order(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    order = await db.orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order["buyer_id"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if order["status"] != OrderStatus.DELIVERED.value:
        raise HTTPException(status_code=400, detail="Order cannot be approved")
    
    # Release payment to seller
    seller = await db.users.find_one({"_id": ObjectId(order["seller_id"])})
    seller_profile = seller.get("seller_profile", {})
    
    # Calculate seller earnings (base cost minus platform fee)
    seller_earnings = order["base_cost"]
    current_pending = seller_profile.get("pending_balance", 0)
    new_pending = current_pending + seller_earnings
    
    # Update seller stats
    total_orders = seller_profile.get("total_orders", 0) + 1
    total_earnings = seller_profile.get("total_earnings", 0) + seller_earnings
    
    await db.users.update_one(
        {"_id": ObjectId(order["seller_id"])},
        {"$set": {
            "seller_profile.pending_balance": new_pending,
            "seller_profile.total_orders": total_orders,
            "seller_profile.total_earnings": total_earnings
        }}
    )
    
    # Update order
    await db.orders.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {
            "status": OrderStatus.APPROVED.value,
            "escrow_status": EscrowStatus.RELEASED.value,
            "completed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }}
    )
    
    # Create transaction record for seller
    transaction_data = {
        "user_id": order["seller_id"],
        "transaction_type": TransactionType.EARNINGS_RECEIVED.value,
        "amount": seller_earnings,
        "balance_before": current_pending,
        "balance_after": new_pending,
        "order_id": order_id,
        "related_user_id": order["buyer_id"],
        "description": f"Earnings from order: {order['order_number']}",
        "created_at": datetime.utcnow()
    }
    await db.transactions.insert_one(transaction_data)
    
    updated_order = await db.orders.find_one({"_id": ObjectId(order_id)})
    updated_order["_id"] = str(updated_order["_id"])
    
    # After 48 hours, move from pending to available
    # This would be handled by a background job in production
    
    return {
        "message": "Order approved. Payment released to seller.",
        "order": updated_order
    }

@router.post("/{order_id}/request-revision")
async def request_revision(
    order_id: str,
    request: RevisionRequestModel,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    order = await db.orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order["buyer_id"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if order["status"] != OrderStatus.DELIVERED.value:
        raise HTTPException(status_code=400, detail="Order cannot be revised")
    
    # Check revision count
    revision_count = order.get("revision_count", 0)
    if revision_count >= 1:
        raise HTTPException(status_code=400, detail="Maximum revisions exceeded")
    
    # Create revision request
    revision = RevisionRequest(
        requested_at=datetime.utcnow(),
        reason=request.reason,
        instructions=request.instructions
    )
    
    revision_requests = order.get("revision_requests", [])
    revision_requests.append(revision.dict())
    
    # Update order
    await db.orders.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {
            "status": OrderStatus.REVISION_REQUESTED.value,
            "revision_count": revision_count + 1,
            "revision_requests": revision_requests,
            "updated_at": datetime.utcnow()
        }}
    )
    
    updated_order = await db.orders.find_one({"_id": ObjectId(order_id)})
    updated_order["_id"] = str(updated_order["_id"])
    
    return {
        "message": "Revision requested",
        "order": updated_order
    }

@router.get("/buyer")
async def get_buyer_orders(
    current_user: dict = Depends(get_current_user),
    status: Optional[str] = None,
    db = Depends(get_db)
):
    if current_user["role"] not in ["buyer", "both"]:
        raise HTTPException(status_code=403, detail="Only buyers can view orders")
    
    query = {"buyer_id": current_user["_id"]}
    if status:
        query["status"] = status
    
    cursor = db.orders.find(query).sort("created_at", -1).limit(100)
    orders = await cursor.to_list(length=100)
    
    for order in orders:
        order["_id"] = str(order["_id"])
    
    return {"orders": orders, "total": len(orders)}

@router.get("/seller")
async def get_seller_orders(
    current_user: dict = Depends(get_current_user),
    status: Optional[str] = None,
    db = Depends(get_db)
):
    if current_user["role"] not in ["seller", "both"]:
        raise HTTPException(status_code=403, detail="Only sellers can view orders")
    
    query = {"seller_id": current_user["_id"]}
    if status:
        query["status"] = status
    
    cursor = db.orders.find(query).sort("created_at", -1).limit(100)
    orders = await cursor.to_list(length=100)
    
    for order in orders:
        order["_id"] = str(order["_id"])
    
    return {"orders": orders, "total": len(orders)}

@router.get("/{order_id}")
async def get_order(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    order = await db.orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check authorization
    if order["buyer_id"] != current_user["_id"] and order["seller_id"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    order["_id"] = str(order["_id"])
    
    return {"order": order}
