from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import asyncio
import time
from loguru import logger

from config import settings
from agents.super_agent import SuperAgent
from agents.product_manager import ProductManagerAgent
from agents.architecture import ArchitectureAgent
from agents.allocator import EmployeeAllocatorAgent
from core.embeddings import embedding_manager
from core.emailer import email_manager

# Initialize FastAPI app
app = FastAPI(
    title="metaGPT Multi-Agent System",
    description="Industry-grade multi-agent system for coordinating Product Manager, Architecture, and Employee Allocator agents",
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

# Initialize agents
super_agent = SuperAgent()
pm_agent = ProductManagerAgent()
architecture_agent = ArchitectureAgent()
allocator_agent = EmployeeAllocatorAgent()

# Request/Response models
class RequirementRequest(BaseModel):
    requirement: str
    priority: Optional[str] = "Medium"
    metadata: Optional[Dict[str, Any]] = {}

class AgentRequest(BaseModel):
    input_data: Dict[str, Any]
    options: Optional[Dict[str, Any]] = {}

class SuperAgentRequest(BaseModel):
    requirement: str
    async_execution: Optional[bool] = False
    notify_stakeholders: Optional[bool] = True

# Global state for async executions
async_executions = {}

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "agents": {
            "super_agent": "initialized",
            "product_manager": "initialized",
            "architecture": "initialized",
            "allocator": "initialized"
        },
        "services": {
            "embedding_manager": "connected",
            "email_manager": "connected",
            "mongodb": "connected" if settings.MONGODB_URI else "not_configured"
        }
    }

@app.get("/metrics")
async def metrics():
    """System metrics endpoint."""
    try:
        # Get embedding statistics
        embedding_stats = embedding_manager.get_stats()
        
        return {
            "system_metrics": {
                "uptime": "active",
                "timestamp": time.time()
            },
            "embedding_metrics": embedding_stats,
            "agent_metrics": {
                "super_agent_executions": len(async_executions),
                "active_async_executions": len([ex for ex in async_executions.values() if ex.get("status") == "running"])
            }
        }
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        return {
            "error": str(e),
            "timestamp": time.time()
        }

