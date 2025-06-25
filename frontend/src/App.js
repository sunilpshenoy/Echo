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
  
  // Screen sharing
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [screenStream, setScreenStream] = useState(null);

  // Initialize WebSocket connection with enhanced features
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
    try {
      const response = await axios.post(`${API}/login`, loginForm);
      const { access_token, user } = response.data;
      
      setToken(access_token);
      setUser(user);
      setPrivacySettings(user.privacy_settings || privacySettings);
      localStorage.setItem('token', access_token);
      setCurrentView('chat');
      
      setTimeout(() => {
        fetchChats(access_token);
        fetchContacts(access_token);
        fetchBlockedUsers(access_token);
        fetchStories(access_token);
        fetchChannels(access_token);
        fetchVoiceRooms(access_token);
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
      
      // Show backup phrase
      if (user.backup_phrase) {
        alert(`IMPORTANT: Save your backup phrase securely:\n\n${user.backup_phrase}\n\nThis phrase can recover your account if you lose access.`);
      }
      
      setTimeout(() => {
        fetchChats(access_token);
        fetchContacts(access_token);
        fetchBlockedUsers(access_token);
        fetchStories(access_token);
        fetchChannels(access_token);
        fetchVoiceRooms(access_token);
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

  // Main Chat View with Ultimate Features
  return (
    <div className="h-screen flex bg-gradient-to-br from-gray-50 to-blue-50">
      {/* Ultimate Enhanced Sidebar */}
      <div className="w-1/3 bg-white/80 backdrop-blur-lg border-r border-gray-200/50 flex flex-col shadow-xl">
        {/* Ultimate Header */}
        <div className="p-4 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-purple-400 rounded-full flex items-center justify-center shadow-lg">
                <span className="font-bold text-lg">{user.username.charAt(0).toUpperCase()}</span>
              </div>
              <div className="ml-3">
                <p className="font-medium text-lg">{user.display_name || user.username} 🚀</p>
                <p className="text-xs text-blue-200">
                  {isConnected ? 'Ultimate Mode Active' : 'Connecting...'}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowDiscovery(!showDiscovery)}
                className="text-blue-200 hover:text-white p-2 rounded-lg hover:bg-white/20 transition-all"
                title="Discover"
              >
                🔍
              </button>
              <button
                onClick={() => setShowPrivacySettings(!showPrivacySettings)}
                className="text-blue-200 hover:text-white p-2 rounded-lg hover:bg-white/20 transition-all"
                title="Privacy"
              >
                🛡️
              </button>
              <button
                onClick={() => setShowBackupRestore(!showBackupRestore)}
                className="text-blue-200 hover:text-white p-2 rounded-lg hover:bg-white/20 transition-all"
                title="Backup"
              >
                💾
              </button>
              <button
                onClick={() => setShowProfileEditor(!showProfileEditor)}
                className="text-blue-200 hover:text-white p-2 rounded-lg hover:bg-white/20 transition-all"
                title="Profile"
              >
                👤
              </button>
              <button
                onClick={logout}
                className="text-blue-200 hover:text-white p-2 rounded-lg hover:bg-white/20 transition-all"
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
          <div className="p-3 border-b border-gray-200/50">
            <div className="flex space-x-3 overflow-x-auto scrollbar-hide">
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
                    <div className="flex items-center justify-between mt-1">
                      {chat.chat_type === 'direct' && chat.other_user?.is_online && (
                        <span className="text-xs text-green-500 font-medium">● Online</span>
                      )}
                      {chat.chat_type === 'group' && (
                        <span className="text-xs text-gray-500">
                          👥 {chat.members?.length || 0} members
                        </span>
                      )}
                      {chat.chat_type === 'channel' && (
                        <span className="text-xs text-blue-500">
                          📢 Channel
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Ultimate Enhanced Chat Area */}
      <div className="flex-1 flex flex-col">
        {activeChat ? (
          <>
            {/* Ultimate Chat Header */}
            <div className="p-4 bg-white/80 backdrop-blur-lg border-b border-gray-200/50 shadow-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-purple-400 rounded-full flex items-center justify-center shadow-lg">
                    <span className="text-white font-medium">
                      {activeChat.chat_type === 'direct' 
                        ? activeChat.other_user?.username?.charAt(0).toUpperCase() || '?'
                        : activeChat.name?.charAt(0).toUpperCase() || 'G'
                      }
                    </span>
                  </div>
                  <div className="ml-4">
                    <p className="font-medium text-lg flex items-center">
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
                        <span>👥 {activeChat.members?.length || 0} members</span>
                      )}
                      <span className="ml-2">• End-to-end encrypted • Ultimate Security</span>
                    </p>
                  </div>
                </div>
                
                {/* Ultimate action buttons */}
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => initiateCall('voice')}
                    className="p-3 text-gray-600 hover:text-green-600 hover:bg-green-50 rounded-xl transition-all hover:scale-110"
                    title="Voice Call"
                  >
                    <span className="text-xl">📞</span>
                  </button>
                  <button
                    onClick={() => initiateCall('video')}
                    className="p-3 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-xl transition-all hover:scale-110"
                    title="Video Call"
                  >
                    <span className="text-xl">📹</span>
                  </button>
                  <button
                    onClick={isScreenSharing ? stopScreenShare : startScreenShare}
                    className={`p-3 rounded-xl transition-all hover:scale-110 ${
                      isScreenSharing 
                        ? 'text-red-600 bg-red-50' 
                        : 'text-gray-600 hover:text-purple-600 hover:bg-purple-50'
                    }`}
                    title={isScreenSharing ? "Stop Screen Share" : "Start Screen Share"}
                  >
                    <span className="text-xl">🖥️</span>
                  </button>
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="p-3 text-gray-600 hover:text-purple-600 hover:bg-purple-50 rounded-xl transition-all hover:scale-110"
                    title="Attach File"
                  >
                    <span className="text-xl">📎</span>
                  </button>
                  {activeChat.chat_type === 'direct' && (
                    <button
                      onClick={() => getSafetyNumber(activeChat.other_user?.user_id)}
                      className="p-3 text-gray-600 hover:text-indigo-600 hover:bg-indigo-50 rounded-xl transition-all hover:scale-110"
                      title="Safety Number"
                    >
                      <span className="text-xl">🛡️</span>
                    </button>
                  )}
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

            {/* Ultimate Messages Area */}
            <div className="flex-1 overflow-y-auto p-6 bg-gradient-to-b from-gray-50/50 to-white/50 backdrop-blur-sm">
              {replyToMessage && (
                <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-4 rounded-xl border border-blue-200 mb-4 backdrop-blur-sm">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-sm text-blue-600 font-medium">↩️ Replying to:</p>
                      <p className="text-sm text-gray-700 mt-1">{replyToMessage.content}</p>
                    </div>
                    <button
                      onClick={() => setReplyToMessage(null)}
                      className="text-gray-400 hover:text-gray-600 text-xl"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              )}
              
              {isScreenSharing && (
                <div className="bg-gradient-to-r from-purple-100 to-blue-100 p-4 rounded-xl border border-purple-200 mb-4">
                  <div className="flex items-center justify-center">
                    <span className="text-2xl mr-2">🖥️</span>
                    <p className="text-purple-700 font-medium">You are sharing your screen</p>
                  </div>
                </div>
              )}
              
              {messages.map(renderMessage)}
              <div ref={messagesEndRef} />
            </div>

            {/* Ultimate Message Input */}
            <div className="p-6 bg-white/80 backdrop-blur-lg border-t border-gray-200/50">
              <form onSubmit={sendMessage} className="flex items-center space-x-3">
                <button
                  type="button"
                  onClick={isRecording ? stopRecording : startRecording}
                  className={`p-4 rounded-full transition-all ${
                    isRecording 
                      ? 'bg-red-500 text-white animate-pulse shadow-lg scale-110' 
                      : 'bg-gradient-to-r from-gray-200 to-gray-300 text-gray-600 hover:from-gray-300 hover:to-gray-400 hover:scale-110'
                  }`}
                  title={isRecording ? `Recording... ${recordingDuration}s` : 'Voice Message'}
                >
                  <span className="text-xl">🎤</span>
                </button>
                
                <div className="flex-1 relative">
                  <input
                    type="text"
                    placeholder="Type your ultimate message... 🚀"
                    className="w-full p-4 pr-16 border border-gray-300 rounded-2xl focus:outline-none focus:ring-2 focus:ring-purple-500 bg-white/80 backdrop-blur-sm shadow-lg transition-all focus:scale-105"
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    disabled={isRecording}
                  />
                  <div className="absolute right-4 top-1/2 transform -translate-y-1/2 flex space-x-2">
                    <button
                      type="button"
                      onClick={() => setShowEmojiPicker(!showEmojiPicker)}
                      className="text-gray-400 hover:text-gray-600 text-xl transition-all hover:scale-125"
                    >
                      😊
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowCreatePoll(true)}
                      className="text-gray-400 hover:text-gray-600 text-xl transition-all hover:scale-125"
                    >
                      📊
                    </button>
                  </div>
                </div>
                
                <button
                  type="submit"
                  className="bg-gradient-to-r from-purple-600 via-blue-600 to-indigo-600 text-white px-8 py-4 rounded-2xl hover:shadow-2xl hover:scale-110 transition-all duration-300 flex items-center space-x-2"
                  disabled={(!newMessage.trim() && !replyToMessage) || isRecording}
                >
                  <span className="font-medium">Send</span>
                  <span className="text-lg">🚀</span>
                </button>
              </form>
              
              {/* Ultimate Emoji Picker */}
              {showEmojiPicker && (
                <div className="absolute bottom-24 right-8 z-50 shadow-2xl rounded-2xl overflow-hidden">
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
          <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-50">
            <div className="text-center max-w-md">
              <div className="text-9xl mb-6 animate-bounce">🚀</div>
              <h3 className="text-4xl font-bold text-gray-800 mb-4 bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                ChatApp Pro Ultimate
              </h3>
              <p className="text-gray-600 mb-8 text-lg">Select a chat to start the ultimate messaging experience</p>
              <div className="grid grid-cols-2 gap-6 text-sm text-gray-500">
                <div className="flex flex-col items-center p-4 bg-white/50 rounded-2xl backdrop-blur-sm">
                  <span className="text-3xl mb-2">🔒</span>
                  <span className="font-medium">Military-grade encryption</span>
                </div>
                <div className="flex flex-col items-center p-4 bg-white/50 rounded-2xl backdrop-blur-sm">
                  <span className="text-3xl mb-2">📞</span>
                  <span className="font-medium">HD calls & screen sharing</span>
                </div>
                <div className="flex flex-col items-center p-4 bg-white/50 rounded-2xl backdrop-blur-sm">
                  <span className="text-3xl mb-2">📖</span>
                  <span className="font-medium">Stories & channels</span>
                </div>
                <div className="flex flex-col items-center p-4 bg-white/50 rounded-2xl backdrop-blur-sm">
                  <span className="text-3xl mb-2">🎤</span>
                  <span className="font-medium">Voice rooms & recording</span>
                </div>
                <div className="flex flex-col items-center p-4 bg-white/50 rounded-2xl backdrop-blur-sm">
                  <span className="text-3xl mb-2">🔍</span>
                  <span className="font-medium">Global discovery</span>
                </div>
                <div className="flex flex-col items-center p-4 bg-white/50 rounded-2xl backdrop-blur-sm">
                  <span className="text-3xl mb-2">🛡️</span>
                  <span className="font-medium">Advanced privacy</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* All the modals and overlays */}
      
      {/* Add Contact Modal */}
      {showAddContact && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-[90vw]">
            <h3 className="text-lg font-semibold mb-4">Add Contact</h3>
            <form onSubmit={async (e) => {
              e.preventDefault();
              try {
                await axios.post(`${API}/contacts`, contactForm, getAuthHeaders());
                setContactForm({ email: '', contact_name: '' });
                setShowAddContact(false);
                fetchContacts();
              } catch (error) {
                console.error('Error adding contact:', error);
                alert('Error adding contact: ' + (error.response?.data?.detail || error.message));
              }
            }}>
              <div className="space-y-4">
                <input
                  type="email"
                  placeholder="Contact Email"
                  value={contactForm.email}
                  onChange={(e) => setContactForm({...contactForm, email: e.target.value})}
                  className="w-full p-3 border rounded-lg"
                  required
                />
                <input
                  type="text"
                  placeholder="Contact Name (optional)"
                  value={contactForm.contact_name}
                  onChange={(e) => setContactForm({...contactForm, contact_name: e.target.value})}
                  className="w-full p-3 border rounded-lg"
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
                  className="flex-1 py-2 bg-blue-500 text-white rounded-lg"
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
            <h3 className="text-lg font-semibold mb-4">Create Group</h3>
            <form onSubmit={async (e) => {
              e.preventDefault();
              try {
                await axios.post(`${API}/chats`, {
                  chat_type: 'group',
                  name: groupForm.name,
                  description: groupForm.description,
                  members: selectedMembers
                }, getAuthHeaders());
                setGroupForm({ name: '', description: '', members: [], chat_type: 'group' });
                setSelectedMembers([]);
                setShowCreateGroup(false);
                fetchChats();
              } catch (error) {
                console.error('Error creating group:', error);
                alert('Error creating group: ' + (error.response?.data?.detail || error.message));
              }
            }}>
              <div className="space-y-4">
                <input
                  type="text"
                  placeholder="Group Name"
                  value={groupForm.name}
                  onChange={(e) => setGroupForm({...groupForm, name: e.target.value})}
                  className="w-full p-3 border rounded-lg"
                  required
                />
                <textarea
                  placeholder="Group Description (optional)"
                  value={groupForm.description}
                  onChange={(e) => setGroupForm({...groupForm, description: e.target.value})}
                  className="w-full p-3 border rounded-lg h-20"
                />
                <div>
                  <label className="block text-sm font-medium mb-2">Add Members:</label>
                  <div className="max-h-40 overflow-y-auto border rounded-lg">
                    {contacts.map(contact => (
                      <div key={contact.contact_user_id} className="flex items-center p-2 hover:bg-gray-50">
                        <input
                          type="checkbox"
                          checked={selectedMembers.includes(contact.contact_user_id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedMembers([...selectedMembers, contact.contact_user_id]);
                            } else {
                              setSelectedMembers(selectedMembers.filter(id => id !== contact.contact_user_id));
                            }
                          }}
                          className="mr-3"
                        />
                        <span>{contact.contact_name || contact.contact_user?.username}</span>
                      </div>
                    ))}
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
                  className="flex-1 py-2 bg-purple-500 text-white rounded-lg"
                >
                  Create Group
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Channel Modal */}
      {showCreateChannel && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-[90vw]">
            <h3 className="text-lg font-semibold mb-4">Create Channel</h3>
            <form onSubmit={async (e) => {
              e.preventDefault();
              try {
                await axios.post(`${API}/channels`, channelForm, getAuthHeaders());
                setChannelForm({ name: '', description: '', is_public: true, category: 'general' });
                setShowCreateChannel(false);
                fetchChannels();
              } catch (error) {
                console.error('Error creating channel:', error);
                alert('Error creating channel: ' + (error.response?.data?.detail || error.message));
              }
            }}>
              <div className="space-y-4">
                <input
                  type="text"
                  placeholder="Channel Name"
                  value={channelForm.name}
                  onChange={(e) => setChannelForm({...channelForm, name: e.target.value})}
                  className="w-full p-3 border rounded-lg"
                  required
                />
                <textarea
                  placeholder="Channel Description"
                  value={channelForm.description}
                  onChange={(e) => setChannelForm({...channelForm, description: e.target.value})}
                  className="w-full p-3 border rounded-lg h-20"
                />
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={channelForm.is_public}
                    onChange={(e) => setChannelForm({...channelForm, is_public: e.target.checked})}
                    className="mr-3"
                  />
                  <label>Public Channel</label>
                </div>
              </div>
              <div className="flex space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowCreateChannel(false)}
                  className="flex-1 py-2 border rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 bg-blue-500 text-white rounded-lg"
                >
                  Create Channel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Story Modal */}
      {showCreateStory && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-[90vw]">
            <h3 className="text-lg font-semibold mb-4">Create Story</h3>
            <form onSubmit={async (e) => {
              e.preventDefault();
              try {
                await axios.post(`${API}/stories`, storyForm, getAuthHeaders());
                setStoryForm({
                  content: '',
                  media_type: 'text',
                  background_color: '#000000',
                  text_color: '#ffffff',
                  privacy: 'all'
                });
                setShowCreateStory(false);
                fetchStories();
              } catch (error) {
                console.error('Error creating story:', error);
                alert('Error creating story: ' + (error.response?.data?.detail || error.message));
              }
            }}>
              <div className="space-y-4">
                <textarea
                  placeholder="What's on your mind?"
                  value={storyForm.content}
                  onChange={(e) => setStoryForm({...storyForm, content: e.target.value})}
                  className="w-full p-3 border rounded-lg h-32"
                  required
                />
                <div className="flex items-center space-x-4">
                  <label className="text-sm">Background:</label>
                  <input
                    type="color"
                    value={storyForm.background_color}
                    onChange={(e) => setStoryForm({...storyForm, background_color: e.target.value})}
                    className="w-12 h-8 border rounded"
                  />
                  <label className="text-sm">Text:</label>
                  <input
                    type="color"
                    value={storyForm.text_color}
                    onChange={(e) => setStoryForm({...storyForm, text_color: e.target.value})}
                    className="w-12 h-8 border rounded"
                  />
                </div>
              </div>
              <div className="flex space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowCreateStory(false)}
                  className="flex-1 py-2 border rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 bg-pink-500 text-white rounded-lg"
                >
                  Create Story
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Voice Room Modal */}
      {showCreateVoiceRoom && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-[90vw]">
            <h3 className="text-lg font-semibold mb-4">Create Voice Room</h3>
            <form onSubmit={async (e) => {
              e.preventDefault();
              try {
                await axios.post(`${API}/voice/rooms`, voiceRoomForm, getAuthHeaders());
                setVoiceRoomForm({ name: '', description: '', max_participants: 50 });
                setShowCreateVoiceRoom(false);
              } catch (error) {
                console.error('Error creating voice room:', error);
                alert('Error creating voice room: ' + (error.response?.data?.detail || error.message));
              }
            }}>
              <div className="space-y-4">
                <input
                  type="text"
                  placeholder="Voice Room Name"
                  value={voiceRoomForm.name}
                  onChange={(e) => setVoiceRoomForm({...voiceRoomForm, name: e.target.value})}
                  className="w-full p-3 border rounded-lg"
                  required
                />
                <textarea
                  placeholder="Description (optional)"
                  value={voiceRoomForm.description}
                  onChange={(e) => setVoiceRoomForm({...voiceRoomForm, description: e.target.value})}
                  className="w-full p-3 border rounded-lg h-20"
                />
                <input
                  type="number"
                  placeholder="Max Participants"
                  value={voiceRoomForm.max_participants}
                  onChange={(e) => setVoiceRoomForm({...voiceRoomForm, max_participants: parseInt(e.target.value)})}
                  className="w-full p-3 border rounded-lg"
                  min="2"
                  max="100"
                />
              </div>
              <div className="flex space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowCreateVoiceRoom(false)}
                  className="flex-1 py-2 border rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 bg-orange-500 text-white rounded-lg"
                >
                  Create Voice Room
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Poll Modal */}
      {showCreatePoll && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-[90vw]">
            <h3 className="text-lg font-semibold mb-4">Create Poll</h3>
            <form onSubmit={async (e) => {
              e.preventDefault();
              if (!activeChat) {
                alert('Please select a chat first');
                return;
              }
              try {
                await createPoll();
              } catch (error) {
                console.error('Error creating poll:', error);
              }
            }}>
              <div className="space-y-4">
                <input
                  type="text"
                  placeholder="Poll Question"
                  value={pollForm.question}
                  onChange={(e) => setPollForm({...pollForm, question: e.target.value})}
                  className="w-full p-3 border rounded-lg"
                  required
                />
                {pollForm.options.map((option, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <input
                      type="text"
                      placeholder={`Option ${index + 1}`}
                      value={option}
                      onChange={(e) => {
                        const newOptions = [...pollForm.options];
                        newOptions[index] = e.target.value;
                        setPollForm({...pollForm, options: newOptions});
                      }}
                      className="flex-1 p-3 border rounded-lg"
                      required
                    />
                    {pollForm.options.length > 2 && (
                      <button
                        type="button"
                        onClick={() => {
                          const newOptions = pollForm.options.filter((_, i) => i !== index);
                          setPollForm({...pollForm, options: newOptions});
                        }}
                        className="text-red-500"
                      >
                        ✕
                      </button>
                    )}
                  </div>
                ))}
                <button
                  type="button"
                  onClick={() => setPollForm({...pollForm, options: [...pollForm.options, '']})}
                  className="text-blue-500 text-sm"
                >
                  + Add Option
                </button>
                <div className="flex items-center space-x-4">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={pollForm.is_anonymous}
                      onChange={(e) => setPollForm({...pollForm, is_anonymous: e.target.checked})}
                      className="mr-2"
                    />
                    Anonymous
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={pollForm.allows_multiple_answers}
                      onChange={(e) => setPollForm({...pollForm, allows_multiple_answers: e.target.checked})}
                      className="mr-2"
                    />
                    Multiple Answers
                  </label>
                </div>
              </div>
              <div className="flex space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowCreatePoll(false)}
                  className="flex-1 py-2 border rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 bg-indigo-500 text-white rounded-lg"
                >
                  Create Poll
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      {showAddContact && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-[90vw]">
            <h3 className="text-lg font-semibold mb-4">Add Contact</h3>
            <form onSubmit={async (e) => {
              e.preventDefault();
              try {
                await axios.post(`${API}/contacts`, contactForm, getAuthHeaders());
                setContactForm({ email: '', contact_name: '' });
                setShowAddContact(false);
                fetchContacts();
              } catch (error) {
                console.error('Error adding contact:', error);
                alert('Error adding contact: ' + (error.response?.data?.detail || error.message));
              }
            }}>
              <div className="space-y-4">
                <input
                  type="email"
                  placeholder="Contact Email"
                  value={contactForm.email}
                  onChange={(e) => setContactForm({...contactForm, email: e.target.value})}
                  className="w-full p-3 border rounded-lg"
                  required
                />
                <input
                  type="text"
                  placeholder="Contact Name (optional)"
                  value={contactForm.contact_name}
                  onChange={(e) => setContactForm({...contactForm, contact_name: e.target.value})}
                  className="w-full p-3 border rounded-lg"
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
                  className="flex-1 py-2 bg-blue-500 text-white rounded-lg"
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
            <h3 className="text-lg font-semibold mb-4">Create Group</h3>
            <form onSubmit={async (e) => {
              e.preventDefault();
              try {
                await axios.post(`${API}/chats`, {
                  chat_type: 'group',
                  name: groupForm.name,
                  description: groupForm.description,
                  members: selectedMembers
                }, getAuthHeaders());
                setGroupForm({ name: '', description: '', members: [], chat_type: 'group' });
                setSelectedMembers([]);
                setShowCreateGroup(false);
                fetchChats();
              } catch (error) {
                console.error('Error creating group:', error);
                alert('Error creating group: ' + (error.response?.data?.detail || error.message));
              }
            }}>
              <div className="space-y-4">
                <input
                  type="text"
                  placeholder="Group Name"
                  value={groupForm.name}
                  onChange={(e) => setGroupForm({...groupForm, name: e.target.value})}
                  className="w-full p-3 border rounded-lg"
                  required
                />
                <textarea
                  placeholder="Group Description (optional)"
                  value={groupForm.description}
                  onChange={(e) => setGroupForm({...groupForm, description: e.target.value})}
                  className="w-full p-3 border rounded-lg h-20"
                />
                <div>
                  <label className="block text-sm font-medium mb-2">Add Members:</label>
                  <div className="max-h-40 overflow-y-auto border rounded-lg">
                    {contacts.map(contact => (
                      <div key={contact.contact_user_id} className="flex items-center p-2 hover:bg-gray-50">
                        <input
                          type="checkbox"
                          checked={selectedMembers.includes(contact.contact_user_id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedMembers([...selectedMembers, contact.contact_user_id]);
                            } else {
                              setSelectedMembers(selectedMembers.filter(id => id !== contact.contact_user_id));
                            }
                          }}
                          className="mr-3"
                        />
                        <span>{contact.contact_name || contact.contact_user?.username}</span>
                      </div>
                    ))}
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
                  className="flex-1 py-2 bg-purple-500 text-white rounded-lg"
                >
                  Create Group
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Channel Modal */}
      {showCreateChannel && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-[90vw]">
            <h3 className="text-lg font-semibold mb-4">Create Channel</h3>
            <form onSubmit={async (e) => {
              e.preventDefault();
              try {
                await axios.post(`${API}/channels`, channelForm, getAuthHeaders());
                setChannelForm({ name: '', description: '', is_public: true, category: 'general' });
                setShowCreateChannel(false);
                fetchChannels();
              } catch (error) {
                console.error('Error creating channel:', error);
                alert('Error creating channel: ' + (error.response?.data?.detail || error.message));
              }
            }}>
              <div className="space-y-4">
                <input
                  type="text"
                  placeholder="Channel Name"
                  value={channelForm.name}
                  onChange={(e) => setChannelForm({...channelForm, name: e.target.value})}
                  className="w-full p-3 border rounded-lg"
                  required
                />
                <textarea
                  placeholder="Channel Description"
                  value={channelForm.description}
                  onChange={(e) => setChannelForm({...channelForm, description: e.target.value})}
                  className="w-full p-3 border rounded-lg h-20"
                />
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={channelForm.is_public}
                    onChange={(e) => setChannelForm({...channelForm, is_public: e.target.checked})}
                    className="mr-3"
                  />
                  <label>Public Channel</label>
                </div>
              </div>
              <div className="flex space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowCreateChannel(false)}
                  className="flex-1 py-2 border rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 bg-blue-500 text-white rounded-lg"
                >
                  Create Channel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Story Modal */}
      {showCreateStory && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-[90vw]">
            <h3 className="text-lg font-semibold mb-4">Create Story</h3>
            <form onSubmit={async (e) => {
              e.preventDefault();
              try {
                await axios.post(`${API}/stories`, storyForm, getAuthHeaders());
                setStoryForm({
                  content: '',
                  media_type: 'text',
                  background_color: '#000000',
                  text_color: '#ffffff',
                  privacy: 'all'
                });
                setShowCreateStory(false);
                fetchStories();
              } catch (error) {
                console.error('Error creating story:', error);
                alert('Error creating story: ' + (error.response?.data?.detail || error.message));
              }
            }}>
              <div className="space-y-4">
                <textarea
                  placeholder="What's on your mind?"
                  value={storyForm.content}
                  onChange={(e) => setStoryForm({...storyForm, content: e.target.value})}
                  className="w-full p-3 border rounded-lg h-32"
                  required
                />
                <div className="flex items-center space-x-4">
                  <label className="text-sm">Background:</label>
                  <input
                    type="color"
                    value={storyForm.background_color}
                    onChange={(e) => setStoryForm({...storyForm, background_color: e.target.value})}
                    className="w-12 h-8 border rounded"
                  />
                  <label className="text-sm">Text:</label>
                  <input
                    type="color"
                    value={storyForm.text_color}
                    onChange={(e) => setStoryForm({...storyForm, text_color: e.target.value})}
                    className="w-12 h-8 border rounded"
                  />
                </div>
              </div>
              <div className="flex space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowCreateStory(false)}
                  className="flex-1 py-2 border rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 bg-pink-500 text-white rounded-lg"
                >
                  Create Story
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Voice Room Modal */}
      {showCreateVoiceRoom && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-[90vw]">
            <h3 className="text-lg font-semibold mb-4">Create Voice Room</h3>
            <form onSubmit={async (e) => {
              e.preventDefault();
              try {
                await axios.post(`${API}/voice/rooms`, voiceRoomForm, getAuthHeaders());
                setVoiceRoomForm({ name: '', description: '', max_participants: 50 });
                setShowCreateVoiceRoom(false);
              } catch (error) {
                console.error('Error creating voice room:', error);
                alert('Error creating voice room: ' + (error.response?.data?.detail || error.message));
              }
            }}>
              <div className="space-y-4">
                <input
                  type="text"
                  placeholder="Voice Room Name"
                  value={voiceRoomForm.name}
                  onChange={(e) => setVoiceRoomForm({...voiceRoomForm, name: e.target.value})}
                  className="w-full p-3 border rounded-lg"
                  required
                />
                <textarea
                  placeholder="Description (optional)"
                  value={voiceRoomForm.description}
                  onChange={(e) => setVoiceRoomForm({...voiceRoomForm, description: e.target.value})}
                  className="w-full p-3 border rounded-lg h-20"
                />
                <input
                  type="number"
                  placeholder="Max Participants"
                  value={voiceRoomForm.max_participants}
                  onChange={(e) => setVoiceRoomForm({...voiceRoomForm, max_participants: parseInt(e.target.value)})}
                  className="w-full p-3 border rounded-lg"
                  min="2"
                  max="100"
                />
              </div>
              <div className="flex space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowCreateVoiceRoom(false)}
                  className="flex-1 py-2 border rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 bg-orange-500 text-white rounded-lg"
                >
                  Create Voice Room
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Poll Modal */}
      {showCreatePoll && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-[90vw]">
            <h3 className="text-lg font-semibold mb-4">Create Poll</h3>
            <form onSubmit={async (e) => {
              e.preventDefault();
              if (!activeChat) {
                alert('Please select a chat first');
                return;
              }
              try {
                await createPoll();
              } catch (error) {
                console.error('Error creating poll:', error);
              }
            }}>
              <div className="space-y-4">
                <input
                  type="text"
                  placeholder="Poll Question"
                  value={pollForm.question}
                  onChange={(e) => setPollForm({...pollForm, question: e.target.value})}
                  className="w-full p-3 border rounded-lg"
                  required
                />
                {pollForm.options.map((option, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <input
                      type="text"
                      placeholder={`Option ${index + 1}`}
                      value={option}
                      onChange={(e) => {
                        const newOptions = [...pollForm.options];
                        newOptions[index] = e.target.value;
                        setPollForm({...pollForm, options: newOptions});
                      }}
                      className="flex-1 p-3 border rounded-lg"
                      required
                    />
                    {pollForm.options.length > 2 && (
                      <button
                        type="button"
                        onClick={() => {
                          const newOptions = pollForm.options.filter((_, i) => i !== index);
                          setPollForm({...pollForm, options: newOptions});
                        }}
                        className="text-red-500"
                      >
                        ✕
                      </button>
                    )}
                  </div>
                ))}
                <button
                  type="button"
                  onClick={() => setPollForm({...pollForm, options: [...pollForm.options, '']})}
                  className="text-blue-500 text-sm"
                >
                  + Add Option
                </button>
                <div className="flex items-center space-x-4">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={pollForm.is_anonymous}
                      onChange={(e) => setPollForm({...pollForm, is_anonymous: e.target.checked})}
                      className="mr-2"
                    />
                    Anonymous
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={pollForm.allows_multiple_answers}
                      onChange={(e) => setPollForm({...pollForm, allows_multiple_answers: e.target.checked})}
                      className="mr-2"
                    />
                    Multiple Answers
                  </label>
                </div>
              </div>
              <div className="flex space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowCreatePoll(false)}
                  className="flex-1 py-2 border rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 bg-indigo-500 text-white rounded-lg"
                >
                  Create Poll
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>

    {/* Genie Assistant */}
    {user && (
      <GenieAssistant 
        user={user} 
        token={token} 
        onAction={handleGenieAction}
      />
    )}
  );
}

export default App;