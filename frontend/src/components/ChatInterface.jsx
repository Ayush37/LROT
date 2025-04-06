// In frontend/src/components/ChatInterface.jsx
// Update the handleSendMessage function

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
    console.log("Sending message to backend:", userMessage);
    
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
    console.log("Making API request to:", '/api/chat');
    const response = await axios.post('/api/chat', {
      message: userMessage,
      history: messages.map(msg => ({
        user: msg.type === 'user' ? msg.content : '',
        assistant: msg.type === 'assistant' ? msg.content : ''
      })).filter(entry => entry.user || entry.assistant)
    });
    
    console.log("Received response:", response.data);
    
    // Add response to chat
    setMessages(prevMessages => [...prevMessages, { 
      type: 'assistant', 
      content: response.data.response.content,
      data: response.data.response.function_call ? response.data.response : null
    }]);
    
  } catch (error) {
    console.error('Error details:', error);
    if (error.response) {
      console.error('Response data:', error.response.data);
      console.error('Response status:', error.response.status);
    }
    
    // Add error message to chat
    setMessages(prevMessages => [...prevMessages, { 
      type: 'assistant', 
      content: 'Sorry, there was an error processing your request. Please try again.' 
    }]);
  }
  
  setIsLoading(false);
};
