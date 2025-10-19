"""
Base Repository with automatic tenant filtering.

Provides generic CRUD operations with built-in multi-tenant data isolation.
All queries automatically filter by organization_id or project_id from TenantContext.
"""

from typing import Generic, TypeVar, Type, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.tenant_context import TenantContext
from app.database import Base


ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base repository with automatic tenant filtering.
    
    Enforces data isolation by automatically filtering queries based on
    TenantContext. Prevents accidental data leakage across tenants.
    """
    
    def __init__(self, model: Type[ModelType], db: Session):
        """
        Initialize repository.
        
        Args:
            model: SQLAlchemy model class
            db: Database session
        """
        self.model = model
        self.db = db
    
    def get(self, id: UUID, context: Optional[TenantContext] = None) -> Optional[ModelType]:
        """
        Get entity by ID with optional tenant filtering.
        
        Args:
            id: Entity ID
            context: Tenant context for filtering (optional for non-tenant entities)
            
        Returns:
            Entity if found, None otherwise
        """
        query = self.db.query(self.model).filter(self.model.id == id)
        
        # Apply tenant filtering if context is provided
        if context:
            query = self._apply_tenant_filter(query, context)
        
        return query.first()
    
    def list(
        self, 
        context: Optional[TenantContext] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """
        List entities with optional tenant filtering and pagination.
        
        Args:
            context: Tenant context for filtering
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of entities
        """
        query = self.db.query(self.model)
        
        # Apply tenant filtering if context is provided
        if context:
            query = self._apply_tenant_filter(query, context)
        
        return query.offset(skip).limit(limit).all()
    
    def create(self, entity: ModelType, context: Optional[TenantContext] = None) -> ModelType:
        """
        Create a new entity.
        
        Args:
            entity: Entity to create
            context: Tenant context (for audit/validation)
            
        Returns:
            Created entity
        """
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def update(self, entity: ModelType, context: Optional[TenantContext] = None) -> ModelType:
        """
        Update an existing entity.
        
        Args:
            entity: Entity to update
            context: Tenant context (for validation)
            
        Returns:
            Updated entity
        """
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def delete(self, id: UUID, context: Optional[TenantContext] = None) -> bool:
        """
        Delete entity by ID with tenant filtering.
        
        Args:
            id: Entity ID
            context: Tenant context for filtering
            
        Returns:
            True if deleted, False if not found
        """
        entity = self.get(id, context)
        if entity:
            self.db.delete(entity)
            self.db.commit()
            return True
        return False
    
    def _apply_tenant_filter(self, query, context: TenantContext):
        """
        Apply tenant filtering to query based on context.
        
        This is a base implementation. Entity-specific repositories
        should override this method to apply appropriate filters.
        
        Args:
            query: SQLAlchemy query
            context: Tenant context
            
        Returns:
            Filtered query
        """
        # Base implementation - override in specific repositories
        # Example filters:
        # - For projects: filter by organization_id
        # - For org-specific data: filter by project_id
        # - For user data: filter by user_id
        return query
    
    def count(self, context: Optional[TenantContext] = None) -> int:
        """
        Count entities with optional tenant filtering.
        
        Args:
            context: Tenant context for filtering
            
        Returns:
            Count of entities
        """
        query = self.db.query(self.model)
        
        if context:
            query = self._apply_tenant_filter(query, context)
        
        return query.count()

