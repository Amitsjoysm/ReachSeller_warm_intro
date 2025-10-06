from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'warm_connects')]

# Create the main app without a prefix
app = FastAPI(title="Warm Connects API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Import route modules
from routes import auth, linkedin, services, wallet, orders, reviews, disputes

# Root endpoint
@api_router.get("/")
async def root():
    return {
        "message": "Warm Connects Marketplace API",
        "version": "1.0.0",
        "status": "active"
    }

# Health check
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}

# Include all routers
api_router.include_router(auth.router)
api_router.include_router(linkedin.router)
api_router.include_router(services.router)
api_router.include_router(wallet.router)
api_router.include_router(orders.router)
api_router.include_router(reviews.router)
api_router.include_router(disputes.router)

# Include the router in the main app
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    logger.info("Warm Connects API started successfully")
    logger.info(f"MongoDB connected to: {mongo_url}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    logger.info("MongoDB connection closed")
