"""FastAPI main application."""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from loguru import logger
from datetime import datetime
import sys
from bson import ObjectId
from config import settings
from models.models import ProductRequirement, ProcessingResult, Organization, Employee
from agents.super_agent import super_agent
from agents.LogCleanupAgent import LogCleanupAgent
from database.database import db
from utils.embedding_service import embedding_service
from services import log_streaming
from logs.log_buffer import log_buffer


# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add(log_buffer, level="INFO")

# Create FastAPI app
app = FastAPI(
    title="AI Agent Task Allocation System",
    description="Multi-agent system for product requirement analysis and task allocation",
    version="1.0.0"
)

# Register log streaming router
app.include_router(log_streaming.router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class ProcessRequirementRequest(BaseModel):
    org_id: str
    requirement_text: str
    priority: str = "medium"
    deadline: Optional[datetime] = None
    additional_context: Optional[str] = None

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now()}

# Main processing endpoint
@app.post("/process-requirement", response_model=ProcessingResult)
async def process_requirement(request: ProcessRequirementRequest, background_tasks: BackgroundTasks):
    """Process a product requirement through the agent system."""
    try:
        logger.info(f"Received requirement processing request for org {request.org_id}")
        
        # Validate organization exists
        org = db.organizations.find_one({"_id": ObjectId(request.org_id)})
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Create ProductRequirement object
        requirement = ProductRequirement(
            org_id=request.org_id,
            requirement_text=request.requirement_text,
            priority=request.priority,
            deadline=request.deadline,
            additional_context=request.additional_context
        )
        
        # Process through super agent
        result = await super_agent.process_requirement(requirement)
        
        logger.info(f"Requirement processing completed for org {request.org_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing requirement: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process-modifying")
async def process_modifying(request: ProcessRequirementRequest, background_tasks: BackgroundTasks):
    """Process a product requirement and return cleaned logs in one go."""
    try:
        logger.info(f"Received requirement processing request for org {request.org_id}")
        org = db.organizations.find_one({"_id": ObjectId(request.org_id)})
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        requirement = ProductRequirement(
            org_id=request.org_id,
            requirement_text=request.requirement_text,
            priority=request.priority,
            deadline=request.deadline,
            additional_context=request.additional_context
        )
        # Process through super agent
        result = await super_agent.process_requirement(requirement)
        logger.info(f"Requirement processing completed for org {request.org_id}")
        # Read and clean logs
        log_path = "logs/app.log"
        cleaned_logs = []
        if os.path.exists(log_path):
            with open(log_path, "r") as f:
                raw_logs = f.readlines()
            agent = LogCleanupAgent()
            response = await agent.process({"raw_logs": raw_logs})
            cleaned_logs = response.data.get("cleaned_logs", [])
        return {
            "result": result,
            "logs": cleaned_logs
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing requirement: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
