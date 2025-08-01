// frontend/src/components/LiveStatusIndicator.jsx
import React from 'react';

function LiveStatusIndicator({ status }) {
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
    </div>
  );
}

export default LiveStatusIndicator;