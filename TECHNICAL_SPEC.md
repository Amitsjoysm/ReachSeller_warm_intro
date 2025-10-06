# Warm Connects Marketplace - Technical Specification

## 1. Executive Summary

### Technology Stack
- **Frontend**: React Native (Expo) with TypeScript
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **Authentication**: JWT with OTP verification
- **Social Integration**: LinkedIn OAuth 2.0
- **State Management**: Zustand
- **Navigation**: Expo Router (file-based routing)
- **UI Framework**: React Native Elements + React Native Paper

### MVP Scope
Complete marketplace with:
- User authentication (email/password + OTP)
- Dual user roles (Seller/Buyer)
- LinkedIn verification for sellers
- Service listings and discovery
- Credit/wallet system (mocked payments)
- Full transaction flow with escrow
- Review and rating system
- Dispute resolution workflow
- Transaction ledger for both parties

---

## 2. Database Schema

### 2.1 Users Collection
```javascript
{
  _id: ObjectId,
  email: String (unique, indexed),
  phone: String,
  password_hash: String,
  role: Enum["seller", "buyer", "both"], // Users can be both
  
  // Profile Info
  full_name: String,
  profile_picture: String (base64),
  bio: String (500 chars max),
  location: {
    city: String,
    country: String
  },
  
  // Verification
  email_verified: Boolean,
  phone_verified: Boolean,
  kyc_status: Enum["pending", "verified", "rejected"],
  kyc_documents: {
    id_proof: String (base64),
    address_proof: String (base64),
    selfie: String (base64),
    submitted_at: DateTime,
    verified_at: DateTime
  },
  
  // Seller-specific fields
  seller_profile: {
    tier: Enum["new", "bronze", "silver", "gold", "platinum"],
    reputation_score: Number (0-100),
    completion_rate: Number (percentage),
    response_time: Number (hours),
    total_orders: Number,
    total_earnings: Number,
    available_balance: Number,
    pending_balance: Number,
    industries: [String], // Max 10
    specializations: [String]
  },
  
  // Buyer-specific fields
  buyer_profile: {
    company_name: String,
    company_website: String,
    company_size: String,
    industry: String,
    verified_business: Boolean,
    credit_balance: Number,
    total_spent: Number,
    total_orders: Number
  },
  
  // Activity tracking
  last_active: DateTime,
  created_at: DateTime,
  updated_at: DateTime
}
```

### 2.2 Social Accounts Collection
```javascript
{
  _id: ObjectId,
  user_id: ObjectId (ref: Users),
  platform: Enum["linkedin", "facebook", "instagram", "twitter", "youtube"],
  
  // OAuth data
  platform_user_id: String,
  access_token: String (encrypted),
  refresh_token: String (encrypted),
  token_expires_at: DateTime,
  
  // Profile data
  profile_url: String,
  username: String,
  
  // Metrics
  follower_count: Number,
  connection_count: Number,
  engagement_rate: Number (percentage),
  account_age_months: Number,
  posts_last_90_days: Number,
  
  // Authenticity
  authenticity_score: Number (0-100),
  bot_follower_percentage: Number,
  
  // Verification
  verification_method: Enum["oauth", "manual"],
  verified_at: DateTime,
  last_reverified: DateTime,
  next_reverification: DateTime,
  verification_status: Enum["verified", "pending", "rejected"],
  
  created_at: DateTime,
  updated_at: DateTime
}
```

