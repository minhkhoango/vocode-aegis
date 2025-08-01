// frontend/src/App.jsx
import React, { useState, useEffect, useCallback, useRef } from 'react';
import './App.css'; // Ensure this path is correct

import LiveStatusIndicator from './components/LiveStatusIndicator';
import ActiveCallsCounter from './components/ActiveCallsCounter';
import ErrorSummaryTable from './components/ErrorSummaryTable';
import DemoControls from './components/DemoControls';

// Get WebSocket URL from environment variable injected by react-scripts (set in .env for frontend)
const WEBSOCKET_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:3001/ws';

function App() {
  const [metrics, setMetrics] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const [ws, setWs] = useState(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 10;
  const baseReconnectDelay = 1000; // 1 second

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
  }, [scheduleReconnect]); // Include scheduleReconnect in dependencies

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

  const handleErrorDrillDown = (errorType) => {
    // Open error logs in new window/modal
    // This URL will be handled by the FastAPI server directly, serving HTML
    window.open(`/logs/${errorType}/viewer`, '_blank', 'width=800,height=600,scrollbars=yes');
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
        <LiveStatusIndicator status={metrics.live_status} />
        <ActiveCallsCounter count={metrics.active_calls.count} />
        <ErrorSummaryTable
          errors={metrics.error_summary}
          onDrillDown={handleErrorDrillDown}
        />
        <DemoControls />
      </div>
    </div>
  );
}

export default App;