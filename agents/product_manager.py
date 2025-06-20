"""Product Manager Agent: defines feature specs and roadmaps."""

import asyncio
from typing import Dict, Any, List
from loguru import logger
from core.metaGPT_client import metagpt_client

class ProductManagerAgent:
    """Product Manager Agent using metaGPT architecture."""
    
    def __init__(self):
        self.agent_name = "ProductManager"
        self.role = "Product Strategy and Specification"
        logger.info(f"Initialized {self.agent_name} agent")
    
    async def analyze_requirement(self, requirement: str) -> Dict[str, Any]:
        """Analyze the initial requirement and break it down."""
        try:
            logger.info(f"PM Agent analyzing requirement: {requirement[:100]}...")
            
            # Use metaGPT client to get product specification
            result = await metagpt_client.get_product_spec(requirement)
            
            # Process and structure the result
            analysis = {
                "original_requirement": requirement,
                "requirement_complexity": self._assess_complexity(requirement),
                "estimated_scope": self._estimate_scope(requirement),
                "key_features": self._extract_key_features(requirement),
                "stakeholders": self._identify_stakeholders(requirement),
                "success_criteria": self._define_success_criteria(requirement),
                "metaGPT_result": result
            }
            
            logger.info("PM Agent requirement analysis completed")
            logger.debug(f"Analysis includes: {list(analysis.keys())}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"PM Agent requirement analysis failed: {str(e)}")
            return {
                "original_requirement": requirement,
                "error": str(e),
                "status": "failed"
            }
    
    def _assess_complexity(self, requirement: str) -> str:
        """Assess the complexity of the requirement."""
        word_count = len(requirement.split())
        
        if word_count < 10:
            return "Low"
        elif word_count < 30:
            return "Medium"
        else:
            return "High"
    
    def _estimate_scope(self, requirement: str) -> Dict[str, Any]:
        """Estimate the project scope."""
        requirement_lower = requirement.lower()
        
        # Simple keyword-based scope estimation
        web_keywords = ['website', 'web', 'api', 'backend', 'frontend', 'dashboard']
        mobile_keywords = ['mobile', 'app', 'ios', 'android', 'smartphone']
        ai_keywords = ['ai', 'machine learning', 'ml', 'artificial intelligence', 'nlp']
        data_keywords = ['data', 'analytics', 'database', 'storage', 'reporting']
        
        platforms = []
        technologies = []
        
        if any(keyword in requirement_lower for keyword in web_keywords):
            platforms.append("Web")
            technologies.extend(["FastAPI", "React/Vue", "Database"])
        
        if any(keyword in requirement_lower for keyword in mobile_keywords):
            platforms.append("Mobile")
            technologies.extend(["React Native", "Flutter"])
        
        if any(keyword in requirement_lower for keyword in ai_keywords):
            technologies.extend(["AI/ML", "Python", "TensorFlow/PyTorch"])
        
        if any(keyword in requirement_lower for keyword in data_keywords):
            technologies.extend(["Database", "Analytics", "ETL"])
        
        return {
            "platforms": platforms or ["Web"],
            "technologies": technologies or ["Standard Web Stack"],
            "estimated_timeline": self._estimate_timeline(requirement),
            "team_size": self._estimate_team_size(requirement)
        }
    
    def _extract_key_features(self, requirement: str) -> List[str]:
        """Extract key features from the requirement."""
        # Simple feature extraction based on common patterns
        features = []
        requirement_lower = requirement.lower()
        
        feature_indicators = {
            "user management": ["user", "login", "signup", "authentication", "account"],
            "data storage": ["store", "save", "database", "data", "record"],
            "reporting": ["report", "analytics", "dashboard", "metrics", "stats"],
            "notifications": ["notify", "alert", "email", "message", "notification"],
            "search": ["search", "find", "filter", "query"],
            "file management": ["file", "upload", "download", "document", "attachment"],
            "real-time updates": ["real-time", "live", "instant", "websocket"],
            "mobile support": ["mobile", "responsive", "app", "smartphone"],
            "integration": ["integrate", "api", "connect", "sync", "third-party"]
        }
        
        for feature, keywords in feature_indicators.items():
            if any(keyword in requirement_lower for keyword in keywords):
                features.append(feature)
        
        return features or ["Core Functionality"]
    
    def _identify_stakeholders(self, requirement: str) -> List[str]:
        """Identify potential stakeholders."""
        stakeholders = ["Product Owner", "Development Team", "End Users"]
        
        requirement_lower = requirement.lower()
        
        if any(word in requirement_lower for word in ["admin", "manager", "management"]):
            stakeholders.append("System Administrators")
        
        if any(word in requirement_lower for word in ["customer", "client", "user"]):
            stakeholders.append("Customers")
        
        if any(word in requirement_lower for word in ["report", "analytics", "business"]):
            stakeholders.append("Business Analysts")
        
        return list(set(stakeholders))
    
    def _define_success_criteria(self, requirement: str) -> List[str]:
        """Define success criteria for the project."""
        criteria = [
            "Functional requirements met",
            "Performance benchmarks achieved",
            "User acceptance criteria satisfied",
            "Security requirements implemented"
        ]
        
        requirement_lower = requirement.lower()
        
        if "fast" in requirement_lower or "quick" in requirement_lower:
            criteria.append("Response time < 2 seconds")
        
        if "scale" in requirement_lower or "many users" in requirement_lower:
            criteria.append("System supports concurrent users")
        
        if "secure" in requirement_lower or "security" in requirement_lower:
            criteria.append("Security audit passed")
        
        return criteria
    
    def _estimate_timeline(self, requirement: str) -> str:
        """Estimate project timeline."""
        complexity = self._assess_complexity(requirement)
        feature_count = len(self._extract_key_features(requirement))
        
        if complexity == "Low" and feature_count <= 3:
            return "2-4 weeks"
        elif complexity == "Medium" or feature_count <= 6:
            return "1-3 months"
        else:
            return "3-6 months"
    
    def _estimate_team_size(self, requirement: str) -> str:
        """Estimate required team size."""
        features = self._extract_key_features(requirement)
        scope = self._estimate_scope(requirement)
        
        if len(features) <= 3 and len(scope["platforms"]) == 1:
            return "2-3 developers"
        elif len(features) <= 6:
            return "3-5 developers"
        else:
            return "5-8 developers"
    
    async def create_product_specification(self, requirement: str) -> Dict[str, Any]:
        """Create a comprehensive product specification."""
        try:
            logger.info("PM Agent creating comprehensive product specification")
            
            # Get requirement analysis
            analysis = await self.analyze_requirement(requirement)
            
            # Create detailed specification
            specification = {
                "project_overview": {
                    "title": self._generate_project_title(requirement),
                    "description": requirement,
                    "objectives": self._define_objectives(requirement),
                    "scope": analysis.get("estimated_scope", {}),
                    "success_criteria": analysis.get("success_criteria", [])
                },
                "functional_requirements": {
                    "core_features": analysis.get("key_features", []),
                    "user_stories": self._generate_user_stories(requirement),
                    "acceptance_criteria": self._generate_acceptance_criteria(requirement)
                },
                "non_functional_requirements": {
                    "performance": self._define_performance_requirements(requirement),
                    "security": self._define_security_requirements(requirement),
                    "scalability": self._define_scalability_requirements(requirement),
                    "usability": self._define_usability_requirements(requirement)
                },
                "technical_considerations": {
                    "platforms": analysis.get("estimated_scope", {}).get("platforms", []),
                    "technologies": analysis.get("estimated_scope", {}).get("technologies", []),
                    "integrations": self._identify_integrations(requirement)
                },
                "project_planning": {
                    "timeline": analysis.get("estimated_scope", {}).get("estimated_timeline", ""),
                    "team_size": analysis.get("estimated_scope", {}).get("team_size", ""),
                    "milestones": self._define_milestones(requirement),
                    "risks": self._identify_risks(requirement)
                },
                "stakeholders": analysis.get("stakeholders", []),
                "metadata": {
                    "created_by": self.agent_name,
                    "complexity": analysis.get("requirement_complexity", ""),
                    "agent_analysis": analysis
                }
            }
            
            logger.info("PM Agent product specification created successfully")
            logger.debug(f"Specification sections: {list(specification.keys())}")
            
            return {
                "agent": self.agent_name,
                "requirement": requirement,
                "specification": specification,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"PM Agent specification creation failed: {str(e)}")
            return {
                "agent": self.agent_name,
                "requirement": requirement,
                "error": str(e),
                "status": "failed"
            }
    
    def _generate_project_title(self, requirement: str) -> str:
        """Generate a project title from the requirement."""
        # Simple title generation
        words = requirement.split()[:5]  # Take first 5 words
        title = " ".join(words).title()
        if len(title) > 50:
            title = title[:47] + "..."
        return title or "Untitled Project"
    
    def _define_objectives(self, requirement: str) -> List[str]:
        """Define project objectives."""
        return [
            f"Deliver solution for: {requirement[:100]}",
            "Meet user requirements and expectations",
            "Ensure scalable and maintainable solution",
            "Deliver on time and within budget"
        ]
    
    def _generate_user_stories(self, requirement: str) -> List[str]:
        """Generate user stories based on requirement."""
        features = self._extract_key_features(requirement)
        stories = []
        
        for feature in features:
            stories.append(f"As a user, I want to use {feature} so that I can accomplish my goals")
        
        # Add some default stories
        stories.extend([
            "As a user, I want an intuitive interface so that I can use the system easily",
            "As an admin, I want to manage the system so that it runs smoothly",
            "As a stakeholder, I want to see progress reports so that I can track development"
        ])
        
        return stories
    
    def _generate_acceptance_criteria(self, requirement: str) -> List[str]:
        """Generate acceptance criteria."""
        return [
            "All functional requirements are implemented",
            "System passes all test cases",
            "Performance meets specified requirements",
            "Security requirements are satisfied",
            "User interface is intuitive and responsive",
            "Documentation is complete and accurate"
        ]
    
    def _define_performance_requirements(self, requirement: str) -> Dict[str, str]:
        """Define performance requirements."""
        return {
            "response_time": "< 2 seconds for standard operations",
            "throughput": "Handle expected user load",
            "availability": "99.9% uptime",
            "scalability": "Support growth in users and data"
        }
    
    def _define_security_requirements(self, requirement: str) -> List[str]:
        """Define security requirements."""
        return [
            "Data encryption in transit and at rest",
            "User authentication and authorization",
            "Input validation and sanitization",
            "Security audit compliance",
            "Regular security updates"
        ]
    
    def _define_scalability_requirements(self, requirement: str) -> List[str]:
        """Define scalability requirements."""
        return [
            "Horizontal scaling capability",
            "Database optimization",
            "Caching strategy implementation",
            "Load balancing support"
        ]
    
    def _define_usability_requirements(self, requirement: str) -> List[str]:
        """Define usability requirements."""
        return [
            "Intuitive user interface",
            "Responsive design",
            "Accessibility compliance",
            "User help and documentation",
            "Error handling and user feedback"
        ]
    
    def _identify_integrations(self, requirement: str) -> List[str]:
        """Identify potential integrations."""
        integrations = []
        requirement_lower = requirement.lower()
        
        integration_keywords = {
            "Email service": ["email", "notification", "mail"],
            "Payment gateway": ["payment", "billing", "transaction"],
            "Authentication service": ["auth", "login", "sso"],
            "Cloud storage": ["storage", "file", "cloud"],
            "Analytics service": ["analytics", "tracking", "metrics"],
            "Social media": ["social", "facebook", "twitter", "linkedin"]
        }
        
        for integration, keywords in integration_keywords.items():
            if any(keyword in requirement_lower for keyword in keywords):
                integrations.append(integration)
        
        return integrations
    
    def _define_milestones(self, requirement: str) -> List[Dict[str, str]]:
        """Define project milestones."""
        return [
            {"milestone": "Requirements Analysis", "timeline": "Week 1"},
            {"milestone": "System Design", "timeline": "Week 2"},
            {"milestone": "Development Phase 1", "timeline": "Week 3-4"},
            {"milestone": "Testing Phase", "timeline": "Week 5"},
            {"milestone": "Deployment", "timeline": "Week 6"},
            {"milestone": "Go Live", "timeline": "Week 7"}
        ]
    
    def _identify_risks(self, requirement: str) -> List[Dict[str, str]]:
        """Identify potential project risks."""
        return [
            {"risk": "Scope creep", "mitigation": "Clear requirements documentation"},
            {"risk": "Technical complexity", "mitigation": "Proof of concept development"},
            {"risk": "Resource availability", "mitigation": "Team planning and backup resources"},
            {"risk": "Timeline delays", "mitigation": "Regular progress monitoring"},
            {"risk": "Integration challenges", "mitigation": "Early integration testing"}
        ]
    
    async def run(self, requirement: str) -> Dict[str, Any]:
        """Main entry point for the Product Manager Agent."""
        try:
            logger.info(f"PM Agent starting execution for requirement: {requirement[:100]}...")
            
            result = await self.create_product_specification(requirement)
            
            logger.info("PM Agent execution completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"PM Agent execution failed: {str(e)}")
            return {
                "agent": self.agent_name,
                "requirement": requirement,
                "error": str(e),
                "status": "failed"
            }