### 2.3 Service Listings Collection
```javascript
{
  _id: ObjectId,
  seller_id: ObjectId (ref: Users),
  
  // Service details
  title: String (100 chars max),
  description: String (1000 chars max),
  service_type: Enum[
    "post_creation",
    "article_share",
    "post_engagement",
    "recommendation",
    "endorsement",
    "introduction",
    "event_promotion",
    "content_repost",
    "story_mention",
    "video_shoutout",
    "tagged_post",
    "product_review",
    "engagement_bundle",
    "campaign_support",
    "launch_package"
  ],
  
  // Pricing
  base_price: Number (credits),
  pricing_type: Enum["per_action", "package"],
  package_quantity: Number (if package),
  
  // Delivery
  turnaround_hours: Number,
  revisions_included: Number,
  
  // Targeting
  platforms: [String], // ["linkedin", "instagram", etc.]
  industries: [String], // Max 5
  content_categories: [String],
  
  // Requirements
  content_guidelines: String,
  restrictions: [String],
  requires_approval: Boolean,
  
  // Add-ons
  addons: [{
    name: String,
    price: Number,
    description: String
  }],
  
  // Status
  active: Boolean,
  total_orders: Number,
  average_rating: Number,
  
  created_at: DateTime,
  updated_at: DateTime
}
```

### 2.4 Orders Collection
```javascript
{
  _id: ObjectId,
  order_number: String (unique, auto-generated),
  
  // Parties
  buyer_id: ObjectId (ref: Users),
  seller_id: ObjectId (ref: Users),
  service_id: ObjectId (ref: Service Listings),
  
  // Order details
  service_title: String,
  service_type: String,
  quantity: Number,
  platform: String,
  
  // Pricing
  base_cost: Number,
  platform_fee: Number,
  express_fee: Number,
  total_cost: Number,
  
  // Content requirements
  brief: String,
  attachments: [String], // base64 or URLs
  hashtags: [String],
  mentions: [String],
  special_instructions: String,
  
  // Timeline
  turnaround_hours: Number,
  deadline: DateTime,
  
  // Status flow
  status: Enum[
    "pending_acceptance",    // Waiting for seller to accept
    "accepted",              // Seller accepted, work in progress
    "delivered",             // Seller submitted proof
    "revision_requested",    // Buyer asked for changes
    "approved",              // Buyer approved
    "completed",             // Payment released
    "disputed",              // Under dispute
    "cancelled",             // Cancelled
    "refunded"              // Refunded
  ],
  
  // Escrow
  escrow_status: Enum["locked", "active", "under_review", "released", "disputed", "refunded"],
  escrow_amount: Number,
  
  // Delivery
  proof_of_completion: {
    url: String,
    screenshots: [String], // base64
    description: String,
    submitted_at: DateTime,
    verified: Boolean,
    verification_method: String
  },
  
  // Revisions
  revision_count: Number,
  revision_requests: [{
    requested_at: DateTime,
    reason: String,
    instructions: String,
    completed_at: DateTime
  }],
  
  // Review window
  review_deadline: DateTime,
  auto_approved: Boolean,
  
  // Communication
  messages: [{
    sender_id: ObjectId,
    message: String,
    timestamp: DateTime,
    read: Boolean
  }],
  
  // Timestamps
  created_at: DateTime,
  accepted_at: DateTime,
  delivered_at: DateTime,
  completed_at: DateTime,
  updated_at: DateTime
}
```

### 2.5 Reviews Collection
```javascript
{
  _id: ObjectId,
  order_id: ObjectId (ref: Orders),
  reviewer_id: ObjectId (ref: Users),
  reviewee_id: ObjectId (ref: Users),
  reviewer_role: Enum["buyer", "seller"],
  
  // Ratings (1-5 stars)
  overall_rating: Number,
  
  // Role-specific ratings
  // If buyer reviewing seller:
  quality_rating: Number,
  communication_rating: Number,
  timeliness_rating: Number,
  professionalism_rating: Number,
  
  // If seller reviewing buyer:
  clear_communication_rating: Number,
  reasonable_expectations_rating: Number,
  timely_responses_rating: Number,
  payment_reliability_rating: Number,
  
  // Written review
  review_text: String (500 chars max),
  would_work_again: Boolean,
  
  // Response
  response_text: String,
  response_date: DateTime,
  
  // Status
  is_public: Boolean,
  flagged: Boolean,
  flag_reason: String,
  
  created_at: DateTime,
  updated_at: DateTime
}
```

