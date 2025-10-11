from fastapi import APIRouter
from app.controllers.health_controller import HealthController
from app.dtos.health_dto import HealthResponseDTO

# Create API router
router = APIRouter()

# Health check routes
router.add_api_route(
    "/health",
    HealthController.check_health,
    methods=["GET"],
    response_model=HealthResponseDTO,
    summary="Health Check",
    description="Check application health status including database connectivity",
    tags=["Health"]
)

