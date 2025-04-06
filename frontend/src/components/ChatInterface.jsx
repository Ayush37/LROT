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
  const [error, setError] = useState(null);
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  
  console.log("ChatInterface component rendered");
  
  // Scroll to bottom when messages change
  useEffect(() => {
    console.log("Messages updated, scrolling to bottom");
    scrollToBottom();
  }, [messages]);
  
  const scrollToBottom = () => {
    console.log("Scrolling to bottom");
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  const handleSendMessage = async () => {
    console.log("handleSendMessage called");
    if (input.trim() === '') {
      console.log("Input is empty, returning");
      return;
    }
    
    const userMessage = input;
    console.log("User message:", userMessage);
    setInput('');
    
    // Add user message to chat
    console.log("Adding user message to chat");
    setMessages(prevMessages => [...prevMessages, { 
      type: 'user', 
      content: userMessage 
    }]);
    
    setIsLoading(true);
    setError(null);
    
    try {
      console.log("Checking if message is related to SLS variance");
      // Check if message is related to SLS variance
      if (userMessage.toLowerCase().includes('variance') && 
          userMessage.toLowerCase().includes('sls')) {
        console.log("Message is related to SLS variance, showing date selector");
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
      
      // Configure request
      const apiUrl = '/api/chat';
      const requestData = {
        message: userMessage,
        history: messages.map(msg => ({
          user: msg.type === 'user' ? msg.content : '',
          assistant: msg.type === 'assistant' ? msg.content : ''
        })).filter(entry => entry.user || entry.assistant)
      };
      
      console.log("Sending request to:", apiUrl);
      console.log("Request data:", JSON.stringify(requestData, null, 2));
      
      // Send message to backend
      const response = await axios.post(apiUrl, requestData);
      
      console.log("Response received:", response);
      console.log("Response data:", JSON.stringify(response.data, null, 2));
      
      if (!response.data || !response.data.response) {
        throw new Error("Invalid response format from server");
      }
      
      // Add response to chat
      console.log("Adding assistant response to chat");
      setMessages(prevMessages => [...prevMessages, { 
        type: 'assistant', 
        content: response.data.response.content,
        data: response.data.response.function_call ? response.data.response : null
      }]);
      
    } catch (error) {
      console.error("Error in handleSendMessage:", error);
      
      // Log detailed error information
      if (error.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        console.error("Error response data:", error.response.data);
        console.error("Error response status:", error.response.status);
        console.error("Error response headers:", error.response.headers);
        setError(`Server error: ${error.response.status}. ${JSON.stringify(error.response.data)}`);
      } else if (error.request) {
        // The request was made but no response was received
        console.error("Error request:", error.request);
        setError("No response received from server. Check if the backend is running.");
      } else {
        // Something happened in setting up the request that triggered an Error
        console.error("Error message:", error.message);
        setError(`Error: ${error.message}`);
      }
      
      // Add error message to chat
      setMessages(prevMessages => [...prevMessages, { 
        type: 'assistant', 
        content: `Sorry, there was an error processing your request. Please try again. ${error.message}` 
      }]);
    }
    
    setIsLoading(false);
  };
  
  const handleDateSelection = async (dates) => {
    console.log("handleDateSelection called with dates:", dates);
    setSelectedDates(dates);
    setShowDateSelector(false);
    
    // Add dates message to chat
    setMessages(prevMessages => [...prevMessages, { 
      type: 'system', 
      content: `Selected dates: ${dates.date1} and ${dates.date2}` 
    }]);
    
    setIsLoading(true);
    setError(null);
    
    try {
      // Call backend function directly
      console.log("Calling backend with SLS variance function");
      
      const apiUrl = '/api/chat';
      const requestData = {
        message: 'Calculate the variance for SLS details',
        function_call: {
          name: 'sls_details_variance',
          arguments: {
            date1: dates.date1,
            date2: dates.date2
          }
        }
      };
      
      console.log("Sending request to:", apiUrl);
      console.log("Request data:", JSON.stringify(requestData, null, 2));
      
      const response = await axios.post(apiUrl, requestData);
      
      console.log("Response received:", response);
      console.log("Response data:", JSON.stringify(response.data, null, 2));
      
      if (!response.data || !response.data.response) {
        throw new Error("Invalid response format from server");
      }
      
      // Add response to chat
      console.log("Adding assistant response to chat with function results");
      setMessages(prevMessages => [...prevMessages, { 
        type: 'assistant', 
        content: response.data.response.content,
        data: response.data.response.function_call ? response.data.response : null
      }]);
      
    } catch (error) {
      console.error("Error in handleDateSelection:", error);
      
      // Log detailed error information
      if (error.response) {
        console.error("Error response data:", error.response.data);
        console.error("Error response status:", error.response.status);
        console.error("Error response headers:", error.response.headers);
        setError(`Server error: ${error.response.status}. ${JSON.stringify(error.response.data)}`);
      } else if (error.request) {
        console.error("Error request:", error.request);
        setError("No response received from server. Check if the backend is running.");
      } else {
        console.error("Error message:", error.message);
        setError(`Error: ${error.message}`);
      }
      
      // Add error message to chat
      setMessages(prevMessages => [...prevMessages, { 
        type: 'assistant', 
        content: `Sorry, there was an error calculating the variance. Please try again. ${error.message}` 
      }]);
    }
    
    setIsLoading(false);
  };
  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      console.log("Enter key pressed without shift");
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="chat-container">
      {error && (
        <div className="error-banner">
          <p>Error: {error}</p>
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}
      
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
      
      <div className="debug-info">
        <p>Backend URL: {process.env.REACT_APP_API_URL || 'http://localhost:5000'}</p>
        <p>Messages Count: {messages.length}</p>
        <p>Loading: {isLoading ? 'Yes' : 'No'}</p>
      </div>
    </div>
  );
}

export default ChatInterface;
