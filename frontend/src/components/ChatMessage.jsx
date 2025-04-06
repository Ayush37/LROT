// frontend/src/components/ChatMessage.jsx
import React from 'react';
import '../styles/ChatMessage.css';

function ChatMessage({ message }) {
  const { type, content, data } = message;
  
  // Helper function to render function call results
  const renderFunctionData = (data) => {
    if (!data || !data.result) return null;
    
    if (data.name === 'time_remaining') {
      return (
        <div className="function-result time-result">
          <div className="time-info">
            <p><strong>Current Time:</strong> {data.result.current_time}</p>
            <p><strong>End of Day:</strong> {data.result.eod_time}</p>
            <p><strong>Time Remaining:</strong> {data.result.hours_remaining}h {data.result.minutes_remaining}m</p>
          </div>
          <div className="message-box">{data.result.message}</div>
        </div>
      );
    }
    
    if (data.name === 'sls_details_variance') {
      const { summary, variance_data } = data.result;
      
      if (data.result.error) {
        return <div className="error-message">{data.result.error}</div>;
      }
      
      return (
        <div className="function-result variance-result">
          <div className="summary-box">
            <h3>Variance Summary</h3>
            <p><strong>Dates:</strong> {summary.date1} to {summary.date2}</p>
            <p><strong>Total SLS Lines:</strong> {summary.total_lines}</p>
            <p><strong>Lines with Variance:</strong> {summary.lines_with_variance}</p>
            <p className={summary.threshold_crossed ? "threshold-alert" : ""}>
              <strong>Threshold Alert:</strong> {summary.threshold_crossed ? "Significant variance detected" : "No significant variance"}
            </p>
          </div>
          
          {variance_data && variance_data.length > 0 && (
            <div className="variance-table-container">
              <h3>Detailed Variance Data</h3>
              <table className="variance-table">
                <thead>
                  <tr>
                    <th>SLS Line</th>
                    <th>Measure (Date 1)</th>
                    <th>Measure (Date 2)</th>
                    <th>Measure Variance</th>
                    <th>COF (Date 1)</th>
                    <th>COF (Date 2)</th>
                    <th>COF Variance</th>
                    <th>Mkt Value (Date 1)</th>
                    <th>Mkt Value (Date 2)</th>
                    <th>Mkt Value Variance</th>
                  </tr>
                </thead>
                <tbody>
                  {variance_data.slice(0, 10).map((row, index) => (
                    <tr key={index}>
                      <td>{row.sls_line_number}</td>
                      <td>{row.amt_reporting_measure_date1.toLocaleString()}</td>
                      <td>{row.amt_reporting_measure_date2.toLocaleString()}</td>
                      <td className={Math.abs(row.amt_reporting_measure_pct) > 10 ? "variance-alert" : ""}>
                        {row.amt_reporting_measure_variance.toLocaleString()} ({row.amt_reporting_measure_pct.toFixed(2)}%)
                      </td>
                      <td>{row.amt_cof_flow_date1.toLocaleString()}</td>
                      <td>{row.amt_cof_flow_date2.toLocaleString()}</td>
                      <td className={Math.abs(row.amt_cof_flow_pct) > 10 ? "variance-alert" : ""}>
                        {row.amt_cof_flow_variance.toLocaleString()} ({row.amt_cof_flow_pct.toFixed(2)}%)
                      </td>
                      <td>{row.amt_curr_mkt_value_date1.toLocaleString()}</td>
                      <td>{row.amt_curr_mkt_value_date2.toLocaleString()}</td>
                      <td className={Math.abs(row.amt_curr_mkt_value_pct) > 10 ? "variance-alert" : ""}>
                        {row.amt_curr_mkt_value_variance.toLocaleString()} ({row.amt_curr_mkt_value_pct.toFixed(2)}%)
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {variance_data.length > 10 && (
                <div className="table-footer">
                  Showing 10 of {variance_data.length} rows
                </div>
              )}
            </div>
          )}
        </div>
      );
    }
    
    return null;
  };
  
  return (
    <div className={`message ${type}-message`}>
      <div className="message-content">
        {content}
        {data && renderFunctionData(data)}
      </div>
    </div>
  );
}

export default ChatMessage;
