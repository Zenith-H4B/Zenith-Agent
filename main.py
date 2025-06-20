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
from database.database import db
from utils.embedding_service import embedding_service


# Configure logging
logger.remove()
logger.add(sys.stderr, level=settings.LOG_LEVEL)
logger.add("logs/app.log", rotation="500 MB", retention="10 days", level=settings.LOG_LEVEL)

# Create FastAPI app
app = FastAPI(
    title="AI Agent Task Allocation System",
    description="Multi-agent system for product requirement analysis and task allocation",
    version="1.0.0"
)

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


# Results endpoints
@app.get("/organizations/{org_id}/results")
async def get_processing_results(org_id: str, limit: int = 10):
    """Get processing results for an organization."""
    try:
        results = list(db.processing_results.find(
            {"org_id": org_id}
        ).sort("created_at", -1).limit(limit))
        
        for result in results:
            result["_id"] = str(result["_id"])
        
        return {"results": results}
        
    except Exception as e:
        logger.error(f"Error getting results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/organizations/{org_id}/tasks")
async def get_tasks(org_id: str, employee_email: Optional[str] = None):
    """Get tasks for an organization or specific employee."""
    try:
        query = {"org_id": org_id}
        if employee_email:
            query["assigned_to_email"] = employee_email
        
        tasks = list(db.tasks.find(query).sort("created_at", -1))
        for task in tasks:
            task["_id"] = str(task["_id"])
        
        return {"tasks": tasks}
        
    except Exception as e:
        logger.error(f"Error getting tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Statistics endpoint
@app.get("/organizations/{org_id}/stats")
async def get_organization_stats(org_id: str):
    """Get organization statistics."""
    try:
        # Get basic counts
        employee_count = db.employees.count_documents({"org_id": org_id, "is_active": True})
        task_count = db.tasks.count_documents({"org_id": org_id})
        processing_count = db.processing_results.count_documents({"org_id": org_id})
        
        # Get recent activity
        recent_tasks = list(db.tasks.find({"org_id": org_id}).sort("created_at", -1).limit(5))
        for task in recent_tasks:
            task["_id"] = str(task["_id"])
        
        return {
            "employee_count": employee_count,
            "task_count": task_count,
            "processing_count": processing_count,
            "recent_tasks": recent_tasks
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
