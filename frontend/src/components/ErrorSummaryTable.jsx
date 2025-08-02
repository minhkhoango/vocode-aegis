// frontend/src/components/ErrorSummaryTable.jsx
import React from 'react';

function ErrorSummaryTable({ errors, onDrillDown }) {
  if (!errors || errors.length === 0) {
    return (
      <div className="metric-card error-summary">
        <h3>24-Hour Error Summary</h3>
        <p className="no-errors">No errors in the last 24 hours ✅</p>
      </div>
    );
  }

  return (
    <div className="metric-card error-summary">
      <h3>24-Hour Error Summary</h3>
      <table className="error-table">
        <thead>
          <tr>
            <th>Error Type</th>
            <th>Count</th>
            <th>Severity</th>
            <th>Last Seen</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {errors.map((error, index) => (
            <tr key={index}>
              <td>{error.error_type}</td>
              <td>{error.count}</td>
              <td>
                <span className={`severity ${error.severity.toLowerCase()}`}>
                  {error.severity}
                </span>
              </td>
              <td>{new Date(error.last_occurrence).toLocaleTimeString()}</td>
              <td>
                <button
                  className="drill-down-btn"
                  onClick={() => {
                    console.log(`Drill down clicked for error type: '${error.error_type}'`);
                    onDrillDown(error.error_type);
                  }}
                >
                  View Logs
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <small style={{ marginTop: '1rem', display: 'block' }}>
        Last updated: {new Date().toLocaleTimeString()}
      </small>
    </div>
  );
}

export default ErrorSummaryTable;