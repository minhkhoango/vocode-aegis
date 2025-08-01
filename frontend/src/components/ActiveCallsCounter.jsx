// frontend/src/components/ActiveCallsCounter.jsx
import React from 'react';

function ActiveCallsCounter({ count }) {
  return (
    <div className="metric-card active-calls">
      <h3>Active Calls</h3>
      <div className="metric-value">
        <span className="count-number">{count}</span>
      </div>
      <small>Real-time count</small>
    </div>
  );
}

export default ActiveCallsCounter;