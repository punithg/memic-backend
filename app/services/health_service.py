from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.config import settings


class HealthService:
    """Service for health check business logic."""
    
    @staticmethod
    def check_health() -> dict:
        """
        Check application health including database connectivity.
        
        Returns:
            dict: Health status information
        """
        try:
            # Check database connectivity
            db_status = HealthService._check_database_health()
            
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow(),
                "database": db_status,
                "version": settings.app_version
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow(),
                "database": "disconnected",
                "version": settings.app_version,
                "error": str(e)
            }
    
    @staticmethod
    def _check_database_health() -> str:
        """
        Check database connection health.
        
        Returns:
            str: Database status
        """
        try:
            db = SessionLocal()
            # Simple query to test database connection
            db.execute(text("SELECT 1"))
            db.close()
            return "connected"
        except Exception:
            return "disconnected"

