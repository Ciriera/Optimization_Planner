/**
 * Hook for real-time algorithm progress tracking
 * Proje açıklamasına göre: Real-time progress tracking sistemi
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { websocketService, AlgorithmProgress, AlgorithmResult, AlgorithmError } from '../services/websocketService';

export interface UseAlgorithmProgressOptions {
  autoConnect?: boolean;
  userId?: number;
}

export interface UseAlgorithmProgressReturn {
  // Connection state
  isConnected: boolean;
  connectionStatus: 'connected' | 'connecting' | 'disconnected';
  
  // Algorithm progress state
  currentProgress: AlgorithmProgress | null;
  isRunning: boolean;
  progress: number;
  status: string;
  message: string;
  
  // Results
  lastResult: AlgorithmResult | null;
  lastError: AlgorithmError | null;
  
  // Actions
  connect: (userId: number) => Promise<void>;
  disconnect: () => void;
  subscribeToAlgorithm: (algorithmId: number) => void;
  getCurrentProgress: () => void;
  
  // Event handlers
  onProgress: (callback: (progress: AlgorithmProgress) => void) => () => void;
  onComplete: (callback: (result: AlgorithmResult) => void) => () => void;
  onError: (callback: (error: AlgorithmError) => void) => () => void;
}

export const useAlgorithmProgress = (options: UseAlgorithmProgressOptions = {}): UseAlgorithmProgressReturn => {
  const { autoConnect = true, userId } = options;
  
  // Connection state
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'connecting' | 'disconnected'>('disconnected');
  
  // Progress state
  const [currentProgress, setCurrentProgress] = useState<AlgorithmProgress | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('');
  const [message, setMessage] = useState('');
  
  // Results
  const [lastResult, setLastResult] = useState<AlgorithmResult | null>(null);
  const [lastError, setLastError] = useState<AlgorithmError | null>(null);
  
  // Refs for cleanup
  const progressUnsubscribe = useRef<(() => void) | null>(null);
  const completeUnsubscribe = useRef<(() => void) | null>(null);
  const errorUnsubscribe = useRef<(() => void) | null>(null);

  // Connection management
  const connect = useCallback(async (connectUserId: number) => {
    try {
      await websocketService.connect(connectUserId);
      setIsConnected(true);
      setConnectionStatus('connected');
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error);
      setIsConnected(false);
      setConnectionStatus('disconnected');
      throw error;
    }
  }, []);

  const disconnect = useCallback(() => {
    websocketService.disconnect();
    setIsConnected(false);
    setConnectionStatus('disconnected');
    setIsRunning(false);
    setProgress(0);
    setStatus('');
    setMessage('');
    setCurrentProgress(null);
  }, []);

  // Algorithm subscription
  const subscribeToAlgorithm = useCallback((algorithmId: number) => {
    if (isConnected) {
      websocketService.subscribeToAlgorithm(algorithmId);
    }
  }, [isConnected]);

  const getCurrentProgress = useCallback(() => {
    if (isConnected) {
      websocketService.getCurrentProgress();
    }
  }, [isConnected]);

  // Event handlers
  const onProgress = useCallback((callback: (progress: AlgorithmProgress) => void) => {
    const unsubscribe = websocketService.onProgress(callback);
    return unsubscribe;
  }, []);

  const onComplete = useCallback((callback: (result: AlgorithmResult) => void) => {
    const unsubscribe = websocketService.onComplete(callback);
    return unsubscribe;
  }, []);

  const onError = useCallback((callback: (error: AlgorithmError) => void) => {
    const unsubscribe = websocketService.onError(callback);
    return unsubscribe;
  }, []);

  // Auto-connect effect
  useEffect(() => {
    if (autoConnect && userId && !isConnected && connectionStatus === 'disconnected') {
      setConnectionStatus('connecting');
      connect(userId).catch((error) => {
        console.error('Auto-connect failed:', error);
        setConnectionStatus('disconnected');
      });
    }
  }, [autoConnect, userId, isConnected, connectionStatus, connect]);

  // WebSocket event subscription
  useEffect(() => {
    // Progress handler
    progressUnsubscribe.current = websocketService.onProgress((progressData) => {
      setCurrentProgress(progressData);
      setProgress(progressData.progress);
      setStatus(progressData.status);
      setMessage(progressData.message);
      setIsRunning(progressData.status === 'running' || progressData.status === 'starting');
    });

    // Complete handler
    completeUnsubscribe.current = websocketService.onComplete((resultData) => {
      setLastResult(resultData);
      setProgress(100);
      setStatus('completed');
      setMessage('Algorithm completed successfully');
      setIsRunning(false);
    });

    // Error handler
    errorUnsubscribe.current = websocketService.onError((errorData) => {
      setLastError(errorData);
      setProgress(0);
      setStatus('failed');
      setMessage(errorData.error);
      setIsRunning(false);
    });

    // Connection status monitoring
    const statusCheckInterval = setInterval(() => {
      const currentStatus = websocketService.getConnectionStatus();
      setConnectionStatus(currentStatus);
      setIsConnected(currentStatus === 'connected');
    }, 1000);

    // Cleanup
    return () => {
      if (progressUnsubscribe.current) {
        progressUnsubscribe.current();
      }
      if (completeUnsubscribe.current) {
        completeUnsubscribe.current();
      }
      if (errorUnsubscribe.current) {
        errorUnsubscribe.current();
      }
      clearInterval(statusCheckInterval);
    };
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    // Connection state
    isConnected,
    connectionStatus,
    
    // Progress state
    currentProgress,
    isRunning,
    progress,
    status,
    message,
    
    // Results
    lastResult,
    lastError,
    
    // Actions
    connect,
    disconnect,
    subscribeToAlgorithm,
    getCurrentProgress,
    
    // Event handlers
    onProgress,
    onComplete,
    onError,
  };
};

export default useAlgorithmProgress;