### 2.6 Disputes Collection
```javascript
{
  _id: ObjectId,
  dispute_number: String (unique),
  order_id: ObjectId (ref: Orders),
  
  // Parties
  initiator_id: ObjectId (ref: Users),
  respondent_id: ObjectId (ref: Users),
  
  // Dispute details
  dispute_type: Enum[
    "non_delivery",
    "quality_issues",
    "requirement_mismatch",
    "platform_violation",
    "missing_disclosure",
    "fake_proof",
    "unauthorized_changes",
    "communication_breakdown",
    "inappropriate_content",
    "payment_issues"
  ],
  
  // Initiator submission
  initiator_reason: String,
  initiator_evidence: [String], // base64 screenshots
  initiator_proposed_resolution: String,
  
  // Respondent submission
  respondent_response: String,
  respondent_evidence: [String],
  respondent_proposed_resolution: String,
  respondent_responded_at: DateTime,
  
  // Status
  status: Enum["open", "awaiting_response", "under_mediation", "resolved", "appealed"],
  
  // Mediation
  mediator_id: ObjectId (ref: Admin/Users),
  mediator_assigned_at: DateTime,
  mediator_notes: String,
  
  // Resolution
  resolution_type: Enum[
    "full_refund",
    "partial_refund",
    "full_payment",
    "order_cancellation",
    "revision_required",
    "split_decision"
  ],
  resolution_details: String,
  refund_percentage: Number,
  resolved_at: DateTime,
  
  // Appeal
  appeal_requested: Boolean,
  appeal_reason: String,
  appeal_evidence: [String],
  appeal_decision: String,
  appeal_resolved_at: DateTime,
  
  created_at: DateTime,
  updated_at: DateTime
}
```

### 2.7 Transactions Collection (Ledger)
```javascript
{
  _id: ObjectId,
  user_id: ObjectId (ref: Users),
  
  // Transaction details
  transaction_type: Enum[
    "credit_purchase",
    "credit_refund",
    "order_payment",
    "order_refund",
    "earnings_received",
    "withdrawal",
    "platform_fee",
    "bonus"
  ],
  
  // Amounts
  amount: Number,
  balance_before: Number,
  balance_after: Number,
  
  // Related entities
  order_id: ObjectId (ref: Orders, optional),
  related_user_id: ObjectId (ref: Users, optional),
  
  // Payment details (for purchases)
  payment_method: String,
  payment_reference: String,
  
  // Metadata
  description: String,
  notes: String,
  
  created_at: DateTime
}
```

### 2.8 OTP Collection
```javascript
{
  _id: ObjectId,
  email: String,
  phone: String,
  otp_code: String,
  otp_type: Enum["email_verification", "phone_verification", "login", "password_reset"],
  verified: Boolean,
  expires_at: DateTime,
  created_at: DateTime
}
```

---

## 3. API Endpoints

### 3.1 Authentication Endpoints

#### POST /api/auth/register
Register new user
```json
Request:
{
  "email": "user@example.com",
  "phone": "+1234567890",
  "password": "securepass123",
  "full_name": "John Doe",
  "role": "seller" // or "buyer" or "both"
}

Response:
{
  "message": "Registration successful. Please verify your email.",
  "user_id": "507f1f77bcf86cd799439011",
  "email_otp_sent": true
}
```

#### POST /api/auth/verify-email
Verify email with OTP
```json
Request:
{
  "email": "user@example.com",
  "otp": "123456"
}

Response:
{
  "message": "Email verified successfully",
  "access_token": "jwt_token_here",
  "refresh_token": "refresh_token_here",
  "user": { user_object }
}
```

#### POST /api/auth/login
Login user
```json
Request:
{
  "email": "user@example.com",
  "password": "securepass123"
}

Response:
{
  "access_token": "jwt_token_here",
  "refresh_token": "refresh_token_here",
  "user": { user_object }
}
```

#### POST /api/auth/resend-otp
Resend OTP
```json
Request:
{
  "email": "user@example.com",
  "otp_type": "email_verification"
}

Response:
{
  "message": "OTP sent successfully"
}
```

