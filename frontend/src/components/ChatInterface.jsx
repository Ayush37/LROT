// frontend/src/components/ChatInterface.jsx
import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { PaperAirplaneIcon, ArrowPathIcon, XCircleIcon, ExclamationCircleIcon } from '@heroicons/react/24/solid';
import { CSSTransition, TransitionGroup } from 'react-transition-group';
import ChatMessage from './ChatMessage';
import DateSelector from './DateSelector';

function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showDateSelector, setShowDateSelector] = useState(false);
  const [selectedDates, setSelectedDates] = useState({ date1: null, date2: null });
  const [error, setError] = useState(null);
  const [awaitingProductIds, setAwaitingProductIds] = useState(false);
  const [productIdentifiers, setProductIdentifiers] = useState('');
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  
  console.log("ChatInterface component rendered");
  
  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  const scrollToBottom = () => {
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
    
    // Check if waiting for product identifiers
    if (awaitingProductIds) {
      console.log("Received product identifiers:", userMessage);
      
      // Reset the flag
      setAwaitingProductIds(false);
      
      // Get product identifiers (or set to empty string if "all")
      const productIds = userMessage.toLowerCase() === 'all' ? '' : userMessage;
      
      // Add user message to chat
      setMessages(prevMessages => [...prevMessages, { 
        type: 'user', 
        content: userMessage 
      }]);
      
      // Show confirmation and date selector
      setMessages(prevMessages => [...prevMessages, { 
        type: 'assistant', 
        content: `Thank you. Now please select two dates for comparison to check 6G variance with product identifiers: ${productIds || 'all'}` 
      }]);
      
      // Store product identifiers for later use and show date selector
      setProductIdentifiers(productIds);
      setShowDateSelector(true);
      return;
    }
    
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
      
      // Check for 6G variance queries
      if (userMessage.toLowerCase().includes('6g variance') || 
          (userMessage.toLowerCase().includes('variance') && userMessage.toLowerCase().includes('6g'))) {
        console.log("Message is related to 6G variance");
        
        // Show product identifiers input dialog
        setMessages(prevMessages => [...prevMessages, { 
          type: 'assistant', 
          content: 'To check for 6G variance, please provide the product identifiers you want to analyze (comma-separated, e.g., "OS-09,OS-10"). If you want to check all, just type "all".' 
        }]);
        
        // Set a flag to indicate we're waiting for product identifiers
        setAwaitingProductIds(true);
        setIsLoading(false);
        return;
      }
      
      // Configure request
      const apiUrl = `${process.env.REACT_APP_API_URL || 'http://172.24.98.189:5001'}/api/chat`;
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
        content: `Sorry, there was an error processing your request. Please try again.` 
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
      // Call backend with SLS variance function
      console.log("Calling backend with SLS variance function");
      
      const apiUrl = `${process.env.REACT_APP_API_URL || 'http://172.24.98.189:5001'}/api/chat`;
      
      const requestData = {
        message: 'Calculate the variance for SLS details',
        function_call: {
          name: 'sls_details_variance',
          arguments: {
            date1: dates.date1,
            date2: dates.date2,
            product_identifiers: productIdentifiers // Include the product identifiers
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
      
      // Reset product identifiers after use
      setProductIdentifiers('');
      
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
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full max-w-6xl mx-auto bg-white shadow-lg rounded-lg overflow-hidden">
      {error && (
        <div className="bg-red-50 p-4 mx-4 mt-4 rounded-lg flex items-center justify-between">
          <div className="flex items-center">
            <ExclamationCircleIcon className="h-5 w-5 text-red-500 mr-3" />
            <p className="text-sm text-red-800">{error}</p>
          </div>
          <button 
            onClick={() => setError(null)}
            className="text-red-500 hover:text-red-700"
          >
            <XCircleIcon className="h-5 w-5" />
          </button>
        </div>
      )}
      
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full space-y-6 pb-20">
            <div className="text-center space-y-2">
              <h2 className="text-2xl font-bold text-gray-800">Welcome to LROT Assistant</h2>
              <p className="text-gray-600">Your AI-powered financial analysis companion</p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-2xl">
              <button 
                onClick={() => setInput('Calculate the variance for SLS details')}
                className="bg-white border border-gray-300 rounded-xl p-4 hover:bg-gray-50 transition-colors text-left shadow-sm"
              >
                <h3 className="font-medium text-gray-900">Calculate SLS details variance</h3>
                <p className="text-sm text-gray-500 mt-1">Compare financial data between two dates</p>
              </button>
              <button 
                onClick={() => setInput('How many hours of work left for today?')}
                className="bg-white border border-gray-300 rounded-xl p-4 hover:bg-gray-50 transition-colors text-left shadow-sm"
              >
                <h3 className="font-medium text-gray-900">Time remaining until EOD</h3>
                <p className="text-sm text-gray-500 mt-1">Check hours left before 5PM EST</p>
              </button>
              <button 
                onClick={() => setInput('What is the status of 6G batch process for today?')}
                className="bg-white border border-gray-300 rounded-xl p-4 hover:bg-gray-50 transition-colors text-left shadow-sm"
              >
                <h3 className="font-medium text-gray-900">Check 6G Batch Status</h3>
                <p className="text-sm text-gray-500 mt-1">Get current status of FR2052a (6G) batch process</p>
              </button>
              <button 
                onClick={() => setInput('Can you check if there is a variance in 6G for today?')}
                className="bg-white border border-gray-300 rounded-xl p-4 hover:bg-gray-50 transition-colors text-left shadow-sm"
              >
                <h3 className="font-medium text-gray-900">Analyze 6G Variance</h3>
                <p className="text-sm text-gray-500 mt-1">Check for variances in 6G data across tables</p>
              </button>
            </div>
          </div>
        ) : (
          <TransitionGroup className="space-y-4">
            {messages.map((message, index) => (
              <CSSTransition
                key={index}
                timeout={300}
                classNames="message"
              >
                <ChatMessage message={message} />
              </CSSTransition>
            ))}
          </TransitionGroup>
        )}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-2 max-w-[80%]">
              <div className="flex space-x-2">
                <div className="h-2 w-2 bg-blue-500 rounded-full animate-bounce"></div>
                <div className="h-2 w-2 bg-blue-500 rounded-full animate-bounce delay-100"></div>
                <div className="h-2 w-2 bg-blue-500 rounded-full animate-bounce delay-200"></div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {showDateSelector && (
        <DateSelector onSelect={handleDateSelection} onCancel={() => setShowDateSelector(false)} />
      )}
      
      <div className="border-t border-gray-200 p-4">
        <div className="flex items-end space-x-3">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              className="w-full border border-gray-300 rounded-lg px-4 py-3 pr-12 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-gray-800 bg-gray-50"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message here..."
              rows="2"
              disabled={isLoading || showDateSelector}
            />
            {input.trim() !== '' && (
              <button 
                className="absolute right-3 bottom-3 text-blue-500 hover:text-blue-700 disabled:text-gray-400"
                onClick={handleSendMessage}
                disabled={isLoading || showDateSelector}
              >
                <PaperAirplaneIcon className="h-6 w-6" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ChatInterface;
