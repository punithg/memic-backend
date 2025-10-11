from datetime import datetime
from app.config import settings


class HealthService:
    """Service for health check business logic."""
    
    @staticmethod
    def check_health() -> dict:
        """
        Check application health (without database connectivity for now).
        
        Returns:
            dict: Health status information
        """
        try:
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow(),
                "database": "not_configured",
                "version": settings.app_version
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow(),
                "database": "not_configured",
                "version": settings.app_version,
                "error": str(e)
            }