### 3.2 LinkedIn Integration Endpoints

#### GET /api/linkedin/auth-url
Get LinkedIn OAuth URL
```json
Response:
{
  "auth_url": "https://www.linkedin.com/oauth/v2/authorization?..."
}
```

#### POST /api/linkedin/callback
Handle LinkedIn OAuth callback
```json
Request:
{
  "code": "authorization_code_from_linkedin",
  "state": "random_state_string"
}

Response:
{
  "message": "LinkedIn account linked successfully",
  "social_account": { social_account_object }
}
```

#### GET /api/linkedin/metrics/{user_id}
Get LinkedIn metrics for user
```json
Response:
{
  "platform": "linkedin",
  "follower_count": 5000,
  "connection_count": 3000,
  "engagement_rate": 4.5,
  "authenticity_score": 85,
  "verified": true
}
```

#### POST /api/linkedin/reverify/{user_id}
Trigger re-verification
```json
Response:
{
  "message": "Re-verification initiated",
  "status": "pending"
}
```

### 3.3 Service Listing Endpoints

#### POST /api/services/create
Create service listing (Seller only)
```json
Request:
{
  "title": "LinkedIn Post Share with Commentary",
  "description": "I will share your content...",
  "service_type": "article_share",
  "base_price": 25,
  "pricing_type": "per_action",
  "turnaround_hours": 24,
  "platforms": ["linkedin"],
  "industries": ["technology", "saas"],
  "content_guidelines": "Professional content only",
  "restrictions": ["No political content"],
  "requires_approval": false
}

Response:
{
  "message": "Service created successfully",
  "service_id": "507f1f77bcf86cd799439011",
  "service": { service_object }
}
```

#### GET /api/services/search
Search and discover services
```json
Query Params:
- platform: linkedin
- min_price: 10
- max_price: 100
- industry: technology
- service_type: article_share
- min_rating: 4.0
- sort: price_low | price_high | rating | popular
- page: 1
- limit: 20

Response:
{
  "services": [ service_objects ],
  "total": 150,
  "page": 1,
  "total_pages": 8
}
```

#### GET /api/services/{service_id}
Get service details
```json
Response:
{
  "service": { service_object },
  "seller": { seller_profile },
  "reviews": [ review_objects ]
}
```

#### PUT /api/services/{service_id}
Update service listing
```json
Request: (same as create)

Response:
{
  "message": "Service updated successfully",
  "service": { service_object }
}
```

#### DELETE /api/services/{service_id}
Delete/deactivate service
```json
Response:
{
  "message": "Service deactivated successfully"
}
```

### 3.4 Order Endpoints

#### POST /api/orders/create
Create new order (Buyer only)
```json
Request:
{
  "service_id": "507f1f77bcf86cd799439011",
  "quantity": 1,
  "platform": "linkedin",
  "brief": "Please share this article about AI...",
  "hashtags": ["AI", "Technology"],
  "mentions": ["@company"],
  "special_instructions": "Post during business hours",
  "turnaround_hours": 24
}

Response:
{
  "message": "Order created successfully",
  "order": { order_object },
  "credits_deducted": 27,
  "new_balance": 73
}
```

#### POST /api/orders/{order_id}/accept
Accept order (Seller only)
```json
Response:
{
  "message": "Order accepted",
  "order": { order_object },
  "deadline": "2025-01-15T10:30:00Z"
}
```

#### POST /api/orders/{order_id}/decline
Decline order (Seller only)
```json
Request:
{
  "reason": "Timeline not feasible"
}

Response:
{
  "message": "Order declined. Credits refunded to buyer.",
  "order": { order_object }
}
```

#### POST /api/orders/{order_id}/deliver
Submit proof of completion (Seller only)
```json
Request:
{
  "url": "https://linkedin.com/post/...",
  "screenshots": ["base64_image_1"],
  "description": "Posted as requested with all hashtags"
}

Response:
{
  "message": "Proof submitted. Awaiting buyer approval.",
  "order": { order_object }
}
```

