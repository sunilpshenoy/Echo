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

  // Workspace and Calendar state
  const [workspaceMode, setWorkspaceMode] = useState('personal');
  const [showCalendar, setShowCalendar] = useState(false);
  const [showTasks, setShowTasks] = useState(false);
  const [showWorkspaceSwitcher, setShowWorkspaceSwitcher] = useState(false);

