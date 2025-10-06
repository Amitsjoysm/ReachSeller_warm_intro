import random
import string
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "warm-connects-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 30

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def generate_otp(length: int = 6) -> str:
    return ''.join(random.choices(string.digits, k=length))

def generate_order_number() -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"WC-{timestamp}-{random_suffix}"

def generate_dispute_number() -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"DISP-{timestamp}-{random_suffix}"

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def calculate_authenticity_score(social_account: dict) -> float:
    """
    Calculate authenticity score (0-100) for social media account
    """
    engagement_rate = social_account.get('engagement_rate', 0)
    bot_percentage = social_account.get('bot_follower_percentage', 0)
    account_age_months = social_account.get('account_age_months', 0)
    posts_90_days = social_account.get('posts_last_90_days', 0)
    
    # Component 1: Engagement Rate (40%)
    engagement_score = min(engagement_rate * 10, 40)
    
    # Component 2: Follower Quality (30%)
    follower_quality = (100 - bot_percentage) * 0.3
    
    # Component 3: Account Age (15%)
    age_score = min(account_age_months / 36 * 15, 15)
    
    # Component 4: Content Consistency (15%)
    expected_posts = 12
    consistency_score = min(posts_90_days / expected_posts * 15, 15)
    
    total_score = engagement_score + follower_quality + age_score + consistency_score
    
    return round(total_score, 2)

def calculate_reputation_score(seller: dict) -> float:
    """
    Calculate seller reputation score (0-100)
    """
    avg_rating = seller.get('average_rating', 0)
    completion_rate = seller.get('completion_rate', 0)
    response_time = seller.get('response_time_hours', 24)
    orders_last_30_days = seller.get('orders_last_30_days', 0)
    dispute_rate = seller.get('dispute_rate', 0)
    
    # Component 1: Average Rating (40%)
    rating_score = (avg_rating / 5.0) * 40
    
    # Component 2: Completion Rate (25%)
    completion_score = completion_rate * 0.25
    
    # Component 3: Response Time (15%)
    response_score = max(15 - (response_time / 24 * 15), 0)
    
    # Component 4: Activity Level (10%)
    activity_score = min(orders_last_30_days / 10 * 10, 10)
    
    # Component 5: Dispute Rate (10%, negative impact)
    dispute_penalty = dispute_rate * 10
    dispute_score = max(10 - dispute_penalty, 0)
    
    total_score = rating_score + completion_score + response_score + activity_score + dispute_score
    
    return round(total_score, 2)

def calculate_seller_tier(seller: dict) -> str:
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
        return 'bronze'

def calculate_platform_fee(base_price: float, seller_tier: str) -> float:
    """
    Calculate platform fee based on seller tier
    """
    tier_fees = {
        'new': 0.15,
        'bronze': 0.14,
        'silver': 0.13,
        'gold': 0.12,
        'platinum': 0.10
    }
    
    fee_percentage = tier_fees.get(seller_tier, 0.15)
    platform_fee = base_price * fee_percentage
    
    return round(platform_fee, 2)

def generate_mock_linkedin_data() -> dict:
    """
    Generate mock LinkedIn data for testing
    """
    follower_count = random.randint(500, 10000)
    engagement_rate = round(random.uniform(2.0, 8.0), 2)
    bot_percentage = round(random.uniform(5.0, 20.0), 2)
    account_age = random.randint(12, 60)
    posts_90_days = random.randint(10, 50)
    
    return {
        'follower_count': follower_count,
        'connection_count': follower_count,
        'engagement_rate': engagement_rate,
        'bot_follower_percentage': bot_percentage,
        'account_age_months': account_age,
        'posts_last_90_days': posts_90_days,
        'profile_url': f'https://linkedin.com/in/mock-user-{random.randint(1000, 9999)}',
        'username': f'mockuser{random.randint(1000, 9999)}'
    }