#### POST /api/orders/{order_id}/approve
Approve delivery (Buyer only)
```json
Response:
{
  "message": "Order approved. Payment released to seller.",
  "order": { order_object }
}
```

#### POST /api/orders/{order_id}/request-revision
Request revision (Buyer only)
```json
Request:
{
  "reason": "Missing hashtags",
  "instructions": "Please add #TechTrends"
}

Response:
{
  "message": "Revision requested",
  "order": { order_object }
}
```

#### POST /api/orders/{order_id}/dispute
Open dispute
```json
Request:
{
  "dispute_type": "quality_issues",
  "reason": "Content doesn't match requirements",
  "evidence": ["base64_screenshot_1"],
  "proposed_resolution": "50% refund"
}

Response:
{
  "message": "Dispute opened",
  "dispute": { dispute_object }
}
```

#### GET /api/orders/buyer
Get buyer's orders
```json
Query Params:
- status: pending_acceptance | accepted | delivered | completed
- page: 1
- limit: 20

Response:
{
  "orders": [ order_objects ],
  "total": 25
}
```

#### GET /api/orders/seller
Get seller's orders
```json
(Same structure as buyer orders)
```

### 3.5 Review Endpoints

#### POST /api/reviews/create
Create review (after order completion)
```json
Request:
{
  "order_id": "507f1f77bcf86cd799439011",
  "overall_rating": 5,
  "quality_rating": 5,
  "communication_rating": 5,
  "timeliness_rating": 4,
  "professionalism_rating": 5,
  "review_text": "Great work! Very professional.",
  "would_work_again": true
}

Response:
{
  "message": "Review submitted successfully",
  "review": { review_object }
}
```

#### GET /api/reviews/user/{user_id}
Get user's reviews
```json
Response:
{
  "reviews": [ review_objects ],
  "average_rating": 4.8,
  "total_reviews": 45,
  "rating_breakdown": {
    "5_star": 35,
    "4_star": 8,
    "3_star": 2,
    "2_star": 0,
    "1_star": 0
  }
}
```

### 3.6 Credit/Wallet Endpoints

#### POST /api/wallet/purchase-credits
Purchase credits (mocked)
```json
Request:
{
  "amount": 100,
  "payment_method": "credit_card_mock"
}

Response:
{
  "message": "Credits purchased successfully",
  "credits_added": 105,
  "bonus": 5,
  "new_balance": 105,
  "transaction_id": "507f1f77bcf86cd799439011"
}
```

#### GET /api/wallet/balance
Get wallet balance
```json
Response:
{
  "available_balance": 75,
  "in_escrow": 25,
  "total": 100
}
```

#### GET /api/wallet/transactions
Get transaction history
```json
Response:
{
  "transactions": [ transaction_objects ],
  "total": 50
}
```

#### POST /api/wallet/withdraw (Seller only)
Withdraw earnings
```json
Request:
{
  "amount": 100,
  "payment_method": "bank_account"
}

Response:
{
  "message": "Withdrawal request submitted",
  "processing_time": "3-5 business days",
  "transaction_id": "507f1f77bcf86cd799439011"
}
```

### 3.7 Dispute Resolution Endpoints

#### POST /api/disputes/{dispute_id}/respond
Respond to dispute (Respondent)
```json
Request:
{
  "response": "I delivered as per requirements",
  "evidence": ["base64_screenshot"],
  "proposed_resolution": "No refund warranted"
}

Response:
{
  "message": "Response submitted",
  "dispute": { dispute_object }
}
```

#### POST /api/disputes/{dispute_id}/mediate
Mediation decision (Admin/Mediator only)
```json
Request:
{
  "resolution_type": "partial_refund",
  "refund_percentage": 50,
  "resolution_details": "Both parties share responsibility"
}

Response:
{
  "message": "Dispute resolved",
  "dispute": { dispute_object }
}
```

#### GET /api/disputes/user
Get user's disputes
```json
Response:
{
  "disputes": [ dispute_objects ]
}
```

### 3.8 User Profile Endpoints

