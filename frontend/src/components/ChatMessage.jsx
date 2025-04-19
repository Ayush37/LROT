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
      const result = data.result;
      
      if (result.error) {
        return <div className="mt-3 bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-800">{result.error}</div>;
      }
      
      // Determine if this is the comprehensive analysis or the original variance analysis
      const isComprehensiveAnalysis = result.reporting_table_analysis !== undefined;
      
      if (isComprehensiveAnalysis) {
        // Render comprehensive analysis
        return (
          <div className="mt-3 bg-gray-50 border border-gray-200 rounded-lg overflow-hidden">
            {/* Header */}
            <div className="bg-blue-50 p-4 border-b border-blue-100">
              <h3 className="text-md font-semibold text-blue-800">6G Variance Analysis</h3>
              <div className="grid grid-cols-2 gap-4 mt-2">
                <div>
                  <p className="text-xs text-gray-500">Date Range</p>
                  <p className="text-sm font-medium">{result.date1} to {result.date2}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Product Identifiers</p>
                  <p className="text-sm font-medium">
                    {result.product_identifiers && result.product_identifiers.length > 0 
                      ? result.product_identifiers.join(', ') 
                      : 'All'}
                  </p>
                </div>
              </div>
            </div>
            
            {/* Step 1: Reporting Table Analysis */}
            <div className="p-4 border-b border-gray-200">
              <div className="flex justify-between items-center mb-3">
                <h4 className="text-sm font-semibold text-gray-700">Step 1: Reporting Table Analysis</h4>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                  result.reporting_table_analysis.variance_data.length > 0 
                    ? 'bg-amber-100 text-amber-800' 
                    : 'bg-green-100 text-green-800'
                }`}>
                  {result.reporting_table_analysis.variance_data.length > 0 
                    ? `${result.reporting_table_analysis.variance_data.length} variances found` 
                    : 'No variances found'}
                </span>
              </div>
              
              <p className="text-sm text-gray-600 mb-3">{result.reporting_table_analysis.message}</p>
              
              {result.reporting_table_analysis.variance_data.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 text-sm">
                    <thead className="bg-gray-100">
                      <tr>
                        <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">SLS Line</th>
                        <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Context Name</th>
                        <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">{result.date1}</th>
                        <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">{result.date2}</th>
                        <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Variance %</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {result.reporting_table_analysis.variance_data.slice(0, 5).map((row, index) => (
                        <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                          <td className="px-3 py-2 whitespace-nowrap text-sm font-medium text-gray-800">{row.sls_line}</td>
                          <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-600">{row.context_name}</td>
                          <td className="px-3 py-2 whitespace-nowrap text-sm text-right text-gray-600">
                            {row.amount_date1.toLocaleString(undefined, {maximumFractionDigits: 2})}
                          </td>
                          <td className="px-3 py-2 whitespace-nowrap text-sm text-right text-gray-600">
                            {row.amount_date2.toLocaleString(undefined, {maximumFractionDigits: 2})}
                          </td>
                          <td className={`px-3 py-2 whitespace-nowrap text-sm text-right font-medium ${
                            Math.abs(row.percentage_variance) > 10 ? 'text-red-600' : 'text-gray-600'
                          }`}>
                            {row.percentage_variance.toFixed(2)}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {result.reporting_table_analysis.variance_data.length > 5 && (
                    <div className="p-2 text-center text-xs text-gray-500 bg-gray-50 border-t border-gray-200">
                      Showing 5 of {result.reporting_table_analysis.variance_data.length} variances
                    </div>
                  )}
                </div>
              ) : (
                <div className="p-4 text-center text-sm text-gray-500 bg-gray-50 rounded-md">
                  No significant variances found in reporting table.
                </div>
              )}
              
              {/* Display Missing Pairs */}
              {result.reporting_table_analysis.missing_pairs && result.reporting_table_analysis.missing_pairs.length > 0 && (
                <div className="mt-3">
                  <h5 className="text-sm font-semibold text-gray-700 mb-2">Missing SLS Line + Context Name Pairs</h5>
                  <div className="bg-gray-50 p-3 rounded-md text-sm text-gray-600">
                    <ul className="list-disc pl-5 space-y-1">
                      {result.reporting_table_analysis.missing_pairs.slice(0, 3).map((pair, index) => (
                        <li key={index}>
                          <span className="font-medium">{pair.sls_line} + {pair.context_name}</span>: 
                          Present in {pair.present_in}, missing from {pair.missing_from}
                        </li>
                      ))}
                    </ul>
                    {result.reporting_table_analysis.missing_pairs.length > 3 && (
                      <p className="mt-1 text-xs text-gray-500">
                        And {result.reporting_table_analysis.missing_pairs.length - 3} more...
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>
            
            {/* Step 2: Base Data Analysis (only show if reporting found variances) */}
            {result.base_data_analysis && (
              <div className="p-4 border-b border-gray-200">
                <div className="flex justify-between items-center mb-3">
                  <h4 className="text-sm font-semibold text-gray-700">Step 2: Base Data Analysis</h4>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                    result.base_data_analysis.variance_data.length > 0 
                      ? 'bg-amber-100 text-amber-800' 
                      : 'bg-green-100 text-green-800'
                  }`}>
                    {result.base_data_analysis.variance_data.length > 0 
                      ? `${result.base_data_analysis.variance_data.length} variances found` 
                      : 'No variances found'}
                  </span>
                </div>
                
                <p className="text-sm text-gray-600 mb-3">{result.base_data_analysis.message}</p>
                
                {result.base_data_analysis.variance_data.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 text-sm">
                      <thead className="bg-gray-100">
                        <tr>
                          <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">SLS Line</th>
                          <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Context Name</th>
                          <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">{result.date1}</th>
                          <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">{result.date2}</th>
                          <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Variance %</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {result.base_data_analysis.variance_data.slice(0, 5).map((row, index) => (
                          <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                            <td className="px-3 py-2 whitespace-nowrap text-sm font-medium text-gray-800">{row.sls_line}</td>
                            <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-600">{row.context_name}</td>
                            <td className="px-3 py-2 whitespace-nowrap text-sm text-right text-gray-600">
                              {row.amount_date1.toLocaleString(undefined, {maximumFractionDigits: 2})}
                            </td>
                            <td className="px-3 py-2 whitespace-nowrap text-sm text-right text-gray-600">
                              {row.amount_date2.toLocaleString(undefined, {maximumFractionDigits: 2})}
                            </td>
                            <td className={`px-3 py-2 whitespace-nowrap text-sm text-right font-medium ${
                              Math.abs(row.percentage_variance) > 10 ? 'text-red-600' : 'text-gray-600'
                            }`}>
                              {row.percentage_variance.toFixed(2)}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {result.base_data_analysis.variance_data.length > 5 && (
                      <div className="p-2 text-center text-xs text-gray-500 bg-gray-50 border-t border-gray-200">
                        Showing 5 of {result.base_data_analysis.variance_data.length} variances
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="p-4 text-center text-sm text-gray-500 bg-gray-50 rounded-md">
                    No significant variances found in base data table for the selected SLS lines.
                  </div>
                )}
                
                {/* Display Missing Pairs */}
                {result.base_data_analysis.missing_pairs && result.base_data_analysis.missing_pairs.length > 0 && (
                  <div className="mt-3">
                    <h5 className="text-sm font-semibold text-gray-700 mb-2">Missing Context Name Pairs in Base Data</h5>
                    <div className="bg-gray-50 p-3 rounded-md text-sm text-gray-600">
                      <ul className="list-disc pl-5 space-y-1">
                        {result.base_data_analysis.missing_pairs.slice(0, 3).map((pair, index) => (
                          <li key={index}>
                            <span className="font-medium">{pair.sls_line} + {pair.context_name}</span>: 
                            Present in {pair.present_in}, missing from {pair.missing_from}
                          </li>
                        ))}
                      </ul>
                      {result.base_data_analysis.missing_pairs.length > 3 && (
                        <p className="mt-1 text-xs text-gray-500">
                          And {result.base_data_analysis.missing_pairs.length - 3} more...
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
            
            {/* Step 3: SLS Details Analysis */}
            {result.sls_details_analysis && (
              <div className="p-4">
                <div className="flex justify-between items-center mb-3">
                  <h4 className="text-sm font-semibold text-gray-700">Step 3: SLS Details Analysis</h4>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                    result.sls_details_analysis.variance_data.length > 0 
                      ? 'bg-amber-100 text-amber-800' 
                      : 'bg-green-100 text-green-800'
                  }`}>
                    {result.sls_details_analysis.variance_data.length > 0 
                      ? `${result.sls_details_analysis.variance_data.length} variances found` 
                      : 'No variances found'}
                  </span>
                </div>
                
                <p className="text-sm text-gray-600 mb-3">{result.sls_details_analysis.message}</p>
                
                {result.sls_details_analysis.variance_data.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 text-sm">
                      <thead className="bg-gray-100">
                        <tr>
                          <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">SLS Line</th>
                          <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Context Name</th>
                          <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">{result.date1}</th>
                          <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">{result.date2}</th>
                          <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Variance %</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {result.sls_details_analysis.variance_data.slice(0, 5).map((row, index) => (
                          <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                            <td className="px-3 py-2 whitespace-nowrap text-sm font-medium text-gray-800">{row.sls_line}</td>
                            <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-600">{row.context_name}</td>
                            <td className="px-3 py-2 whitespace-nowrap text-sm text-right text-gray-600">
                              {row.amount_date1.toLocaleString(undefined, {maximumFractionDigits: 2})}
                            </td>
                            <td className="px-3 py-2 whitespace-nowrap text-sm text-right text-gray-600">
                              {row.amount_date2.toLocaleString(undefined, {maximumFractionDigits: 2})}
                            </td>
                            <td className={`px-3 py-2 whitespace-nowrap text-sm text-right font-medium ${
                              Math.abs(row.percentage_variance) > 10 ? 'text-red-600' : 'text-gray-600'
                            }`}>
                              {row.percentage_variance.toFixed(2)}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {result.sls_details_analysis.variance_data.length > 5 && (
                      <div className="p-2 text-center text-xs text-gray-500 bg-gray-50 border-t border-gray-200">
                        Showing 5 of {result.sls_details_analysis.variance_data.length} variances
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="p-4 text-center text-sm text-gray-500 bg-gray-50 rounded-md">
                    No significant variances found in SLS details table for the selected SLS lines.
                  </div>
                )}
                
                {/* Display Missing Pairs */}
                {result.sls_details_analysis.missing_pairs && result.sls_details_analysis.missing_pairs.length > 0 && (
                  <div className="mt-3">
                    <h5 className="text-sm font-semibold text-gray-700 mb-2">Missing Context Name Pairs in SLS Details</h5>
                    <div className="bg-gray-50 p-3 rounded-md text-sm text-gray-600">
                      <ul className="list-disc pl-5 space-y-1">
                        {result.sls_details_analysis.missing_pairs.slice(0, 3).map((pair, index) => (
                          <li key={index}>
                            <span className="font-medium">{pair.sls_line} + {pair.context_name}</span>: 
                            Present in {pair.present_in}, missing from {pair.missing_from}
                          </li>
                        ))}
                      </ul>
                      {result.sls_details_analysis.missing_pairs.length > 3 && (
                        <p className="mt-1 text-xs text-gray-500">
                          And {result.sls_details_analysis.missing_pairs.length - 3} more...
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      }
      
      // Handle original variance function
      if (!isComprehensiveAnalysis) {
        const { summary, variance_data } = result;
          
        if (result.error) {
          return <div className="mt-3 bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-800">{result.error}</div>;
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
                  <p className="text-sm font-medium">{summary.total_combinations} total / {summary.combinations_with_variance} with variance</p>
                </div>
              </div>
              <div className={`mt-3 p-2 rounded-md ${summary.combinations_with_variance > 0 ? "bg-red-100 text-red-800" : "bg-green-100 text-green-800"} text-sm font-medium text-center`}>
                {summary.combinations_with_variance > 0 ? "⚠️ Significant variance detected" : "✓ No significant variance"}
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
    }
    
    if (data.name === 'get_6g_status') {
      const result = data.result;
      
      if (result.error) {
        return <div className="mt-3 bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-800">{result.error}</div>;
      }
      
      return (
        <div className="mt-3 bg-gray-50 border border-gray-200 rounded-lg overflow-hidden">
          <div className="bg-blue-50 p-4 border-b border-blue-100">
            <h3 className="text-md font-semibold text-blue-800">
              {result.process_name} ({result.process_alias}) Status
            </h3>
            <div className="grid grid-cols-2 gap-4 mt-2">
              <div>
                <p className="text-xs text-gray-500">COB Date</p>
                <p className="text-sm font-medium">{result.cob_date}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Completion</p>
                <p className="text-sm font-medium">{result.tables_completed} of {result.total_tables} tables ({result.completion_percentage}%)</p>
              </div>
            </div>
            <div className="mt-3">
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div 
                  className={`h-2.5 rounded-full ${result.completion_percentage === 100 ? 'bg-green-500' : 'bg-blue-500'}`} 
                  style={{ width: `${result.completion_percentage}%` }}
                ></div>
              </div>
            </div>
          </div>
          
          {result.tables && result.tables.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-100">
                  <tr>
                    <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Table Name</th>
                    <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">BPF ID</th>
                    <th scope="col" className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Start Time</th>
                    <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">End Time</th>
                    <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Duration (min)</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {result.tables.map((table, index) => (
                    <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-3 py-2 whitespace-nowrap text-sm font-medium text-gray-800">
                        {table.name}
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-600">
                        {table.bpf_id}
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap text-sm text-center">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          table.status === 'COMPLETED' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {table.status}
                        </span>
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap text-sm text-right text-gray-600">
                        {table.start_time}
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap text-sm text-right text-gray-600">
                        {table.end_time}
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap text-sm text-right text-gray-600">
                        {table.duration_minutes !== null ? table.duration_minutes : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-4 text-center text-sm text-gray-500">
              No completed tables found for this COB date.
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
