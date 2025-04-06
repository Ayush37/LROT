// frontend/src/services/api.js
import axios from 'axios';

// Configure axios with more debugging
const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for debugging
apiClient.interceptors.request.use(request => {
  console.log('Starting Request', request);
  return request;
});

// Add response interceptor for debugging
apiClient.interceptors.response.use(
  response => {
    console.log('Response:', response);
    return response;
  },
  error => {
    console.error('Response Error:', error);
    return Promise.reject(error);
  }
);

export const sendMessage = async (message, history = []) => {
  try {
    console.log(`Sending message to ${apiClient.defaults.baseURL}/api/chat`);
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
