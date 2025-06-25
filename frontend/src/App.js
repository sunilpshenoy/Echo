import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';
import GenieAssistant from './components/GenieAssistant';
import Calendar from './components/Calendar';
import TaskManager from './components/TaskManager';
import WorkspaceSwitcher from './components/WorkspaceSwitcher';
import GameCenter from './components/GameCenter';
import AdvancedCustomization from './components/AdvancedCustomization';
import "./components/AdvancedCustomization.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://1f08d9c4-28b0-437e-b8a1-ad0ba8b89e9a.preview.emergentagent.com';
const API = `${BACKEND_URL}/api`;

// Initialize audio recorder
const MicRecorder = require("mic-recorder-to-mp3");
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
  const [registerForm, setRegisterForm] = useState({ username: '', email: '', password: '', phone: '', display_name: '' });
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showAddContact, setShowAddContact] = useState(false);
  const [contactForm, setContactForm] = useState({ email: '', contact_name: '' });
  
  // Group chat state
  const [showCreateGroup, setShowCreateGroup] = useState(false);
  const [groupForm, setGroupForm] = useState({ name: '', description: '', members: [], chat_type: 'group' });
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

  // Customization state
  const [showCustomization, setShowCustomization] = useState(false);
  const [customSettings, setCustomSettings] = useState({
    fontFamily: 'Inter', // Default font
    fontSize: 'medium',
    backgroundColor: 'white',
    primaryColor: '#25D366', // WhatsApp green
    textColor: 'black',
    userNameColor: '#128C7E',
    theme: 'light'
  });

  // Enhanced features state
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [showVoiceCall, setShowVoiceCall] = useState(false);
  const [showVideoCall, setShowVideoCall] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [peer, setPeer] = useState(null);
  const [stream, setStream] = useState(null);
  const [callStatus, setCallStatus] = useState('idle');
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
    text_color: '#ffffff',
    privacy: 'all'
  });
  const [activeStory, setActiveStory] = useState(null);
  
  // Channels state
  const [channels, setChannels] = useState([]);
  const [showCreateChannel, setShowCreateChannel] = useState(false);
  const [channelForm, setChannelForm] = useState({
    name: '',
    description: '',
    is_public: true,
    category: 'general'
  });
  
  // Voice rooms state
  const [voiceRooms, setVoiceRooms] = useState([]);
  const [activeVoiceRoom, setActiveVoiceRoom] = useState(null);
  const [showCreateVoiceRoom, setShowCreateVoiceRoom] = useState(false);
  const [voiceRoomForm, setVoiceRoomForm] = useState({
    name: '',
    description: '',
    max_participants: 50
  });
  
  // Discovery state
  const [discoveredUsers, setDiscoveredUsers] = useState([]);
  const [discoveredChannels, setDiscoveredChannels] = useState([]);
  const [showDiscovery, setShowDiscovery] = useState(false);
  const [discoveryTab, setDiscoveryTab] = useState('users');
  
  // Privacy and Security state
  const [showPrivacySettings, setShowPrivacySettings] = useState(false);
  const [privacySettings, setPrivacySettings] = useState({
    profile_photo: 'everyone',
    last_seen: 'everyone',
    phone_number: 'contacts',
    read_receipts: true,
    typing_indicators: true
  });
  const [showSafetyNumber, setShowSafetyNumber] = useState(false);
  const [safetyNumberData, setSafetyNumberData] = useState(null);
  const [selectedUserForSafety, setSelectedUserForSafety] = useState(null);
  
  // Advanced features
  const [showBackupRestore, setShowBackupRestore] = useState(false);
  const [backupHistory, setBackupHistory] = useState([]);
  const [userStatus, setUserStatus] = useState({
    activity_status: 'online',
    custom_status: '',
    game_activity: ''
  });
  const [userProfile, setUserProfile] = useState({
    bio: '',
    location: '',
    website: '',
    interests: [],
    languages: []
  });
  const [showProfileEditor, setShowProfileEditor] = useState(false);
  
  // Polls state
  const [showCreatePoll, setShowCreatePoll] = useState(false);
  const [pollForm, setPollForm] = useState({
    question: '',
    options: ['', ''],
    is_anonymous: false,
    allows_multiple_answers: false,
    expires_in_hours: null
  });
  
  // Workspace and Calendar state
  const [workspaceMode, setWorkspaceMode] = useState('personal');
  const [showCalendar, setShowCalendar] = useState(false);
  const [showTasks, setShowTasks] = useState(false);
  const [showWorkspaceSwitcher, setShowWorkspaceSwitcher] = useState(false);
  const [showGameCenter, setShowGameCenter] = useState(false);
  const [showAdvancedCustomization, setShowAdvancedCustomization] = useState(false);
  
  // Advanced customization settings are defined in the AdvancedCustomization component
  
  // Screen sharing
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [screenStream, setScreenStream] = useState(null);

  // Initialize WebSocket connection with enhanced features
  // Load custom settings from localStorage on component mount
  useEffect(() => {
    const savedSettings = localStorage.getItem('chatapp-custom-settings');
    if (savedSettings) {
      const settings = JSON.parse(savedSettings);
      setCustomSettings(settings);
      
      // Apply settings to CSS variables
      const root = document.documentElement;
      root.style.setProperty('--font-family', settings.fontFamily);
      root.style.setProperty('--font-size', settings.fontSize === 'small' ? '12px' : settings.fontSize === 'large' ? '16px' : settings.fontSize === 'xl' ? '18px' : '14px');
      root.style.setProperty('--bg-color', settings.backgroundColor);
      root.style.setProperty('--primary-color', settings.primaryColor);
      root.style.setProperty('--text-color', settings.textColor);
      root.style.setProperty('--username-color', settings.userNameColor);
      
      // Apply theme
      if (settings.theme === 'dark') {
        document.body.setAttribute('data-theme', 'dark');
      }
    }
    
    // Check if user is already logged in
    if (token && !user) {
      // Validate token by fetching user profile
      axios.get(`${API}/users/me`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      .then(response => {
        setUser(response.data);
        setCurrentView('chat');
        // Fetch user data
        fetchChats(token);
        fetchContacts(token);
        fetchBlockedUsers(token);
        fetchStories(token);
        fetchChannels(token);
        fetchVoiceRooms(token);
      })
      .catch(error => {
        console.error('Token validation failed:', error);
        localStorage.removeItem('token');
        setToken(null);
        setCurrentView('login');
      });
    }
  }, []);

  useEffect(() => {
    if (user && !websocket) {
      const wsUrl = BACKEND_URL.replace('https:', 'wss:').replace('http:', 'ws:');
      const ws = new WebSocket(`${wsUrl}/api/ws/${user.user_id}`);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        
        // Send initial status
        ws.send(JSON.stringify({
          type: 'user_status',
          status: userStatus.activity_status,
          activity: userStatus.custom_status,
          game: userStatus.game_activity
        }));
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
          case 'user_joined_voice':
            fetchVoiceRooms();
            break;
          case 'status_update':
            // Handle contact status updates
            console.log('Status update:', data.data);
            break;
          case 'screen_share_toggle':
            console.log('Screen share toggled:', data.data);
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

  // Authentication functions
  const login = async (e) => {
    e.preventDefault();
    console.log('Login form submitted:', loginForm);
    console.log('API URL:', API);
    try {
      console.log('Attempting to login with:', loginForm);
      const response = await axios.post(`${API}/login`, loginForm);
      console.log('Login response:', response.data);
      const { access_token, user } = response.data;
      
      setToken(access_token);
      setUser(user);
      setPrivacySettings(user.privacy_settings || privacySettings);
      localStorage.setItem('token', access_token);
      setCurrentView('chat');
      
      setTimeout(() => {
        console.log('Fetching user data after login');
        fetchChats(access_token);
        fetchContacts(access_token);
        fetchBlockedUsers(access_token);
        fetchStories(access_token);
        fetchChannels(access_token);
        fetchVoiceRooms(access_token);
      }, 100);
      
    } catch (error) {
      console.error('Login error:', error);
      console.error('Login error details:', error.response?.data);
      alert('Login failed: ' + (error.response?.data?.detail || error.message));
    }
  };

  const register = async (e) => {
    e.preventDefault();
    console.log('Register form submitted:', registerForm);
    try {
      console.log('Attempting to register with:', registerForm);
      const response = await axios.post(`${API}/register`, registerForm);
      console.log('Register response:', response.data);
      const { access_token, user } = response.data;
      
      setToken(access_token);
      setUser(user);
      localStorage.setItem('token', access_token);
      setCurrentView('chat');
      
      // Show backup phrase
      if (user.backup_phrase) {
        alert(`IMPORTANT: Save your backup phrase securely:\n\n${user.backup_phrase}\n\nThis phrase can recover your account if you lose access.`);
      }
      
      setTimeout(() => {
        console.log('Fetching user data after registration');
        fetchChats(access_token);
        fetchContacts(access_token);
        fetchBlockedUsers(access_token);
        fetchStories(access_token);
        fetchChannels(access_token);
        fetchVoiceRooms(access_token);
      }, 100);
      
    } catch (error) {
      console.error('Registration error:', error);
      console.error('Registration error details:', error.response?.data);
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
    setVoiceRooms([]);
    localStorage.removeItem('token');
    if (websocket) {
      websocket.close();
      setWebsocket(null);
    }
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
    if (screenStream) {
      screenStream.getTracks().forEach(track => track.stop());
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

  const fetchVoiceRooms = async (authToken = null) => {
    try {
      const response = await axios.get(`${API}/voice/rooms`, getAuthHeaders(authToken));
      setVoiceRooms(response.data);
    } catch (error) {
      console.error('Error fetching voice rooms:', error);
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

  // Enhanced message sending
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

  // Voice/Video calls with enhanced features
  const initiateCall = async (callType = 'voice') => {
    try {
      const response = await axios.post(`${API}/calls/initiate`, {
        chat_id: activeChat.chat_id,
        call_type: callType,
        screen_sharing: false
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

  // Screen sharing
  const startScreenShare = async () => {
    try {
      const screenStream = await navigator.mediaDevices.getDisplayMedia({
        video: true,
        audio: true
      });
      setScreenStream(screenStream);
      setIsScreenSharing(true);
      
      // Notify other participants
      if (activeChat) {
        await axios.post(`${API}/calls/${activeChat.call_id}/screen-share`, {
          enable: true
        }, getAuthHeaders());
      }
    } catch (error) {
      console.error('Error starting screen share:', error);
    }
  };

  const stopScreenShare = async () => {
    if (screenStream) {
      screenStream.getTracks().forEach(track => track.stop());
      setScreenStream(null);
      setIsScreenSharing(false);
      
      // Notify other participants
      if (activeChat) {
        await axios.post(`${API}/calls/${activeChat.call_id}/screen-share`, {
          enable: false
        }, getAuthHeaders());
      }
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
        text_color: '#ffffff',
        privacy: 'all'
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
        is_public: true,
        category: 'general'
      });
      fetchChannels();
    } catch (error) {
      console.error('Error creating channel:', error);
    }
  };

  // Voice room functions
  const createVoiceRoom = async () => {
    try {
      await axios.post(`${API}/voice/rooms`, voiceRoomForm, getAuthHeaders());
      setShowCreateVoiceRoom(false);
      setVoiceRoomForm({
        name: '',
        description: '',
        max_participants: 50
      });
      fetchVoiceRooms();
    } catch (error) {
      console.error('Error creating voice room:', error);
    }
  };

  const joinVoiceRoom = async (roomId) => {
    try {
      await axios.post(`${API}/voice/rooms/${roomId}/join`, {}, getAuthHeaders());
      setActiveVoiceRoom(roomId);
      
      if (websocket) {
        websocket.send(JSON.stringify({
          type: 'join_voice_room',
          room_id: roomId
        }));
      }
    } catch (error) {
      console.error('Error joining voice room:', error);
    }
  };

  // Discovery functions
  const discoverUsers = async (query = '') => {
    try {
      const response = await axios.get(`${API}/discover/users?query=${query}`, getAuthHeaders());
      setDiscoveredUsers(response.data);
    } catch (error) {
      console.error('Error discovering users:', error);
    }
  };

  const discoverChannels = async (query = '', category = 'all') => {
    try {
      const response = await axios.get(`${API}/discover/channels?query=${query}&category=${category}`, getAuthHeaders());
      setDiscoveredChannels(response.data);
    } catch (error) {
      console.error('Error discovering channels:', error);
    }
  };

  // Privacy functions
  const updatePrivacySettings = async (newSettings) => {
    try {
      await axios.put(`${API}/privacy/settings`, { settings: newSettings }, getAuthHeaders());
      setPrivacySettings(newSettings);
    } catch (error) {
      console.error('Error updating privacy settings:', error);
    }
  };

  const getSafetyNumber = async (userId) => {
    try {
      const response = await axios.get(`${API}/safety/number/${userId}`, getAuthHeaders());
      setSafetyNumberData(response.data);
      setSelectedUserForSafety(userId);
      setShowSafetyNumber(true);
    } catch (error) {
      console.error('Error getting safety number:', error);
    }
  };

  // Backup functions
  const createBackup = async (backupType = 'full') => {
    try {
      const response = await axios.post(`${API}/backup/create?backup_type=${backupType}`, {}, getAuthHeaders());
      alert(`Backup created successfully! Size: ${(response.data.file_size / 1024 / 1024).toFixed(2)} MB`);
    } catch (error) {
      console.error('Error creating backup:', error);
      alert('Error creating backup: ' + (error.response?.data?.detail || error.message));
    }
  };

  // User status functions
  const updateUserStatus = async (statusData) => {
    try {
      setUserStatus(statusData);
      if (websocket) {
        websocket.send(JSON.stringify({
          type: 'user_status',
          ...statusData
        }));
      }
    } catch (error) {
      console.error('Error updating status:', error);
    }
  };

  // Genie Assistant action handler
  const handleGenieAction = async (action) => {
    try {
      switch (action.type) {
        case 'create_chat':
          if (action.target_user) {
            // Find user by name/email and create direct chat
            const searchResponse = await axios.get(`${API}/users/search?query=${action.target_user}`, getAuthHeaders());
            const users = searchResponse.data;
            const targetUser = users.find(u => 
              u.username.toLowerCase().includes(action.target_user.toLowerCase()) ||
              u.display_name?.toLowerCase().includes(action.target_user.toLowerCase()) ||
              u.email.toLowerCase().includes(action.target_user.toLowerCase())
            );
            
            if (targetUser) {
              const chatResponse = await axios.post(`${API}/chats`, {
                chat_type: 'direct',
                other_user_id: targetUser.user_id
              }, getAuthHeaders());
              
              fetchChats();
              setActiveChat(chatResponse.data);
              return { success: true, message: `Chat created with ${targetUser.username}!` };
            } else {
              return { success: false, message: `Couldn't find user: ${action.target_user}` };
            }
          }
          break;

        case 'create_group':
          const groupResponse = await axios.post(`${API}/chats`, {
            chat_type: 'group',
            name: action.name,
            members: []
          }, getAuthHeaders());
          
          fetchChats();
          setActiveChat(groupResponse.data);
          return { success: true, message: `Group "${action.name}" created!` };

        case 'add_contact':
          const contactResponse = await axios.post(`${API}/contacts`, {
            email: action.contact_info,
            contact_name: action.contact_info.split('@')[0]
          }, getAuthHeaders());
          
          fetchContacts();
          return { success: true, message: `Contact added: ${action.contact_info}` };

        case 'send_message':
          if (action.recipient && action.message) {
            // Find or create chat with recipient
            const searchResponse = await axios.get(`${API}/users/search?query=${action.recipient}`, getAuthHeaders());
            const users = searchResponse.data;
            const recipient = users.find(u => 
              u.username.toLowerCase().includes(action.recipient.toLowerCase()) ||
              u.display_name?.toLowerCase().includes(action.recipient.toLowerCase())
            );
            
            if (recipient) {
              // Create or find existing chat
              const chatResponse = await axios.post(`${API}/chats`, {
                chat_type: 'direct',
                other_user_id: recipient.user_id
              }, getAuthHeaders());
              
              // Send message
              await axios.post(`${API}/chats/${chatResponse.data.chat_id}/messages`, {
                content: action.message,
                message_type: 'text'
              }, getAuthHeaders());
              
              fetchChats();
              return { success: true, message: `Message sent to ${recipient.username}!` };
            }
          }
          break;

        case 'block_user':
          if (action.target_user) {
            const searchResponse = await axios.get(`${API}/users/search?query=${action.target_user}`, getAuthHeaders());
            const users = searchResponse.data;
            const targetUser = users.find(u => 
              u.username.toLowerCase().includes(action.target_user.toLowerCase()) ||
              u.display_name?.toLowerCase().includes(action.target_user.toLowerCase())
            );
            
            if (targetUser) {
              await axios.post(`${API}/users/${targetUser.user_id}/block`, {}, getAuthHeaders());
              fetchBlockedUsers();
              return { success: true, message: `User ${targetUser.username} blocked!` };
            }
          }
          break;

        case 'list_chats':
          fetchChats();
          return { success: true, message: "Your chats are now displayed!" };

        case 'list_contacts':
          fetchContacts();
          return { success: true, message: "Your contacts are now displayed!" };

        case 'show_help':
          // You could open a help modal or navigate to help
          return { success: true, message: "Here are the magical commands I understand:\n• Create chat with [name]\n• Add contact [email]\n• Send message to [name] saying [message]\n• Block user [name]\n• Show my chats/contacts\n• Create group called [name]\n• Create story [content]" };

        case 'show_settings':
          // You could open settings modal
          return { success: true, message: "Settings portal is now accessible through the app interface!" };

        default:
          return { success: false, message: "Unknown action type" };
      }
    } catch (error) {
      console.error('Genie action error:', error);
      return { success: false, message: `Error: ${error.response?.data?.detail || error.message}` };
    }
    
    return { success: false, message: "Action could not be completed" };
  };


  // Poll functions
  const createPoll = async () => {
    try {
      await axios.post(`${API}/polls`, {
        ...pollForm,
        chat_id: activeChat.chat_id
      }, getAuthHeaders());
      setShowCreatePoll(false);
      setPollForm({
        question: '',
        options: ['', ''],
        is_anonymous: false,
        allows_multiple_answers: false,
        expires_in_hours: null
      });
    } catch (error) {
      console.error('Error creating poll:', error);
    }
  };

  // Helper functions
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

  // Enhanced message rendering with all features
  const renderMessage = (message) => {
    const isEditing = editingMessage === message.message_id;
    
    return (
      <div
        key={message.message_id}
        className={`flex ${message.sender_id === user.user_id ? 'justify-end' : 'justify-start'} group mb-4`}
      >
        <div
          className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl relative ${
            message.sender_id === user.user_id
              ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white'
              : 'bg-white text-gray-800 shadow-lg border'
          } ${message.is_deleted ? 'opacity-50 italic' : ''}`}
        >
          {/* Reply indicator */}
          {message.reply_to && (
            <div className="text-xs opacity-75 border-l-2 border-current pl-2 mb-2">
              <span className="text-xs">↩️ Replying to previous message</span>
            </div>
          )}
          
          {/* Sender name for group chats */}
          {message.sender_id !== user.user_id && activeChat?.chat_type === 'group' && (
            <p className="text-xs font-medium mb-1 opacity-75">{message.sender_name}</p>
          )}
          
          {/* Message content */}
          {isEditing ? (
            <div>
              <input
                type="text"
                value={editText}
                onChange={(e) => setEditText(e.target.value)}
                className="w-full bg-transparent border-b text-current p-1"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    editMessage(message.message_id, editText);
                  }
                }}
                autoFocus
              />
              <div className="flex space-x-2 mt-2">
                <button
                  onClick={() => editMessage(message.message_id, editText)}
                  className="text-xs px-2 py-1 bg-green-500 text-white rounded"
                >
                  Save
                </button>
                <button
                  onClick={() => {
                    setEditingMessage(null);
                    setEditText('');
                  }}
                  className="text-xs px-2 py-1 bg-red-500 text-white rounded"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <>
              {/* Message type specific rendering */}
              {message.message_type === 'voice' ? (
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-current bg-opacity-20 rounded-full flex items-center justify-center">
                    <span className="text-lg">🎤</span>
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">Voice message</p>
                    <p className="text-xs opacity-75">{message.voice_duration}s</p>
                    {message.file_data && (
                      <audio controls className="mt-2 w-full">
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
                    className="max-w-full max-h-64 rounded-lg cursor-pointer transition-transform hover:scale-105"
                    onClick={() => window.open(`data:image/jpeg;base64,${message.file_data}`, '_blank')}
                  />
                  {message.content && <p className="mt-2">{message.content}</p>}
                </div>
              ) : message.message_type === 'file' ? (
                <div className="flex items-center space-x-3 p-3 bg-current bg-opacity-10 rounded-lg">
                  <span className="text-2xl">📎</span>
                  <div className="flex-1">
                    <p className="font-medium">{message.file_name}</p>
                    <p className="text-xs opacity-75">
                      {message.file_size ? `${(message.file_size / 1024).toFixed(1)} KB` : 'File'}
                    </p>
                  </div>
                </div>
              ) : (
                <p className="leading-relaxed">{message.content}</p>
              )}
              
              {/* Reactions */}
              {message.reactions && Object.keys(message.reactions).length > 0 && (
                <div className="flex flex-wrap gap-1 mt-3">
                  {Object.entries(message.reactions).map(([emoji, userIds]) => (
                    <button
                      key={emoji}
                      onClick={() => reactToMessage(message.message_id, emoji)}
                      className={`px-2 py-1 rounded-full text-xs flex items-center space-x-1 transition-all hover:scale-110 ${
                        userIds.includes(user.user_id)
                          ? 'bg-blue-100 text-blue-800 border border-blue-300'
                          : 'bg-gray-100 text-gray-600 border border-gray-300'
                      }`}
                    >
                      <span>{emoji}</span>
                      <span className="font-medium">{userIds.length}</span>
                    </button>
                  ))}
                </div>
              )}
              
              {/* Message actions */}
              <div className="opacity-0 group-hover:opacity-100 absolute -right-2 -top-2 flex space-x-1 transition-opacity">
                <button
                  onClick={() => setShowEmojiPicker(message.message_id)}
                  className="bg-gray-600 text-white rounded-full w-7 h-7 flex items-center justify-center text-xs hover:bg-gray-700 transition-colors"
                  title="React"
                >
                  😊
                </button>
                <button
                  onClick={() => setReplyToMessage(message)}
                  className="bg-blue-600 text-white rounded-full w-7 h-7 flex items-center justify-center text-xs hover:bg-blue-700 transition-colors"
                  title="Reply"
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
                      className="bg-yellow-600 text-white rounded-full w-7 h-7 flex items-center justify-center text-xs hover:bg-yellow-700 transition-colors"
                      title="Edit"
                    >
                      ✏️
                    </button>
                    <button
                      onClick={() => deleteMessage(message.message_id)}
                      className="bg-red-600 text-white rounded-full w-7 h-7 flex items-center justify-center text-xs hover:bg-red-700 transition-colors"
                      title="Delete"
                    >
                      🗑️
                    </button>
                  </>
                )}
              </div>
            </>
          )}
          
          {/* Timestamp and status */}
          <div className="flex items-center justify-between mt-2">
            <p className={`text-xs opacity-75`}>
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

  // Login/Register views with enhanced UI
  if (currentView === 'login') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 flex items-center justify-center p-4">
        <div className="bg-white/10 backdrop-blur-lg rounded-3xl shadow-2xl p-8 w-full max-w-md border border-white/20">
          <div className="text-center mb-8">
            <div className="text-8xl mb-4">🚀</div>
            <h1 className="text-4xl font-bold text-white mb-2">
              ChatApp Pro 
              <span className="text-2xl ml-2">Ultimate</span>
            </h1>
            <p className="text-gray-200">The Ultimate Communication Platform</p>
            <div className="flex flex-wrap justify-center gap-2 mt-3 text-xs text-gray-300">
              <span className="bg-white/20 px-2 py-1 rounded-full">🔒 Encryption</span>
              <span className="bg-white/20 px-2 py-1 rounded-full">📞 Calls</span>
              <span className="bg-white/20 px-2 py-1 rounded-full">📖 Stories</span>
              <span className="bg-white/20 px-2 py-1 rounded-full">📢 Channels</span>
              <span className="bg-white/20 px-2 py-1 rounded-full">🎤 Voice Rooms</span>
              <span className="bg-white/20 px-2 py-1 rounded-full">🔍 Discovery</span>
            </div>
          </div>
          
          <div className="flex mb-6">
            <button
              onClick={() => setCurrentView('login')}
              className={`flex-1 py-3 px-4 rounded-l-xl font-medium transition-all ${
                currentView === 'login' 
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg' 
                  : 'bg-white/20 text-gray-200 hover:bg-white/30'
              }`}
            >
              Login
            </button>
            <button
              onClick={() => setCurrentView('register')}
              className={`flex-1 py-3 px-4 rounded-r-xl font-medium transition-all ${
                currentView === 'register' 
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg' 
                  : 'bg-white/20 text-gray-200 hover:bg-white/30'
              }`}
            >
              Register
            </button>
          </div>

          <form onSubmit={login} className="space-y-4">
            <div>
              <input
                type="email"
                placeholder="Email"
                className="w-full p-4 bg-white/20 border border-white/30 rounded-xl text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:bg-white/30 transition-all"
                value={loginForm.email}
                onChange={(e) => setLoginForm({...loginForm, email: e.target.value})}
                required
              />
            </div>
            <div>
              <input
                type="password"
                placeholder="Password"
                className="w-full p-4 bg-white/20 border border-white/30 rounded-xl text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:bg-white/30 transition-all"
                value={loginForm.password}
                onChange={(e) => setLoginForm({...loginForm, password: e.target.value})}
                required
              />
            </div>
            <button
              type="submit"
              className="w-full bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 text-white py-4 rounded-xl font-medium hover:shadow-2xl hover:scale-105 transition-all duration-300"
            >
              🚀 Launch ChatApp Pro
            </button>
          </form>
        </div>
      </div>
    );
  }

  if (currentView === 'register') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 flex items-center justify-center p-4">
        <div className="bg-white/10 backdrop-blur-lg rounded-3xl shadow-2xl p-8 w-full max-w-md border border-white/20">
          <div className="text-center mb-8">
            <div className="text-8xl mb-4">🚀</div>
            <h1 className="text-4xl font-bold text-white mb-2">
              Join ChatApp Pro
            </h1>
            <p className="text-gray-200">Create your ultimate account</p>
          </div>
          
          <div className="flex mb-6">
            <button
              onClick={() => setCurrentView('login')}
              className={`flex-1 py-3 px-4 rounded-l-xl font-medium transition-all ${
                currentView === 'login' 
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg' 
                  : 'bg-white/20 text-gray-200 hover:bg-white/30'
              }`}
            >
              Login
            </button>
            <button
              onClick={() => setCurrentView('register')}
              className={`flex-1 py-3 px-4 rounded-r-xl font-medium transition-all ${
                currentView === 'register' 
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg' 
                  : 'bg-white/20 text-gray-200 hover:bg-white/30'
              }`}
            >
              Register
            </button>
          </div>

          <form onSubmit={register} className="space-y-4">
            <div>
              <input
                type="text"
                placeholder="Username"
                className="w-full p-4 bg-white/20 border border-white/30 rounded-xl text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:bg-white/30 transition-all"
                value={registerForm.username}
                onChange={(e) => setRegisterForm({...registerForm, username: e.target.value})}
                required
              />
            </div>
            <div>
              <input
                type="text"
                placeholder="Display Name (optional)"
                className="w-full p-4 bg-white/20 border border-white/30 rounded-xl text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:bg-white/30 transition-all"
                value={registerForm.display_name}
                onChange={(e) => setRegisterForm({...registerForm, display_name: e.target.value})}
              />
            </div>
            <div>
              <input
                type="email"
                placeholder="Email"
                className="w-full p-4 bg-white/20 border border-white/30 rounded-xl text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:bg-white/30 transition-all"
                value={registerForm.email}
                onChange={(e) => setRegisterForm({...registerForm, email: e.target.value})}
                required
              />
            </div>
            <div>
              <input
                type="tel"
                placeholder="Phone (optional)"
                className="w-full p-4 bg-white/20 border border-white/30 rounded-xl text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:bg-white/30 transition-all"
                value={registerForm.phone}
                onChange={(e) => setRegisterForm({...registerForm, phone: e.target.value})}
              />
            </div>
            <div>
              <input
                type="password"
                placeholder="Password"
                className="w-full p-4 bg-white/20 border border-white/30 rounded-xl text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:bg-white/30 transition-all"
                value={registerForm.password}
                onChange={(e) => setRegisterForm({...registerForm, password: e.target.value})}
                required
              />
            </div>
            <button
              type="submit"
              className="w-full bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 text-white py-4 rounded-xl font-medium hover:shadow-2xl hover:scale-105 transition-all duration-300"
            >
              🚀 Create Ultimate Account
            </button>
          </form>
        </div>
      </div>
    );
  }

  // Main Chat View with WhatsApp-like Design
  return (
    <div className="h-screen flex bg-gray-100">
      {/* WhatsApp-style Sidebar */}
      <div className="w-1/3 bg-white border-r border-gray-200 flex flex-col shadow-sm">
        {/* WhatsApp-style Header */}
        <div className="p-4 bg-gray-50 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="relative">
                <div className="w-12 h-12 bg-gray-300 rounded-full flex items-center justify-center">
                  <span className="font-medium text-lg text-gray-700">
                    {user.username.charAt(0).toUpperCase()}
                  </span>
                </div>
                <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white"></div>
              </div>
              <div className="ml-3">
                <p className="font-medium text-lg text-gray-900">{user.display_name || user.username}</p>
                <p className="text-sm text-gray-500">
                  {isConnected ? 'Online' : 'Connecting...'}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowDiscovery(!showDiscovery)}
                className="text-gray-500 hover:text-gray-700 p-2 rounded-lg hover:bg-gray-100 transition-all"
                title="Discover"
              >
                🔍
              </button>
              <button
                onClick={() => setShowPrivacySettings(!showPrivacySettings)}
                className="text-gray-500 hover:text-gray-700 p-2 rounded-lg hover:bg-gray-100 transition-all"
                title="Privacy"
              >
                🛡️
              </button>
              <button
                onClick={() => setShowBackupRestore(!showBackupRestore)}
                className="text-gray-500 hover:text-gray-700 p-2 rounded-lg hover:bg-gray-100 transition-all"
                title="Backup"
              >
                💾
              </button>
              <button
                onClick={() => setShowProfileEditor(!showProfileEditor)}
                className="text-gray-500 hover:text-gray-700 p-2 rounded-lg hover:bg-gray-100 transition-all"
                title="Profile"
              >
                👤
              </button>
              <button
                onClick={() => setShowWorkspaceSwitcher(!showWorkspaceSwitcher)}
                className={`text-gray-500 hover:text-gray-700 p-2 rounded-lg hover:bg-gray-100 transition-all ${
                  workspaceMode === 'business' ? 'bg-purple-100 text-purple-700' : ''
                }`}
                title="Workspace"
              >
                {workspaceMode === 'personal' ? '🏠' : '🏢'}
              </button>
              <button
                onClick={() => setShowCalendar(!showCalendar)}
                className="text-gray-500 hover:text-gray-700 p-2 rounded-lg hover:bg-gray-100 transition-all"
                title="Calendar"
              >
                📅
              </button>
              <button
                onClick={() => setShowTasks(!showTasks)}
                className="text-gray-500 hover:text-gray-700 p-2 rounded-lg hover:bg-gray-100 transition-all"
                title="Tasks"
              >
                ✅
              </button>
              <button
                onClick={() => setShowGameCenter(!showGameCenter)}
                className="text-gray-500 hover:text-gray-700 p-2 rounded-lg hover:bg-gray-100 transition-all"
                title="Games"
              >
                🎮
              </button>
              <button
                onClick={() => setShowCustomization(!showCustomization)}
                className="text-gray-500 hover:text-gray-700 p-2 rounded-lg hover:bg-gray-100 transition-all"
                title="Customize"
              >
                🎨
              </button>
              <button
                onClick={logout}
                className="text-gray-500 hover:text-gray-700 p-2 rounded-lg hover:bg-gray-100 transition-all"
                title="Logout"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* Enhanced Stories section */}
        {stories.length > 0 && (
          <div className="p-4 border-b border-white/10">
            <div className="flex items-center space-x-2 mb-3">
              <span className="text-sm font-semibold text-white/80">✨ Stories</span>
              <div className="w-2 h-2 bg-gradient-to-r from-pink-400 to-purple-400 rounded-full animate-pulse"></div>
            </div>
            <div className="flex space-x-4 overflow-x-auto scrollbar-hide">
              {stories.map(userStories => (
                <div
                  key={userStories.user.user_id}
                  className="flex-shrink-0 text-center cursor-pointer group"
                  onClick={() => setActiveStory(userStories)}
                >
                  <div className="w-14 h-14 bg-gradient-to-br from-purple-400 to-pink-400 rounded-full p-0.5 group-hover:scale-110 transition-transform">
                    <div className="w-full h-full bg-gray-300 rounded-full flex items-center justify-center text-white font-bold">
                      {userStories.user.username.charAt(0).toUpperCase()}
                    </div>
                  </div>
                  <p className="text-xs mt-1 truncate w-14 font-medium">{userStories.user.username}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Voice Rooms */}
        {voiceRooms.length > 0 && (
          <div className="p-3 border-b border-gray-200/50">
            <h3 className="text-sm font-medium text-gray-700 mb-2">🎤 Active Voice Rooms</h3>
            <div className="space-y-2">
              {voiceRooms.slice(0, 3).map(room => (
                <div
                  key={room.room_id}
                  className={`p-2 rounded-lg cursor-pointer transition-all ${
                    activeVoiceRoom === room.room_id 
                      ? 'bg-green-100 border border-green-300' 
                      : 'bg-gray-50 hover:bg-gray-100'
                  }`}
                  onClick={() => joinVoiceRoom(room.room_id)}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-sm">{room.name}</p>
                      <p className="text-xs text-gray-500">
                        {room.participant_count}/{room.max_participants} users
                      </p>
                    </div>
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Search */}
        <div className="p-3">
          <input
            type="text"
            placeholder="Search everything... 🔍"
            className="w-full p-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 bg-white/50 backdrop-blur-sm"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              // searchUsers(e.target.value);
            }}
          />
        </div>

        {/* Ultimate Actions Grid */}
        <div className="px-3 pb-3 grid grid-cols-3 gap-2">
          <button
            onClick={() => setShowAddContact(true)}
            className="bg-gradient-to-r from-green-500 to-emerald-500 text-white py-2 rounded-lg text-xs hover:shadow-lg transition-all flex flex-col items-center"
          >
            <span className="text-lg">👥</span>
            <span>Add</span>
          </button>
          <button
            onClick={() => setShowCreateGroup(true)}
            className="bg-gradient-to-r from-purple-500 to-violet-500 text-white py-2 rounded-lg text-xs hover:shadow-lg transition-all flex flex-col items-center"
          >
            <span className="text-lg">👨‍👩‍👧‍👦</span>
            <span>Group</span>
          </button>
          <button
            onClick={() => setShowCreateChannel(true)}
            className="bg-gradient-to-r from-blue-500 to-cyan-500 text-white py-2 rounded-lg text-xs hover:shadow-lg transition-all flex flex-col items-center"
          >
            <span className="text-lg">📢</span>
            <span>Channel</span>
          </button>
          <button
            onClick={() => setShowCreateStory(true)}
            className="bg-gradient-to-r from-pink-500 to-rose-500 text-white py-2 rounded-lg text-xs hover:shadow-lg transition-all flex flex-col items-center"
          >
            <span className="text-lg">📖</span>
            <span>Story</span>
          </button>
          <button
            onClick={() => setShowCreateVoiceRoom(true)}
            className="bg-gradient-to-r from-orange-500 to-red-500 text-white py-2 rounded-lg text-xs hover:shadow-lg transition-all flex flex-col items-center"
          >
            <span className="text-lg">🎤</span>
            <span>Voice</span>
          </button>
          <button
            onClick={() => setShowCreatePoll(true)}
            className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white py-2 rounded-lg text-xs hover:shadow-lg transition-all flex flex-col items-center"
          >
            <span className="text-lg">📊</span>
            <span>Poll</span>
          </button>
        </div>

        {/* Enhanced Chat List */}
        <div className="flex-1 overflow-y-auto">
          {chats.length === 0 ? (
            <div className="p-6 text-center text-gray-500">
              <div className="text-8xl mb-4">🚀</div>
              <p className="font-medium text-lg mb-2">Welcome to ChatApp Pro Ultimate!</p>
              <p className="text-sm">Create your first chat, story, channel, or voice room</p>
              <div className="mt-4 text-xs space-y-1">
                <div className="flex items-center justify-center">
                  <span className="mr-2">🔒</span>
                  <span>End-to-end encryption</span>
                </div>
                <div className="flex items-center justify-center">
                  <span className="mr-2">🎥</span>
                  <span>Video calls & screen sharing</span>
                </div>
                <div className="flex items-center justify-center">
                  <span className="mr-2">🌐</span>
                  <span>Global discovery & channels</span>
                </div>
              </div>
            </div>
          ) : (
            chats.map(chat => (
              <div
                key={chat.chat_id}
                className={`p-4 border-b border-gray-100/50 cursor-pointer transition-all duration-200 ${
                  activeChat?.chat_id === chat.chat_id 
                    ? 'bg-gradient-to-r from-purple-100 to-blue-100 border-purple-200 shadow-lg' 
                    : 'hover:bg-gradient-to-r hover:from-gray-50 hover:to-blue-50'
                }`}
                onClick={() => selectChat(chat)}
              >
                <div className="flex items-center">
                  <div className="w-14 h-14 bg-gradient-to-br from-blue-400 to-purple-400 rounded-full flex items-center justify-center relative shadow-lg">
                    <span className="text-white font-medium text-lg">
                      {chat.chat_type === 'direct' 
                        ? chat.other_user?.username?.charAt(0).toUpperCase() || '?'
                        : chat.name?.charAt(0).toUpperCase() || 'G'
                      }
                    </span>
                    {chat.other_user?.is_online && (
                      <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-400 rounded-full border-2 border-white animate-pulse"></div>
                    )}
                  </div>
                  <div className="ml-4 flex-1">
                    <div className="flex items-center justify-between">
                      <p className="font-medium text-gray-800">
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
                      <div className="flex items-center mt-1">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                          <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                        </div>
                        <p className="text-xs text-purple-500 italic ml-2">typing...</p>
                      </div>
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
            <div className="p-4 bg-white border-b border-gray-200 flex items-center justify-between">
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
                  <p className="font-medium text-gray-900">
                    {activeChat.chat_type === 'direct' 
                      ? activeChat.other_user?.username || 'Unknown User'
                      : activeChat.name
                    } <span className="text-xs text-gray-500">🔒</span>
                  </p>
                  <p className="text-xs text-gray-500">
                    {activeChat.chat_type === 'direct' 
                      ? activeChat.other_user?.is_online ? 'Online' : 'Offline'
                      : `${activeChat.members?.length || 0} members`
                    }
                  </p>
                </div>
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={() => initiateCall('voice')}
                  className="p-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-full transition-colors"
                  title="Voice Call"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                  </svg>
                </button>
                <button
                  onClick={() => initiateCall('video')}
                  className="p-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-full transition-colors"
                  title="Video Call"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                </button>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="p-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-full transition-colors"
                  title="Attach File"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                  </svg>
                </button>
                {activeChat.chat_type === 'direct' && (
                  <>
                    <button
                      onClick={() => {
                        if (window.confirm(`Block ${activeChat.other_user?.username}?`)) {
                          axios.post(`${API}/users/${activeChat.other_user?.user_id}/block`, {}, getAuthHeaders())
                            .then(() => {
                              fetchBlockedUsers();
                              alert(`${activeChat.other_user?.username} has been blocked`);
                            })
                            .catch(error => {
                              console.error('Error blocking user:', error);
                            });
                        }
                      }}
                      className="p-2 text-gray-600 hover:text-red-600 hover:bg-gray-100 rounded-full transition-colors"
                      title="Block User"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                      </svg>
                    </button>
                    <button
                      onClick={() => {
                        setReportForm({
                          ...reportForm,
                          user_id: activeChat.other_user?.user_id,
                          chat_id: activeChat.chat_id
                        });
                        setShowReportModal(true);
                      }}
                      className="p-2 text-gray-600 hover:text-orange-600 hover:bg-gray-100 rounded-full transition-colors"
                      title="Report User"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* Messages Area */}
            <div 
              className="flex-1 p-4 overflow-y-auto bg-gray-50"
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragOver(false);
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                  // Handle file upload
                  const file = files[0];
                  if (file.size > 10 * 1024 * 1024) {
                    alert('File size exceeds 10MB limit');
                    return;
                  }
                  
                  setUploadingFile(true);
                  const reader = new FileReader();
                  reader.onload = async () => {
                    const base64Data = reader.result.split(',')[1];
                    
                    try {
                      const messageType = file.type.startsWith('image/') ? 'image' : 'file';
                      await axios.post(`${API}/chats/${activeChat.chat_id}/messages`, {
                        content: file.name,
                        message_type: messageType,
                        file_data: base64Data,
                        file_name: file.name,
                        file_size: file.size,
                        file_type: file.type
                      }, getAuthHeaders());
                      
                      setUploadingFile(false);
                    } catch (error) {
                      console.error('Error uploading file:', error);
                      setUploadingFile(false);
                      alert('Failed to upload file');
                    }
                  };
                  reader.readAsDataURL(file);
                }
              }}
            >
              {messages.map(message => renderMessage(message))}
              <div ref={messagesEndRef} />
              
              {/* File Drop Overlay */}
              {dragOver && (
                <div className="absolute inset-0 bg-blue-500 bg-opacity-20 flex items-center justify-center">
                  <div className="bg-white p-6 rounded-lg shadow-xl">
                    <p className="text-lg font-medium">Drop file to send</p>
                    <p className="text-sm text-gray-500">Max size: 10MB</p>
                  </div>
                </div>
              )}
              
              {/* File Upload Progress */}
              {uploadingFile && (
                <div className="fixed bottom-20 right-8 bg-white p-4 rounded-lg shadow-lg">
                  <div className="flex items-center">
                    <svg className="animate-spin h-5 w-5 mr-3 text-blue-500" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>Uploading file...</span>
                  </div>
                </div>
              )}
            </div>

            {/* Reply to Message */}
            {replyToMessage && (
              <div className="bg-gray-100 p-3 border-t border-gray-200">
                <div className="flex justify-between items-center">
                  <div className="flex items-center">
                    <div className="w-1 h-8 bg-blue-500 rounded-full mr-2"></div>
                    <div>
                      <p className="text-xs text-gray-500">Replying to</p>
                      <p className="text-sm font-medium truncate max-w-md">{replyToMessage.content}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setReplyToMessage(null)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    ✕
                  </button>
                </div>
              </div>
            )}

            {/* Message Input */}
            <div className="p-3 bg-white border-t border-gray-200">
              <form onSubmit={sendMessage} className="flex items-center space-x-2">
                <button
                  type="button"
                  className="p-2 text-gray-500 hover:text-gray-700 rounded-full hover:bg-gray-100"
                  onClick={() => setShowEmojiPicker(true)}
                >
                  😊
                </button>
                <div className="relative flex-1">
                  <input
                    type="text"
                    placeholder="Type a message..."
                    className="w-full p-3 pr-10 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                  />
                  <button
                    type="button"
                    className={`absolute right-3 top-1/2 transform -translate-y-1/2 p-1 rounded-full ${
                      isRecording ? 'text-red-500 bg-red-100' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                    }`}
                    onMouseDown={startRecording}
                    onMouseUp={stopRecording}
                    onMouseLeave={() => isRecording && stopRecording()}
                  >
                    🎤
                    {isRecording && (
                      <span className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-red-500 text-white text-xs py-1 px-2 rounded">
                        {recordingDuration}s
                      </span>
                    )}
                  </button>
                </div>
                <button
                  type="submit"
                  className="p-3 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors"
                  disabled={!newMessage.trim() && !replyToMessage}
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                </button>
                <input
                  type="file"
                  ref={fileInputRef}
                  className="hidden"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) {
                      if (file.size > 10 * 1024 * 1024) {
                        alert('File size exceeds 10MB limit');
                        return;
                      }
                      
                      setUploadingFile(true);
                      const reader = new FileReader();
                      reader.onload = async () => {
                        const base64Data = reader.result.split(',')[1];
                        
                        try {
                          const messageType = file.type.startsWith('image/') ? 'image' : 'file';
                          await axios.post(`${API}/chats/${activeChat.chat_id}/messages`, {
                            content: file.name,
                            message_type: messageType,
                            file_data: base64Data,
                            file_name: file.name,
                            file_size: file.size,
                            file_type: file.type
                          }, getAuthHeaders());
                          
                          setUploadingFile(false);
                          e.target.value = '';
                        } catch (error) {
                          console.error('Error uploading file:', error);
                          setUploadingFile(false);
                          alert('Failed to upload file');
                        }
                      };
                      reader.readAsDataURL(file);
                    }
                  }}
                />
              </form>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center bg-gray-50">
            <div className="text-center p-8 max-w-md">
              <div className="text-8xl mb-6">🚀</div>
              <h2 className="text-2xl font-bold text-gray-800 mb-2">Welcome to ChatApp Pro Ultimate!</h2>
              <p className="text-gray-600 mb-6">Select a chat to start messaging or create a new one.</p>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                  <div className="text-3xl mb-2">🔒</div>
                  <h3 className="font-medium text-gray-800">End-to-End Encryption</h3>
                  <p className="text-sm text-gray-600">Your messages are secure and private</p>
                </div>
                <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                  <div className="text-3xl mb-2">📱</div>
                  <h3 className="font-medium text-gray-800">Multi-Device</h3>
                  <p className="text-sm text-gray-600">Access your chats from anywhere</p>
                </div>
                <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                  <div className="text-3xl mb-2">🎮</div>
                  <h3 className="font-medium text-gray-800">Games & Fun</h3>
                  <p className="text-sm text-gray-600">Play games with your friends</p>
                </div>
                <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                  <div className="text-3xl mb-2">🎨</div>
                  <h3 className="font-medium text-gray-800">Customization</h3>
                  <p className="text-sm text-gray-600">Make it your own with themes</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Add Contact Modal */}
      {showAddContact && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-[90vw]">
            <h3 className="text-lg font-semibold mb-4">Add New Contact</h3>
            <form onSubmit={(e) => {
              e.preventDefault();
              axios.post(`${API}/contacts`, contactForm, getAuthHeaders())
                .then(() => {
                  setShowAddContact(false);
                  setContactForm({ email: '', contact_name: '' });
                  fetchContacts();
                  alert('Contact added successfully!');
                })
                .catch(error => {
                  console.error('Error adding contact:', error);
                  alert('Failed to add contact: ' + (error.response?.data?.detail || error.message));
                });
            }}>
              <div className="space-y-4">
                <input
                  type="email"
                  placeholder="Email Address"
                  className="w-full p-3 border rounded-lg"
                  value={contactForm.email}
                  onChange={(e) => setContactForm({...contactForm, email: e.target.value})}
                  required
                />
                <input
                  type="text"
                  placeholder="Contact Name (optional)"
                  className="w-full p-3 border rounded-lg"
                  value={contactForm.contact_name}
                  onChange={(e) => setContactForm({...contactForm, contact_name: e.target.value})}
                />
              </div>
              <div className="flex space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowAddContact(false)}
                  className="flex-1 py-2 border rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 bg-blue-600 text-white rounded-lg"
                >
                  Add Contact
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Group Modal */}
      {showCreateGroup && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-[90vw]">
            <h3 className="text-lg font-semibold mb-4">Create New Group</h3>
            <form onSubmit={(e) => {
              e.preventDefault();
              const groupData = {
                ...groupForm,
                members: selectedMembers
              };
              axios.post(`${API}/chats`, groupData, getAuthHeaders())
                .then(response => {
                  setShowCreateGroup(false);
                  setGroupForm({ name: '', description: '', members: [], chat_type: 'group' });
                  setSelectedMembers([]);
                  fetchChats();
                  setActiveChat(response.data);
                })
                .catch(error => {
                  console.error('Error creating group:', error);
                  alert('Failed to create group: ' + (error.response?.data?.detail || error.message));
                });
            }}>
              <div className="space-y-4">
                <input
                  type="text"
                  placeholder="Group Name"
                  className="w-full p-3 border rounded-lg"
                  value={groupForm.name}
                  onChange={(e) => setGroupForm({...groupForm, name: e.target.value})}
                  required
                />
                <textarea
                  placeholder="Group Description (optional)"
                  className="w-full p-3 border rounded-lg h-20"
                  value={groupForm.description}
                  onChange={(e) => setGroupForm({...groupForm, description: e.target.value})}
                />
                <div>
                  <p className="text-sm font-medium mb-2">Select Members:</p>
                  <div className="max-h-40 overflow-y-auto border rounded-lg p-2">
                    {contacts.length === 0 ? (
                      <p className="text-sm text-gray-500 p-2">No contacts available</p>
                    ) : (
                      contacts.map(contact => (
                        <label key={contact.user_id} className="flex items-center p-2 hover:bg-gray-50">
                          <input
                            type="checkbox"
                            checked={selectedMembers.includes(contact.user_id)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedMembers([...selectedMembers, contact.user_id]);
                              } else {
                                setSelectedMembers(selectedMembers.filter(id => id !== contact.user_id));
                              }
                            }}
                            className="mr-3"
                          />
                          <span>{contact.contact_name || contact.username}</span>
                        </label>
                      ))
                    )}
                  </div>
                </div>
              </div>
              <div className="flex space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowCreateGroup(false)}
                  className="flex-1 py-2 border rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 bg-blue-600 text-white rounded-lg"
                  disabled={groupForm.name.trim() === '' || selectedMembers.length === 0}
                >
                  Create Group
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Report User Modal */}
      {showReportModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-[90vw]">
            <h3 className="text-lg font-semibold mb-4">Report User</h3>
            <form onSubmit={(e) => {
              e.preventDefault();
              axios.post(`${API}/users/report`, reportForm, getAuthHeaders())
                .then(() => {
                  setShowReportModal(false);
                  setReportForm({
                    user_id: '',
                    reason: '',
                    description: '',
                    message_id: null,
                    chat_id: null
                  });
                  alert('Report submitted successfully');
                })
                .catch(error => {
                  console.error('Error reporting user:', error);
                  alert('Failed to submit report: ' + (error.response?.data?.detail || error.message));
                });
            }}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Reason</label>
                  <select
                    value={reportForm.reason}
                    onChange={(e) => setReportForm({...reportForm, reason: e.target.value})}
                    className="w-full p-3 border rounded-lg"
                    required
                  >
                    <option value="">Select a reason</option>
                    <option value="spam">Spam</option>
                    <option value="harassment">Harassment</option>
                    <option value="inappropriate_content">Inappropriate Content</option>
                    <option value="impersonation">Impersonation</option>
                    <option value="hate_speech">Hate Speech</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <textarea
                    placeholder="Please provide details about the issue"
                    className="w-full p-3 border rounded-lg h-32"
                    value={reportForm.description}
                    onChange={(e) => setReportForm({...reportForm, description: e.target.value})}
                    required
                  />
                </div>
              </div>
              <div className="flex space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowReportModal(false)}
                  className="flex-1 py-2 border rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 bg-red-600 text-white rounded-lg"
                >
                  Submit Report
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Customization Modal */}
      {showCustomization && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-[90vw]">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Customize Appearance</h3>
              <button
                onClick={() => setShowCustomization(false)}
                className="text-gray-500 hover:text-gray-700 p-2"
              >
                ✕
              </button>
            </div>
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Font Family</label>
                <select
                  value={customSettings.fontFamily}
                  onChange={(e) => {
                    const newSettings = {...customSettings, fontFamily: e.target.value};
                    setCustomSettings(newSettings);
                    const root = document.documentElement;
                    root.style.setProperty('--font-family', e.target.value);
                  }}
                  className="w-full p-3 border rounded-lg"
                >
                  <option value="Inter">Inter (Modern)</option>
                  <option value="Roboto">Roboto (Android)</option>
                  <option value="San Francisco">SF Pro (iOS)</option>
                  <option value="Helvetica Neue">Helvetica Neue</option>
                  <option value="Arial">Arial (Classic)</option>
                  <option value="Georgia">Georgia (Serif)</option>
                  <option value="Courier New">Courier (Mono)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Font Size</label>
                <div className="flex space-x-2">
                  {['small', 'medium', 'large', 'xl'].map(size => (
                    <button
                      key={size}
                      onClick={() => {
                        const newSettings = {...customSettings, fontSize: size};
                        setCustomSettings(newSettings);
                        const root = document.documentElement;
                        root.style.setProperty('--font-size', size === 'small' ? '12px' : size === 'large' ? '16px' : size === 'xl' ? '18px' : '14px');
                      }}
                      className={`flex-1 py-2 px-3 rounded-lg border ${
                        customSettings.fontSize === size
                          ? 'bg-blue-100 border-blue-300 text-blue-800'
                          : 'bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      {size.charAt(0).toUpperCase() + size.slice(1)}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Background Color</label>
                <div className="flex items-center space-x-3">
                  <input
                    type="color"
                    value={customSettings.backgroundColor}
                    onChange={(e) => {
                      const newSettings = {...customSettings, backgroundColor: e.target.value};
                      setCustomSettings(newSettings);
                      const root = document.documentElement;
                      root.style.setProperty('--bg-color', e.target.value);
                    }}
                    className="w-12 h-10 rounded border"
                  />
                  <input
                    type="text"
                    value={customSettings.backgroundColor}
                    onChange={(e) => {
                      const newSettings = {...customSettings, backgroundColor: e.target.value};
                      setCustomSettings(newSettings);
                      const root = document.documentElement;
                      root.style.setProperty('--bg-color', e.target.value);
                    }}
                    className="flex-1 p-2 border rounded-lg"
                    placeholder="#ffffff"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Primary Color</label>
                <div className="flex items-center space-x-3">
                  <input
                    type="color"
                    value={customSettings.primaryColor}
                    onChange={(e) => {
                      const newSettings = {...customSettings, primaryColor: e.target.value};
                      setCustomSettings(newSettings);
                      const root = document.documentElement;
                      root.style.setProperty('--primary-color', e.target.value);
                    }}
                    className="w-12 h-10 rounded border"
                  />
                  <input
                    type="text"
                    value={customSettings.primaryColor}
                    onChange={(e) => {
                      const newSettings = {...customSettings, primaryColor: e.target.value};
                      setCustomSettings(newSettings);
                      const root = document.documentElement;
                      root.style.setProperty('--primary-color', e.target.value);
                    }}
                    className="flex-1 p-2 border rounded-lg"
                    placeholder="#25D366"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Text Color</label>
                <div className="flex items-center space-x-3">
                  <input
                    type="color"
                    value={customSettings.textColor}
                    onChange={(e) => {
                      const newSettings = {...customSettings, textColor: e.target.value};
                      setCustomSettings(newSettings);
                      const root = document.documentElement;
                      root.style.setProperty('--text-color', e.target.value);
                    }}
                    className="w-12 h-10 rounded border"
                  />
                  <input
                    type="text"
                    value={customSettings.textColor}
                    onChange={(e) => {
                      const newSettings = {...customSettings, textColor: e.target.value};
                      setCustomSettings(newSettings);
                      const root = document.documentElement;
                      root.style.setProperty('--text-color', e.target.value);
                    }}
                    className="flex-1 p-2 border rounded-lg"
                    placeholder="#000000"
                  />
                </div>
              </div>
              <div>
                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={customSettings.theme === 'dark'}
                    onChange={(e) => {
                      const newTheme = e.target.checked ? 'dark' : 'light';
                      const newSettings = {...customSettings, theme: newTheme};
                      setCustomSettings(newSettings);
                      if (newTheme === 'dark') {
                        document.body.setAttribute('data-theme', 'dark');
                      } else {
                        document.body.removeAttribute('data-theme');
                      }
                    }}
                    className="rounded"
                  />
                  <span>Dark Mode</span>
                </label>
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={() => {
                    const defaultSettings = {
                      fontFamily: 'Inter',
                      fontSize: 'medium',
                      backgroundColor: 'white',
                      primaryColor: '#25D366',
                      textColor: 'black',
                      userNameColor: '#128C7E',
                      theme: 'light'
                    };
                    setCustomSettings(defaultSettings);
                    localStorage.removeItem('chatapp-custom-settings');
                    
                    // Apply default settings
                    const root = document.documentElement;
                    root.style.setProperty('--font-family', defaultSettings.fontFamily);
                    root.style.setProperty('--font-size', '14px');
                    root.style.setProperty('--bg-color', defaultSettings.backgroundColor);
                    root.style.setProperty('--primary-color', defaultSettings.primaryColor);
                    root.style.setProperty('--text-color', defaultSettings.textColor);
                    root.style.setProperty('--username-color', defaultSettings.userNameColor);
                    document.body.removeAttribute('data-theme');
                  }}
                  className="flex-1 py-2 border rounded-lg"
                >
                  Reset to Default
                </button>
                <button
                  onClick={() => {
                    localStorage.setItem('chatapp-custom-settings', JSON.stringify(customSettings));
                    setShowCustomization(false);
                  }}
                  className="flex-1 py-2 bg-blue-600 text-white rounded-lg"
                >
                  Save Changes
                </button>
              </div>
              <div className="text-center">
                <button
                  onClick={() => setShowAdvancedCustomization(true)}
                  className="text-blue-600 hover:text-blue-800 text-sm"
                >
                  Advanced Customization Options
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Workspace Switcher */}
      {showWorkspaceSwitcher && (
        <WorkspaceSwitcher
          user={user}
          token={token}
          currentMode={workspaceMode}
          onModeChange={setWorkspaceMode}
          onClose={() => setShowWorkspaceSwitcher(false)}
        />
      )}

      {/* Calendar */}
      {showCalendar && (
        <Calendar
          user={user}
          token={token}
          workspaceMode={workspaceMode}
          onClose={() => setShowCalendar(false)}
        />
      )}

      {/* Task Manager */}
      {showTasks && (
        <TaskManager
          user={user}
          token={token}
          workspaceMode={workspaceMode}
          onClose={() => setShowTasks(false)}
        />
      )}

      {/* Game Center */}
      {showGameCenter && (
        <GameCenter
          user={user}
          token={token}
          activeChat={activeChat}
          onClose={() => setShowGameCenter(false)}
          onSendMessage={(content, messageType, metadata) => {
            if (!activeChat) return;
            
            const messageData = {
              content,
              message_type: messageType || 'text'
            };
            
            if (metadata) {
              messageData.metadata = JSON.stringify(metadata);
            }
            
            axios.post(`${API}/chats/${activeChat.chat_id}/messages`, messageData, getAuthHeaders())
              .catch(error => {
                console.error('Error sending game message:', error);
              });
          }}
        />
      )}

      {/* Advanced Customization */}
      {showAdvancedCustomization && (
        <AdvancedCustomization
          onClose={() => setShowAdvancedCustomization(false)}
          currentSettings={customSettings}
          onSettingsChange={(newSettings) => {
            setCustomSettings(newSettings);
            localStorage.setItem('chatapp-custom-settings', JSON.stringify(newSettings));
          }}
        />
      )}

      {/* Genie Assistant */}
      <GenieAssistant
        user={user}
        token={token}
        onAction={handleGenieAction}
      />
    </div>
  );
}

export default App;
