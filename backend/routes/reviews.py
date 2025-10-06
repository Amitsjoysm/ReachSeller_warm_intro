from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import sys
sys.path.append('/app/backend')
from models import Review, OrderStatus
from routes.auth import get_current_user
from bson import ObjectId

router = APIRouter(prefix="/reviews", tags=["Reviews"])

def get_db():
    from server import db
    return db

class CreateReviewRequest(BaseModel):
    order_id: str
    overall_rating: float
    quality_rating: Optional[float] = None
    communication_rating: Optional[float] = None
    timeliness_rating: Optional[float] = None
    professionalism_rating: Optional[float] = None
    clear_communication_rating: Optional[float] = None
    reasonable_expectations_rating: Optional[float] = None
    timely_responses_rating: Optional[float] = None
    payment_reliability_rating: Optional[float] = None
    review_text: Optional[str] = None
    would_work_again: bool = True

@router.post("/create")
async def create_review(
    request: CreateReviewRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    # Get order
    order = await db.orders.find_one({"_id": ObjectId(request.order_id)})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check if order is completed
    if order["status"] not in [OrderStatus.APPROVED.value, OrderStatus.COMPLETED.value]:
        raise HTTPException(status_code=400, detail="Can only review completed orders")
    
    # Determine reviewer and reviewee
    if order["buyer_id"] == current_user["_id"]:
        reviewer_role = "buyer"
        reviewee_id = order["seller_id"]
    elif order["seller_id"] == current_user["_id"]:
        reviewer_role = "seller"
        reviewee_id = order["buyer_id"]
    else:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if already reviewed
    existing_review = await db.reviews.find_one({
        "order_id": request.order_id,
        "reviewer_id": current_user["_id"]
    })
    
    if existing_review:
        raise HTTPException(status_code=400, detail="You have already reviewed this order")
    
    # Create review
    review_data = request.dict()
    review_data["reviewer_id"] = current_user["_id"]
    review_data["reviewee_id"] = reviewee_id
    review_data["reviewer_role"] = reviewer_role
    review_data["created_at"] = datetime.utcnow()
    review_data["updated_at"] = datetime.utcnow()
    
    result = await db.reviews.insert_one(review_data)
    review_data["_id"] = str(result.inserted_id)
    
    # Update reviewee's average rating
    pipeline = [
        {"$match": {"reviewee_id": reviewee_id}},
        {"$group": {
            "_id": None,
            "avg_rating": {"$avg": "$overall_rating"},
            "count": {"$sum": 1}
        }}
    ]
    
    result_agg = await db.reviews.aggregate(pipeline).to_list(1)
    
    if result_agg:
        avg_rating = result_agg[0]["avg_rating"]
        review_count = result_agg[0]["count"]
        
        # Update user's rating
        reviewee = await db.users.find_one({"_id": ObjectId(reviewee_id)})
        if reviewee:
            if reviewee["role"] in ["seller", "both"]:
                await db.users.update_one(
                    {"_id": ObjectId(reviewee_id)},
                    {"$set": {"seller_profile.average_rating": round(avg_rating, 2)}}
                )
    
    return {
        "message": "Review submitted successfully",
        "review": review_data
    }

@router.get("/user/{user_id}")
async def get_user_reviews(
    user_id: str,
    db = Depends(get_db)
):
    # Get all reviews for user
    cursor = db.reviews.find({"reviewee_id": user_id, "is_public": True}).sort("created_at", -1).limit(50)
    reviews = await cursor.to_list(length=50)
    
    for review in reviews:
        review["_id"] = str(review["_id"])
    
    # Calculate rating breakdown
    rating_breakdown = {"5_star": 0, "4_star": 0, "3_star": 0, "2_star": 0, "1_star": 0}
    total_rating = 0
    
    for review in reviews:
        rating = int(review["overall_rating"])
        rating_breakdown[f"{rating}_star"] += 1
        total_rating += review["overall_rating"]
    
    avg_rating = round(total_rating / len(reviews), 2) if reviews else 0
    
    return {
        "reviews": reviews,
        "average_rating": avg_rating,
        "total_reviews": len(reviews),
        "rating_breakdown": rating_breakdown
    }

@router.get("/my-reviews")
async def get_my_reviews(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    # Get reviews I received
    cursor = db.reviews.find({"reviewee_id": current_user["_id"]}).sort("created_at", -1)
    reviews = await cursor.to_list(length=100)
    
    for review in reviews:
        review["_id"] = str(review["_id"])
    
    return {"reviews": reviews}
