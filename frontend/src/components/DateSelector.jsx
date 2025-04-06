// frontend/src/components/DateSelector.jsx
import React, { useState } from 'react';
import Calendar from 'react-calendar';
import 'react-calendar/dist/Calendar.css';
import '../styles/DateSelector.css';

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
// frontend/src/components/DateSelector.jsx (continued)
    <div className="date-selector-modal">
      <div className="date-selector-content">
        <button className="close-button" onClick={onCancel}>&times;</button>
        
        {step === 1 && (
          <div>
            <h3>Select First Date</h3>
            <Calendar onChange={handleDate1Change} />
          </div>
        )}
        
        {step === 2 && (
          <div>
            <h3>Select Second Date</h3>
            <p>First date selected: {date1}</p>
            <Calendar onChange={handleDate2Change} />
          </div>
        )}
        
        {step === 3 && (
          <div className="date-confirmation">
            <h3>Confirm Selected Dates</h3>
            <p>First date: {date1}</p>
            <p>Second date: {date2}</p>
            <div className="button-group">
              <button className="cancel-button" onClick={onCancel}>Cancel</button>
              <button className="confirm-button" onClick={handleConfirm}>Confirm</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default DateSelector;	  
