from fastapi import APIRouter
from app.controllers.health_controller import HealthController
from app.dtos.health_dto import HealthResponseDTO
from app.controllers import (
    auth_controller,
    user_controller,
    organization_controller,
    project_controller,
    member_controller,
    file_controller
)

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

# Include all API routes
router.include_router(auth_controller.router)
router.include_router(user_controller.router)
router.include_router(organization_controller.router)
router.include_router(project_controller.router)
router.include_router(member_controller.router)
router.include_router(file_controller.router)

