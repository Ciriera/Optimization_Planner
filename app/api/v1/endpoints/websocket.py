"""
WebSocket endpoints for real-time algorithm progress tracking
"""

from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.websockets import WebSocketState
import json
import asyncio
import logging

from app.api import deps

router = APIRouter()
logger = logging.getLogger(__name__)

class ConnectionManager:
    """WebSocket bağlantı yöneticisi"""
    
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        self.algorithm_progress: Dict[int, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Kullanıcı bağlantısını kabul et"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected to WebSocket")
    
    def disconnect(self, user_id: int):
        """Kullanıcı bağlantısını kes"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.algorithm_progress:
            del self.algorithm_progress[user_id]
        logger.info(f"User {user_id} disconnected from WebSocket")
    
    async def send_personal_message(self, message: str, user_id: int):
        """Belirli kullanıcıya mesaj gönder"""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            if websocket.client_state == WebSocketState.CONNECTED:
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
                    self.disconnect(user_id)
    
    async def send_algorithm_progress(self, user_id: int, progress_data: Dict[str, Any]):
        """Algoritma ilerleme durumunu gönder"""
        self.algorithm_progress[user_id] = progress_data
        message = json.dumps({
            "type": "algorithm_progress",
            "data": progress_data
        })
        await self.send_personal_message(message, user_id)
    
    async def send_algorithm_complete(self, user_id: int, result_data: Dict[str, Any]):
        """Algoritma tamamlandığında sonucu gönder"""
        message = json.dumps({
            "type": "algorithm_complete",
            "data": result_data
        })
        await self.send_personal_message(message, user_id)
    
    async def send_algorithm_error(self, user_id: int, error_data: Dict[str, Any]):
        """Algoritma hatası durumunda hata mesajını gönder"""
        message = json.dumps({
            "type": "algorithm_error",
            "data": error_data
        })
        await self.send_personal_message(message, user_id)

# Global connection manager
manager = ConnectionManager()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """
    WebSocket endpoint for real-time algorithm progress tracking.
    Proje açıklamasına göre: Real-time progress tracking sistemi
    """
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "ping":
                    # Client ping, respond with pong
                    await manager.send_personal_message(
                        json.dumps({"type": "pong", "timestamp": message.get("timestamp")}),
                        user_id
                    )
                elif message_type == "get_progress":
                    # Client requests current progress
                    current_progress = manager.algorithm_progress.get(user_id, {})
                    await manager.send_algorithm_progress(user_id, current_progress)
                elif message_type == "subscribe_algorithm":
                    # Client subscribes to algorithm progress
                    algorithm_id = message.get("algorithm_id")
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "subscription_confirmed",
                            "algorithm_id": algorithm_id
                        }),
                        user_id
                    )
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from user {user_id}")
                await manager.send_personal_message(
                    json.dumps({"type": "error", "message": "Invalid JSON format"}),
                    user_id
                )
            except Exception as e:
                logger.error(f"Error processing message from user {user_id}: {e}")
                await manager.send_personal_message(
                    json.dumps({"type": "error", "message": "Internal server error"}),
                    user_id
                )
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(user_id)

# Utility functions for algorithm progress tracking
async def update_algorithm_progress(user_id: int, algorithm_id: int, progress: float, 
                                  status: str, message: str = "", details: Dict[str, Any] = None):
    """
    Algoritma ilerleme durumunu güncelle.
    
    Args:
        user_id: Kullanıcı ID'si
        algorithm_id: Algoritma çalıştırma ID'si
        progress: İlerleme yüzdesi (0-100)
        status: Durum (running, completed, failed, paused)
        message: Durum mesajı
        details: Ek detaylar
    """
    progress_data = {
        "algorithm_id": algorithm_id,
        "progress": progress,
        "status": status,
        "message": message,
        "details": details or {},
        "timestamp": asyncio.get_event_loop().time()
    }
    
    await manager.send_algorithm_progress(user_id, progress_data)

async def complete_algorithm(user_id: int, algorithm_id: int, result: Dict[str, Any]):
    """
    Algoritma tamamlandığında sonucu gönder.
    
    Args:
        user_id: Kullanıcı ID'si
        algorithm_id: Algoritma çalıştırma ID'si
        result: Algoritma sonucu
    """
    result_data = {
        "algorithm_id": algorithm_id,
        "status": "completed",
        "progress": 100,
        "result": result,
        "timestamp": asyncio.get_event_loop().time()
    }
    
    await manager.send_algorithm_complete(user_id, result_data)

async def fail_algorithm(user_id: int, algorithm_id: int, error: str, details: Dict[str, Any] = None):
    """
    Algoritma başarısız olduğunda hata mesajını gönder.
    
    Args:
        user_id: Kullanıcı ID'si
        algorithm_id: Algoritma çalıştırma ID'si
        error: Hata mesajı
        details: Ek hata detayları
    """
    error_data = {
        "algorithm_id": algorithm_id,
        "status": "failed",
        "progress": 0,
        "error": error,
        "details": details or {},
        "timestamp": asyncio.get_event_loop().time()
    }
    
    await manager.send_algorithm_error(user_id, error_data)

# Algorithm progress tracking decorator
def track_algorithm_progress(algorithm_id: int, user_id: int):
    """
    Algoritma çalıştırma sırasında progress tracking için decorator.
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                # Başlangıç durumu
                await update_algorithm_progress(
                    user_id, algorithm_id, 0, "starting", 
                    "Algorithm is starting..."
                )
                
                # Algoritma çalıştır
                result = await func(*args, **kwargs)
                
                # Tamamlandı durumu
                await complete_algorithm(user_id, algorithm_id, result)
                
                return result
                
            except Exception as e:
                # Hata durumu
                await fail_algorithm(user_id, algorithm_id, str(e))
                raise
        
        return wrapper
    return decorator
