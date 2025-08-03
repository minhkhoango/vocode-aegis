// frontend/src/App.jsx
import React, { useState, useEffect, useCallback, useRef } from 'react';
import './App.css'; // Ensure this path is correct

import LiveStatusIndicator from './components/LiveStatusIndicator';
import ErrorSummaryTable from './components/ErrorSummaryTable';
import LogViewerModal from './components/LogViewerModal';

// Dynamically determine WebSocket URL based on current host and protocol
const getWebSocketUrl = () => {
  try {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Use the current host for both local and tunnel access
    const host = window.location.host;
    return `${protocol}//${host}/ws`;
  } catch (error) {
    console.error('Error constructing WebSocket URL:', error);
    // Fallback to localhost if dynamic construction fails
    return 'ws://localhost:3001/ws';
  }
};

// Get API URL from environment variable or construct dynamically
const getApiUrl = () => {
  // If we have an environment variable and it's not empty, use it
  if (process.env.REACT_APP_API_URL && process.env.REACT_APP_API_URL.trim() !== '') {
    return process.env.REACT_APP_API_URL;
  }
  
  // Otherwise, use relative URLs which will work with both local and tunnel access
  return '';
};

function App() {
  const [metrics, setMetrics] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const [ws, setWs] = useState(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 10;
  const baseReconnectDelay = 1000; // 1 second
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedErrorType, setSelectedErrorType] = useState('');
  const [modalLogs, setModalLogs] = useState([]);

  // Get dynamic URLs
  const WEBSOCKET_URL = getWebSocketUrl();
  const API_URL = getApiUrl();

  // Exponential backoff reconnection strategy
  const scheduleReconnect = useCallback(() => {
    if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
      console.error('Max reconnection attempts reached. Stopping reconnection.');
      setConnectionStatus('error');
      return;
    }

    const delay = Math.min(baseReconnectDelay * Math.pow(2, reconnectAttemptsRef.current), 30000); // Max 30 seconds
    console.log(`Scheduling reconnection attempt ${reconnectAttemptsRef.current + 1} in ${delay}ms`);
    
    reconnectTimeoutRef.current = setTimeout(() => {
      setConnectionStatus('connecting');
      connectWebSocket();
    }, delay);
  }, []);

  // Use useCallback for memoized function to prevent unnecessary re-renders
  const connectWebSocket = useCallback(() => {
    console.log(`Attempting to connect to WebSocket at ${WEBSOCKET_URL}...`);
    
    // Clear any existing reconnection timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    const websocket = new WebSocket(WEBSOCKET_URL);

    websocket.onopen = () => {
      console.log('WebSocket connection opened successfully.');
      setConnectionStatus('connected');
      setWs(websocket);
      reconnectAttemptsRef.current = 0; // Reset reconnection attempts on successful connection
    };

    websocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('Received WebSocket data:', data); // Debug log
        if (data.financial_impact) {
          console.log('Financial metrics received:', data.financial_impact); // Debug financial metrics
        }
        setMetrics(data);
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e, event.data);
      }
    };

    websocket.onclose = (event) => {
      console.warn('WebSocket connection closed:', event.code, event.reason);
      setConnectionStatus('disconnected');
      setWs(null); // Clear the WebSocket instance
      
      // Only attempt reconnection if it wasn't a clean close
      if (event.code !== 1000) { // 1000 = Normal closure
        reconnectAttemptsRef.current += 1;
        scheduleReconnect();
      }
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnectionStatus('error');
      // onError usually precedes onclose, so onclose will handle reconnection
    };

    return websocket; // Return the websocket instance for cleanup
  }, [WEBSOCKET_URL, scheduleReconnect]); // Include WEBSOCKET_URL and scheduleReconnect in dependencies

  useEffect(() => {
    const websocket = connectWebSocket();

    // Cleanup function for useEffect
    return () => {
      if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.close();
      }
      // Clear any pending reconnection timeout
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };
  }, [connectWebSocket]); // Re-run effect if connectWebSocket changes (it won't in this case due to useCallback)

  const handleErrorDrillDown = async (errorType) => {
    setSelectedErrorType(errorType);
    try {
      console.log(`Fetching logs for error type: ${errorType}`); // Log the error type
      const response = await fetch(`${API_URL}/logs/${errorType}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      console.log('Received data from /logs endpoint:', data); // Log the received data
      setModalLogs(data.errors || []);
      setIsModalOpen(true); // Open the modal
    } catch (error) {
      console.error('Failed to fetch logs for modal:', error);
      setModalLogs([]); // Clear logs on error
      setIsModalOpen(true); // Still open modal to show error message or "no logs"
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedErrorType('');
    setModalLogs([]);
  };

  if (!metrics) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading dashboard... ({connectionStatus})</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Vocode Analytics Dashboard</h1>
        <div className={`connection-status ${connectionStatus}`}>
          {connectionStatus.toUpperCase()}
        </div>
      </header>

      <div className="metrics-grid">
        <LiveStatusIndicator
          status={metrics.live_status}
          activeCalls={metrics.active_calls.count}
          financialImpact={metrics.financial_impact}
          metrics={metrics}
        />
        <ErrorSummaryTable
          errors={metrics.error_summary}
          onDrillDown={handleErrorDrillDown}
        />
      </div>
      <LogViewerModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        errorType={selectedErrorType}
        logs={modalLogs}
      />
    </div>
  );
}

export default App;