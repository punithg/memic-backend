from fastapi import HTTPException
from app.services.health_service import HealthService
from app.dtos.health_dto import HealthResponseDTO


class HealthController:
    """Controller for health check endpoints."""
    
    @staticmethod
    async def check_health() -> HealthResponseDTO:
        """
        Health check endpoint handler.
        
        Returns:
            HealthResponseDTO: Health status response
            
        Raises:
            HTTPException: If health check fails
        """
        try:
            health_data = HealthService.check_health()
            
            # If unhealthy, return 503 Service Unavailable
            if health_data["status"] == "unhealthy":
                raise HTTPException(
                    status_code=503,
                    detail="Service is unhealthy"
                )
            
            return HealthResponseDTO(**health_data)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error: {str(e)}"
            )

