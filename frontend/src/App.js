// frontend/src/App.js
import React from 'react';
import ChatInterface from './components/ChatInterface';
import Header from './components/Header';

function App() {
  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <Header />
      <main className="flex-1 overflow-hidden">
        <ChatInterface />
      </main>
    </div>
  );
}

export default App;
