from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any


class HealthResponseDTO(BaseModel):
    """Health check response schema."""
    
    status: str
    timestamp: datetime
    database: str
    version: str
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

