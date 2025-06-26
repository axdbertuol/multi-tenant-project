import pytest
from src.infrastructure.repositories.sqlalchemy_unit_of_work import SQLAlchemyUnitOfWork
from tests.factories.user_factory import UserFactory
from tests.factories.session_factory import UserSessionFactory


@pytest.mark.integration
class TestUnitOfWork:
    """Integration tests for Unit of Work pattern."""
    
    @pytest.fixture
    def unit_of_work(self, db_session):
        """Create UnitOfWork instance with test database session."""
        return SQLAlchemyUnitOfWork(db_session)
    
    @pytest.mark.asyncio
    async def test_unit_of_work_context_manager(self, unit_of_work):
        """Test Unit of Work as async context manager."""
        # Act & Assert
        async with unit_of_work as uow:
            assert uow is not None
            assert hasattr(uow, 'users')
            assert hasattr(uow, 'user_sessions')
    
    @pytest.mark.asyncio
    async def test_successful_transaction_commits(self, unit_of_work):
        """Test that successful operations are committed."""
        # Arrange
        user = UserFactory.create_user(email="commit@example.com")
        
        # Act
        async with unit_of_work as uow:
            created_user = await uow.users.create(user)
            # No exception raised, should commit
        
        # Assert - Verify data persisted
        async with unit_of_work as uow:
            retrieved_user = await uow.users.get_by_email("commit@example.com")
            assert retrieved_user is not None
            assert retrieved_user.id == created_user.id
    
    @pytest.mark.asyncio
    async def test_exception_causes_rollback(self, unit_of_work):
        """Test that exceptions cause rollback."""
        # Arrange
        user = UserFactory.create_user(email="rollback@example.com")
        
        # Act
        with pytest.raises(ValueError):
            async with unit_of_work as uow:
                await uow.users.create(user)
                # Simulate error after operation
                raise ValueError("Test error")
        
        # Assert - Verify data was rolled back
        async with unit_of_work as uow:
            retrieved_user = await uow.users.get_by_email("rollback@example.com")
            assert retrieved_user is None
    
    @pytest.mark.asyncio
    async def test_multiple_repository_operations(self, unit_of_work):
        """Test operations across multiple repositories in same transaction."""
        # Arrange
        user = UserFactory.create_user(email="multi@example.com")
        
        # Act
        async with unit_of_work as uow:
            # Create user
            created_user = await uow.users.create(user)
            
            # Create session for the user
            session = UserSessionFactory.create_session(
                user_id=created_user.id,
                session_token="multi_test_token"
            )
            created_session = await uow.user_sessions.create(session)
        
        # Assert - Both operations committed
        async with unit_of_work as uow:
            retrieved_user = await uow.users.get_by_email("multi@example.com")
            retrieved_session = await uow.user_sessions.get_by_session_token("multi_test_token")
            
            assert retrieved_user is not None
            assert retrieved_session is not None
            assert retrieved_session.user_id == retrieved_user.id
    
    @pytest.mark.asyncio
    async def test_rollback_affects_all_operations(self, unit_of_work):
        """Test that rollback affects all operations in transaction."""
        # Arrange
        user = UserFactory.create_user(email="rollback_all@example.com")
        
        # Act
        with pytest.raises(ValueError):
            async with unit_of_work as uow:
                # Create user
                created_user = await uow.users.create(user)
                
                # Create session
                session = UserSessionFactory.create_session(
                    user_id=created_user.id,
                    session_token="rollback_session_token"
                )
                await uow.user_sessions.create(session)
                
                # Cause rollback
                raise ValueError("Rollback test")
        
        # Assert - Neither operation persisted
        async with unit_of_work as uow:
            retrieved_user = await uow.users.get_by_email("rollback_all@example.com")
            retrieved_session = await uow.user_sessions.get_by_session_token("rollback_session_token")
            
            assert retrieved_user is None
            assert retrieved_session is None
    
    @pytest.mark.asyncio
    async def test_nested_unit_of_work_operations(self, unit_of_work):
        """Test multiple separate UoW operations."""
        # Arrange
        user1 = UserFactory.create_user(email="nested1@example.com")
        user2 = UserFactory.create_user(email="nested2@example.com")
        
        # Act - First transaction
        async with unit_of_work as uow:
            await uow.users.create(user1)
        
        # Act - Second transaction
        async with unit_of_work as uow:
            await uow.users.create(user2)
        
        # Assert - Both operations persisted independently
        async with unit_of_work as uow:
            retrieved_user1 = await uow.users.get_by_email("nested1@example.com")
            retrieved_user2 = await uow.users.get_by_email("nested2@example.com")
            
            assert retrieved_user1 is not None
            assert retrieved_user2 is not None
    
    @pytest.mark.asyncio
    async def test_unit_of_work_with_update_operations(self, unit_of_work):
        """Test UoW with update operations."""
        # Arrange - Create user first
        user = UserFactory.create_user(email="update@example.com", name="Original Name")
        
        async with unit_of_work as uow:
            created_user = await uow.users.create(user)
        
        # Act - Update user in new transaction
        async with unit_of_work as uow:
            retrieved_user = await uow.users.get_by_id(created_user.id)
            updated_user = retrieved_user.update_name("Updated Name")
            await uow.users.update(updated_user)
        
        # Assert - Update persisted
        async with unit_of_work as uow:
            final_user = await uow.users.get_by_id(created_user.id)
            assert final_user.name == "Updated Name"
    
    @pytest.mark.asyncio
    async def test_unit_of_work_with_delete_operations(self, unit_of_work):
        """Test UoW with delete operations."""
        # Arrange - Create user and session
        user = UserFactory.create_user(email="delete@example.com")
        
        async with unit_of_work as uow:
            created_user = await uow.users.create(user)
            session = UserSessionFactory.create_session(
                user_id=created_user.id,
                session_token="delete_test_token"
            )
            created_session = await uow.user_sessions.create(session)
        
        # Act - Delete session and user
        async with unit_of_work as uow:
            await uow.user_sessions.delete(created_session.id)
            await uow.users.delete(created_user.id)
        
        # Assert - Both deleted
        async with unit_of_work as uow:
            retrieved_user = await uow.users.get_by_id(created_user.id)
            retrieved_session = await uow.user_sessions.get_by_id(created_session.id)
            
            assert retrieved_user is None
            assert retrieved_session is None
    
    @pytest.mark.asyncio
    async def test_repository_isolation(self, unit_of_work):
        """Test that repositories are properly isolated."""
        # Act
        async with unit_of_work as uow:
            # Assert repositories are different instances
            assert uow.users is not uow.user_sessions
            
            # Assert repositories have access to same session
            assert uow.users.db is uow.user_sessions.db
    
    @pytest.mark.asyncio
    async def test_database_constraint_violations(self, unit_of_work):
        """Test that database constraint violations cause rollback."""
        # Arrange
        user1 = UserFactory.create_user(email="constraint@example.com")
        user2 = UserFactory.create_user(email="constraint@example.com")  # Same email
        
        # Act - First user succeeds
        async with unit_of_work as uow:
            await uow.users.create(user1)
        
        # Act - Second user fails due to unique constraint
        with pytest.raises(Exception):  # Database integrity error
            async with unit_of_work as uow:
                await uow.users.create(user2)
        
        # Assert - Only first user exists
        async with unit_of_work as uow:
            users = await uow.users.get_all()
            constraint_users = [u for u in users if u.email.value == "constraint@example.com"]
            assert len(constraint_users) == 1
            assert constraint_users[0].id == user1.id