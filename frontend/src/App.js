import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import EmojiPicker from 'emoji-picker-react';
import Peer from 'simple-peer';
import io from 'socket.io-client';
import Webcam from 'react-webcam';
import MicRecorder from 'mic-recorder-to-mp3';
import GenieAssistant from './components/GenieAssistant';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Initialize audio recorder
const Mp3Recorder = new MicRecorder({ bitRate: 128 });

function App() {
  const [currentView, setCurrentView] = useState('login');
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  
  // Simplified version for testing
  const handleGenieAction = async (action) => {
    console.log("Genie action:", action);
    return { success: true, message: "Action handled" };
  };
  
  // Return the JSX
  return (
    <div className="h-screen flex bg-gradient-to-br from-gray-50 to-blue-50">
      {currentView === 'login' && (
        <div className="login-container">
          <h1>Login Page</h1>
        </div>
      )}
      
      {currentView === 'chat' && (
        <div className="chat-container">
          <h1>Chat Page</h1>
        </div>
      )}
      
      {user && (
        <GenieAssistant 
          user={user} 
          token={token} 
          onAction={handleGenieAction}
        />
      )}
    </div>
  );
}

export default App;
