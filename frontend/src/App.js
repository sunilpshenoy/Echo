import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

// Debug environment variables
console.log('Environment variables:', process.env);
console.log('REACT_APP_BACKEND_URL:', process.env.REACT_APP_BACKEND_URL);

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
console.log('BACKEND_URL constant:', BACKEND_URL);

const API = `${BACKEND_URL}/api`;
console.log('API URL:', API);

function App() {
  const [currentView, setCurrentView] = useState('login');
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [chats, setChats] = useState([]);
  const [activeChat, setActiveChat] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [contacts, setContacts] = useState([]);
  const [websocket, setWebsocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const messagesEndRef = useRef(null);

  // Auth state
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [registerForm, setRegisterForm] = useState({ username: '', email: '', password: '', phone: '' });
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showAddContact, setShowAddContact] = useState(false);
  const [contactForm, setContactForm] = useState({ email: '', contact_name: '' });

  // Initialize WebSocket connection
  useEffect(() => {
    if (user && !websocket) {
      const wsUrl = BACKEND_URL.replace('https:', 'wss:').replace('http:', 'ws:');
      const ws = new WebSocket(`${wsUrl}/api/ws/${user.user_id}`);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'new_message') {
          setMessages(prev => [...prev, data.data]);
          // Update chat list
          fetchChats();
        }
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      setWebsocket(ws);
    }
    
    return () => {
      if (websocket) {
        websocket.close();
      }
    };
  }, [user]);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Authentication functions
  const login = async (e) => {
    e.preventDefault();
    console.log('Login form submitted:', loginForm);
    console.log('Backend URL:', BACKEND_URL);
    console.log('API URL:', API);
    try {
      const response = await axios.post(`${API}/login`, loginForm);
      console.log('Login successful:', response.data);
      setToken(response.data.access_token);
      setUser(response.data.user);
      localStorage.setItem('token', response.data.access_token);
      setCurrentView('chat');
      fetchChats();
      fetchContacts();
    } catch (error) {
      console.error('Login error:', error);
      alert('Login failed: ' + (error.response?.data?.detail || error.message));
    }
  };

  const register = async (e) => {
    e.preventDefault();
    console.log('Register form submitted:', registerForm);
    console.log('Backend URL:', BACKEND_URL);
    console.log('API URL:', API);
    try {
      const response = await axios.post(`${API}/register`, registerForm);
      console.log('Registration successful:', response.data);
      setToken(response.data.access_token);
      setUser(response.data.user);
      localStorage.setItem('token', response.data.access_token);
      setCurrentView('chat');
      fetchChats();
      fetchContacts();
    } catch (error) {
      console.error('Registration error:', error);
      alert('Registration failed: ' + (error.response?.data?.detail || error.message));
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    setChats([]);
    setActiveChat(null);
    setMessages([]);
    setContacts([]);
    localStorage.removeItem('token');
    if (websocket) {
      websocket.close();
      setWebsocket(null);
    }
    setCurrentView('login');
  };

  // API functions
  const getAuthHeaders = () => ({
    headers: { Authorization: `Bearer ${token}` }
  });

  const fetchChats = async () => {
    try {
      const response = await axios.get(`${API}/chats`, getAuthHeaders());
      setChats(response.data);
    } catch (error) {
      console.error('Error fetching chats:', error);
    }
  };

  const fetchContacts = async () => {
    try {
      const response = await axios.get(`${API}/contacts`, getAuthHeaders());
      setContacts(response.data);
    } catch (error) {
      console.error('Error fetching contacts:', error);
    }
  };

  const fetchMessages = async (chatId) => {
    try {
      const response = await axios.get(`${API}/chats/${chatId}/messages`, getAuthHeaders());
      setMessages(response.data);
    } catch (error) {
      console.error('Error fetching messages:', error);
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || !activeChat) return;

    try {
      await axios.post(`${API}/chats/${activeChat.chat_id}/messages`, {
        content: newMessage,
        message_type: 'text'
      }, getAuthHeaders());
      
      setNewMessage('');
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  const selectChat = (chat) => {
    setActiveChat(chat);
    fetchMessages(chat.chat_id);
  };

  const createDirectChat = async (contactUserId) => {
    try {
      const response = await axios.post(`${API}/chats`, {
        chat_type: 'direct',
        other_user_id: contactUserId
      }, getAuthHeaders());
      
      fetchChats();
      selectChat(response.data);
    } catch (error) {
      console.error('Error creating chat:', error);
    }
  };

  const searchUsers = async (query) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }
    
    try {
      const response = await axios.get(`${API}/users/search?q=${query}`, getAuthHeaders());
      setSearchResults(response.data);
    } catch (error) {
      console.error('Error searching users:', error);
    }
  };

  const addContact = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/contacts`, contactForm, getAuthHeaders());
      setContactForm({ email: '', contact_name: '' });
      setShowAddContact(false);
      fetchContacts();
      alert('Contact added successfully');
    } catch (error) {
      alert('Error adding contact: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Format timestamp
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Login View
  if (currentView === 'login') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 to-purple-900 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-800 mb-2">ChatApp</h1>
            <p className="text-gray-600">Connect with anyone, anywhere</p>
          </div>
          
          <div className="flex mb-6">
            <button
              onClick={() => setCurrentView('login')}
              className={`flex-1 py-2 px-4 rounded-l-lg font-medium ${
                currentView === 'login' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-200 text-gray-700'
              }`}
            >
              Login
            </button>
            <button
              onClick={() => setCurrentView('register')}
              className={`flex-1 py-2 px-4 rounded-r-lg font-medium ${
                currentView === 'register' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-200 text-gray-700'
              }`}
            >
              Register
            </button>
          </div>

          <form onSubmit={login}>
            <div className="mb-4">
              <input
                type="email"
                placeholder="Email"
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={loginForm.email}
                onChange={(e) => setLoginForm({...loginForm, email: e.target.value})}
                required
              />
            </div>
            <div className="mb-6">
              <input
                type="password"
                placeholder="Password"
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={loginForm.password}
                onChange={(e) => setLoginForm({...loginForm, password: e.target.value})}
                required
              />
            </div>
            <button
              type="submit"
              className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition duration-200"
            >
              Login
            </button>
          </form>
        </div>
      </div>
    );
  }

  // Register View
  if (currentView === 'register') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 to-purple-900 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-800 mb-2">ChatApp</h1>
            <p className="text-gray-600">Create your account</p>
          </div>
          
          <div className="flex mb-6">
            <button
              onClick={() => setCurrentView('login')}
              className={`flex-1 py-2 px-4 rounded-l-lg font-medium ${
                currentView === 'login' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-200 text-gray-700'
              }`}
            >
              Login
            </button>
            <button
              onClick={() => setCurrentView('register')}
              className={`flex-1 py-2 px-4 rounded-r-lg font-medium ${
                currentView === 'register' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-200 text-gray-700'
              }`}
            >
              Register
            </button>
          </div>

          <form onSubmit={register}>
            <div className="mb-4">
              <input
                type="text"
                placeholder="Username"
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={registerForm.username}
                onChange={(e) => setRegisterForm({...registerForm, username: e.target.value})}
                required
              />
            </div>
            <div className="mb-4">
              <input
                type="email"
                placeholder="Email"
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={registerForm.email}
                onChange={(e) => setRegisterForm({...registerForm, email: e.target.value})}
                required
              />
            </div>
            <div className="mb-4">
              <input
                type="tel"
                placeholder="Phone (optional)"
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={registerForm.phone}
                onChange={(e) => setRegisterForm({...registerForm, phone: e.target.value})}
              />
            </div>
            <div className="mb-6">
              <input
                type="password"
                placeholder="Password"
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={registerForm.password}
                onChange={(e) => setRegisterForm({...registerForm, password: e.target.value})}
                required
              />
            </div>
            <button
              type="submit"
              className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition duration-200"
            >
              Register
            </button>
          </form>
        </div>
      </div>
    );
  }

  // Main Chat View
  return (
    <div className="h-screen flex bg-gray-100">
      {/* Sidebar */}
      <div className="w-1/3 bg-white border-r border-gray-200 flex flex-col">
        {/* Header */}
        <div className="p-4 bg-blue-600 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-blue-400 rounded-full flex items-center justify-center">
                <span className="font-bold">{user.username.charAt(0).toUpperCase()}</span>
              </div>
              <div className="ml-3">
                <p className="font-medium">{user.username}</p>
                <p className="text-xs text-blue-200">
                  {isConnected ? 'Online' : 'Connecting...'}
                </p>
              </div>
            </div>
            <button
              onClick={logout}
              className="text-blue-200 hover:text-white"
              title="Logout"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="p-3">
          <input
            type="text"
            placeholder="Search chats or add new contact..."
            className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              searchUsers(e.target.value);
            }}
          />
          {searchResults.length > 0 && (
            <div className="mt-2 bg-white border border-gray-200 rounded-lg shadow-lg">
              {searchResults.map(searchUser => (
                <div
                  key={searchUser.user_id}
                  className="p-2 hover:bg-gray-50 cursor-pointer border-b last:border-b-0"
                  onClick={() => createDirectChat(searchUser.user_id)}
                >
                  <div className="flex items-center">
                    <div className="w-8 h-8 bg-gray-400 rounded-full flex items-center justify-center">
                      <span className="text-white text-sm">{searchUser.username.charAt(0).toUpperCase()}</span>
                    </div>
                    <div className="ml-2">
                      <p className="font-medium text-sm">{searchUser.username}</p>
                      <p className="text-xs text-gray-500">{searchUser.email}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Action buttons */}
        <div className="px-3 pb-3 flex space-x-2">
          <button
            onClick={() => setShowAddContact(!showAddContact)}
            className="flex-1 bg-green-600 text-white py-2 px-3 rounded-lg text-sm hover:bg-green-700"
          >
            Add Contact
          </button>
        </div>

        {/* Add Contact Form */}
        {showAddContact && (
          <div className="mx-3 mb-3 p-3 bg-gray-50 rounded-lg">
            <form onSubmit={addContact}>
              <input
                type="email"
                placeholder="Contact Email"
                className="w-full p-2 mb-2 border border-gray-300 rounded text-sm"
                value={contactForm.email}
                onChange={(e) => setContactForm({...contactForm, email: e.target.value})}
                required
              />
              <input
                type="text"
                placeholder="Contact Name (optional)"
                className="w-full p-2 mb-2 border border-gray-300 rounded text-sm"
                value={contactForm.contact_name}
                onChange={(e) => setContactForm({...contactForm, contact_name: e.target.value})}
              />
              <div className="flex space-x-2">
                <button
                  type="submit"
                  className="flex-1 bg-blue-600 text-white py-1 px-2 rounded text-sm hover:bg-blue-700"
                >
                  Add
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddContact(false)}
                  className="flex-1 bg-gray-400 text-white py-1 px-2 rounded text-sm hover:bg-gray-500"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Chats List */}
        <div className="flex-1 overflow-y-auto">
          {chats.length === 0 ? (
            <div className="p-4 text-center text-gray-500">
              <p>No chats yet</p>
              <p className="text-sm">Search for users above to start chatting</p>
            </div>
          ) : (
            chats.map(chat => (
              <div
                key={chat.chat_id}
                className={`p-3 border-b border-gray-100 cursor-pointer hover:bg-gray-50 ${
                  activeChat?.chat_id === chat.chat_id ? 'bg-blue-50 border-blue-200' : ''
                }`}
                onClick={() => selectChat(chat)}
              >
                <div className="flex items-center">
                  <div className="w-12 h-12 bg-gray-400 rounded-full flex items-center justify-center">
                    <span className="text-white font-medium">
                      {chat.chat_type === 'direct' 
                        ? chat.other_user?.username?.charAt(0).toUpperCase() || '?'
                        : chat.name?.charAt(0).toUpperCase() || 'G'
                      }
                    </span>
                  </div>
                  <div className="ml-3 flex-1">
                    <div className="flex items-center justify-between">
                      <p className="font-medium">
                        {chat.chat_type === 'direct' 
                          ? chat.other_user?.username || 'Unknown User'
                          : chat.name
                        }
                      </p>
                      {chat.last_message && (
                        <span className="text-xs text-gray-500">
                          {formatTime(chat.last_message.timestamp)}
                        </span>
                      )}
                    </div>
                    {chat.last_message && (
                      <p className="text-sm text-gray-600 truncate">
                        {chat.last_message.content}
                      </p>
                    )}
                    {chat.chat_type === 'direct' && chat.other_user?.is_online && (
                      <span className="text-xs text-green-500">Online</span>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {activeChat ? (
          <>
            {/* Chat Header */}
            <div className="p-4 bg-white border-b border-gray-200">
              <div className="flex items-center">
                <div className="w-10 h-10 bg-gray-400 rounded-full flex items-center justify-center">
                  <span className="text-white font-medium">
                    {activeChat.chat_type === 'direct' 
                      ? activeChat.other_user?.username?.charAt(0).toUpperCase() || '?'
                      : activeChat.name?.charAt(0).toUpperCase() || 'G'
                    }
                  </span>
                </div>
                <div className="ml-3">
                  <p className="font-medium">
                    {activeChat.chat_type === 'direct' 
                      ? activeChat.other_user?.username || 'Unknown User'
                      : activeChat.name
                    }
                  </p>
                  {activeChat.chat_type === 'direct' && (
                    <p className="text-sm text-gray-500">
                      {activeChat.other_user?.is_online ? 'Online' : 'Offline'}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map(message => (
                <div
                  key={message.message_id}
                  className={`flex ${message.sender_id === user.user_id ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                      message.sender_id === user.user_id
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-200 text-gray-800'
                    }`}
                  >
                    {message.sender_id !== user.user_id && (
                      <p className="text-xs font-medium mb-1">{message.sender_name}</p>
                    )}
                    <p>{message.content}</p>
                    <p className={`text-xs mt-1 ${
                      message.sender_id === user.user_id ? 'text-blue-200' : 'text-gray-500'
                    }`}>
                      {formatTime(message.timestamp)}
                    </p>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Message Input */}
            <div className="p-4 bg-white border-t border-gray-200">
              <form onSubmit={sendMessage} className="flex space-x-2">
                <input
                  type="text"
                  placeholder="Type a message..."
                  className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                />
                <button
                  type="submit"
                  className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition duration-200"
                >
                  Send
                </button>
              </form>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center bg-gray-50">
            <div className="text-center">
              <div className="w-20 h-20 bg-gray-300 rounded-full mx-auto mb-4 flex items-center justify-center">
                <svg className="w-10 h-10 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <h3 className="text-xl font-medium text-gray-800 mb-2">Welcome to ChatApp</h3>
              <p className="text-gray-600">Select a chat to start messaging</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;