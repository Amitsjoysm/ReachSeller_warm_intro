from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    SELLER = "seller"
    BUYER = "buyer"
    BOTH = "both"

class KYCStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"

class SellerTier(str, Enum):
    NEW = "new"
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"

class Platform(str, Enum):
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    YOUTUBE = "youtube"

class ServiceType(str, Enum):
    POST_CREATION = "post_creation"
    ARTICLE_SHARE = "article_share"
    POST_ENGAGEMENT = "post_engagement"
    RECOMMENDATION = "recommendation"
    ENDORSEMENT = "endorsement"
    INTRODUCTION = "introduction"
    EVENT_PROMOTION = "event_promotion"
    CONTENT_REPOST = "content_repost"
    STORY_MENTION = "story_mention"
    VIDEO_SHOUTOUT = "video_shoutout"
    TAGGED_POST = "tagged_post"
    PRODUCT_REVIEW = "product_review"
    ENGAGEMENT_BUNDLE = "engagement_bundle"
    CAMPAIGN_SUPPORT = "campaign_support"
    LAUNCH_PACKAGE = "launch_package"

class OrderStatus(str, Enum):
    PENDING_ACCEPTANCE = "pending_acceptance"
    ACCEPTED = "accepted"
    DELIVERED = "delivered"
    REVISION_REQUESTED = "revision_requested"
    APPROVED = "approved"
    COMPLETED = "completed"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class EscrowStatus(str, Enum):
    LOCKED = "locked"
    ACTIVE = "active"
    UNDER_REVIEW = "under_review"
    RELEASED = "released"
    DISPUTED = "disputed"
    REFUNDED = "refunded"

class DisputeType(str, Enum):
    NON_DELIVERY = "non_delivery"
    QUALITY_ISSUES = "quality_issues"
    REQUIREMENT_MISMATCH = "requirement_mismatch"
    PLATFORM_VIOLATION = "platform_violation"
    MISSING_DISCLOSURE = "missing_disclosure"
    FAKE_PROOF = "fake_proof"
    UNAUTHORIZED_CHANGES = "unauthorized_changes"
    COMMUNICATION_BREAKDOWN = "communication_breakdown"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    PAYMENT_ISSUES = "payment_issues"

class DisputeStatus(str, Enum):
    OPEN = "open"
    AWAITING_RESPONSE = "awaiting_response"
    UNDER_MEDIATION = "under_mediation"
    RESOLVED = "resolved"
    APPEALED = "appealed"

class ResolutionType(str, Enum):
    FULL_REFUND = "full_refund"
    PARTIAL_REFUND = "partial_refund"
    FULL_PAYMENT = "full_payment"
    ORDER_CANCELLATION = "order_cancellation"
    REVISION_REQUIRED = "revision_required"
    SPLIT_DECISION = "split_decision"

class TransactionType(str, Enum):
    CREDIT_PURCHASE = "credit_purchase"
    CREDIT_REFUND = "credit_refund"
    ORDER_PAYMENT = "order_payment"
    ORDER_REFUND = "order_refund"
    EARNINGS_RECEIVED = "earnings_received"
    WITHDRAWAL = "withdrawal"
    PLATFORM_FEE = "platform_fee"
    BONUS = "bonus"

# Pydantic Models
class Location(BaseModel):
    city: Optional[str] = None
    country: Optional[str] = None

class KYCDocuments(BaseModel):
    id_proof: Optional[str] = None
    address_proof: Optional[str] = None
    selfie: Optional[str] = None
    submitted_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None

class SellerProfile(BaseModel):
    tier: SellerTier = SellerTier.NEW
    reputation_score: float = 0.0
    completion_rate: float = 0.0
    response_time: float = 0.0
    total_orders: int = 0
    total_earnings: float = 0.0
    available_balance: float = 0.0
    pending_balance: float = 0.0
    industries: List[str] = []
    specializations: List[str] = []

class BuyerProfile(BaseModel):
    company_name: Optional[str] = None
    company_website: Optional[str] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None
    verified_business: bool = False
    credit_balance: float = 0.0
    total_spent: float = 0.0
    total_orders: int = 0

