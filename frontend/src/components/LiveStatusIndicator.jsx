// frontend/src/components/LiveStatusIndicator.jsx
import React, { useState, useEffect } from 'react';

const errorDefinitions = {
  low: { level: 'low', type: 'CONNECTION_TIMEOUT', message: 'A minor connection timeout occurred.' },
  medium: { level: 'medium', type: 'LLM_TIMEOUT', message: 'A medium severity LLM timeout occurred.' },
  high: { level: 'high', type: 'SYSTEM_CRASH', message: 'A high severity system crash occurred.' },
};

const errorInjectionSequence = [
  errorDefinitions.low,
  errorDefinitions.low,
  errorDefinitions.medium,
  errorDefinitions.high,
];

// Get API URL dynamically based on current location
const getApiUrl = () => {
  // If we have an environment variable and it's not empty, use it
  if (process.env.REACT_APP_API_URL && process.env.REACT_APP_API_URL.trim() !== '') {
    return process.env.REACT_APP_API_URL;
  }
  
  // Otherwise, use relative URLs which will work with both local and tunnel access
  return '';
};

const API_URL = getApiUrl();

function LiveStatusIndicator({ status, activeCalls, financialImpact, metrics }) {
  const [statusMessage, setStatusMessage] = useState('');
  const [showToast, setShowToast] = useState(false);
  const [isInjecting, setIsInjecting] = useState(false);
  const [pulseActiveCalls, setPulseActiveCalls] = useState(false);

  useEffect(() => {
    if (showToast) {
      const timer = setTimeout(() => {
        setShowToast(false);
      }, 3000); // Toast visible for 3 seconds
      return () => clearTimeout(timer);
    }
  }, [showToast]);

  useEffect(() => {
    if (activeCalls > 0) { // Only pulse when calls increase or are set
      setPulseActiveCalls(true);
      const timer = setTimeout(() => setPulseActiveCalls(false), 800); // Pulse for 0.8s
      return () => clearTimeout(timer);
    }
  }, [activeCalls]);

  const showSuccessToast = (message) => {
    setStatusMessage(message);
    setShowToast(true);
  };

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  const handleSimulateError = async () => {
    setIsInjecting(true);
    setStatusMessage('Starting error injection sequence...');

    for (const error of errorInjectionSequence) {
      await triggerDemoError(error.type, error.message, error.level, 1);
      
      if (error.level === 'critical' || error.level === 'high') {
          const currentActiveCalls = metrics.active_calls.count;
          const dropPercentage = error.level === 'critical' ? 0.7 : 0.3; // 70% for critical, 30% for high
          const newActiveCalls = Math.max(0, Math.round(currentActiveCalls * (1 - dropPercentage)));
          const delta = newActiveCalls - currentActiveCalls; // Calculate the change needed
          await triggerActiveCallsSimulation(delta);
          setStatusMessage(`Injected ${error.level} error. Active calls dropped to ${newActiveCalls}.`);
      }

      await sleep(2000); // Wait 2 seconds
    }

    setStatusMessage('Error injection sequence complete.');
    setIsInjecting(false);
  };

  const triggerDemoError = async (errorType, message, severity, count) => {
    setStatusMessage(`Injecting ${severity} error...`);
    try {
      const response = await fetch(`${API_URL}/demo/error?broadcast=true`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          error_type: errorType,
          message: message,
          severity: severity,
          count: count,
          conversation_id: 'demo-conv-12345'
        }),
      });
      const data = await response.json();
      if (response.ok) {
        showSuccessToast(data.message);
      } else {
        setStatusMessage(`Error: ${data.detail || data.message || 'Unknown backend error'}`);
      }
    } catch (error) {
      console.error('Frontend network error during demo injection:', error);
      setStatusMessage('Network error. Check browser console.');
    }
  };

  const triggerActiveCallsSimulation = async (delta) => {
    const action = delta >= 0 ? 'Adding' : 'Removing';
    setStatusMessage(`${action} ${Math.abs(delta)} active calls...`);
    try {
      const response = await fetch(`${API_URL}/demo/active_calls`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ delta: delta }),
      });
      const data = await response.json();
      if (response.ok) {
        showSuccessToast(data.message);
      } else {
        setStatusMessage(`Error: ${data.detail || data.message || 'Unknown backend error'}`);
      }
    } catch (error) {
      console.error('Frontend network error during active calls simulation:', error);
      setStatusMessage('Network error. Check browser console.');
    }
  };

  const handleResetAll = async () => {
    setStatusMessage('Resetting all demo states...');
    try {
      const response = await fetch(`${API_URL}/demo/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await response.json();
      if (response.ok) {
        showSuccessToast(data.message);
      } else {
        setStatusMessage(`Error: ${data.detail || data.message || 'Unknown backend error'}`);
      }
    } catch (error) {
      console.error('Frontend network error during reset:', error);
      setStatusMessage('Network error. Check browser console.');
    }
  };
  
  const getStatusColor = (statusValue) => {
    const colors = {
      'green': '#4CAF50',
      'yellow': '#FF9800',
      'red': '#F44336',
    };
    return colors[statusValue] || '#757575'; // Default to grey if unknown
  };

  return (
    <div className="metric-card live-status">
      <h3>System Status</h3>
      <div className="status-indicator">
        <div
          className="status-circle"
          style={{ backgroundColor: getStatusColor(status.status) }}
        />
        <span className="status-text">{status.status.toUpperCase()}</span>
      </div>
      {status.message && (
        <p className="status-message">{status.message}</p>
      )}
      <small>Last updated: {new Date(status.last_updated).toLocaleTimeString()}</small>
      
      <div className="active-calls-display">
          <h4>Active Calls</h4>
          <p className={`active-calls-count ${pulseActiveCalls ? 'pulse-effect' : ''} ${activeCalls > 0 ? 'glowing-effect' : ''}`}>{activeCalls}</p>
      </div>

      {financialImpact && (
          <div className="financial-metrics">
              <div className="financial-metric">
                  <span className="financial-label">Estimated Value / Min</span>
                  <span className="financial-value revenue">${financialImpact.estimated_revenue_per_min.toFixed(2)}</span>
              </div>
              <div className="financial-metric">
                  <span className="financial-label">Cost of Recent Errors</span>
                  <span className="financial-value cost">-${financialImpact.estimated_cost_of_recent_errors.toFixed(2)}</span>
              </div>
              <div className="financial-metric">
                  <span className="financial-label">Total ROI</span>
                  <span className={`financial-value ${financialImpact.total_roi >= 0 ? 'revenue' : 'cost'}`}>
                      ${financialImpact.total_roi.toFixed(2)}
                  </span>
              </div>
          </div>
      )}

      <div className="demo-controls-section">
        <p>Trigger simulated failures and scenarios to demonstrate real-time crisis monitoring.</p>
        <button
          onClick={handleSimulateError}
          className="demo-button critical"
          disabled={isInjecting}
        >
          {isInjecting ? 'Injecting Errors...' : 'Simulate Error Sequence'}
        </button>
        <button
          onClick={() => triggerActiveCallsSimulation(50)}
          className="demo-button success"
        >
          Add 50 Active Calls
        </button>
        <button
          onClick={handleResetAll}
          className="demo-button reset"
        >
          Reset All
        </button>
        {showToast && (
          <div className="toast-notification">
            {statusMessage}
          </div>
        )}
        {statusMessage && !showToast && <p className="demo-status-message">{statusMessage}</p>}
      </div>
    </div>
  );
}

export default LiveStatusIndicator;