#### GET /api/users/profile
Get current user profile
```json
Response:
{
  "user": { user_object }
}
```

#### PUT /api/users/profile
Update profile
```json
Request:
{
  "full_name": "John Updated",
  "bio": "Updated bio",
  "location": { "city": "NYC", "country": "USA" }
}

Response:
{
  "message": "Profile updated",
  "user": { user_object }
}
```

#### POST /api/users/kyc-submit
Submit KYC documents
```json
Request:
{
  "id_proof": "base64_image",
  "address_proof": "base64_image",
  "selfie": "base64_image"
}

Response:
{
  "message": "KYC documents submitted for review",
  "status": "pending"
}
```

#### GET /api/users/seller/{seller_id}
Get seller public profile
```json
Response:
{
  "seller": { seller_profile },
  "services": [ service_objects ],
  "reviews": [ review_objects ],
  "stats": {
    "completion_rate": 98,
    "avg_response_time": 2.5,
    "total_orders": 150
  }
}
```

---

## 4. Frontend Structure (Expo Router)

### 4.1 File-Based Routing Structure
```
frontend/
├── app/
│   ├── (auth)/
│   │   ├── login.tsx
│   │   ├── register.tsx
│   │   ├── verify-email.tsx
│   │   └── forgot-password.tsx
│   │
│   ├── (tabs)/                    # Main app tabs
│   │   ├── _layout.tsx            # Tab navigator
│   │   ├── index.tsx              # Home/Discovery
│   │   ├── orders.tsx             # Orders list
│   │   ├── messages.tsx           # Messages
│   │   └── profile.tsx            # Profile
│   │
│   ├── seller/
│   │   ├── onboarding.tsx
│   │   ├── linkedin-connect.tsx
│   │   ├── create-service.tsx
│   │   ├── services.tsx           # My services list
│   │   ├── dashboard.tsx
│   │   └── earnings.tsx
│   │
│   ├── buyer/
│   │   ├── credits.tsx            # Purchase credits
│   │   ├── wallet.tsx             # Wallet management
│   │   └── favorites.tsx
│   │
│   ├── orders/
│   │   ├── [id].tsx               # Order details
│   │   ├── create.tsx             # Create order
│   │   └── review.tsx             # Review order
│   │
│   ├── services/
│   │   ├── [id].tsx               # Service details
│   │   └── search.tsx             # Search services
│   │
│   ├── disputes/
│   │   ├── [id].tsx               # Dispute details
│   │   └── create.tsx             # Create dispute
│   │
│   ├── _layout.tsx                # Root layout
│   └── index.tsx                  # Entry point / onboarding
│
├── components/
│   ├── auth/
│   ├── common/
│   ├── seller/
│   ├── buyer/
│   └── orders/
│
├── services/
│   ├── api.ts                     # API client
│   ├── auth.service.ts
│   ├── linkedin.service.ts
│   └── order.service.ts
│
├── store/
│   ├── authStore.ts               # Zustand store
│   ├── orderStore.ts
│   └── walletStore.ts
│
├── utils/
│   ├── validation.ts
│   ├── formatting.ts
│   └── constants.ts
│
└── types/
    └── index.ts                   # TypeScript types
```

---

## 5. Key Algorithms

### 5.1 Authenticity Score Algorithm
```python
def calculate_authenticity_score(social_account):
    """
    Calculate authenticity score (0-100) for social media account
    """
    # Component 1: Engagement Rate (40%)
    engagement_score = min(social_account['engagement_rate'] * 10, 40)
    
    # Component 2: Follower Quality (30%)
    bot_percentage = social_account['bot_follower_percentage']
    follower_quality = (100 - bot_percentage) * 0.3
    
    # Component 3: Account Age (15%)
    account_age_months = social_account['account_age_months']
    age_score = min(account_age_months / 36 * 15, 15)  # Cap at 36 months
    
    # Component 4: Content Consistency (15%)
    posts_90_days = social_account['posts_last_90_days']
    expected_posts = 12  # ~1 post per week
    consistency_score = min(posts_90_days / expected_posts * 15, 15)
    
    total_score = engagement_score + follower_quality + age_score + consistency_score
    
    return round(total_score, 2)
```

