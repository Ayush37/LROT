// frontend/src/components/DateSelector.jsx
import React, { useState } from 'react';
import Calendar from 'react-calendar';
import 'react-calendar/dist/Calendar.css';
import { XMarkIcon } from '@heroicons/react/24/outline';

function DateSelector({ onSelect, onCancel }) {
  const [step, setStep] = useState(1);
  const [date1, setDate1] = useState(null);
  const [date2, setDate2] = useState(null);
  
  const handleDate1Change = (date) => {
    setDate1(formatDate(date));
    setStep(2);
  };
  
  const handleDate2Change = (date) => {
    setDate2(formatDate(date));
    setStep(3);
  };
  
  const formatDate = (date) => {
    return date.toISOString().split('T')[0];
  };
  
  const handleConfirm = () => {
    onSelect({ date1, date2 });
  };
  
  return (
    <div className="fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full overflow-hidden">
        <div className="flex justify-between items-center p-4 bg-gray-50 border-b">
          <h3 className="text-lg font-medium text-gray-800">
            {step === 1 ? 'Select First Date' : step === 2 ? 'Select Second Date' : 'Confirm Dates'}
          </h3>
          <button 
            onClick={onCancel}
            className="rounded-full p-1 hover:bg-gray-200 text-gray-500"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>
        
        <div className="p-4">
          {step === 1 && (
            <div className="space-y-4">
              <p className="text-sm text-gray-600">Please select the first date for variance calculation:</p>
              <div className="date-picker-container">
                <Calendar 
                  onChange={handleDate1Change} 
                  className="border rounded shadow-sm mx-auto"
                />
              </div>
            </div>
          )}
          
          {step === 2 && (
            <div className="space-y-4">
              <div className="bg-blue-50 p-3 rounded-md">
                <p className="text-sm text-blue-800">First date selected: <span className="font-medium">{date1}</span></p>
              </div>
              <p className="text-sm text-gray-600">Now select the second date for comparison:</p>
              <div className="date-picker-container">
                <Calendar 
                  onChange={handleDate2Change} 
                  className="border rounded shadow-sm mx-auto"
                />
              </div>
            </div>
          )}
          
          {step === 3 && (
            <div className="space-y-4">
              <div className="bg-gray-50 p-4 rounded-md space-y-3">
                <div>
                  <p className="text-sm text-gray-500">First Date</p>
                  <p className="text-lg font-medium">{date1}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Second Date</p>
                  <p className="text-lg font-medium">{date2}</p>
                </div>
              </div>
              <p className="text-sm text-gray-600">
                Calculate variance between these dates?
              </p>
              <div className="flex space-x-3 pt-2">
                <button 
                  onClick={onCancel}
                  className="flex-1 px-4 py-2 bg-white border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button 
                  onClick={handleConfirm}
                  className="flex-1 px-4 py-2 bg-blue-600 border border-transparent rounded-md text-white hover:bg-blue-700"
                >
                  Confirm
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default DateSelector;
