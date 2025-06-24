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
  const fileInputRef = useRef(null);

  // Auth state
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [registerForm, setRegisterForm] = useState({ username: '', email: '', password: '', phone: '' });
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showAddContact, setShowAddContact] = useState(false);
  const [contactForm, setContactForm] = useState({ email: '', contact_name: '' });
  
  // Group chat state
  const [showCreateGroup, setShowCreateGroup] = useState(false);
  const [groupForm, setGroupForm] = useState({ name: '', description: '', members: [] });
  const [selectedMembers, setSelectedMembers] = useState([]);
  
  // File upload state
  const [uploadingFile, setUploadingFile] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  
  // Blocking and reporting state
  const [blockedUsers, setBlockedUsers] = useState([]);
  const [showBlockedUsers, setShowBlockedUsers] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);
  const [reportForm, setReportForm] = useState({
    user_id: '',
    reason: '',
    description: '',
    message_id: null,
    chat_id: null
  });

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
        } else if (data.type === 'message_read') {
          // Update read status
          setMessages(prev => prev.map(msg => 
            msg.message_id === data.data.message_id 
              ? { ...msg, read_status: 'read' }
              : msg
          ));
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
  
  // Debug effect to monitor view changes
  useEffect(() => {
    console.log('Current view changed to:', currentView);
    
    if (currentView === 'chat') {
      console.log('Loading chat view with token:', token);
      console.log('User data:', user);
    }
  }, [currentView, token, user]);

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
      console.log('Making login API call to:', `${API}/login`);
      const response = await axios.post(`${API}/login`, loginForm);
      console.log('Login successful:', response.data);
      
      const { access_token, user } = response.data;
      
      // Update state
      setToken(access_token);
      setUser(user);
      localStorage.setItem('token', access_token);
      
      console.log('Token and user set, now switching to chat view...');
      setCurrentView('chat');
      
      // Fetch data after view change
      setTimeout(() => {
        fetchChats(access_token);
        fetchContacts(access_token);
        fetchBlockedUsers(access_token);
      }, 100);
      
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
      console.log('Making register API call to:', `${API}/register`);
      const response = await axios.post(`${API}/register`, registerForm);
      console.log('Registration successful:', response.data);
      
      const { access_token, user } = response.data;
      
      // Update state
      setToken(access_token);
      setUser(user);
      localStorage.setItem('token', access_token);
      
      console.log('Token and user set, now switching to chat view...');
      setCurrentView('chat');
      
      // Fetch data after view change
      setTimeout(() => {
        fetchChats(access_token);
        fetchContacts(access_token);
        fetchBlockedUsers(access_token);
      }, 100);
      
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
    setBlockedUsers([]);
    localStorage.removeItem('token');
    if (websocket) {
      websocket.close();
      setWebsocket(null);
    }
    setCurrentView('login');
  };

  // API functions
  const getAuthHeaders = (authToken = null) => ({
    headers: { Authorization: `Bearer ${authToken || token}` }
  });

  const fetchChats = async (authToken = null) => {
    try {
      console.log('Fetching chats with token:', authToken || token);
      const response = await axios.get(`${API}/chats`, getAuthHeaders(authToken));
      console.log('Chats fetched successfully:', response.data);
      setChats(response.data);
    } catch (error) {
      console.error('Error fetching chats:', error);
      if (error.response?.status === 401) {
        console.error('Unauthorized - token might be invalid');
      }
    }
  };

  const fetchContacts = async (authToken = null) => {
    try {
      console.log('Fetching contacts with token:', authToken || token);
      const response = await axios.get(`${API}/contacts`, getAuthHeaders(authToken));
      console.log('Contacts fetched successfully:', response.data);
      setContacts(response.data);
    } catch (error) {
      console.error('Error fetching contacts:', error);
      if (error.response?.status === 401) {
        console.error('Unauthorized - token might be invalid');
      }
    }
  };

  const fetchBlockedUsers = async (authToken = null) => {
    try {
      const response = await axios.get(`${API}/users/blocked`, getAuthHeaders(authToken));
      setBlockedUsers(response.data);
    } catch (error) {
      console.error('Error fetching blocked users:', error);
    }
  };

  const fetchMessages = async (chatId) => {
    try {
      console.log('Fetching messages for chat:', chatId, 'with token:', token);
      const response = await axios.get(`${API}/chats/${chatId}/messages`, getAuthHeaders());
      console.log('Messages fetched successfully:', response.data);
      setMessages(response.data);
      
      // Mark messages as read
      const unreadMessages = response.data.filter(msg => 
        msg.sender_id !== user.user_id && msg.read_status === 'unread'
      );
      
      if (unreadMessages.length > 0) {
        markMessagesRead(unreadMessages.map(msg => msg.message_id));
      }
    } catch (error) {
      console.error('Error fetching messages:', error);
      if (error.response?.status === 401) {
        console.error('Unauthorized - token might be invalid');
      }
    }
  };

  const markMessagesRead = async (messageIds) => {
    try {
      await axios.post(`${API}/messages/read`, {
        message_ids: messageIds
      }, getAuthHeaders());
    } catch (error) {
      console.error('Error marking messages as read:', error);
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || !activeChat) return;

    try {
      console.log('Sending message:', newMessage, 'to chat:', activeChat.chat_id);
      await axios.post(`${API}/chats/${activeChat.chat_id}/messages`, {
        content: newMessage,
        message_type: 'text'
      }, getAuthHeaders());
      
      setNewMessage('');
      console.log('Message sent successfully');
    } catch (error) {
      console.error('Error sending message:', error);
      if (error.response?.status === 403) {
        alert('Cannot send message to blocked user');
      } else if (error.response?.status === 401) {
        console.error('Unauthorized - token might be invalid');
      }
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
      if (error.response?.status === 403) {
        alert('Cannot create chat with blocked user');
      }
    }
  };

  const createGroupChat = async (e) => {
    e.preventDefault();
    if (!groupForm.name.trim() || selectedMembers.length === 0) {
      alert('Please enter a group name and select at least one member');
      return;
    }

    try {
      const response = await axios.post(`${API}/chats/group`, {
        name: groupForm.name,
        description: groupForm.description,
        members: selectedMembers.map(m => m.user_id)
      }, getAuthHeaders());
      
      setGroupForm({ name: '', description: '', members: [] });
      setSelectedMembers([]);
      setShowCreateGroup(false);
      fetchChats();
      selectChat(response.data);
    } catch (error) {
      console.error('Error creating group:', error);
      alert('Error creating group: ' + (error.response?.data?.detail || error.message));
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

  // Blocking and reporting functions
  const blockUser = async (userId, reason = null) => {
    try {
      await axios.post(`${API}/users/block`, {
        user_id: userId,
        reason: reason
      }, getAuthHeaders());
      
      alert('User blocked successfully');
      fetchBlockedUsers();
      fetchChats(); // Refresh chats to update block status
      fetchContacts(); // Refresh contacts to update block status
    } catch (error) {
      alert('Error blocking user: ' + (error.response?.data?.detail || error.message));
    }
  };

  const unblockUser = async (userId) => {
    try {
      await axios.delete(`${API}/users/block/${userId}`, getAuthHeaders());
      alert('User unblocked successfully');
      fetchBlockedUsers();
      fetchChats(); // Refresh chats to update block status
      fetchContacts(); // Refresh contacts to update block status
    } catch (error) {
      alert('Error unblocking user: ' + (error.response?.data?.detail || error.message));
    }
  };

  const reportUser = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/users/report`, reportForm, getAuthHeaders());
      alert('Report submitted successfully');
      setShowReportModal(false);
      setReportForm({
        user_id: '',
        reason: '',
        description: '',
        message_id: null,
        chat_id: null
      });
    } catch (error) {
      alert('Error submitting report: ' + (error.response?.data?.detail || error.message));
    }
  };

  // File upload functions
  const handleFileSelect = async (file) => {
    if (!file || !activeChat) return;

    setUploadingFile(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const uploadResponse = await axios.post(`${API}/upload`, formData, {
        ...getAuthHeaders(),
        headers: {
          ...getAuthHeaders().headers,
          'Content-Type': 'multipart/form-data',
        },
      });

      // Send message with file
      await axios.post(`${API}/chats/${activeChat.chat_id}/messages`, {
        content: file.name,
        message_type: file.type.startsWith('image/') ? 'image' : 'file',
        file_name: uploadResponse.data.file_name,
        file_size: uploadResponse.data.file_size,
        file_data: uploadResponse.data.file_data
      }, getAuthHeaders());

      console.log('File sent successfully');
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Error uploading file: ' + (error.response?.data?.detail || error.message));
    } finally {
      setUploadingFile(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  // Format timestamp
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Render message status icon
  const renderMessageStatus = (message) => {
    if (message.sender_id !== user.user_id) return null;
    
    if (message.read_status === 'read') {
      return <span className="text-blue-400 ml-1">✓✓</span>;
    } else {
      return <span className="text-gray-400 ml-1">✓✓</span>;
    }
  };

  // Render file message
  const renderFileMessage = (message) => {
    if (message.message_type === 'image' && message.file_data) {
      return (
        <div>
          <img 
            src={`data:image/jpeg;base64,${message.file_data}`}
            alt={message.file_name}
            className="max-w-xs max-h-64 rounded-lg cursor-pointer"
            onClick={() => window.open(`data:image/jpeg;base64,${message.file_data}`, '_blank')}
          />
          <p className="text-sm mt-1">{message.file_name}</p>
        </div>
      );
    } else if (message.message_type === 'file') {
      return (
        <div className="flex items-center bg-gray-100 p-2 rounded">
          <span className="text-2xl mr-2">📎</span>
          <div>
            <p className="font-medium">{message.file_name}</p>
            <p className="text-sm text-gray-500">
              {message.file_size ? `${(message.file_size / 1024).toFixed(1)} KB` : 'File'}
            </p>
          </div>
        </div>
      );
    }
    
    // Handle encrypted messages
    if (message.is_encrypted && message.content === '[Encrypted Message]') {
      return (
        <div className="flex items-center text-gray-500">
          <span className="mr-2">🔒</span>
          <p className="italic">This message is encrypted</p>
        </div>
      );
    }
    
    return <p>{message.content}</p>;
  };

  // Login View
  if (currentView === 'login') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 to-purple-900 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-800 mb-2">
              ChatApp Pro 
              <span className="text-lg ml-2">🔒</span>
            </h1>
            <p className="text-gray-600">Secure messaging with end-to-end encryption</p>
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
                name="email"
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
                name="password"
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
          
          {/* Test API Connection Button */}
          <div className="mt-4">
            <button
              onClick={async () => {
                console.log('Testing API connection...');
                try {
                  console.log('API URL:', `${API}/test-connection`);
                  const response = await fetch(`${API}/test-connection`);
                  console.log('Response status:', response.status);
                  const data = await response.text();
                  console.log('Response data:', data);
                  alert(`API Connection Test: ${response.status} ${data}`);
                } catch (error) {
                  console.error('API connection test error:', error);
                  alert(`API Connection Test Error: ${error.message}`);
                }
              }}
              className="w-full mt-2 bg-gray-200 text-gray-700 py-2 rounded-lg font-medium hover:bg-gray-300 transition duration-200"
            >
              Test API Connection
            </button>
          </div>
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
            <h1 className="text-3xl font-bold text-gray-800 mb-2">
              ChatApp Pro 
              <span className="text-lg ml-2">🔒</span>
            </h1>
            <p className="text-gray-600">Create your secure account</p>
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
                name="username"
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
                name="email"
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
                name="phone"
                placeholder="Phone (optional)"
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={registerForm.phone}
                onChange={(e) => setRegisterForm({...registerForm, phone: e.target.value})}
              />
            </div>
            <div className="mb-6">
              <input
                type="password"
                name="password"
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
                <p className="font-medium">{user.username} 🔒</p>
                <p className="text-xs text-blue-200">
                  {isConnected ? 'Online • Encrypted' : 'Connecting...'}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowBlockedUsers(!showBlockedUsers)}
                className="text-blue-200 hover:text-white p-1 rounded"
                title="Blocked Users"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L18.364 5.636" />
                </svg>
              </button>
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
        </div>

        {/* Blocked Users Panel */}
        {showBlockedUsers && (
          <div className="p-3 bg-red-50 border-b">
            <h3 className="font-medium text-red-800 mb-2">Blocked Users ({blockedUsers.length})</h3>
            {blockedUsers.length === 0 ? (
              <p className="text-sm text-red-600">No blocked users</p>
            ) : (
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {blockedUsers.map(block => (
                  <div key={block.block_id} className="flex items-center justify-between bg-white p-2 rounded">
                    <span className="text-sm">{block.blocked_user?.username || 'Unknown User'}</span>
                    <button
                      onClick={() => unblockUser(block.blocked_id)}
                      className="text-xs bg-green-600 text-white px-2 py-1 rounded hover:bg-green-700"
                    >
                      Unblock
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

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
                  className="p-2 hover:bg-gray-50 cursor-pointer border-b last:border-b-0 flex items-center justify-between"
                >
                  <div className="flex items-center" onClick={() => !searchUser.is_blocked && createDirectChat(searchUser.user_id)}>
                    <div className="w-8 h-8 bg-gray-400 rounded-full flex items-center justify-center">
                      <span className="text-white text-sm">{searchUser.username.charAt(0).toUpperCase()}</span>
                    </div>
                    <div className="ml-2">
                      <p className={`font-medium text-sm ${searchUser.is_blocked ? 'text-red-500' : ''}`}>
                        {searchUser.username} {searchUser.is_blocked ? '(Blocked)' : ''}
                      </p>
                      <p className="text-xs text-gray-500">{searchUser.email}</p>
                      <p className="text-xs text-blue-500">{searchUser.status_message}</p>
                    </div>
                  </div>
                  <div className="flex space-x-1">
                    {!searchUser.is_blocked ? (
                      <>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedMembers(prev => {
                              const exists = prev.find(m => m.user_id === searchUser.user_id);
                              if (exists) {
                                return prev.filter(m => m.user_id !== searchUser.user_id);
                              } else {
                                return [...prev, searchUser];
                              }
                            });
                          }}
                          className={`px-2 py-1 rounded text-xs ${
                            selectedMembers.find(m => m.user_id === searchUser.user_id)
                              ? 'bg-green-500 text-white'
                              : 'bg-gray-200 text-gray-700'
                          }`}
                        >
                          {selectedMembers.find(m => m.user_id === searchUser.user_id) ? 'Added' : 'Add'}
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            blockUser(searchUser.user_id, 'Blocked from search');
                          }}
                          className="px-2 py-1 rounded text-xs bg-red-500 text-white hover:bg-red-600"
                        >
                          Block
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setReportForm({ ...reportForm, user_id: searchUser.user_id });
                            setShowReportModal(true);
                          }}
                          className="px-2 py-1 rounded text-xs bg-yellow-500 text-white hover:bg-yellow-600"
                        >
                          Report
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          unblockUser(searchUser.user_id);
                        }}
                        className="px-2 py-1 rounded text-xs bg-green-500 text-white hover:bg-green-600"
                      >
                        Unblock
                      </button>
                    )}
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
          <button
            onClick={() => setShowCreateGroup(!showCreateGroup)}
            className="flex-1 bg-purple-600 text-white py-2 px-3 rounded-lg text-sm hover:bg-purple-700"
          >
            Create Group
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

        {/* Create Group Form */}
        {showCreateGroup && (
          <div className="mx-3 mb-3 p-3 bg-purple-50 rounded-lg">
            <form onSubmit={createGroupChat}>
              <input
                type="text"
                placeholder="Group Name"
                className="w-full p-2 mb-2 border border-gray-300 rounded text-sm"
                value={groupForm.name}
                onChange={(e) => setGroupForm({...groupForm, name: e.target.value})}
                required
              />
              <input
                type="text"
                placeholder="Group Description (optional)"
                className="w-full p-2 mb-2 border border-gray-300 rounded text-sm"
                value={groupForm.description}
                onChange={(e) => setGroupForm({...groupForm, description: e.target.value})}
              />
              {selectedMembers.length > 0 && (
                <div className="mb-2">
                  <p className="text-xs text-gray-600 mb-1">Selected Members:</p>
                  <div className="flex flex-wrap gap-1">
                    {selectedMembers.map(member => (
                      <span key={member.user_id} className="bg-purple-200 text-purple-800 px-2 py-1 rounded text-xs">
                        {member.username}
                        <button
                          onClick={() => setSelectedMembers(prev => prev.filter(m => m.user_id !== member.user_id))}
                          className="ml-1 text-purple-600 hover:text-purple-800"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                </div>
              )}
              <div className="flex space-x-2">
                <button
                  type="submit"
                  className="flex-1 bg-purple-600 text-white py-1 px-2 rounded text-sm hover:bg-purple-700"
                  disabled={selectedMembers.length === 0}
                >
                  Create
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateGroup(false);
                    setSelectedMembers([]);
                    setGroupForm({ name: '', description: '', members: [] });
                  }}
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
                } ${chat.other_user?.is_blocked ? 'opacity-50' : ''}`}
                onClick={() => selectChat(chat)}
              >
                <div className="flex items-center">
                  <div className="w-12 h-12 bg-gray-400 rounded-full flex items-center justify-center relative">
                    <span className="text-white font-medium">
                      {chat.chat_type === 'direct' 
                        ? chat.other_user?.username?.charAt(0).toUpperCase() || '?'
                        : chat.name?.charAt(0).toUpperCase() || 'G'
                      }
                    </span>
                    {chat.other_user?.is_blocked && (
                      <div className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full flex items-center justify-center">
                        <span className="text-white text-xs">!</span>
                      </div>
                    )}
                  </div>
                  <div className="ml-3 flex-1">
                    <div className="flex items-center justify-between">
                      <p className={`font-medium ${chat.other_user?.is_blocked ? 'text-red-500' : ''}`}>
                        {chat.chat_type === 'direct' 
                          ? (chat.other_user?.username || 'Unknown User') + (chat.other_user?.is_blocked ? ' (Blocked)' : '')
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
                        🔒 {chat.last_message.content}
                      </p>
                    )}
                    {chat.chat_type === 'direct' && chat.other_user?.is_online && !chat.other_user?.is_blocked && (
                      <span className="text-xs text-green-500">Online</span>
                    )}
                    {chat.chat_type === 'group' && (
                      <span className="text-xs text-gray-500">
                        {chat.members?.length || 0} members
                      </span>
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
              <div className="flex items-center justify-between">
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
                    <p className="font-medium flex items-center">
                      {activeChat.chat_type === 'direct' 
                        ? activeChat.other_user?.username || 'Unknown User'
                        : activeChat.name
                      }
                      <span className="ml-2 text-green-500">🔒</span>
                    </p>
                    {activeChat.chat_type === 'direct' && (
                      <p className="text-sm text-gray-500">
                        {activeChat.other_user?.status_message || 'Available'}
                        {activeChat.other_user?.is_online && (
                          <span className="text-green-500 ml-2">● Online</span>
                        )}
                        {activeChat.other_user?.is_blocked && (
                          <span className="text-red-500 ml-2">● Blocked</span>
                        )}
                      </p>
                    )}
                    {activeChat.chat_type === 'group' && (
                      <p className="text-sm text-gray-500">
                        {activeChat.members?.length || 0} members • End-to-end encrypted
                      </p>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  {/* File upload button */}
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg"
                    disabled={uploadingFile || activeChat.other_user?.is_blocked}
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                    </svg>
                  </button>
                  
                  {/* User actions for direct chat */}
                  {activeChat.chat_type === 'direct' && activeChat.other_user && (
                    <div className="flex space-x-1">
                      {!activeChat.other_user.is_blocked ? (
                        <>
                          <button
                            onClick={() => blockUser(activeChat.other_user.user_id, 'Blocked from chat')}
                            className="p-2 text-red-600 hover:text-red-800 hover:bg-red-50 rounded-lg"
                            title="Block User"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636" />
                            </svg>
                          </button>
                          <button
                            onClick={() => {
                              setReportForm({ 
                                ...reportForm, 
                                user_id: activeChat.other_user.user_id,
                                chat_id: activeChat.chat_id
                              });
                              setShowReportModal(true);
                            }}
                            className="p-2 text-yellow-600 hover:text-yellow-800 hover:bg-yellow-50 rounded-lg"
                            title="Report User"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                            </svg>
                          </button>
                        </>
                      ) : (
                        <button
                          onClick={() => unblockUser(activeChat.other_user.user_id)}
                          className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
                        >
                          Unblock
                        </button>
                      )}
                    </div>
                  )}
                  
                  <input
                    ref={fileInputRef}
                    type="file"
                    hidden
                    onChange={(e) => {
                      if (e.target.files?.[0]) {
                        handleFileSelect(e.target.files[0]);
                      }
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Messages */}
            <div 
              className={`flex-1 overflow-y-auto p-4 space-y-4 ${dragOver ? 'bg-blue-50 border-2 border-dashed border-blue-300' : ''}`}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
            >
              {dragOver && (
                <div className="absolute inset-0 flex items-center justify-center bg-blue-50 bg-opacity-90 z-10">
                  <div className="text-center">
                    <svg className="w-16 h-16 text-blue-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <p className="text-blue-600 font-medium">Drop file here to send securely</p>
                  </div>
                </div>
              )}
              
              {uploadingFile && (
                <div className="text-center text-gray-500">
                  <p>🔒 Encrypting and uploading file...</p>
                </div>
              )}
              
              {activeChat.other_user?.is_blocked && (
                <div className="text-center p-4 bg-red-50 rounded-lg">
                  <p className="text-red-600 font-medium">This user is blocked</p>
                  <p className="text-red-500 text-sm">You cannot send or receive messages</p>
                </div>
              )}
              
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
                    {message.sender_id !== user.user_id && activeChat.chat_type === 'group' && (
                      <p className="text-xs font-medium mb-1">{message.sender_name}</p>
                    )}
                    {renderFileMessage(message)}
                    <div className="flex items-center justify-between mt-1">
                      <p className={`text-xs ${
                        message.sender_id === user.user_id ? 'text-blue-200' : 'text-gray-500'
                      }`}>
                        {formatTime(message.timestamp)}
                        {message.is_encrypted && <span className="ml-1">🔒</span>}
                      </p>
                      {renderMessageStatus(message)}
                    </div>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Message Input */}
            <div className="p-4 bg-white border-t border-gray-200">
              {!activeChat.other_user?.is_blocked ? (
                <form onSubmit={sendMessage} className="flex space-x-2">
                  <input
                    type="text"
                    placeholder="Type an encrypted message..."
                    className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                  />
                  <button
                    type="submit"
                    className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition duration-200 flex items-center"
                    disabled={uploadingFile}
                  >
                    <span className="mr-1">Send</span>
                    <span>🔒</span>
                  </button>
                </form>
              ) : (
                <div className="text-center p-3 bg-red-50 rounded-lg">
                  <p className="text-red-600">Cannot send messages to blocked user</p>
                </div>
              )}
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
              <h3 className="text-xl font-medium text-gray-800 mb-2">Welcome to ChatApp Pro 🔒</h3>
              <p className="text-gray-600">Select a chat to start secure messaging</p>
              <p className="text-sm text-gray-500 mt-2">
                ✨ End-to-end encryption • File sharing • Read receipts • User blocking & reporting
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Report Modal */}
      {showReportModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium mb-4">Report User</h3>
            <form onSubmit={reportUser}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Reason</label>
                <select
                  value={reportForm.reason}
                  onChange={(e) => setReportForm({...reportForm, reason: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">Select a reason</option>
                  <option value="spam">Spam</option>
                  <option value="harassment">Harassment</option>
                  <option value="inappropriate_content">Inappropriate Content</option>
                  <option value="fake_account">Fake Account</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Description (Optional)</label>
                <textarea
                  value={reportForm.description}
                  onChange={(e) => setReportForm({...reportForm, description: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows="3"
                  placeholder="Additional details..."
                />
              </div>
              <div className="flex space-x-2">
                <button
                  type="submit"
                  className="flex-1 bg-red-600 text-white py-2 rounded hover:bg-red-700"
                >
                  Submit Report
                </button>
                <button
                  type="button"
                  onClick={() => setShowReportModal(false)}
                  className="flex-1 bg-gray-400 text-white py-2 rounded hover:bg-gray-500"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;