### 5.2 Reputation Score Algorithm
```python
def calculate_reputation_score(seller):
    """
    Calculate seller reputation score (0-100)
    """
    # Component 1: Average Rating (40%)
    avg_rating = seller.get('average_rating', 0)
    rating_score = (avg_rating / 5.0) * 40
    
    # Component 2: Completion Rate (25%)
    completion_rate = seller.get('completion_rate', 0)
    completion_score = completion_rate * 0.25
    
    # Component 3: Response Time (15%)
    response_time = seller.get('response_time_hours', 24)
    # Lower is better, max 15 points for < 2 hours, 0 for > 24 hours
    response_score = max(15 - (response_time / 24 * 15), 0)
    
    # Component 4: Activity Level (10%)
    orders_last_30_days = seller.get('orders_last_30_days', 0)
    activity_score = min(orders_last_30_days / 10 * 10, 10)
    
    # Component 5: Dispute Rate (10%, negative impact)
    dispute_rate = seller.get('dispute_rate', 0)
    dispute_penalty = dispute_rate * 10
    dispute_score = max(10 - dispute_penalty, 0)
    
    total_score = rating_score + completion_score + response_score + activity_score + dispute_score
    
    return round(total_score, 2)
```

### 5.3 Seller Tier Calculation
```python
def calculate_seller_tier(seller):
    """
    Determine seller tier based on orders and rating
    """
    total_orders = seller.get('total_orders', 0)
    avg_rating = seller.get('average_rating', 0)
    dispute_rate = seller.get('dispute_rate', 0)
    
    if total_orders < 11:
        return 'new'
    elif total_orders < 51 and avg_rating >= 4.0:
        return 'bronze'
    elif total_orders < 201 and avg_rating >= 4.3:
        return 'silver'
    elif total_orders < 501 and avg_rating >= 4.5 and dispute_rate < 0.05:
        return 'gold'
    elif total_orders >= 501 and avg_rating >= 4.7 and dispute_rate < 0.02:
        return 'platinum'
    else:
        return 'bronze'  # Default fallback
```

### 5.4 Platform Fee Calculation
```python
def calculate_platform_fee(base_price, seller_tier):
    """
    Calculate platform fee based on seller tier
    """
    tier_fees = {
        'new': 0.15,      # 15%
        'bronze': 0.14,   # 14%
        'silver': 0.13,   # 13%
        'gold': 0.12,     # 12%
        'platinum': 0.10  # 10%
    }
    
    fee_percentage = tier_fees.get(seller_tier, 0.15)
    platform_fee = base_price * fee_percentage
    
    return round(platform_fee, 2)
```

---

## 6. User Flows

### 6.1 Seller Onboarding Flow
1. Register account (email/password)
2. Verify email with OTP
3. Select role as "Seller" or "Both"
4. Complete profile (name, bio, location)
5. Submit KYC documents (ID, address proof, selfie)
6. Connect LinkedIn account (OAuth)
7. System verifies LinkedIn metrics
8. Create first service listing
9. Wait for account approval (KYC review)
10. Start receiving orders

### 6.2 Buyer Purchase Flow
1. Register/Login as Buyer
2. Browse marketplace or search sellers
3. Filter by platform, price, rating, industry
4. View seller profile and reviews
5. Select service listing
6. Purchase credits (mocked payment)
7. Customize order (brief, hashtags, instructions)
8. Place order (credits moved to escrow)
9. Wait for seller acceptance
10. Monitor order progress
11. Receive delivery notification
12. Review proof of completion
13. Approve or request revision
14. Leave review

### 6.3 Order Fulfillment Flow (Seller)
1. Receive order notification
2. Review requirements and deadline
3. Accept or decline order
4. Complete work on LinkedIn
5. Submit proof (URL + screenshot)
6. Wait for buyer approval (72 hours)
7. If approved: Receive payment (48-hour clearance)
8. If revision requested: Update and resubmit
9. If disputed: Provide evidence and response
10. Receive review from buyer

