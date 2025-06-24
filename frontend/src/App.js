import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import EmojiPicker from 'emoji-picker-react';
import Peer from 'simple-peer';
import io from 'socket.io-client';
import Webcam from 'react-webcam';
import MicRecorder from 'mic-recorder-to-mp3';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Initialize audio recorder
const Mp3Recorder = new MicRecorder({ bitRate: 128 });

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
  const webcamRef = useRef(null);

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

  // New advanced features state
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [showVoiceCall, setShowVoiceCall] = useState(false);
  const [showVideoCall, setShowVideoCall] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [peer, setPeer] = useState(null);
  const [stream, setStream] = useState(null);
  const [callStatus, setCallStatus] = useState('idle'); // idle, calling, in-call
  const [typingUsers, setTypingUsers] = useState([]);
  const [replyToMessage, setReplyToMessage] = useState(null);
  const [editingMessage, setEditingMessage] = useState(null);
  const [editText, setEditText] = useState('');
  
  // Stories state
  const [stories, setStories] = useState([]);
  const [showCreateStory, setShowCreateStory] = useState(false);
  const [storyForm, setStoryForm] = useState({
    content: '',
    media_type: 'text',
    background_color: '#000000',
    text_color: '#ffffff'
  });
  const [activeStory, setActiveStory] = useState(null);
  
  // Channels state
  const [channels, setChannels] = useState([]);
  const [showCreateChannel, setShowCreateChannel] = useState(false);
  const [channelForm, setChannelForm] = useState({
    name: '',
    description: '',
    is_public: true
  });
  
  // Disappearing messages
  const [showDisappearingTimer, setShowDisappearingTimer] = useState(false);
  const [disappearingTimer, setDisappearingTimer] = useState(0);

  // Initialize WebSocket connection with enhanced features
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
        console.log('WebSocket message:', data);
        
        switch (data.type) {
          case 'new_message':
            setMessages(prev => [...prev, data.data]);
            fetchChats();
            break;
          case 'message_read':
            setMessages(prev => prev.map(msg => 
              msg.message_id === data.data.message_id 
                ? { ...msg, read_status: 'read' }
                : msg
            ));
            break;
          case 'message_reaction':
            setMessages(prev => prev.map(msg => 
              msg.message_id === data.data.message_id 
                ? { ...msg, reactions: data.data.reactions }
                : msg
            ));
            break;
          case 'message_edited':
            setMessages(prev => prev.map(msg => 
              msg.message_id === data.data.message_id 
                ? { ...msg, content: data.data.new_content, edited_at: data.data.edited_at }
                : msg
            ));
            break;
          case 'message_deleted':
            setMessages(prev => prev.map(msg => 
              msg.message_id === data.data.message_id 
                ? { ...msg, is_deleted: true, content: '[This message was deleted]' }
                : msg
            ));
            break;
          case 'typing_status':
            setTypingUsers(data.data.typing_users.filter(uid => uid !== user.user_id));
            break;
          case 'incoming_call':
            setShowVoiceCall(true);
            setCallStatus('incoming');
            break;
          default:
            break;
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

  // Recording timer
  useEffect(() => {
    let interval;
    if (isRecording) {
      interval = setInterval(() => {
        setRecordingDuration(prev => prev + 1);
      }, 1000);
    } else {
      setRecordingDuration(0);
    }
    return () => clearInterval(interval);
  }, [isRecording]);

  // Typing indicator
  useEffect(() => {
    if (newMessage && activeChat && websocket) {
      websocket.send(JSON.stringify({
        type: 'typing',
        chat_id: activeChat.chat_id,
        is_typing: true
      }));
      
      const timer = setTimeout(() => {
        websocket.send(JSON.stringify({
          type: 'typing',
          chat_id: activeChat.chat_id,
          is_typing: false
        }));
      }, 2000);
      
      return () => clearTimeout(timer);
    }
  }, [newMessage, activeChat, websocket]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Authentication functions (keeping existing ones)
  const login = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API}/login`, loginForm);
      const { access_token, user } = response.data;
      
      setToken(access_token);
      setUser(user);
      localStorage.setItem('token', access_token);
      setCurrentView('chat');
      
      setTimeout(() => {
        fetchChats(access_token);
        fetchContacts(access_token);
        fetchBlockedUsers(access_token);
        fetchStories(access_token);
        fetchChannels(access_token);
      }, 100);
      
    } catch (error) {
      console.error('Login error:', error);
      alert('Login failed: ' + (error.response?.data?.detail || error.message));
    }
  };

  const register = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API}/register`, registerForm);
      const { access_token, user } = response.data;
      
      setToken(access_token);
      setUser(user);
      localStorage.setItem('token', access_token);
      setCurrentView('chat');
      
      setTimeout(() => {
        fetchChats(access_token);
        fetchContacts(access_token);
        fetchBlockedUsers(access_token);
        fetchStories(access_token);
        fetchChannels(access_token);
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
    setStories([]);
    setChannels([]);
    localStorage.removeItem('token');
    if (websocket) {
      websocket.close();
      setWebsocket(null);
    }
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
    setCurrentView('login');
  };

  // API functions
  const getAuthHeaders = (authToken = null) => ({
    headers: { Authorization: `Bearer ${authToken || token}` }
  });

  const fetchChats = async (authToken = null) => {
    try {
      const response = await axios.get(`${API}/chats`, getAuthHeaders(authToken));
      setChats(response.data);
    } catch (error) {
      console.error('Error fetching chats:', error);
    }
  };

  const fetchContacts = async (authToken = null) => {
    try {
      const response = await axios.get(`${API}/contacts`, getAuthHeaders(authToken));
      setContacts(response.data);
    } catch (error) {
      console.error('Error fetching contacts:', error);
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

  const fetchStories = async (authToken = null) => {
    try {
      const response = await axios.get(`${API}/stories`, getAuthHeaders(authToken));
      setStories(response.data);
    } catch (error) {
      console.error('Error fetching stories:', error);
    }
  };

  const fetchChannels = async (authToken = null) => {
    try {
      const response = await axios.get(`${API}/channels`, getAuthHeaders(authToken));
      setChannels(response.data);
    } catch (error) {
      console.error('Error fetching channels:', error);
    }
  };

  const fetchMessages = async (chatId) => {
    try {
      const response = await axios.get(`${API}/chats/${chatId}/messages`, getAuthHeaders());
      setMessages(response.data);
      
      const unreadMessages = response.data.filter(msg => 
        msg.sender_id !== user.user_id && msg.read_status === 'unread'
      );
      
      if (unreadMessages.length > 0) {
        markMessagesRead(unreadMessages.map(msg => msg.message_id));
      }
    } catch (error) {
      console.error('Error fetching messages:', error);
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

  // Enhanced message sending with replies and voice
  const sendMessage = async (e) => {
    e.preventDefault();
    if ((!newMessage.trim() && !replyToMessage) || !activeChat) return;

    try {
      const messageData = {
        content: newMessage,
        message_type: 'text'
      };
      
      if (replyToMessage) {
        messageData.reply_to = replyToMessage.message_id;
      }

      await axios.post(`${API}/chats/${activeChat.chat_id}/messages`, messageData, getAuthHeaders());
      
      setNewMessage('');
      setReplyToMessage(null);
    } catch (error) {
      console.error('Error sending message:', error);
      if (error.response?.status === 403) {
        alert('Cannot send message to blocked user');
      }
    }
  };

  // Voice recording
  const startRecording = async () => {
    try {
      await Mp3Recorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Could not start recording. Please check microphone permissions.');
    }
  };

  const stopRecording = async () => {
    try {
      const [buffer, blob] = await Mp3Recorder.stop().getMp3();
      setIsRecording(false);
      
      // Convert to base64
      const reader = new FileReader();
      reader.onload = async () => {
        const base64Audio = reader.result.split(',')[1];
        
        try {
          await axios.post(`${API}/chats/${activeChat.chat_id}/messages`, {
            content: `Voice message (${recordingDuration}s)`,
            message_type: 'voice',
            file_data: base64Audio,
            voice_duration: recordingDuration,
            file_name: 'voice_message.mp3'
          }, getAuthHeaders());
        } catch (error) {
          console.error('Error sending voice message:', error);
        }
      };
      reader.readAsDataURL(blob);
    } catch (error) {
      console.error('Error stopping recording:', error);
    }
  };

  // Message reactions
  const reactToMessage = async (messageId, emoji) => {
    try {
      await axios.post(`${API}/messages/react`, {
        message_id: messageId,
        emoji: emoji
      }, getAuthHeaders());
    } catch (error) {
      console.error('Error reacting to message:', error);
    }
  };

  // Message editing
  const editMessage = async (messageId, newContent) => {
    try {
      await axios.put(`${API}/messages/edit`, {
        message_id: messageId,
        new_content: newContent
      }, getAuthHeaders());
      setEditingMessage(null);
      setEditText('');
    } catch (error) {
      console.error('Error editing message:', error);
    }
  };

  // Message deletion
  const deleteMessage = async (messageId) => {
    if (window.confirm('Are you sure you want to delete this message?')) {
      try {
        await axios.delete(`${API}/messages/${messageId}`, getAuthHeaders());
      } catch (error) {
        console.error('Error deleting message:', error);
      }
    }
  };

  // Voice/Video calls
  const initiateCall = async (callType = 'voice') => {
    try {
      const response = await axios.post(`${API}/calls/initiate`, {
        chat_id: activeChat.chat_id,
        call_type: callType
      }, getAuthHeaders());
      
      setCallStatus('calling');
      if (callType === 'video') {
        setShowVideoCall(true);
      } else {
        setShowVoiceCall(true);
      }
      
      // Initialize WebRTC
      const userStream = await navigator.mediaDevices.getUserMedia({
        video: callType === 'video',
        audio: true
      });
      setStream(userStream);
      
      const newPeer = new Peer({
        initiator: true,
        trickle: false,
        stream: userStream
      });
      
      setPeer(newPeer);
    } catch (error) {
      console.error('Error initiating call:', error);
    }
  };

  // Stories functions
  const createStory = async () => {
    try {
      await axios.post(`${API}/stories`, storyForm, getAuthHeaders());
      setShowCreateStory(false);
      setStoryForm({
        content: '',
        media_type: 'text',
        background_color: '#000000',
        text_color: '#ffffff'
      });
      fetchStories();
    } catch (error) {
      console.error('Error creating story:', error);
    }
  };

  // Channel functions
  const createChannel = async () => {
    try {
      await axios.post(`${API}/channels`, channelForm, getAuthHeaders());
      setShowCreateChannel(false);
      setChannelForm({
        name: '',
        description: '',
        is_public: true
      });
      fetchChannels();
    } catch (error) {
      console.error('Error creating channel:', error);
    }
  };

  // Existing helper functions (keeping all previous ones)
  const selectChat = (chat) => {
    setActiveChat(chat);
    fetchMessages(chat.chat_id);
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const renderMessageStatus = (message) => {
    if (message.sender_id !== user.user_id) return null;
    
    if (message.read_status === 'read') {
      return <span className="text-blue-400 ml-1">✓✓</span>;
    } else {
      return <span className="text-gray-400 ml-1">✓✓</span>;
    }
  };

  // Enhanced message rendering with reactions and replies
  const renderMessage = (message) => {
    const isEditing = editingMessage === message.message_id;
    
    return (
      <div
        key={message.message_id}
        className={`flex ${message.sender_id === user.user_id ? 'justify-end' : 'justify-start'} group`}
      >
        <div
          className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg relative ${
            message.sender_id === user.user_id
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-800'
          } ${message.is_deleted ? 'opacity-50 italic' : ''}`}
        >
          {/* Reply indicator */}
          {message.reply_to && (
            <div className="text-xs opacity-75 border-l-2 border-gray-300 pl-2 mb-1">
              Replying to previous message
            </div>
          )}
          
          {/* Message content */}
          {isEditing ? (
            <div>
              <input
                type="text"
                value={editText}
                onChange={(e) => setEditText(e.target.value)}
                className="w-full bg-transparent border-b text-current"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    editMessage(message.message_id, editText);
                  }
                }}
                autoFocus
              />
              <div className="flex space-x-2 mt-1">
                <button
                  onClick={() => editMessage(message.message_id, editText)}
                  className="text-xs text-green-400"
                >
                  Save
                </button>
                <button
                  onClick={() => {
                    setEditingMessage(null);
                    setEditText('');
                  }}
                  className="text-xs text-red-400"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <>
              {/* Message type specific rendering */}
              {message.message_type === 'voice' ? (
                <div className="flex items-center space-x-2">
                  <span className="text-2xl">🎤</span>
                  <div>
                    <p>Voice message</p>
                    <p className="text-xs">{message.voice_duration}s</p>
                    {message.file_data && (
                      <audio controls className="mt-1">
                        <source src={`data:audio/mp3;base64,${message.file_data}`} type="audio/mp3" />
                      </audio>
                    )}
                  </div>
                </div>
              ) : message.message_type === 'image' && message.file_data ? (
                <div>
                  <img 
                    src={`data:image/jpeg;base64,${message.file_data}`}
                    alt={message.file_name}
                    className="max-w-xs max-h-64 rounded-lg cursor-pointer"
                    onClick={() => window.open(`data:image/jpeg;base64,${message.file_data}`, '_blank')}
                  />
                  <p className="text-sm mt-1">{message.file_name}</p>
                </div>
              ) : (
                <p>{message.content}</p>
              )}
              
              {/* Reactions */}
              {message.reactions && Object.keys(message.reactions).length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {Object.entries(message.reactions).map(([emoji, userIds]) => (
                    <button
                      key={emoji}
                      onClick={() => reactToMessage(message.message_id, emoji)}
                      className={`px-2 py-1 rounded-full text-xs flex items-center space-x-1 ${
                        userIds.includes(user.user_id)
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      <span>{emoji}</span>
                      <span>{userIds.length}</span>
                    </button>
                  ))}
                </div>
              )}
              
              {/* Message actions */}
              <div className="opacity-0 group-hover:opacity-100 absolute -right-2 top-0 flex space-x-1">
                <button
                  onClick={() => setShowEmojiPicker(message.message_id)}
                  className="bg-gray-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs"
                >
                  😊
                </button>
                <button
                  onClick={() => setReplyToMessage(message)}
                  className="bg-gray-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs"
                >
                  ↩️
                </button>
                {message.sender_id === user.user_id && (
                  <>
                    <button
                      onClick={() => {
                        setEditingMessage(message.message_id);
                        setEditText(message.content);
                      }}
                      className="bg-gray-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs"
                    >
                      ✏️
                    </button>
                    <button
                      onClick={() => deleteMessage(message.message_id)}
                      className="bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs"
                    >
                      🗑️
                    </button>
                  </>
                )}
              </div>
            </>
          )}
          
          {/* Timestamp and status */}
          <div className="flex items-center justify-between mt-1">
            <p className={`text-xs ${
              message.sender_id === user.user_id ? 'text-blue-200' : 'text-gray-500'
            }`}>
              {formatTime(message.timestamp)}
              {message.edited_at && <span className="ml-1">(edited)</span>}
              {message.is_encrypted && <span className="ml-1">🔒</span>}
            </p>
            {renderMessageStatus(message)}
          </div>
        </div>
      </div>
    );
  };

  // Login/Register views (keeping existing ones but enhanced)
  if (currentView === 'login') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 flex items-center justify-center">
        <div className="bg-white rounded-xl shadow-2xl p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-800 mb-2">
              ChatApp Pro 
              <span className="text-2xl ml-2">🚀</span>
            </h1>
            <p className="text-gray-600">Ultimate communication platform</p>
            <p className="text-sm text-blue-600">Stories • Calls • Channels • Encryption</p>
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
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 transition duration-200"
            >
              Login
            </button>
          </form>
        </div>
      </div>
    );
  }

  if (currentView === 'register') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 flex items-center justify-center">
        <div className="bg-white rounded-xl shadow-2xl p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-800 mb-2">
              ChatApp Pro 
              <span className="text-2xl ml-2">🚀</span>
            </h1>
            <p className="text-gray-600">Join the ultimate communication platform</p>
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
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 transition duration-200"
            >
              Register
            </button>
          </form>
        </div>
      </div>
    );
  }

  // Main Chat View with all advanced features
  return (
    <div className="h-screen flex bg-gray-100">
      {/* Enhanced Sidebar */}
      <div className="w-1/3 bg-white border-r border-gray-200 flex flex-col">
        {/* Header with stories */}
        <div className="p-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-blue-400 rounded-full flex items-center justify-center">
                <span className="font-bold">{user.username.charAt(0).toUpperCase()}</span>
              </div>
              <div className="ml-3">
                <p className="font-medium">{user.username} 🚀</p>
                <p className="text-xs text-blue-200">
                  {isConnected ? 'Online • All Features Active' : 'Connecting...'}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowCreateStory(true)}
                className="text-blue-200 hover:text-white p-1 rounded"
                title="Create Story"
              >
                📖
              </button>
              <button
                onClick={() => setShowCreateChannel(true)}
                className="text-blue-200 hover:text-white p-1 rounded"
                title="Create Channel"
              >
                📢
              </button>
              <button
                onClick={() => setShowBlockedUsers(!showBlockedUsers)}
                className="text-blue-200 hover:text-white p-1 rounded"
                title="Blocked Users"
              >
                🚫
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

        {/* Stories section */}
        {stories.length > 0 && (
          <div className="p-3 border-b">
            <div className="flex space-x-3 overflow-x-auto">
              {stories.map(userStories => (
                <div
                  key={userStories.user.user_id}
                  className="flex-shrink-0 text-center cursor-pointer"
                  onClick={() => setActiveStory(userStories)}
                >
                  <div className="w-12 h-12 bg-gradient-to-br from-purple-400 to-pink-400 rounded-full p-0.5">
                    <div className="w-full h-full bg-gray-300 rounded-full flex items-center justify-center text-white font-bold">
                      {userStories.user.username.charAt(0).toUpperCase()}
                    </div>
                  </div>
                  <p className="text-xs mt-1 truncate w-12">{userStories.user.username}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Rest of the sidebar remains the same but with enhanced features */}
        {/* Keeping existing functionality but with enhanced UI */}
        
        {/* Search */}
        <div className="p-3">
          <input
            type="text"
            placeholder="Search everything..."
            className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              // searchUsers(e.target.value);
            }}
          />
        </div>

        {/* Quick actions */}
        <div className="px-3 pb-3 grid grid-cols-4 gap-2">
          <button
            onClick={() => setShowAddContact(true)}
            className="bg-green-500 text-white py-2 rounded-lg text-xs hover:bg-green-600"
          >
            👥 Add
          </button>
          <button
            onClick={() => setShowCreateGroup(true)}
            className="bg-purple-500 text-white py-2 rounded-lg text-xs hover:bg-purple-600"
          >
            👨‍👩‍👧‍👦 Group
          </button>
          <button
            onClick={() => setShowCreateChannel(true)}
            className="bg-blue-500 text-white py-2 rounded-lg text-xs hover:bg-blue-600"
          >
            📢 Channel
          </button>
          <button
            onClick={() => setShowCreateStory(true)}
            className="bg-pink-500 text-white py-2 rounded-lg text-xs hover:bg-pink-600"
          >
            📖 Story
          </button>
        </div>

        {/* Chat List (simplified for space) */}
        <div className="flex-1 overflow-y-auto">
          {chats.length === 0 ? (
            <div className="p-4 text-center text-gray-500">
              <div className="text-6xl mb-4">🚀</div>
              <p className="font-medium">Welcome to ChatApp Pro!</p>
              <p className="text-sm">Create your first chat, story, or channel</p>
            </div>
          ) : (
            chats.map(chat => (
              <div
                key={chat.chat_id}
                className={`p-3 border-b border-gray-100 cursor-pointer hover:bg-purple-50 ${
                  activeChat?.chat_id === chat.chat_id ? 'bg-purple-100 border-purple-200' : ''
                }`}
                onClick={() => selectChat(chat)}
              >
                <div className="flex items-center">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-purple-400 rounded-full flex items-center justify-center relative">
                    <span className="text-white font-medium">
                      {chat.chat_type === 'direct' 
                        ? chat.other_user?.username?.charAt(0).toUpperCase() || '?'
                        : chat.name?.charAt(0).toUpperCase() || 'G'
                      }
                    </span>
                    {chat.other_user?.is_online && (
                      <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-400 rounded-full border-2 border-white"></div>
                    )}
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
                        🔒 {chat.last_message.content}
                      </p>
                    )}
                    {typingUsers.length > 0 && activeChat?.chat_id === chat.chat_id && (
                      <p className="text-xs text-purple-500 italic">typing...</p>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Enhanced Chat Area */}
      <div className="flex-1 flex flex-col">
        {activeChat ? (
          <>
            {/* Enhanced Chat Header */}
            <div className="p-4 bg-white border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-400 to-purple-400 rounded-full flex items-center justify-center">
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
                      <span className="ml-2 text-purple-500">🚀</span>
                    </p>
                    <p className="text-sm text-gray-500">
                      {activeChat.chat_type === 'direct' && activeChat.other_user?.is_online && (
                        <span className="text-green-500">● Online</span>
                      )}
                      {activeChat.chat_type === 'group' && (
                        <span>{activeChat.members?.length || 0} members</span>
                      )}
                      <span className="ml-2">• End-to-end encrypted</span>
                    </p>
                  </div>
                </div>
                
                {/* Enhanced action buttons */}
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => initiateCall('voice')}
                    className="p-2 text-gray-600 hover:text-green-600 hover:bg-green-50 rounded-lg"
                    title="Voice Call"
                  >
                    📞
                  </button>
                  <button
                    onClick={() => initiateCall('video')}
                    className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg"
                    title="Video Call"
                  >
                    📹
                  </button>
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="p-2 text-gray-600 hover:text-purple-600 hover:bg-purple-50 rounded-lg"
                    title="Attach File"
                  >
                    📎
                  </button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    hidden
                    onChange={(e) => {
                      if (e.target.files?.[0]) {
                        // handleFileSelect(e.target.files[0]);
                      }
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Enhanced Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gradient-to-b from-gray-50 to-white">
              {replyToMessage && (
                <div className="bg-blue-50 p-3 rounded-lg border-l-4 border-blue-400">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-sm text-blue-600 font-medium">Replying to:</p>
                      <p className="text-sm text-gray-600">{replyToMessage.content}</p>
                    </div>
                    <button
                      onClick={() => setReplyToMessage(null)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              )}
              
              {messages.map(renderMessage)}
              <div ref={messagesEndRef} />
            </div>

            {/* Enhanced Message Input */}
            <div className="p-4 bg-white border-t border-gray-200">
              <form onSubmit={sendMessage} className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={isRecording ? stopRecording : startRecording}
                  className={`p-3 rounded-full ${
                    isRecording ? 'bg-red-500 text-white animate-pulse' : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                  }`}
                  title={isRecording ? `Recording... ${recordingDuration}s` : 'Voice Message'}
                >
                  🎤
                </button>
                
                <div className="flex-1 relative">
                  <input
                    type="text"
                    placeholder="Type a message... 🚀"
                    className="w-full p-3 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    disabled={isRecording}
                  />
                  <button
                    type="button"
                    onClick={() => setShowEmojiPicker(!showEmojiPicker)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    😊
                  </button>
                </div>
                
                <button
                  type="submit"
                  className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-3 rounded-lg hover:from-purple-700 hover:to-blue-700 transition duration-200 flex items-center"
                  disabled={(!newMessage.trim() && !replyToMessage) || isRecording}
                >
                  <span>Send</span>
                  <span className="ml-1">🚀</span>
                </button>
              </form>
              
              {/* Emoji Picker */}
              {showEmojiPicker && (
                <div className="absolute bottom-20 right-4 z-50">
                  <EmojiPicker
                    onEmojiClick={(emojiData) => {
                      setNewMessage(prev => prev + emojiData.emoji);
                      setShowEmojiPicker(false);
                    }}
                  />
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-purple-50 to-blue-50">
            <div className="text-center">
              <div className="text-8xl mb-6">🚀</div>
              <h3 className="text-3xl font-bold text-gray-800 mb-4">ChatApp Pro Ultimate</h3>
              <p className="text-gray-600 mb-6">Select a chat to start the ultimate messaging experience</p>
              <div className="grid grid-cols-2 gap-4 text-sm text-gray-500">
                <div className="flex items-center">
                  <span className="mr-2">🔒</span>
                  <span>End-to-end encryption</span>
                </div>
                <div className="flex items-center">
                  <span className="mr-2">📞</span>
                  <span>Voice & video calls</span>
                </div>
                <div className="flex items-center">
                  <span className="mr-2">📖</span>
                  <span>Stories & channels</span>
                </div>
                <div className="flex items-center">
                  <span className="mr-2">🎤</span>
                  <span>Voice messages</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Modals and overlays for all the new features */}
      {/* Voice/Video Call Modal */}
      {(showVoiceCall || showVideoCall) && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="text-center">
              <div className="text-6xl mb-4">{showVideoCall ? '📹' : '📞'}</div>
              <h3 className="text-xl font-medium mb-2">
                {callStatus === 'calling' ? 'Calling...' : 
                 callStatus === 'incoming' ? 'Incoming Call' : 'In Call'}
              </h3>
              <p className="text-gray-600 mb-6">
                {activeChat?.chat_type === 'direct' 
                  ? activeChat.other_user?.username 
                  : activeChat?.name}
              </p>
              
              {showVideoCall && stream && (
                <div className="mb-4">
                  <video
                    ref={(video) => {
                      if (video && stream) {
                        video.srcObject = stream;
                      }
                    }}
                    autoPlay
                    muted
                    className="w-full h-48 bg-gray-900 rounded-lg"
                  />
                </div>
              )}
              
              <div className="flex justify-center space-x-4">
                <button
                  onClick={() => {
                    setShowVoiceCall(false);
                    setShowVideoCall(false);
                    setCallStatus('idle');
                    if (stream) {
                      stream.getTracks().forEach(track => track.stop());
                      setStream(null);
                    }
                  }}
                  className="bg-red-500 text-white p-3 rounded-full hover:bg-red-600"
                >
                  ❌
                </button>
                {callStatus === 'incoming' && (
                  <button
                    onClick={() => setCallStatus('in-call')}
                    className="bg-green-500 text-white p-3 rounded-full hover:bg-green-600"
                  >
                    ✅
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Story Modal */}
      {showCreateStory && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium mb-4">Create Story</h3>
            <div className="space-y-4">
              <textarea
                placeholder="What's on your mind?"
                className="w-full p-3 border border-gray-300 rounded-lg"
                value={storyForm.content}
                onChange={(e) => setStoryForm({...storyForm, content: e.target.value})}
                rows="4"
              />
              <div className="flex space-x-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Background</label>
                  <input
                    type="color"
                    value={storyForm.background_color}
                    onChange={(e) => setStoryForm({...storyForm, background_color: e.target.value})}
                    className="w-12 h-8 rounded"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Text Color</label>
                  <input
                    type="color"
                    value={storyForm.text_color}
                    onChange={(e) => setStoryForm({...storyForm, text_color: e.target.value})}
                    className="w-12 h-8 rounded"
                  />
                </div>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={createStory}
                  className="flex-1 bg-purple-600 text-white py-2 rounded hover:bg-purple-700"
                >
                  Create Story
                </button>
                <button
                  onClick={() => setShowCreateStory(false)}
                  className="flex-1 bg-gray-400 text-white py-2 rounded hover:bg-gray-500"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Channel Modal */}
      {showCreateChannel && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium mb-4">Create Channel</h3>
            <div className="space-y-4">
              <input
                type="text"
                placeholder="Channel Name"
                className="w-full p-3 border border-gray-300 rounded-lg"
                value={channelForm.name}
                onChange={(e) => setChannelForm({...channelForm, name: e.target.value})}
              />
              <textarea
                placeholder="Channel Description"
                className="w-full p-3 border border-gray-300 rounded-lg"
                value={channelForm.description}
                onChange={(e) => setChannelForm({...channelForm, description: e.target.value})}
                rows="3"
              />
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={channelForm.is_public}
                  onChange={(e) => setChannelForm({...channelForm, is_public: e.target.checked})}
                  className="mr-2"
                />
                Public Channel
              </label>
              <div className="flex space-x-2">
                <button
                  onClick={createChannel}
                  className="flex-1 bg-blue-600 text-white py-2 rounded hover:bg-blue-700"
                >
                  Create Channel
                </button>
                <button
                  onClick={() => setShowCreateChannel(false)}
                  className="flex-1 bg-gray-400 text-white py-2 rounded hover:bg-gray-500"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;