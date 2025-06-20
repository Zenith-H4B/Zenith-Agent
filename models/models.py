"""Data models for the application."""
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EmployeeRole(str, Enum):
    DEVELOPER = "developer"
    DESIGNER = "designer"
    PRODUCT_MANAGER = "product_manager"
    QA_ENGINEER = "qa_engineer"
    DEVOPS_ENGINEER = "devops_engineer"
    DATA_SCIENTIST = "data_scientist"
    ARCHITECT = "architect"


class Employee(BaseModel):
    """Employee model."""
    id: Optional[str] = None
    name: str
    email: EmailStr
    role: EmployeeRole
    skills: List[str] = Field(default_factory=list)
    capacity_hours_per_week: int = Field(default=40, ge=1, le=80)
    current_workload_hours: int = Field(default=0, ge=0)
    org_id: str
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Organization(BaseModel):
    """Organization model."""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    industry: Optional[str] = None
    employees: List[Employee] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProductRequirement(BaseModel):
    """Product requirement input model."""
    org_id: str
    requirement_text: str
    priority: Priority = Priority.MEDIUM
    deadline: Optional[datetime] = None
    additional_context: Optional[str] = None


class Task(BaseModel):
    """Task model."""
    id: Optional[str] = None
    title: str
    description: str
    priority: Priority
    estimated_duration_hours: int
    due_date: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    assigned_to: Optional[str] = None  # Employee ID
    assigned_to_email: Optional[str] = None
    created_by_agent: str
    org_id: str
    additional_details: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class FeatureSpec(BaseModel):
    """Feature specification from Product Manager Agent."""
    title: str
    description: str
    user_stories: List[str]
    acceptance_criteria: List[str]
    priority: Priority
    estimated_effort: str
    dependencies: List[str] = Field(default_factory=list)


class SystemArchitecture(BaseModel):
    """System architecture from Architecture Agent."""
    tech_stack: List[str]
    system_components: List[str]
    architecture_diagram_description: str
    database_schema: Optional[str] = None
    api_endpoints: List[str] = Field(default_factory=list)
    security_considerations: List[str] = Field(default_factory=list)


class TaskAllocation(BaseModel):
    """Task allocation from Employee Allocator Agent."""
    employee_id: str
    employee_email: str
    employee_name: str
    tasks: List[Task]
    total_estimated_hours: int
    allocation_reasoning: str


class AgentResponse(BaseModel):
    """Base response model for agents."""
    agent_name: str
    success: bool
    data: Dict[str, Any]
    reasoning: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ProcessingResult(BaseModel):
    """Final processing result."""
    org_id: str
    requirement: ProductRequirement
    feature_specs: Optional[FeatureSpec] = None
    architecture: Optional[SystemArchitecture] = None
    task_allocations: List[TaskAllocation] = Field(default_factory=list)
    email_results: Optional[Dict[str, Any]] = None
    processing_time_seconds: Optional[float] = None
    success: bool
    errors: List[str] = Field(default_factory=list)
