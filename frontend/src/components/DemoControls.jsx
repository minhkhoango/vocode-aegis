import React, { useState, useEffect } from 'react';

const errorLevels = [
  {
    level: 'low',
    type: 'CONNECTION_TIMEOUT',
    message: 'A minor connection timeout occurred.',
    count: 1,
  },
  {
    level: 'medium',
    type: 'LLM_TIMEOUT',
    message: 'A medium severity LLM timeout occurred.',
    count: 2,
  },
  {
    level: 'high',
    type: 'SYSTEM_CRASH',
    message: 'A high severity system crash occurred.',
    count: 2,
  },
  {
    level: 'critical',
    type: 'LLM_CRITICAL_FAILURE',
    message: 'AI brain unresponsive - immediate impact on calls!',
    count: 3,
  },
];

const DemoControls = () => {
  const [statusMessage, setStatusMessage] = useState('');
  const [showToast, setShowToast] = useState(false);
  const [errorLevelIndex, setErrorLevelIndex] = useState(0);
  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:3001';

  useEffect(() => {
    if (showToast) {
      const timer = setTimeout(() => {
        setShowToast(false);
      }, 3000); // Toast visible for 3 seconds
      return () => clearTimeout(timer);
    }
  }, [showToast]);

  const showSuccessToast = (message) => {
    setStatusMessage(message);
    setShowToast(true);
  };

  const handleSimulateError = () => {
    const error = errorLevels[errorLevelIndex];
    triggerDemoError(error.type, error.message, error.level, error.count);
    setErrorLevelIndex((prevIndex) => (prevIndex + 1) % errorLevels.length);
  };

  const triggerDemoError = async (errorType, message, severity, count) => {
    setStatusMessage('Injecting...');
    try {
      const response = await fetch(`${API_URL}/demo/error`, {
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

  const triggerActiveCallsSimulation = async (count) => {
    setStatusMessage(`Simulating ${count} active calls...`);
    try {
      const response = await fetch(`${API_URL}/demo/active_calls`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ count: count }),
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

  const triggerResetAll = async () => {
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

  const currentErrorLevel = errorLevels[errorLevelIndex].level;

  return (
    <div className="metric-card demo-controls">
      <h3>Demo Controls</h3>
      <p>Trigger simulated failures and scenarios to demonstrate real-time crisis monitoring and response capabilities.</p>
      <button
        onClick={handleSimulateError}
        className={`demo-button ${currentErrorLevel}`}
      >
        Simulate Error ({currentErrorLevel})
      </button>
      <button
        onClick={() => triggerActiveCallsSimulation(50)}
        className="demo-button success"
      >
        Simulate 50 Active Calls
      </button>
      <button
        onClick={triggerResetAll}
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
  );
};

export default DemoControls; 