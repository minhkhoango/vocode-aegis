// frontend/src/components/LogViewerModal.jsx
import React from 'react';
import './LogViewerModal.css'; // Create this new CSS file

const LogViewerModal = ({ isOpen, onClose, errorType, logs }) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Logs for: {errorType}</h3>
          <button className="close-button" onClick={onClose}>&times;</button>
        </div>
        <div className="modal-body">
          {logs.length === 0 ? (
            <p>No logs found for this error type.</p>
          ) : (
            <div className="log-list">
              {logs.map((log, index) => (
                <div key={index} className="log-entry-modal">
                  <span className="log-timestamp">
                    {new Date(parseInt(log.timestamp)).toLocaleString()}
                  </span>
                  <p className="log-message">{log.message}</p>
                  <span className={`log-severity severity ${log.severity.toLowerCase()}`}>
                    {log.severity}
                  </span>
                  <span className="log-conv-id">Conv ID: {log.conversation_id || 'N/A'}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LogViewerModal; 