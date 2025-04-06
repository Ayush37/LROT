// frontend/src/components/ChatInterface.jsx
import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import ChatMessage from './ChatMessage';
import DateSelector from './DateSelector';
import '../styles/ChatInterface.css';

function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showDateSelector, setShowDateSelector] = useState(false);
  const [selectedDates, setSelectedDates] = useState({ date1: null, date2: null });
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  
  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  const handleSendMessage = async () => {
    if (input.trim() === '') return;
    
    const userMessage = input;
    setInput('');
    
    // Add user message to chat
    setMessages(prevMessages => [...prevMessages, { 
      type: 'user', 
      content: userMessage 
    }]);
    
    setIsLoading(true);
    
    try {
      // Check if message is related to SLS variance
      if (userMessage.toLowerCase().includes('variance') && 
          userMessage.toLowerCase().includes('sls')) {
        // Show date selector
        setShowDateSelector(true);
        
        // Add system message explaining date selection
        setMessages(prevMessages => [...prevMessages, { 
          type: 'assistant', 
          content: 'To calculate SLS details variance, please select two dates for comparison.' 
        }]);
        
        setIsLoading(false);
        return;
      }
      
      // Send message to backend
      const response = await axios.post('/api/chat', {
        message: userMessage,
        history: messages.map(msg => ({
          user: msg.type === 'user' ? msg.content : '',
          assistant: msg.type === 'assistant' ? msg.content : ''
        })).filter(entry => entry.user || entry.assistant)
      });
      
      // Add response to chat
      setMessages(prevMessages => [...prevMessages, { 
        type: 'assistant', 
        content: response.data.response.content,
        data: response.data.response.function_call ? response.data.response : null
      }]);
      
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Add error message to chat
      setMessages(prevMessages => [...prevMessages, { 
        type: 'assistant', 
        content: 'Sorry, there was an error processing your request. Please try again.' 
      }]);
    }
    
    setIsLoading(false);
  };
  
  const handleDateSelection = async (dates) => {
    setSelectedDates(dates);
    setShowDateSelector(false);
    
    // Add dates message to chat
    setMessages(prevMessages => [...prevMessages, { 
      type: 'system', 
      content: `Selected dates: ${dates.date1} and ${dates.date2}` 
    }]);
    
    setIsLoading(true);
    
    try {
      // Call backend function directly
      const response = await axios.post('/api/chat', {
        message: 'Calculate the variance for SLS details',
        function_call: {
          name: 'sls_details_variance',
          arguments: {
            date1: dates.date1,
            date2: dates.date2
          }
        }
      });
      
      // Add response to chat
      setMessages(prevMessages => [...prevMessages, { 
        type: 'assistant', 
        content: response.data.response.content,
        data: response.data.response.function_call ? response.data.response : null
      }]);
      
    } catch (error) {
      console.error('Error calculating variance:', error);
      
      // Add error message to chat
      setMessages(prevMessages => [...prevMessages, { 
        type: 'assistant', 
        content: 'Sorry, there was an error calculating the variance. Please try again.' 
      }]);
    }
    
    setIsLoading(false);
  };
  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="welcome-message">
            <h2>Welcome to LROT Assistant</h2>
            <p>How can I help you today?</p>
            <div className="suggested-queries">
              <button onClick={() => setInput('Calculate the variance for SLS details')}>
                Calculate SLS details variance
              </button>
              <button onClick={() => setInput('How many hours of work left for today?')}>
                Time remaining until EOD
              </button>
            </div>
          </div>
        )}
        
        {messages.map((message, index) => (
          <ChatMessage key={index} message={message} />
        ))}
        
        {isLoading && (
          <div className="message assistant-message">
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {showDateSelector && (
        <DateSelector onSelect={handleDateSelection} onCancel={() => setShowDateSelector(false)} />
      )}
      
      <div className="chat-input-container">
        <textarea
          ref={inputRef}
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message here..."
          disabled={isLoading || showDateSelector}
        />
        <button 
          className="send-button" 
          onClick={handleSendMessage}
          disabled={isLoading || showDateSelector || input.trim() === ''}
        >
          Send
        </button>
      </div>
    </div>
  );
}

export default ChatInterface;
