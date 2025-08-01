// frontend/src/components/DemoControls.jsx
import React, { useState } from 'react';

const DemoControls = () => {
  const [statusMessage, setStatusMessage] = useState('');
  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:3001';

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
        setStatusMessage(`Success: ${data.message}`);
        setTimeout(() => setStatusMessage(''), 5000); // Clear message after 5s
      } else {
        setStatusMessage(`Error: ${data.detail || data.message || 'Unknown backend error'}`);
      }
    } catch (error) {
      console.error('Frontend network error during demo injection:', error);
      setStatusMessage('Network error. Check browser console.');
    }
  };

  return (
    <div className="metric-card demo-controls">
      <h3>Demo Controls</h3>
      <p>Trigger simulated failures to see real-time crisis response.</p>
      <button
        onClick={() => triggerDemoError(
          'LLM_CRITICAL_FAILURE',
          'AI brain unresponsive - immediate impact on calls!',
          'critical',
          3 // Inject 3 critical errors
        )}
        className="demo-button critical"
      >
        Simulate CRITICAL AI Failure
      </button>
      {statusMessage && <p className="demo-status-message">{statusMessage}</p>}
    </div>
  );
};

export default DemoControls; 