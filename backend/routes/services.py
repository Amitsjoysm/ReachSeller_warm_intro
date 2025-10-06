from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
import sys
sys.path.append('/app/backend')
from models import ServiceListing, ServiceType, ServiceAddon
from routes.auth import get_current_user
from bson import ObjectId
import math

router = APIRouter(prefix="/services", tags=["Services"])

def get_db():
    from server import db
    return db

class CreateServiceRequest(BaseModel):
    title: str
    description: str
    service_type: ServiceType
    base_price: float
    pricing_type: str = "per_action"
    package_quantity: Optional[int] = None
    turnaround_hours: int
    revisions_included: int = 1
    platforms: List[str]
    industries: List[str] = []
    content_categories: List[str] = []
    content_guidelines: Optional[str] = None
    restrictions: List[str] = []
    requires_approval: bool = False
    addons: List[ServiceAddon] = []

class UpdateServiceRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    base_price: Optional[float] = None
    turnaround_hours: Optional[int] = None
    active: Optional[bool] = None
    platforms: Optional[List[str]] = None
    industries: Optional[List[str]] = None

@router.post("/create")
async def create_service(
    request: CreateServiceRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    # Check if user is a seller
    if current_user["role"] not in ["seller", "both"]:
        raise HTTPException(status_code=403, detail="Only sellers can create services")
    
    # Check if LinkedIn is connected
    linkedin_account = await db.social_accounts.find_one({
        "user_id": current_user["_id"],
        "platform": "linkedin"
    })
    
    if not linkedin_account:
        raise HTTPException(status_code=400, detail="Please connect your LinkedIn account first")
    
    service_data = request.dict()
    service_data["seller_id"] = current_user["_id"]
    service_data["service_type"] = request.service_type.value
    service_data["created_at"] = datetime.utcnow()
    service_data["updated_at"] = datetime.utcnow()
    
    result = await db.service_listings.insert_one(service_data)
    service_data["_id"] = str(result.inserted_id)
    
    return {
        "message": "Service created successfully",
        "service_id": str(result.inserted_id),
        "service": service_data
    }

@router.get("/search")
async def search_services(
    platform: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    industry: Optional[str] = Query(None),
    service_type: Optional[str] = Query(None),
    min_rating: Optional[float] = Query(None),
    sort: str = Query("relevance"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db = Depends(get_db)
):
    # Build query
    query = {"active": True}
    
    if platform:
        query["platforms"] = platform
    
    if min_price is not None or max_price is not None:
        query["base_price"] = {}
        if min_price is not None:
            query["base_price"]["$gte"] = min_price
        if max_price is not None:
            query["base_price"]["$lte"] = max_price
    
    if industry:
        query["industries"] = industry
    
    if service_type:
        query["service_type"] = service_type
    
    if min_rating is not None:
        query["average_rating"] = {"$gte": min_rating}
    
    # Determine sort
    sort_options = {
        "price_low": [("base_price", 1)],
        "price_high": [("base_price", -1)],
        "rating": [("average_rating", -1)],
        "popular": [("total_orders", -1)],
        "newest": [("created_at", -1)],
        "relevance": [("average_rating", -1), ("total_orders", -1)]
    }
    
    sort_by = sort_options.get(sort, sort_options["relevance"])
    
    # Get total count
    total = await db.service_listings.count_documents(query)
    
    # Get paginated results
    skip = (page - 1) * limit
    cursor = db.service_listings.find(query).sort(sort_by).skip(skip).limit(limit)
    services = await cursor.to_list(length=limit)
    
    # Get seller info for each service
    for service in services:
        service["_id"] = str(service["_id"])
        seller = await db.users.find_one({"_id": ObjectId(service["seller_id"])})
        if seller:
            service["seller"] = {
                "full_name": seller.get("full_name"),
                "profile_picture": seller.get("profile_picture"),
                "seller_profile": seller.get("seller_profile", {})
            }
    
    total_pages = math.ceil(total / limit)
    
    return {
        "services": services,
        "total": total,
        "page": page,
        "total_pages": total_pages
    }

@router.get("/{service_id}")
async def get_service(service_id: str, db = Depends(get_db)):
    service = await db.service_listings.find_one({"_id": ObjectId(service_id)})
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    service["_id"] = str(service["_id"])
    
    # Get seller info
    seller = await db.users.find_one({"_id": ObjectId(service["seller_id"])})
    if seller:
        seller["_id"] = str(seller["_id"])
        seller.pop("password_hash", None)
        service["seller"] = seller
    
    # Get reviews for this seller
    reviews_cursor = db.reviews.find({"reviewee_id": service["seller_id"]})
    reviews = await reviews_cursor.to_list(length=10)
    for review in reviews:
        review["_id"] = str(review["_id"])
    
    return {
        "service": service,
        "reviews": reviews
    }

@router.put("/{service_id}")
async def update_service(
    service_id: str,
    request: UpdateServiceRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    # Find service
    service = await db.service_listings.find_one({"_id": ObjectId(service_id)})
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Check ownership
    if service["seller_id"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Update fields
    update_data = {k: v for k, v in request.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    await db.service_listings.update_one(
        {"_id": ObjectId(service_id)},
        {"$set": update_data}
    )
    
    updated_service = await db.service_listings.find_one({"_id": ObjectId(service_id)})
    updated_service["_id"] = str(updated_service["_id"])
    
    return {
        "message": "Service updated successfully",
        "service": updated_service
    }

@router.delete("/{service_id}")
async def delete_service(
    service_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    # Find service
    service = await db.service_listings.find_one({"_id": ObjectId(service_id)})
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Check ownership
    if service["seller_id"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Deactivate instead of deleting
    await db.service_listings.update_one(
        {"_id": ObjectId(service_id)},
        {"$set": {"active": False, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Service deactivated successfully"}

@router.get("/seller/my-services")
async def get_my_services(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    if current_user["role"] not in ["seller", "both"]:
        raise HTTPException(status_code=403, detail="Only sellers can view services")
    
    cursor = db.service_listings.find({"seller_id": current_user["_id"]})
    services = await cursor.to_list(length=100)
    
    for service in services:
        service["_id"] = str(service["_id"])
    
    return {"services": services}
