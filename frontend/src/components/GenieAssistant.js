import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

// Simple speech recognition polyfill for better browser support
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const SpeechSynthesis = window.speechSynthesis;

const GenieAssistant = ({ user, token, onAction }) => {
  const [isVisible, setIsVisible] = useState(true);
  const [isExpanded, setIsExpanded] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [responseMode, setResponseMode] = useState('both'); // 'text', 'voice', 'both'
  const [pendingAction, setPendingAction] = useState(null);
  const [showPreferences, setShowPreferences] = useState(false);
  
  const recognitionRef = useRef(null);
  const messagesEndRef = useRef(null);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
  const API = `${BACKEND_URL}/api`;

  useEffect(() => {
    // Initialize with welcome message
    addGenieMessage("🧞‍♂️ *Poof!* Your wish is my command! I'm your personal genie assistant. How would you like me to respond to you?", true);
    setShowPreferences(true);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const addGenieMessage = (text, isWelcome = false) => {
    const message = {
      id: Date.now(),
      type: 'genie',
      text,
      timestamp: new Date().toLocaleTimeString(),
      isWelcome
    };
    setMessages(prev => [...prev, message]);
    
    // Speak if voice mode is enabled and not welcome message
    if ((responseMode === 'voice' || responseMode === 'both') && !isWelcome && SpeechSynthesis) {
      const utterance = new SpeechSynthesisUtterance(text.replace(/🧞‍♂️|\*[^*]*\*/g, ''));
      utterance.rate = 0.9;
      utterance.pitch = 1.1;
      SpeechSynthesis.speak(utterance);
    }
  };

  const addUserMessage = (text) => {
    const message = {
      id: Date.now(),
      type: 'user',
      text,
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, message]);
  };

  const processCommand = async (command) => {
    setIsProcessing(true);
    addUserMessage(command);

    try {
      const response = await axios.post(`${API}/genie/process`, {
        command: command.toLowerCase(),
        user_id: user?.user_id,
        current_context: getCurrentContext()
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const { intent, response_text, action, confirmation_needed } = response.data;

      if (confirmation_needed && action) {
        setPendingAction(action);
        addGenieMessage(`🧞‍♂️ ${response_text} Shall I proceed? Say "yes" or "confirm" to continue, or "no" to cancel.`);
      } else if (action) {
        await executeAction(action);
        addGenieMessage(`🧞‍♂️ ${response_text}`);
      } else {
        addGenieMessage(`🧞‍♂️ ${response_text}`);
      }
    } catch (error) {
      console.error('Error processing command:', error);
      addGenieMessage("🧞‍♂️ *Mystical interference detected!* I couldn't process that command. Could you try rephrasing your wish?");
    } finally {
      setIsProcessing(false);
    }
  };

  const executeAction = async (action) => {
    try {
      if (onAction) {
        const result = await onAction(action);
        if (result?.success) {
          // Log action for potential reversal
          logAction(action, result);
        }
        return result;
      }
    } catch (error) {
      console.error('Error executing action:', error);
      throw error;
    }
  };

  const logAction = (action, result) => {
    const actionLog = {
      id: Date.now(),
      action,
      result,
      timestamp: new Date(),
      user_id: user?.user_id
    };
    
    // Store in localStorage for reversal capability
    const existingLogs = JSON.parse(localStorage.getItem('genie_actions') || '[]');
    existingLogs.push(actionLog);
    // Keep only last 50 actions
    if (existingLogs.length > 50) {
      existingLogs.shift();
    }
    localStorage.setItem('genie_actions', JSON.stringify(existingLogs));
  };

  const getCurrentContext = () => {
    return {
      current_page: window.location.pathname,
      timestamp: new Date().toISOString()
    };
  };

  const handleSpeechRecognition = () => {
    if (!SpeechRecognition) {
      addGenieMessage("🧞‍♂️ *Ancient magic detected!* Your browser doesn't support voice commands. Please type your wish instead.");
      return;
    }

    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognitionRef.current = recognition;
    
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setInputText(transcript);
      setIsListening(false);
      
      // Auto-process voice commands
      if (transcript.trim()) {
        processCommand(transcript);
        setInputText('');
      }
    };

    recognition.onerror = (event) => {
      setIsListening(false);
      addGenieMessage("🧞‍♂️ *Whispers got lost in the wind!* I couldn't hear you clearly. Please try again.");
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputText.trim() || isProcessing) return;

    const command = inputText.trim();
    setInputText('');

    // Handle confirmation for pending actions
    if (pendingAction) {
      if (['yes', 'confirm', 'ok', 'proceed', 'do it'].includes(command.toLowerCase())) {
        executeAction(pendingAction);
        addGenieMessage("🧞‍♂️ *Snapping fingers* ✨ Your wish has been granted!");
        setPendingAction(null);
        return;
      } else if (['no', 'cancel', 'stop', 'never mind'].includes(command.toLowerCase())) {
        addGenieMessage("🧞‍♂️ *Nods wisely* As you wish! Your command has been cancelled.");
        setPendingAction(null);
        return;
      }
    }

    processCommand(command);
  };

  const handlePreferenceSelect = (mode) => {
    setResponseMode(mode);
    setShowPreferences(false);
    
    const modeText = {
      'text': 'text messages only',
      'voice': 'voice responses only', 
      'both': 'both text and voice'
    };
    
    addGenieMessage(`🧞‍♂️ *Magical adjustment complete!* I'll now respond with ${modeText[mode]}. What can I help you with today?`);
  };

  if (!isVisible) {
    return (
      <button
        onClick={() => setIsVisible(true)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-gradient-to-br from-purple-600 via-blue-600 to-purple-800 rounded-full shadow-2xl hover:shadow-purple-500/25 hover:scale-110 transition-all duration-300 z-50 flex items-center justify-center animate-pulse"
        title="Summon Genie Assistant"
      >
        <span className="text-2xl">🪔</span>
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {/* Floating Assistant */}
      {!isExpanded && (
        <div className="relative">
          <button
            onClick={() => setIsExpanded(true)}
            className="w-16 h-16 bg-gradient-to-br from-purple-600 via-blue-600 to-purple-800 rounded-full shadow-2xl hover:shadow-purple-500/25 hover:scale-110 transition-all duration-300 flex items-center justify-center animate-bounce"
            title="Chat with Genie"
          >
            <span className="text-3xl">🧞‍♂️</span>
          </button>
          
          {/* Minimize button */}
          <button
            onClick={() => setIsVisible(false)}
            className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full text-xs hover:bg-red-600 transition-colors"
            title="Hide Genie"
          >
            ✕
          </button>
        </div>
      )}

      {/* Expanded Chat Interface */}
      {isExpanded && (
        <div className="w-80 h-96 bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 rounded-2xl shadow-2xl border border-purple-500/30 overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-purple-600 to-blue-600 p-4 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="text-2xl">🧞‍♂️</span>
              <div>
                <h3 className="text-white font-semibold">Genie Assistant</h3>
                <p className="text-purple-200 text-xs">Your wish is my command!</p>
              </div>
            </div>
            <div className="flex space-x-1">
              <button
                onClick={() => setIsExpanded(false)}
                className="w-6 h-6 bg-white/20 text-white rounded-full text-xs hover:bg-white/30 transition-colors"
                title="Minimize"
              >
                −
              </button>
              <button
                onClick={() => setIsVisible(false)}
                className="w-6 h-6 bg-red-500/80 text-white rounded-full text-xs hover:bg-red-500 transition-colors"
                title="Hide"
              >
                ✕
              </button>
            </div>
          </div>

          {/* Preferences Modal */}
          {showPreferences && (
            <div className="absolute inset-0 bg-black/50 flex items-center justify-center z-10">
              <div className="bg-white rounded-xl p-6 m-4 max-w-sm">
                <h4 className="font-semibold mb-4 text-gray-800">How should I respond?</h4>
                <div className="space-y-2">
                  <button
                    onClick={() => handlePreferenceSelect('text')}
                    className="w-full p-3 text-left bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
                  >
                    💬 Text messages only
                  </button>
                  <button
                    onClick={() => handlePreferenceSelect('voice')}
                    className="w-full p-3 text-left bg-green-50 hover:bg-green-100 rounded-lg transition-colors"
                  >
                    🎤 Voice responses only
                  </button>
                  <button
                    onClick={() => handlePreferenceSelect('both')}
                    className="w-full p-3 text-left bg-purple-50 hover:bg-purple-100 rounded-lg transition-colors"
                  >
                    🎯 Both text and voice
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Messages */}
          <div className="flex-1 p-4 overflow-y-auto h-64 space-y-3">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] p-3 rounded-xl ${
                    message.type === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white/90 text-gray-800'
                  }`}
                >
                  <p className="text-sm">{message.text}</p>
                  <p className="text-xs opacity-70 mt-1">{message.timestamp}</p>
                </div>
              </div>
            ))}
            {isProcessing && (
              <div className="flex justify-start">
                <div className="bg-white/90 text-gray-800 p-3 rounded-xl">
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin w-4 h-4 border-2 border-purple-600 border-t-transparent rounded-full"></div>
                    <span className="text-sm">Genie is thinking...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-purple-500/30 p-4">
            <form onSubmit={handleSubmit} className="flex space-x-2">
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Type your wish..."
                className="flex-1 px-3 py-2 border border-purple-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm"
                disabled={isProcessing}
              />
              <button
                type="button"
                onClick={handleSpeechRecognition}
                className={`p-2 rounded-lg transition-all duration-200 ${
                  isListening
                    ? 'bg-red-500 text-white animate-pulse'
                    : 'bg-purple-600 text-white hover:bg-purple-700'
                }`}
                disabled={isProcessing}
                title={isListening ? 'Stop listening' : 'Voice command'}
              >
                🎤
              </button>
              <button
                type="submit"
                className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                disabled={isProcessing || !inputText.trim()}
              >
                ✨
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default GenieAssistant;