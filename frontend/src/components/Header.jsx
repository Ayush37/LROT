// frontend/src/components/Header.jsx
import React from 'react';
import { ChartBarIcon } from '@heroicons/react/24/outline';

function Header() {
  return (
    <header className="bg-gradient-to-r from-indigo-700 to-blue-700 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <ChartBarIcon className="h-8 w-8 text-white" />
            <div className="ml-3">
              <h1 className="text-xl font-semibold text-white">LROT Assistant</h1>
              <p className="text-blue-100 text-sm">AI Chatbot for Financial Analysis</p>
            </div>
          </div>
          <div className="flex space-x-4 items-center">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              <span className="h-2 w-2 mr-1 bg-green-500 rounded-full"></span>
              Online
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;
