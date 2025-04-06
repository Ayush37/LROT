// frontend/src/App.js
import React from 'react';
import './styles/App.css';
import ChatInterface from './components/ChatInterface';
import Header from './components/Header';

function App() {
  return (
    <div className="App">
      <Header />
      <main className="App-main">
        <ChatInterface />
      </main>
    </div>
  );
}

export default App;