@app.post("/agent/product-manager/run")
async def run_product_manager(request: AgentRequest):
    """Run Product Manager Agent."""
    try:
        logger.info("Running Product Manager Agent via API")
        
        input_data = request.input_data
        requirement = input_data.get("requirement")
        
        if not requirement:
            raise HTTPException(status_code=400, detail="Requirement is required")
        
        result = await pm_agent.run(requirement)
        
        return {
            "agent": "ProductManager",
            "status": "completed",
            "result": result,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Product Manager Agent failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/architecture/run")
async def run_architecture_agent(request: AgentRequest):
    """Run Architecture Agent."""
    try:
        logger.info("Running Architecture Agent via API")
        
        input_data = request.input_data
        specification = input_data.get("specification")
        
        if not specification:
            raise HTTPException(status_code=400, detail="Specification is required")
        
        result = await architecture_agent.run(specification)
        
        return {
            "agent": "Architecture",
            "status": "completed",
            "result": result,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Architecture Agent failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/allocator/run")
async def run_allocator_agent(request: AgentRequest):
    """Run Employee Allocator Agent."""
    try:
        logger.info("Running Employee Allocator Agent via API")
        
        input_data = request.input_data
        architecture = input_data.get("architecture")
        
        if not architecture:
            raise HTTPException(status_code=400, detail="Architecture is required")
        
        result = await allocator_agent.run(architecture)
        
        return {
            "agent": "EmployeeAllocator",
            "status": "completed",
            "result": result,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Employee Allocator Agent failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def execute_super_agent_async(execution_id: str, requirement: str):
    """Execute Super Agent asynchronously."""
    try:
        logger.info(f"Starting async Super Agent execution: {execution_id}")
        
        # Update status
        async_executions[execution_id]["status"] = "running"
        async_executions[execution_id]["start_time"] = time.time()
        
        # Execute workflow
        result = await super_agent.execute(requirement)
        
        # Update with results
        async_executions[execution_id].update({
            "status": "completed",
            "result": result,
            "end_time": time.time(),
            "duration": time.time() - async_executions[execution_id]["start_time"]
        })
        
        logger.info(f"Async Super Agent execution completed: {execution_id}")
        
    except Exception as e:
        logger.error(f"Async Super Agent execution failed: {execution_id} - {str(e)}")
        
        async_executions[execution_id].update({
            "status": "failed",
            "error": str(e),
            "end_time": time.time(),
            "duration": time.time() - async_executions[execution_id]["start_time"]
        })

@app.post("/superagent/execute")
async def execute_super_agent(request: SuperAgentRequest, background_tasks: BackgroundTasks):
    """Execute Super Agent workflow."""
    try:
        logger.info("Executing Super Agent workflow via API")
        
        requirement = request.requirement
        if not requirement or len(requirement.strip()) < 10:
            raise HTTPException(
                status_code=400, 
                detail="Requirement must be at least 10 characters long"
            )
        
        if request.async_execution:
            # Async execution
            execution_id = f"exec_{int(time.time() * 1000)}"
            
            # Initialize execution state
            async_executions[execution_id] = {
                "id": execution_id,
                "requirement": requirement,
                "status": "queued",
                "created_time": time.time()
            }
            
            # Add background task
            background_tasks.add_task(execute_super_agent_async, execution_id, requirement)
            
            return {
                "execution_id": execution_id,
                "status": "queued",
                "message": "Super Agent execution started asynchronously",
                "check_status_url": f"/superagent/status/{execution_id}",
                "timestamp": time.time()
            }
        
        else:
            # Synchronous execution
            result = await super_agent.execute(requirement)
            
            return {
                "execution_type": "synchronous",
                "status": "completed",
                "result": result,
                "timestamp": time.time()
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Super Agent execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/superagent/status/{execution_id}")
async def get_execution_status(execution_id: str):
    """Get status of async Super Agent execution."""
    if execution_id not in async_executions:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    execution = async_executions[execution_id]
    
    return {
        "execution_id": execution_id,
        "status": execution["status"],
        "created_time": execution["created_time"],
        "start_time": execution.get("start_time"),
        "end_time": execution.get("end_time"),
        "duration": execution.get("duration"),
        "result": execution.get("result") if execution["status"] == "completed" else None,
        "error": execution.get("error") if execution["status"] == "failed" else None,
        "timestamp": time.time()
    }

@app.get("/superagent/executions")
async def list_executions():
    """List all Super Agent executions."""
    return {
        "executions": [
            {
                "execution_id": exec_id,
                "status": execution["status"],
                "created_time": execution["created_time"],
                "duration": execution.get("duration")
            }
            for exec_id, execution in async_executions.items()
        ],
        "total_executions": len(async_executions),
        "timestamp": time.time()
    }

@app.post("/embeddings/search")
async def search_embeddings(request: Dict[str, Any]):
    """Search for similar embeddings."""
    try:
        query = request.get("query")
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        k = request.get("k", 5)
        
        # For demo purposes, create a dummy embedding
        # In production, you'd use a real embedding model
        query_embedding = [0.1] * 384
        
        results = embedding_manager.search_similar(query_embedding, k)
        
        return {
            "query": query,
            "results": results,
            "count": len(results),
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Embedding search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/embeddings/stats")
async def get_embedding_stats():
    """Get embedding statistics."""
    try:
        stats = embedding_manager.get_stats()
        return {
            "embedding_stats": stats,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error getting embedding stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/test/email")
async def test_email(request: Dict[str, Any]):
    """Test email functionality."""
    try:
        to_email = request.get("to_email", "test@example.com")
        subject = request.get("subject", "Test Email from metaGPT System")
        body = request.get("body", "This is a test email from the metaGPT multi-agent system.")
        
        result = await email_manager.send_email([to_email], subject, body)
        
        return {
            "email_test": "completed",
            "result": result,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Email test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents/status")
async def get_agents_status():
    """Get status of all agents."""
    try:
        # Get workflow status from super agent
        super_agent_status = await super_agent.get_workflow_status()
        
        return {
            "agents": {
                "super_agent": {
                    "status": "active",
                    "current_workflow": super_agent_status
                },
                "product_manager": {
                    "status": "active",
                    "agent_name": pm_agent.agent_name
                },
                "architecture": {
                    "status": "active",
                    "agent_name": architecture_agent.agent_name
                },
                "allocator": {
                    "status": "active",
                    "agent_name": allocator_agent.agent_name
                }
            },
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Error getting agents status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("🚀 metaGPT Multi-Agent System starting up...")
    logger.info(f"📡 MongoDB URI: {settings.MONGODB_URI}")
    logger.info(f"📧 Email configured: {bool(settings.SMTP_SERVER)}")
    logger.info("✅ All agents initialized and ready!")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("🛑 metaGPT Multi-Agent System shutting down...")
    logger.info("✅ Cleanup completed!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
