// frontend/src/components/ChatMessage.jsx
import React from 'react';
import { UserCircleIcon } from '@heroicons/react/24/solid';
import { ChartBarIcon } from '@heroicons/react/24/outline';

function ChatMessage({ message }) {
  const { type, content, data } = message;
  
  // Helper function to render function call results
  const renderFunctionData = (data) => {
    if (!data || !data.result) return null;
    
    if (data.name === 'time_remaining') {
      return (
        <div className="mt-3 bg-blue-50 border border-blue-100 rounded-lg p-4">
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm font-medium text-gray-700">Current Time:</span>
              <span className="text-sm text-gray-800">{data.result.current_time}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm font-medium text-gray-700">End of Day:</span>
              <span className="text-sm text-gray-800">{data.result.eod_time}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm font-medium text-gray-700">Time Remaining:</span>
              <span className="text-sm text-gray-800">{data.result.hours_remaining}h {data.result.minutes_remaining}m</span>
            </div>
            <div className="mt-3 p-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg text-center">
              {data.result.message}
            </div>
          </div>
        </div>
      );
    }
    
    if (data.name === 'sls_details_variance') {
      const { summary, variance_data } = data.result;
      
      if (data.result.error) {
        return <div className="mt-3 bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-800">{data.result.error}</div>;
      }
      
      return (
        <div className="mt-3 bg-gray-50 border border-gray-200 rounded-lg overflow-hidden">
          <div className="bg-blue-50 p-4 border-b border-blue-100">
            <h3 className="text-md font-semibold text-blue-800">Variance Summary</h3>
            <div className="grid grid-cols-2 gap-4 mt-2">
              <div>
                <p className="text-xs text-gray-500">Date Range</p>
                <p className="text-sm font-medium">{summary.date1} to {summary.date2}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">SLS Lines</p>
                <p className="text-sm font-medium">{summary.total_lines} total / {summary.lines_with_variance} with variance</p>
              </div>
            </div>
            <div className={`mt-3 p-2 rounded-md ${summary.threshold_crossed ? "bg-red-100 text-red-800" : "bg-green-100 text-green-800"} text-sm font-medium text-center`}>
              {summary.threshold_crossed ? "⚠️ Significant variance detected" : "✓ No significant variance"}
            </div>
          </div>
          
          {variance_data && variance_data.length > 0 && (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-100">
                  <tr>
                    <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">SLS Line</th>
                    <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Measure (Date 1)</th>
                    <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Measure (Date 2)</th>
                    <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Variance</th>
                    <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">COF (Date 1)</th>
                    <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">COF (Date 2)</th>
                    <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Variance</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {variance_data.slice(0, 8).map((row, index) => (
                    <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-3 py-2 whitespace-nowrap text-sm font-medium text-gray-800">{row.sls_line_number}</td>
                      <td className="px-3 py-2 whitespace-nowrap text-sm text-right text-gray-600">{row.amt_reporting_measure_date1.toLocaleString()}</td>
                      <td className="px-3 py-2 whitespace-nowrap text-sm text-right text-gray-600">{row.amt_reporting_measure_date2.toLocaleString()}</td>
                      <td className={`px-3 py-2 whitespace-nowrap text-sm text-right font-medium ${Math.abs(row.amt_reporting_measure_pct) > 10 ? "text-red-600" : "text-gray-600"}`}>
                        {row.amt_reporting_measure_variance.toLocaleString()} ({row.amt_reporting_measure_pct.toFixed(2)}%)
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap text-sm text-right text-gray-600">{row.amt_cof_flow_date1.toLocaleString()}</td>
                      <td className="px-3 py-2 whitespace-nowrap text-sm text-right text-gray-600">{row.amt_cof_flow_date2.toLocaleString()}</td>
                      <td className={`px-3 py-2 whitespace-nowrap text-sm text-right font-medium ${Math.abs(row.amt_cof_flow_pct) > 10 ? "text-red-600" : "text-gray-600"}`}>
                        {row.amt_cof_flow_variance.toLocaleString()} ({row.amt_cof_flow_pct.toFixed(2)}%)
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {variance_data.length > 8 && (
                <div className="p-2 text-center text-xs text-gray-500 bg-gray-50 border-t border-gray-200">
                  Showing 8 of {variance_data.length} rows
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
    <div className={`flex ${type === 'user' ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex max-w-[80%] ${type === 'user' ? 'flex-row-reverse' : ''}`}>
        <div className={`flex-shrink-0 ${type === 'user' ? 'ml-3' : 'mr-3'}`}>
          {type === 'user' ? (
            <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
              <UserCircleIcon className="h-6 w-6 text-blue-500" />
            </div>
          ) : (
            <div className="h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center">
              <ChartBarIcon className="h-5 w-5 text-indigo-500" />
            </div>
          )}
        </div>
        
        <div className={`
          px-4 py-3 rounded-2xl shadow-sm
          ${type === 'user' 
            ? 'bg-blue-500 text-white rounded-tr-none' 
            : type === 'system' 
              ? 'bg-gray-200 text-gray-700 italic text-sm' 
              : 'bg-gray-100 text-gray-800 rounded-tl-none'}
        `}>
          <div className="whitespace-pre-wrap">{content}</div>
          {data && renderFunctionData(data)}
        </div>
      </div>
    </div>
  );
}

export default ChatMessage;
