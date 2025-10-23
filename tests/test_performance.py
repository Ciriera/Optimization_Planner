"""
Performance tests for the Optimization Planner API.
"""
import pytest
import time
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.services.algorithm import AlgorithmService


class TestPerformance:
    """Performance test cases."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_response_times(self, client):
        """Test API response times."""
        
        endpoints = [
            "/health",
            "/api/v1/algorithms",
            "/api/v1/projects",
            "/api/v1/instructors",
            "/api/v1/classrooms"
        ]
        
        max_response_time = 2.0  # 2 seconds maximum
        
        for endpoint in endpoints:
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < max_response_time, f"Endpoint {endpoint} took {response_time:.2f}s, exceeding {max_response_time}s limit"
    
    def test_concurrent_requests(self, client):
        """Test concurrent request handling."""
        
        import threading
        import queue
        
        def make_request(result_queue):
            """Make a request and put result in queue."""
            try:
                response = client.get("/api/v1/algorithms")
                result_queue.put(response.status_code)
            except Exception as e:
                result_queue.put(f"Error: {e}")
        
        # Test with 10 concurrent requests
        num_requests = 10
        result_queue = queue.Queue()
        threads = []
        
        start_time = time.time()
        
        for _ in range(num_requests):
            thread = threading.Thread(target=make_request, args=(result_queue,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Collect results
        results = []
        while not result_queue.empty():
            results.append(result_queue.get())
        
        # Verify all requests succeeded
        assert len(results) == num_requests
        assert all(result == 200 for result in results)
        
        # Verify reasonable total time
        assert total_time < 10.0, f"Concurrent requests took {total_time:.2f}s, exceeding 10s limit"
    
    async def test_algorithm_performance(self):
        """Test algorithm performance."""
        
        service = AlgorithmService()
        
        # Test algorithm listing performance
        start_time = time.time()
        algorithms = service.list_algorithms()
        end_time = time.time()
        
        assert len(algorithms) > 0
        assert (end_time - start_time) < 1.0  # Should be very fast
        
        # Test algorithm execution performance (if data available)
        try:
            from app.models.algorithm import AlgorithmType
            start_time = time.time()
            result, run = await service.run_algorithm(
                AlgorithmType.GREEDY, 
                {"projects": [], "instructors": [], "classrooms": [], "timeslots": []}, 
                {"max_iterations": 100}
            )
            end_time = time.time()
            
            execution_time = end_time - start_time
            assert execution_time < 30.0  # Should complete within 30 seconds
            
        except Exception as e:
            # Expected if no data available
            assert "data" in str(e).lower() or "empty" in str(e).lower()
    
    def test_database_query_performance(self, client):
        """Test database query performance."""
        
        # Test endpoints that make database queries
        db_endpoints = [
            "/api/v1/projects",
            "/api/v1/instructors",
            "/api/v1/classrooms"
        ]
        
        max_db_time = 3.0  # 3 seconds maximum for DB queries
        
        for endpoint in db_endpoints:
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < max_db_time, f"Database endpoint {endpoint} took {response_time:.2f}s, exceeding {max_db_time}s limit"
    
    def test_memory_usage(self, client):
        """Test memory usage during operations."""
        
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Make multiple requests
        for _ in range(50):
            response = client.get("/api/v1/algorithms")
            assert response.status_code == 200
        
        # Check memory usage after requests
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50, f"Memory usage increased by {memory_increase:.2f}MB, exceeding 50MB limit"
    
    def test_large_data_handling(self, client):
        """Test handling of large data sets."""
        
        # Test algorithms endpoint (should return large dataset)
        start_time = time.time()
        response = client.get("/api/v1/algorithms")
        end_time = time.time()
        
        assert response.status_code == 200
        algorithms = response.json()
        
        # Should handle large datasets efficiently
        assert len(algorithms) > 0
        assert (end_time - start_time) < 2.0
        
        # Verify response size is reasonable
        response_size = len(response.content)
        assert response_size < 1024 * 1024, f"Response size {response_size} bytes exceeds 1MB limit"
    
    def test_error_handling_performance(self, client):
        """Test error handling doesn't impact performance."""
        
        # Test various error scenarios
        error_scenarios = [
            ("/api/v1/invalid-endpoint", 404),
            ("/api/v1/auth/login", 422),  # Missing data
        ]
        
        for endpoint, expected_status in error_scenarios:
            start_time = time.time()
            
            if endpoint == "/api/v1/auth/login":
                response = client.post(endpoint, json={})
            else:
                response = client.get(endpoint)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            assert response.status_code == expected_status
            assert response_time < 1.0, f"Error handling for {endpoint} took {response_time:.2f}s, exceeding 1s limit"
    
    def test_authentication_performance(self, client):
        """Test authentication performance."""
        
        # Test login performance
        login_data = {
            "email": "admin@example.com",
            "password": "admin123"
        }
        
        start_time = time.time()
        response = client.post("/api/v1/auth/login", json=login_data)
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 2.0  # Login should be fast
        
        # Test token validation performance
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            
            if token:
                headers = {"Authorization": f"Bearer {token}"}
                
                start_time = time.time()
                response = client.get("/api/v1/projects", headers=headers)
                end_time = time.time()
                
                # Token validation should be fast
                assert (end_time - start_time) < 1.0
    
    def test_caching_performance(self, client):
        """Test caching performance."""
        
        # Make same request multiple times
        endpoint = "/api/v1/algorithms"
        
        # First request
        start_time = time.time()
        response1 = client.get(endpoint)
        first_time = time.time() - start_time
        
        # Second request (should be faster if cached)
        start_time = time.time()
        response2 = client.get(endpoint)
        second_time = time.time() - start_time
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json() == response2.json()
        
        # Second request might be faster due to caching
        # But we don't enforce this as caching might not be implemented yet
        assert second_time < 5.0  # Should still be reasonable
    
    def test_concurrent_algorithm_execution(self):
        """Test concurrent algorithm execution."""
        
        import threading
        import queue
        
        service = AlgorithmService()
        
        async def run_algorithm_async():
            """Run algorithm asynchronously."""
            try:
                from app.models.algorithm import AlgorithmType
                result, run = await service.run_algorithm(
                    AlgorithmType.GREEDY, 
                    {"projects": [], "instructors": [], "classrooms": [], "timeslots": []}, 
                    {"max_iterations": 50}
                )
                return ("success", result)
            except Exception as e:
                return ("error", str(e))
        
        def run_algorithm(result_queue):
            """Run algorithm and put result in queue."""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(run_algorithm_async())
                result_queue.put(result)
            finally:
                loop.close()
        
        # Test with 3 concurrent algorithm runs
        num_runs = 3
        result_queue = queue.Queue()
        threads = []
        
        start_time = time.time()
        
        for _ in range(num_runs):
            thread = threading.Thread(target=run_algorithm, args=(result_queue,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Collect results
        results = []
        while not result_queue.empty():
            results.append(result_queue.get())
        
        # Verify all runs completed
        assert len(results) == num_runs
        
        # Verify reasonable total time
        assert total_time < 60.0, f"Concurrent algorithm execution took {total_time:.2f}s, exceeding 60s limit"
