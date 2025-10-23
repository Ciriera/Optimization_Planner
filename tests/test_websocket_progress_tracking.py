"""
Test suite for WebSocket real-time progress tracking
Proje açıklamasına göre: Real-time progress tracking sistemi testleri
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.api.v1.endpoints.websocket import (
    ConnectionManager,
    update_algorithm_progress,
    complete_algorithm,
    fail_algorithm,
    track_algorithm_progress
)


class TestWebSocketProgressTracking:
    """Test cases for WebSocket progress tracking"""
    
    @pytest.fixture
    def connection_manager(self):
        """ConnectionManager instance"""
        return ConnectionManager()
    
    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket connection"""
        websocket = Mock()
        websocket.client_state = Mock()
        websocket.client_state.CONNECTED = "CONNECTED"
        websocket.client_state = "CONNECTED"
        websocket.send_text = AsyncMock()
        return websocket
    
    @pytest.mark.asyncio
    async def test_connection_manager_connect(self, connection_manager, mock_websocket):
        """Test WebSocket connection"""
        user_id = 1
        
        await connection_manager.connect(mock_websocket, user_id)
        
        assert user_id in connection_manager.active_connections
        assert connection_manager.active_connections[user_id] == mock_websocket
        mock_websocket.accept.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connection_manager_disconnect(self, connection_manager, mock_websocket):
        """Test WebSocket disconnection"""
        user_id = 1
        
        # Connect first
        await connection_manager.connect(mock_websocket, user_id)
        assert user_id in connection_manager.active_connections
        
        # Disconnect
        connection_manager.disconnect(user_id)
        
        assert user_id not in connection_manager.active_connections
        assert user_id not in connection_manager.algorithm_progress
    
    @pytest.mark.asyncio
    async def test_send_personal_message(self, connection_manager, mock_websocket):
        """Test sending personal message"""
        user_id = 1
        message = "Test message"
        
        # Connect first
        await connection_manager.connect(mock_websocket, user_id)
        
        # Send message
        await connection_manager.send_personal_message(message, user_id)
        
        mock_websocket.send_text.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_send_personal_message_disconnected_user(self, connection_manager):
        """Test sending message to disconnected user"""
        user_id = 1
        message = "Test message"
        
        # Try to send message without connecting
        await connection_manager.send_personal_message(message, user_id)
        
        # Should not raise exception
        assert user_id not in connection_manager.active_connections
    
    @pytest.mark.asyncio
    async def test_send_algorithm_progress(self, connection_manager, mock_websocket):
        """Test sending algorithm progress"""
        user_id = 1
        progress_data = {
            "algorithm_id": 123,
            "progress": 50.0,
            "status": "running",
            "message": "Processing...",
            "details": {"iteration": 5, "total_iterations": 10}
        }
        
        # Connect first
        await connection_manager.connect(mock_websocket, user_id)
        
        # Send progress
        await connection_manager.send_algorithm_progress(user_id, progress_data)
        
        # Check that progress is stored
        assert connection_manager.algorithm_progress[user_id] == progress_data
        
        # Check that message was sent
        mock_websocket.send_text.assert_called_once()
        sent_message = mock_websocket.send_text.call_args[0][0]
        parsed_message = json.loads(sent_message)
        
        assert parsed_message["type"] == "algorithm_progress"
        assert parsed_message["data"] == progress_data
    
    @pytest.mark.asyncio
    async def test_send_algorithm_complete(self, connection_manager, mock_websocket):
        """Test sending algorithm completion"""
        user_id = 1
        result_data = {
            "algorithm_id": 123,
            "status": "completed",
            "progress": 100,
            "result": {"score": 85.5, "assignments": []},
            "timestamp": 1234567890.0
        }
        
        # Connect first
        await connection_manager.connect(mock_websocket, user_id)
        
        # Send completion
        await connection_manager.send_algorithm_complete(user_id, result_data)
        
        # Check that message was sent
        mock_websocket.send_text.assert_called_once()
        sent_message = mock_websocket.send_text.call_args[0][0]
        parsed_message = json.loads(sent_message)
        
        assert parsed_message["type"] == "algorithm_complete"
        assert parsed_message["data"] == result_data
    
    @pytest.mark.asyncio
    async def test_send_algorithm_error(self, connection_manager, mock_websocket):
        """Test sending algorithm error"""
        user_id = 1
        error_data = {
            "algorithm_id": 123,
            "status": "failed",
            "progress": 0,
            "error": "Constraint violation",
            "details": {"constraint": "classroom_capacity"},
            "timestamp": 1234567890.0
        }
        
        # Connect first
        await connection_manager.connect(mock_websocket, user_id)
        
        # Send error
        await connection_manager.send_algorithm_error(user_id, error_data)
        
        # Check that message was sent
        mock_websocket.send_text.assert_called_once()
        sent_message = mock_websocket.send_text.call_args[0][0]
        parsed_message = json.loads(sent_message)
        
        assert parsed_message["type"] == "algorithm_error"
        assert parsed_message["data"] == error_data
    
    @pytest.mark.asyncio
    async def test_update_algorithm_progress_utility(self, connection_manager, mock_websocket):
        """Test update_algorithm_progress utility function"""
        user_id = 1
        algorithm_id = 123
        progress = 75.0
        status = "running"
        message = "Optimizing..."
        details = {"iteration": 7, "total_iterations": 10}
        
        # Connect first
        await connection_manager.connect(mock_websocket, user_id)
        
        # Update progress
        await update_algorithm_progress(user_id, algorithm_id, progress, status, message, details)
        
        # Check that progress was stored and sent
        stored_progress = connection_manager.algorithm_progress[user_id]
        assert stored_progress["algorithm_id"] == algorithm_id
        assert stored_progress["progress"] == progress
        assert stored_progress["status"] == status
        assert stored_progress["message"] == message
        assert stored_progress["details"] == details
    
    @pytest.mark.asyncio
    async def test_complete_algorithm_utility(self, connection_manager, mock_websocket):
        """Test complete_algorithm utility function"""
        user_id = 1
        algorithm_id = 123
        result = {"score": 92.5, "assignments": [{"project_id": 1, "classroom_id": 1}]}
        
        # Connect first
        await connection_manager.connect(mock_websocket, user_id)
        
        # Complete algorithm
        await complete_algorithm(user_id, algorithm_id, result)
        
        # Check that completion message was sent
        mock_websocket.send_text.assert_called_once()
        sent_message = mock_websocket.send_text.call_args[0][0]
        parsed_message = json.loads(sent_message)
        
        assert parsed_message["type"] == "algorithm_complete"
        assert parsed_message["data"]["algorithm_id"] == algorithm_id
        assert parsed_message["data"]["status"] == "completed"
        assert parsed_message["data"]["progress"] == 100
        assert parsed_message["data"]["result"] == result
    
    @pytest.mark.asyncio
    async def test_fail_algorithm_utility(self, connection_manager, mock_websocket):
        """Test fail_algorithm utility function"""
        user_id = 1
        algorithm_id = 123
        error = "Infeasible solution"
        details = {"constraint_violations": ["classroom_capacity", "time_conflict"]}
        
        # Connect first
        await connection_manager.connect(mock_websocket, user_id)
        
        # Fail algorithm
        await fail_algorithm(user_id, algorithm_id, error, details)
        
        # Check that error message was sent
        mock_websocket.send_text.assert_called_once()
        sent_message = mock_websocket.send_text.call_args[0][0]
        parsed_message = json.loads(sent_message)
        
        assert parsed_message["type"] == "algorithm_error"
        assert parsed_message["data"]["algorithm_id"] == algorithm_id
        assert parsed_message["data"]["status"] == "failed"
        assert parsed_message["data"]["progress"] == 0
        assert parsed_message["data"]["error"] == error
        assert parsed_message["data"]["details"] == details
    
    @pytest.mark.asyncio
    async def test_track_algorithm_progress_decorator(self, connection_manager, mock_websocket):
        """Test track_algorithm_progress decorator"""
        user_id = 1
        algorithm_id = 123
        
        # Connect first
        await connection_manager.connect(mock_websocket, user_id)
        
        # Mock algorithm function
        async def mock_algorithm():
            await asyncio.sleep(0.1)  # Simulate work
            return {"score": 85.0, "assignments": []}
        
        # Apply decorator
        decorated_algorithm = track_algorithm_progress(algorithm_id, user_id)(mock_algorithm)
        
        # Run decorated algorithm
        result = await decorated_algorithm()
        
        # Check that progress was tracked and algorithm completed
        assert result == {"score": 85.0, "assignments": []}
        
        # Check that messages were sent (start, progress, complete)
        assert mock_websocket.send_text.call_count >= 2  # At least start and complete
    
    @pytest.mark.asyncio
    async def test_track_algorithm_progress_decorator_with_error(self, connection_manager, mock_websocket):
        """Test track_algorithm_progress decorator with error"""
        user_id = 1
        algorithm_id = 123
        
        # Connect first
        await connection_manager.connect(mock_websocket, user_id)
        
        # Mock algorithm function that raises error
        async def mock_algorithm_with_error():
            await asyncio.sleep(0.1)  # Simulate work
            raise ValueError("Test error")
        
        # Apply decorator
        decorated_algorithm = track_algorithm_progress(algorithm_id, user_id)(mock_algorithm_with_error)
        
        # Run decorated algorithm and expect error
        with pytest.raises(ValueError, match="Test error"):
            await decorated_algorithm()
        
        # Check that error message was sent
        mock_websocket.send_text.assert_called()
        sent_messages = [call[0][0] for call in mock_websocket.send_text.call_args_list]
        
        # Should have error message
        error_message_found = False
        for message in sent_messages:
            parsed_message = json.loads(message)
            if parsed_message["type"] == "algorithm_error":
                error_message_found = True
                assert parsed_message["data"]["error"] == "Test error"
                break
        
        assert error_message_found
    
    def test_websocket_message_parsing(self):
        """Test WebSocket message parsing"""
        # Test valid message
        valid_message = json.dumps({
            "type": "algorithm_progress",
            "data": {
                "algorithm_id": 123,
                "progress": 50.0,
                "status": "running"
            }
        })
        
        parsed = json.loads(valid_message)
        assert parsed["type"] == "algorithm_progress"
        assert parsed["data"]["algorithm_id"] == 123
        
        # Test invalid message
        invalid_message = "invalid json"
        with pytest.raises(json.JSONDecodeError):
            json.loads(invalid_message)
    
    @pytest.mark.asyncio
    async def test_multiple_users_progress_tracking(self, connection_manager):
        """Test progress tracking for multiple users"""
        user1_websocket = Mock()
        user1_websocket.client_state = "CONNECTED"
        user1_websocket.send_text = AsyncMock()
        
        user2_websocket = Mock()
        user2_websocket.client_state = "CONNECTED"
        user2_websocket.send_text = AsyncMock()
        
        # Connect both users
        await connection_manager.connect(user1_websocket, 1)
        await connection_manager.connect(user2_websocket, 2)
        
        # Send progress to user 1
        progress_data_1 = {
            "algorithm_id": 123,
            "progress": 50.0,
            "status": "running"
        }
        await connection_manager.send_algorithm_progress(1, progress_data_1)
        
        # Send different progress to user 2
        progress_data_2 = {
            "algorithm_id": 456,
            "progress": 75.0,
            "status": "running"
        }
        await connection_manager.send_algorithm_progress(2, progress_data_2)
        
        # Check that each user received their own progress
        assert connection_manager.algorithm_progress[1] == progress_data_1
        assert connection_manager.algorithm_progress[2] == progress_data_2
        
        # Check that messages were sent to correct users
        user1_websocket.send_text.assert_called_once()
        user2_websocket.send_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connection_cleanup_on_error(self, connection_manager, mock_websocket):
        """Test connection cleanup when WebSocket error occurs"""
        user_id = 1
        
        # Connect first
        await connection_manager.connect(mock_websocket, user_id)
        assert user_id in connection_manager.active_connections
        
        # Simulate WebSocket error
        mock_websocket.send_text.side_effect = Exception("Connection error")
        
        # Try to send message
        await connection_manager.send_personal_message("test", user_id)
        
        # Connection should be cleaned up
        assert user_id not in connection_manager.active_connections


if __name__ == "__main__":
    pytest.main([__file__])