### 6.4 Dispute Resolution Flow
1. Buyer/Seller opens dispute
2. Select dispute type and provide evidence
3. Respondent has 48 hours to respond
4. Both parties provide evidence and proposed resolution
5. System assigns mediator (auto)
6. Mediator reviews all evidence
7. Mediator makes decision (5 business days)
8. Decision executed (refund/payment/revision)
9. Both parties notified
10. Appeal option available (72 hours)

---

## 7. Mobile UI/UX Considerations

### 7.1 Navigation Pattern
- **Tab Navigation**: Primary navigation for main sections
  - Home (Discovery)
  - Orders
  - Messages
  - Profile
- **Stack Navigation**: For deeper flows (order details, service creation)
- **Modal Navigation**: For quick actions (filters, purchase credits)

### 7.2 Touch Targets
- Minimum 44pt (iOS) / 48px (Android) for all touchable elements
- Adequate spacing between interactive elements
- Thumb-friendly bottom navigation

### 7.3 Responsive Design
- Use Flexbox for layouts
- Test on multiple screen sizes (phones, tablets)
- Handle keyboard interactions properly
- Safe area insets for notched devices

### 7.4 Performance
- Implement FlatList/FlashList for long lists
- Image optimization (compress base64)
- Lazy loading for non-critical data
- Pull-to-refresh on list screens
- Skeleton loaders for better perceived performance

### 7.5 Offline Handling
- Cache user data locally
- Queue actions when offline
- Show appropriate offline indicators
- Sync when connection restored

---

## 8. Security Considerations

### 8.1 Authentication
- JWT tokens with expiration
- Refresh token rotation
- Secure token storage (SecureStore)
- OTP expiration (10 minutes)

### 8.2 Data Protection
- Encrypt sensitive data at rest
- HTTPS for all API calls
- No sensitive data in logs
- Proper input validation

### 8.3 Authorization
- Role-based access control
- Verify user permissions on every API call
- Separate seller/buyer endpoints

---

## 9. Testing Strategy

### 9.1 Backend Testing
- Test all API endpoints with curl
- Validate authentication flows
- Test escrow logic
- Verify MongoDB operations
- Test LinkedIn OAuth flow

### 9.2 Frontend Testing
- Test navigation flows
- Verify form validations
- Test order creation and approval
- Test credit purchase
- Test dispute flow
- Verify mobile responsiveness

---

## 10. Implementation Phases

### Phase 1: Foundation (Core Infrastructure)
- Setup project structure
- Implement authentication (register, login, OTP)
- User profile management
- Basic navigation structure
- MongoDB models

### Phase 2: LinkedIn Integration
- LinkedIn OAuth implementation
- Metrics collection
- Authenticity scoring
- Seller onboarding flow

### Phase 3: Marketplace Core
- Service listing creation
- Service discovery and search
- Seller profiles
- Credit/wallet system (mocked)

### Phase 4: Transaction Flow
- Order creation
- Escrow system
- Order acceptance/decline
- Proof of completion
- Approval/revision flow

### Phase 5: Review & Dispute Systems
- Review creation and display
- Rating calculations
- Dispute creation
- Dispute resolution workflow
- Transaction ledger

### Phase 6: Polish & Testing
- UI/UX refinements
- Comprehensive testing
- Bug fixes
- Performance optimization

---

## 11. Success Metrics

- Users can register and authenticate
- Sellers can connect LinkedIn and create services
- Buyers can purchase credits and place orders
- Escrow system correctly holds and releases funds
- Review system works end-to-end
- Dispute resolution flow is functional
- Mobile app is responsive and performant

---

## 12. Future Enhancements (Post-MVP)
- Additional social platforms (Instagram, Twitter, etc.)
- Real payment integration (Stripe)
- Push notifications
- In-app messaging
- Advanced analytics
- Admin panel
- AI-powered fraud detection