class User(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    email: EmailStr
    phone: Optional[str] = None
    password_hash: str
    role: UserRole
    full_name: str
    profile_picture: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[Location] = None
    email_verified: bool = False
    phone_verified: bool = False
    kyc_status: KYCStatus = KYCStatus.PENDING
    kyc_documents: Optional[KYCDocuments] = None
    seller_profile: Optional[SellerProfile] = None
    buyer_profile: Optional[BuyerProfile] = None
    last_active: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True

class SocialAccount(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    platform: Platform
    platform_user_id: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    profile_url: Optional[str] = None
    username: Optional[str] = None
    follower_count: int = 0
    connection_count: int = 0
    engagement_rate: float = 0.0
    account_age_months: int = 0
    posts_last_90_days: int = 0
    authenticity_score: float = 0.0
    bot_follower_percentage: float = 0.0
    verification_method: str = "mock"
    verified_at: Optional[datetime] = None
    last_reverified: Optional[datetime] = None
    next_reverification: Optional[datetime] = None
    verification_status: str = "verified"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True

class ServiceAddon(BaseModel):
    name: str
    price: float
    description: str

class ServiceListing(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    seller_id: str
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
    active: bool = True
    total_orders: int = 0
    average_rating: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True

class ProofOfCompletion(BaseModel):
    url: Optional[str] = None
    screenshots: List[str] = []
    description: Optional[str] = None
    submitted_at: Optional[datetime] = None
    verified: bool = False
    verification_method: Optional[str] = None

class RevisionRequest(BaseModel):
    requested_at: datetime
    reason: str
    instructions: str
    completed_at: Optional[datetime] = None

class OrderMessage(BaseModel):
    sender_id: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    read: bool = False

class Order(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    order_number: str
    buyer_id: str
    seller_id: str
    service_id: str
    service_title: str
    service_type: str
    quantity: int = 1
    platform: str
    base_cost: float
    platform_fee: float
    express_fee: float = 0.0
    total_cost: float
    brief: Optional[str] = None
    attachments: List[str] = []
    hashtags: List[str] = []
    mentions: List[str] = []
    special_instructions: Optional[str] = None
    turnaround_hours: int
    deadline: Optional[datetime] = None
    status: OrderStatus = OrderStatus.PENDING_ACCEPTANCE
    escrow_status: EscrowStatus = EscrowStatus.LOCKED
    escrow_amount: float
    proof_of_completion: Optional[ProofOfCompletion] = None
    revision_count: int = 0
    revision_requests: List[RevisionRequest] = []
    review_deadline: Optional[datetime] = None
    auto_approved: bool = False
    messages: List[OrderMessage] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    accepted_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True

class Review(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    order_id: str
    reviewer_id: str
    reviewee_id: str
    reviewer_role: str
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
    response_text: Optional[str] = None
    response_date: Optional[datetime] = None
    is_public: bool = True
    flagged: bool = False
    flag_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True

class Dispute(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    dispute_number: str
    order_id: str
    initiator_id: str
    respondent_id: str
    dispute_type: DisputeType
    initiator_reason: str
    initiator_evidence: List[str] = []
    initiator_proposed_resolution: Optional[str] = None
    respondent_response: Optional[str] = None
    respondent_evidence: List[str] = []
    respondent_proposed_resolution: Optional[str] = None
    respondent_responded_at: Optional[datetime] = None
    status: DisputeStatus = DisputeStatus.OPEN
    mediator_id: Optional[str] = None
    mediator_assigned_at: Optional[datetime] = None
    mediator_notes: Optional[str] = None
    resolution_type: Optional[ResolutionType] = None
    resolution_details: Optional[str] = None
    refund_percentage: Optional[float] = None
    resolved_at: Optional[datetime] = None
    appeal_requested: bool = False
    appeal_reason: Optional[str] = None
    appeal_evidence: List[str] = []
    appeal_decision: Optional[str] = None
    appeal_resolved_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True

class Transaction(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    transaction_type: TransactionType
    amount: float
    balance_before: float
    balance_after: float
    order_id: Optional[str] = None
    related_user_id: Optional[str] = None
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True

class OTP(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    email: Optional[str] = None
    phone: Optional[str] = None
    otp_code: str
    otp_type: str
    verified: bool = False
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
