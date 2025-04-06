// frontend/src/services/api.js
import axios from 'axios';

// Configure axios
const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const sendMessage = async (message, history = []) => {
  try {
    const response = await apiClient.post('/api/chat', { message, history });
    return response.data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

export const executeFunction = async (functionName, args) => {
  try {
    const response = await apiClient.post('/api/function', { name: functionName, args });
    return response.data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};
