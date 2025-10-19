"""User service for user management operations."""

from typing import Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.dtos.auth_dto import SignupRequest, UserResponse
from app.dtos.user_dto import UserUpdate


class UserService:
    """Service for user operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
    
    def create_user(self, signup_data: SignupRequest) -> User:
        """
        Create a new user account.
        
        Args:
            signup_data: User signup information
            
        Returns:
            Created user
            
        Raises:
            HTTPException: 400 if email already exists
        """
        # Check if email already exists
        if self.user_repo.email_exists(signup_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = AuthService.hash_password(signup_data.password)
        
        # Create user
        user = User(
            email=signup_data.email,
            password_hash=hashed_password,
            name=signup_data.name,
            is_active=True
        )
        
        return self.user_repo.create(user)
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user with email and password.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            User if authentication successful, None otherwise
        """
        user = self.user_repo.get_by_email(email)
        if not user:
            return None
        
        if not AuthService.verify_password(password, user.password_hash):
            return None
        
        if not user.is_active:
            return None
        
        return user
    
    def get_user(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User if found, None otherwise
        """
        return self.user_repo.get(user_id)
    
    def update_user(self, user: User, update_data: UserUpdate) -> User:
        """
        Update user profile.
        
        Args:
            user: User to update
            update_data: Update data
            
        Returns:
            Updated user
            
        Raises:
            HTTPException: 400 if email already taken
        """
        # Check if email is being changed and if it's already taken
        if update_data.email and update_data.email != user.email:
            if self.user_repo.email_exists(update_data.email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already taken"
                )
            user.email = update_data.email
        
        # Update name if provided
        if update_data.name:
            user.name = update_data.name
        
        return self.user_repo.update(user)

