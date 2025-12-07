/**
 * WebSocket service for real-time algorithm progress tracking
 * Proje açıklamasına göre: Real-time progress tracking sistemi
 */

export interface ProgressUpdate {
  type: 'algorithm_progress' | 'algorithm_complete' | 'algorithm_error' | 'pong' | 'subscription_confirmed' | 'error';
  data?: any;
  message?: string;
  timestamp?: number;
}

export interface AlgorithmProgress {
  algorithm_id: number;
  progress: number;
  status: 'starting' | 'running' | 'completed' | 'failed' | 'paused';
  message: string;
  details: Record<string, any>;
  timestamp: number;
}

export interface AlgorithmResult {
  algorithm_id: number;
  status: 'completed';
  progress: 100;
  result: any;
  timestamp: number;
}

export interface AlgorithmError {
  algorithm_id: number;
  status: 'failed';
  progress: 0;
  error: string;
  details: Record<string, any>;
  timestamp: number;
}

export type ProgressCallback = (progress: AlgorithmProgress) => void;
export type CompleteCallback = (result: AlgorithmResult) => void;
export type ErrorCallback = (error: AlgorithmError) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private userId: number | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 3000;
  private isConnecting = false;
  private isManualDisconnect = false;
  
  // Event callbacks
  private progressCallbacks: ProgressCallback[] = [];
  private completeCallbacks: CompleteCallback[] = [];
  private errorCallbacks: ErrorCallback[] = [];
  
  // Ping interval for keep-alive
  private pingInterval: NodeJS.Timeout | null = null;
  private pingIntervalMs = 30000; // 30 seconds

  constructor() {
    // Auto-reconnect on window focus
    window.addEventListener('focus', () => {
      if (!this.isConnected() && !this.isConnecting && !this.isManualDisconnect) {
        this.reconnect();
      }
    });
  }

  connect(userId: number): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.isConnected()) {
        console.log('WebSocket already connected');
        resolve();
        return;
      }

      if (this.isConnecting) {
        console.log('WebSocket connection already in progress');
        reject(new Error('Connection already in progress'));
        return;
      }

      this.isConnecting = true;
      this.isManualDisconnect = false;
      this.userId = userId;
      
      console.log(`Attempting to connect WebSocket for user ${userId}`);

      try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        // Development modunda backend portunu kullan (localhost kullan çünkü 127.0.0.1 bazı tarayıcılarda sorun yaratabilir)
        const host = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
          ? 'localhost:8000' 
          : window.location.host;
        const wsUrl = `${protocol}//${host}/ws/${userId}`;

        console.log(`🔗 Creating WebSocket connection to: ${wsUrl}`);
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('✅ WebSocket connected successfully');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.startPingInterval();
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data);
        };

        this.ws.onclose = (event) => {
          console.log(`❌ WebSocket disconnected - Code: ${event.code}, Reason: ${event.reason}`);
          this.isConnecting = false;
          this.stopPingInterval();
          
          // Normal closure (1000) veya manual disconnect değilse reconnect dene
          if (!this.isManualDisconnect && event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            console.log(`🔄 Attempting to reconnect... (${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);
            this.reconnect();
          } else if (event.code === 1000) {
            console.log('✅ WebSocket closed normally');
          } else {
            console.log('❌ WebSocket connection lost');
          }
        };

        this.ws.onerror = (error) => {
          console.error('❌ WebSocket error:', error);
          this.isConnecting = false;
          // Hata durumunda da resolve et, böylece frontend donmaz
          reject(new Error('WebSocket connection failed'));
        };

      } catch (error) {
        console.error('❌ WebSocket connection failed:', error);
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  disconnect(): void {
    this.isManualDisconnect = true;
    this.stopPingInterval();
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  private reconnect(): void {
    if (this.isConnecting || this.isManualDisconnect || !this.userId) {
      return;
    }

    this.reconnectAttempts++;
    console.log(`🔄 Attempting to reconnect WebSocket (attempt ${this.reconnectAttempts})`);

    setTimeout(() => {
      if (!this.isConnected() && !this.isConnecting) {
        this.connect(this.userId!).catch((error) => {
          console.error('❌ WebSocket reconnection failed:', error);
        });
      }
    }, this.reconnectInterval * this.reconnectAttempts);
  }

  private startPingInterval(): void {
    this.stopPingInterval();
    this.pingInterval = setInterval(() => {
      if (this.isConnected()) {
        this.ping();
      }
    }, this.pingIntervalMs);
  }

  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  private ping(): void {
    if (this.isConnected()) {
      this.send({
        type: 'ping',
        timestamp: Date.now()
      });
    }
  }

  private handleMessage(data: string): void {
    try {
      const message: ProgressUpdate = JSON.parse(data);
      
      switch (message.type) {
        case 'algorithm_progress':
          this.progressCallbacks.forEach(callback => {
            if (message.data) {
              callback(message.data);
            }
          });
          break;
          
        case 'algorithm_complete':
          this.completeCallbacks.forEach(callback => {
            if (message.data) {
              callback(message.data);
            }
          });
          break;
          
        case 'algorithm_error':
          this.errorCallbacks.forEach(callback => {
            if (message.data) {
              callback(message.data);
            }
          });
          break;
          
        case 'pong':
          // Keep-alive response
          break;
          
        case 'subscription_confirmed':
          console.log('Algorithm subscription confirmed:', message.data);
          break;
          
        case 'error':
          console.error('WebSocket server error:', message.message);
          break;
          
        default:
          console.warn('Unknown WebSocket message type:', message.type);
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  }

  private send(message: any): void {
    if (this.isConnected()) {
      this.ws!.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, cannot send message:', message);
    }
  }

  // Public methods
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  subscribeToAlgorithm(algorithmId: number): void {
    this.send({
      type: 'subscribe_algorithm',
      algorithm_id: algorithmId
    });
  }

  getCurrentProgress(): void {
    this.send({
      type: 'get_progress'
    });
  }

  // Event subscription methods
  onProgress(callback: ProgressCallback): () => void {
    this.progressCallbacks.push(callback);
    return () => {
      const index = this.progressCallbacks.indexOf(callback);
      if (index > -1) {
        this.progressCallbacks.splice(index, 1);
      }
    };
  }

  onComplete(callback: CompleteCallback): () => void {
    this.completeCallbacks.push(callback);
    return () => {
      const index = this.completeCallbacks.indexOf(callback);
      if (index > -1) {
        this.completeCallbacks.splice(index, 1);
      }
    };
  }

  onError(callback: ErrorCallback): () => void {
    this.errorCallbacks.push(callback);
    return () => {
      const index = this.errorCallbacks.indexOf(callback);
      if (index > -1) {
        this.errorCallbacks.splice(index, 1);
      }
    };
  }

  // Utility methods
  getConnectionStatus(): 'connected' | 'connecting' | 'disconnected' {
    if (this.isConnecting) return 'connecting';
    if (this.isConnected()) return 'connected';
    return 'disconnected';
  }

  getUserId(): number | null {
    return this.userId;
  }
}

// Singleton instance
export const websocketService = new WebSocketService();
export default websocketService;
