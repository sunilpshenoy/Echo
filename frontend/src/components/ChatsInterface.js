import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import QRCode from 'react-qr-code';
import { useTranslation } from 'react-i18next';
import CallInterface from './CallInterface';

const ConnectionManager = ({ user, token, api, onConnectionUpdate }) => {
  const [showPinModal, setShowPinModal] = useState(false);
  const [showSearchModal, setShowSearchModal] = useState(false);
  const [qrCodeData, setQrCodeData] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [connectionMessage, setConnectionMessage] = useState('');

  const getQRCode = async () => {
    try {
      const response = await axios.get(`${api}/users/qr-code`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setQrCodeData(response.data);
    } catch (error) {
      console.error('Failed to get QR code:', error);
    }
  };

  const sharePin = async () => {
    if (!qrCodeData) return;
    
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Connect with me',
          text: `Use my PIN: ${qrCodeData.connection_pin}`,
        });
      } catch (error) {
        fallbackShare();
      }
    } else {
      fallbackShare();
    }
  };

  const fallbackShare = () => {
    if (!qrCodeData) return;
    
    if (navigator.clipboard) {
      navigator.clipboard.writeText(qrCodeData.connection_pin)
        .then(() => alert('PIN copied to clipboard! 📋'))
        .catch(() => alert(`Your PIN: ${qrCodeData.connection_pin}`));
    } else {
      alert(`Your PIN: ${qrCodeData.connection_pin}`);
    }
  };

  const sendConnectionRequest = async () => {
    if (!searchQuery.trim()) {
      alert('Please enter a PIN');
      return;
    }
    
    try {
      await axios.post(`${api}/connections/request-by-pin`, {
        connection_pin: searchQuery,
        message: connectionMessage
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      alert('Connection request sent! 🎉');
      setSearchQuery('');
      setConnectionMessage('');
      setShowSearchModal(false);
      
      if (onConnectionUpdate) {
        onConnectionUpdate();
      }
    } catch (error) {
      console.error('Failed to send connection request:', error);
      alert(error.response?.data?.detail || 'Failed to send connection request');
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex space-x-2">
        <button 
          onClick={() => {
            setShowPinModal(true);
            getQRCode();
          }}
          className="flex-1 bg-green-500 text-white p-2 rounded-lg hover:bg-green-600 text-sm"
        >
          📤 Share PIN
        </button>
        
        <button 
          onClick={() => setShowSearchModal(true)}
          className="flex-1 bg-blue-500 text-white p-2 rounded-lg hover:bg-blue-600 text-sm"
        >
          🔍 Find People
        </button>
      </div>

      {/* Share PIN Modal */}
      {showPinModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-sm w-full p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-bold text-gray-900">Share My PIN</h2>
              <button
                onClick={() => setShowPinModal(false)}
                className="text-gray-500 hover:text-gray-700 text-xl"
              >
                ✕
              </button>
            </div>
            
            {qrCodeData ? (
              <div className="text-center">
                <div className="bg-gray-50 p-4 rounded-lg mb-4">
                  <QRCode 
                    value={qrCodeData.connection_pin} 
                    size={120}
                    className="mx-auto mb-3"
                  />
                  <p className="text-lg font-mono font-bold text-gray-900">
                    {qrCodeData.connection_pin}
                  </p>
                </div>
                
                <p className="text-sm text-gray-600 mb-4">
                  Share this PIN with people you want to connect with
                </p>
                
                <button
                  onClick={sharePin}
                  className="w-full bg-blue-500 text-white py-2 rounded-lg hover:bg-blue-600"
                >
                  Share PIN
                </button>
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-2"></div>
                <p className="text-gray-600">Loading...</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Search Modal */}
      {showSearchModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-sm w-full p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-bold text-gray-900">Add Contact</h2>
              <button
                onClick={() => setShowSearchModal(false)}
                className="text-gray-500 hover:text-gray-700 text-xl"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Enter Connection PIN
                </label>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="PIN-ABC123"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Message (Optional)
                </label>
                <textarea
                  value={connectionMessage}
                  onChange={(e) => setConnectionMessage(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Hi! I'd like to connect..."
                  rows={2}
                />
              </div>
              
              <button
                onClick={sendConnectionRequest}
                disabled={!searchQuery.trim()}
                className="w-full bg-blue-500 text-white py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50"
              >
                Send Connection Request
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const ChatsInterface = ({ 
  user, 
  token, 
  api, 
  chats, 
  selectedChat, 
  chatMessages, 
  newMessage, 
  setNewMessage, 
  onSelectChat, 
  onSendMessage, 
  isLoading 
}) => {
  const { t } = useTranslation();
  const [showAddContact, setShowAddContact] = useState(false);
  const [showMyPin, setShowMyPin] = useState(false);
  const [contactPin, setContactPin] = useState('');
  // const [contactRequests, setContactRequests] = useState([]);
  // const [showQRScanner, setShowQRScanner] = useState(false);
  const [contactEmail, setContactEmail] = useState('');
  // const [contactPhone, setContactPhone] = useState('');
  const [addContactMethod, setAddContactMethod] = useState('pin');
  const [viewMode, setViewMode] = useState('contacts');
  const [activeContact, setActiveContact] = useState(null);
  
  // Real-time messaging state
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [typingUsers, setTypingUsers] = useState({});
  const [onlineUsers, setOnlineUsers] = useState(new Set());
  const [isTyping, setIsTyping] = useState(false);
  const typingTimeoutRef = useRef(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  // Double-tap protection state
  const [doubleTapState, setDoubleTapState] = useState({});
  const doubleTapTimeoutRef = useRef({});

  // WebSocket connection setup
  useEffect(() => {
    if (user && token) {
      connectWebSocket();
    }
    
    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, [user, token]);

  const connectWebSocket = () => {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const wsUrl = backendUrl.replace('http', 'ws') + `/api/ws/${user.user_id}`;
      
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setSocket(ws);
      };
      
      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        setSocket(null);
        // Attempt to reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  };

  const handleWebSocketMessage = (message) => {
    console.log('Received WebSocket message:', message);
    
    switch (message.type) {
      case 'new_message':
        // Real-time message received - refresh messages if it's for current chat
        if (selectedChat && message.data.chat_id === selectedChat.chat_id) {
          onSelectChat(selectedChat); // This will refresh messages
        }
        break;
        
      case 'typing':
        setTypingUsers(prev => ({
          ...prev,
          [message.data.chat_id]: message.data.typing_users || []
        }));
        break;
        
      case 'user_online':
        setOnlineUsers(prev => new Set([...prev, message.data.user_id]));
        break;
        
      case 'user_offline':
        setOnlineUsers(prev => {
          const newSet = new Set(prev);
          newSet.delete(message.data.user_id);
          return newSet;
        });
        break;

      // Call-related WebSocket messages
      case 'incoming_call':
        console.log('Incoming call:', message.data);
        setIncomingCall(message.data);
        break;
        
      case 'call_accepted':
        console.log('Call accepted:', message.data);
        if (currentCall && message.data.call_id === currentCall.call_id) {
          setCurrentCall(prev => ({ ...prev, status: 'active' }));
        }
        break;
        
      case 'call_declined':
        console.log('Call declined:', message.data);
        if (currentCall && message.data.call_id === currentCall.call_id) {
          handleCallEnded();
        }
        break;
        
      case 'call_ended':
        console.log('Call ended:', message.data);
        if (currentCall && message.data.call_id === currentCall.call_id) {
          handleCallEnded();
        }
        break;
        
      case 'webrtc_offer':
        handleWebRTCOffer(message.data);
        break;
        
      case 'webrtc_answer':
        handleWebRTCAnswer(message.data);
        break;
        
      case 'webrtc_ice':
        handleWebRTCIce(message.data);
        break;
        
      default:
        console.log('Unknown message type:', message.type);
    }
  };

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom();
  }, [chatMessages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Typing indicator functionality
  const handleTyping = () => {
    if (!socket || !selectedChat) return;
    
    if (!isTyping) {
      setIsTyping(true);
      socket.send(JSON.stringify({
        type: 'typing',
        chat_id: selectedChat.chat_id,
        is_typing: true
      }));
    }
    
    // Clear existing timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
    
    // Set new timeout to stop typing indicator
    typingTimeoutRef.current = setTimeout(() => {
      setIsTyping(false);
      socket.send(JSON.stringify({
        type: 'typing',
        chat_id: selectedChat.chat_id,
        is_typing: false
      }));
    }, 2000);
  };

  // Enhanced message sending with real-time updates
  const sendMessage = async () => {
    if (!newMessage.trim() || !selectedChat) return;
    
    try {
      // Send typing stop indicator
      if (socket && isTyping) {
        socket.send(JSON.stringify({
          type: 'typing',
          chat_id: selectedChat.chat_id,
          is_typing: false
        }));
        setIsTyping(false);
      }
      
      await onSendMessage();
      
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  // File sharing functionality
  const handleFileShare = () => {
    fileInputRef.current?.click();
  };

  // Enhanced file sharing state
  const [isUploadingFile, setIsUploadingFile] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  // Message search state
  const [showMessageSearch, setShowMessageSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  const handleFileSelect = async (event) => {
    const file = event.target.files[0];
    if (!file || !selectedChat) return;
    
    // Enhanced file validation
    const maxSize = 10 * 1024 * 1024; // 10MB
    const allowedTypes = [
      'image/jpeg', 'image/png', 'image/gif', 'image/webp',
      'application/pdf', 'text/plain', 'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ];
    
    if (file.size > maxSize) {
      alert(`File too large! Maximum size is ${(maxSize / (1024 * 1024)).toFixed(1)}MB.\nYour file: ${(file.size / (1024 * 1024)).toFixed(1)}MB`);
      return;
    }
    
    if (!allowedTypes.includes(file.type)) {
      alert(`File type not supported!\nAllowed: Images (JPG, PNG, GIF), PDF, Text, Word documents\nYour file: ${file.type}`);
      return;
    }
    
    setIsUploadingFile(true);
    setUploadProgress(0);
    
    try {
      // Convert file to base64 with progress
      const reader = new FileReader();
      
      reader.onprogress = (e) => {
        if (e.lengthComputable) {
          const progress = (e.loaded / e.total) * 50; // First 50% for reading
          setUploadProgress(progress);
        }
      };
      
      reader.onload = async () => {
        try {
          setUploadProgress(50); // Reading complete
          
          const base64Data = reader.result.split(',')[1];
          const messageType = file.type.startsWith('image/') ? 'image' : 'file';
          
          const response = await axios.post(`${api}/chats/${selectedChat.chat_id}/messages`, {
            content: file.name,
            message_type: messageType,
            file_name: file.name,
            file_size: file.size,
            file_data: base64Data
          }, {
            headers: { Authorization: `Bearer ${token}` },
            onUploadProgress: (progressEvent) => {
              const uploadProgress = 50 + (progressEvent.loaded / progressEvent.total) * 50;
              setUploadProgress(uploadProgress);
            }
          });
          
          setUploadProgress(100);
          
          // Show success message
          const fileIcon = messageType === 'image' ? '🖼️' : '📄';
          alert(`${fileIcon} File "${file.name}" shared successfully!`);
          
          // Refresh messages
          onSelectChat(selectedChat);
          
        } catch (error) {
          console.error('Failed to send file:', error);
          const errorMsg = error.response?.data?.detail || 'Failed to send file. Please try again.';
          alert(`❌ Upload failed: ${errorMsg}`);
        } finally {
          setIsUploadingFile(false);
          setUploadProgress(0);
        }
      };
      
      reader.onerror = () => {
        alert('❌ Failed to read file. Please try again.');
        setIsUploadingFile(false);
        setUploadProgress(0);
      };
      
      reader.readAsDataURL(file);
      
    } catch (error) {
      console.error('File upload error:', error);
      alert('❌ File upload error occurred.');
      setIsUploadingFile(false);
      setUploadProgress(0);
    }
    
    // Clear file input
    event.target.value = '';
  };

  // Handle contact tap - open chat
  const handleContactTap = (chat) => {
    setActiveContact(chat);
    setViewMode('chat');
    onSelectChat(chat);
  };

  // Handle back to contacts
  const handleBackToContacts = () => {
    setViewMode('contacts');
    setActiveContact(null);
  };

  // Send connection request using PIN
  const sendConnectionRequest = async () => {
    console.log('sendConnectionRequest called with PIN:', contactPin);
    if (!contactPin.trim()) {
      alert('Please enter a PIN');
      return;
    }
    
    try {
      const response = await axios.post(`${api}/connections/request-by-pin`, {
        connection_pin: contactPin
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      alert('Connection request sent! 🎉');
      setContactPin('');
      setShowAddContact(false);
      
    } catch (error) {
      console.error('Failed to send connection request:', error);
      alert(error.response?.data?.detail || 'Failed to send connection request');
    }
  };

  // Add contact by email
  const addContactByEmail = async () => {
    if (!contactEmail.trim()) {
      alert('Please enter an email address');
      return;
    }
    
    try {
      await axios.post(`${api}/contacts`, {
        email: contactEmail
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      alert('Contact added successfully! 🎉');
      setContactEmail('');
      setShowAddContact(false);
      
    } catch (error) {
      console.error('Failed to add contact:', error);
      alert(error.response?.data?.detail || 'Failed to add contact');
    }
  };

  // Get user's QR code for PIN sharing
  const getMyQRCode = async () => {
    try {
      const response = await axios.get(`${api}/users/qr-code`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data.qr_code;
    } catch (error) {
      console.error('Failed to get QR code:', error);
      return null;
    }
  };

  // Share PIN functionality
  const shareMyPin = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'My Connection PIN',
          text: `Connect with me using PIN: ${user.connection_pin}`,
        });
      } catch (error) {
        console.log('Share cancelled or failed');
        fallbackShare();
      }
    } else {
      fallbackShare();
    }
  };

  const fallbackShare = () => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(user.connection_pin)
        .then(() => alert('PIN copied to clipboard! 📋'))
        .catch(() => alert(`Your PIN: ${user.connection_pin}`));
    } else {
      alert(`Your PIN: ${user.connection_pin}`);
    }
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Double-tap protection system
  const handleDoubleTapAction = (actionType, contactId, callback) => {
    const key = `${actionType}_${contactId}`;
    
    if (doubleTapState[key]) {
      // Second tap - execute action
      clearTimeout(doubleTapTimeoutRef.current[key]);
      setDoubleTapState(prev => ({ ...prev, [key]: false }));
      delete doubleTapTimeoutRef.current[key];
      callback();
    } else {
      // First tap - show confirmation state
      setDoubleTapState(prev => ({ ...prev, [key]: true }));
      
      // Auto-clear confirmation after 3 seconds
      doubleTapTimeoutRef.current[key] = setTimeout(() => {
        setDoubleTapState(prev => ({ ...prev, [key]: false }));
        delete doubleTapTimeoutRef.current[key];
      }, 3000);
    }
  };

  // Call functionality - Enhanced with backend integration
  const [isCallActive, setIsCallActive] = useState(false);
  const [callType, setCallType] = useState(null); // 'voice' or 'video'
  const [currentCall, setCurrentCall] = useState(null);
  const [localStream, setLocalStream] = useState(null);
  const [remoteStream, setRemoteStream] = useState(null);
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoOff, setIsVideoOff] = useState(false);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const localVideoRef = useRef(null);
  const remoteVideoRef = useRef(null);
  const peerConnection = useRef(null);
  const [incomingCall, setIncomingCall] = useState(null);

  // WebRTC Configuration
  const pcConfig = {
    iceServers: [
      { urls: 'stun:stun.l.google.com:19302' },
      { urls: 'stun:stun1.l.google.com:19302' }
    ]
  };

  // Enhanced WebRTC Implementation
  const initializeWebRTC = async (type) => {
    try {
      // Get user media
      const stream = await navigator.mediaDevices.getUserMedia({
        video: type === 'video',
        audio: true
      });
      
      setLocalStream(stream);
      
      // Create peer connection
      peerConnection.current = new RTCPeerConnection(pcConfig);
      
      // Add local stream to peer connection
      stream.getTracks().forEach(track => {
        peerConnection.current.addTrack(track, stream);
      });
      
      // Handle remote stream
      peerConnection.current.ontrack = (event) => {
        console.log('Received remote stream');
        setRemoteStream(event.streams[0]);
      };
      
      // Handle ICE candidates
      peerConnection.current.onicecandidate = async (event) => {
        if (event.candidate && currentCall) {
          try {
            await axios.post(`${api}/calls/${currentCall.call_id}/webrtc/ice`, {
              candidate: event.candidate
            }, {
              headers: { Authorization: `Bearer ${token}` }
            });
          } catch (error) {
            console.error('Failed to send ICE candidate:', error);
          }
        }
      };
      
      return true;
    } catch (error) {
      console.error('Error accessing media devices:', error);
      alert('❌ Unable to access camera/microphone. Please check permissions.');
      return false;
    }
  };

  // WebRTC Signaling Handlers
  const handleWebRTCOffer = async (data) => {
    if (!currentCall || data.call_id !== currentCall.call_id) return;
    
    try {
      // Set remote description
      await peerConnection.current.setRemoteDescription(data.offer);
      
      // Create answer
      const answer = await peerConnection.current.createAnswer();
      await peerConnection.current.setLocalDescription(answer);
      
      // Send answer
      await axios.post(`${api}/calls/${currentCall.call_id}/webrtc/answer`, {
        answer: answer
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
    } catch (error) {
      console.error('Error handling WebRTC offer:', error);
    }
  };

  const handleWebRTCAnswer = async (data) => {
    if (!currentCall || data.call_id !== currentCall.call_id) return;
    
    try {
      await peerConnection.current.setRemoteDescription(data.answer);
    } catch (error) {
      console.error('Error handling WebRTC answer:', error);
    }
  };

  const handleWebRTCIce = async (data) => {
    if (!currentCall || data.call_id !== currentCall.call_id) return;
    
    try {
      await peerConnection.current.addIceCandidate(data.candidate);
    } catch (error) {
      console.error('Error adding ICE candidate:', error);
    }
  };

  // Call Management Functions
  const initiateCall = async (type) => {
    if (!selectedChat) return;
    
    try {
      // Initialize WebRTC first
      const success = await initializeWebRTC(type);
      if (!success) return;
      
      // Create call via backend
      const response = await axios.post(`${api}/calls/initiate`, {
        chat_id: selectedChat.chat_id,
        call_type: type
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const call = response.data;
      setCurrentCall(call);
      setIsCallActive(true);
      setCallType(type);
      
      // Create and send WebRTC offer
      const offer = await peerConnection.current.createOffer();
      await peerConnection.current.setLocalDescription(offer);
      
      await axios.post(`${api}/calls/${call.call_id}/webrtc/offer`, {
        offer: offer
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
    } catch (error) {
      console.error('Failed to initiate call:', error);
      alert('Failed to start call. Please try again.');
      handleCallEnded();
    }
  };

  const acceptCall = async (call) => {
    try {
      // Accept the call via backend
      await axios.put(`${api}/calls/${call.call_id}/respond`, {
        action: 'accept'
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Initialize WebRTC
      const success = await initializeWebRTC(call.call_type);
      if (success) {
        setCurrentCall(call);
        setIsCallActive(true);
        setCallType(call.call_type);
        setIncomingCall(null);
      }
      
    } catch (error) {
      console.error('Failed to accept call:', error);
      alert('Failed to accept call. Please try again.');
    }
  };

  const declineCall = async (call) => {
    try {
      await axios.put(`${api}/calls/${call.call_id}/respond`, {
        action: 'decline'
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setIncomingCall(null);
      
    } catch (error) {
      console.error('Failed to decline call:', error);
    }
  };

  const endCall = async () => {
    try {
      if (currentCall) {
        await axios.put(`${api}/calls/${currentCall.call_id}/end`, {}, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }
    } catch (error) {
      console.error('Failed to end call:', error);
    } finally {
      handleCallEnded();
    }
  };

  const handleCallEnded = () => {
    // Clean up streams
    if (localStream) {
      localStream.getTracks().forEach(track => track.stop());
    }
    if (peerConnection.current) {
      peerConnection.current.close();
    }
    
    setIsCallActive(false);
    setCallType(null);
    setCurrentCall(null);
    setLocalStream(null);
    setRemoteStream(null);
    setIncomingCall(null);
    setIsMuted(false);
    setIsVideoOff(false);
    setIsScreenSharing(false);
  };

  // Call Control Functions
  const toggleMute = () => {
    if (localStream) {
      const audioTrack = localStream.getAudioTracks()[0];
      if (audioTrack) {
        audioTrack.enabled = !audioTrack.enabled;
        setIsMuted(!audioTrack.enabled);
      }
    }
  };

  const toggleVideo = () => {
    if (localStream) {
      const videoTrack = localStream.getVideoTracks()[0];
      if (videoTrack) {
        videoTrack.enabled = !videoTrack.enabled;
        setIsVideoOff(!videoTrack.enabled);
      }
    }
  };

  const toggleScreenShare = async () => {
    try {
      if (!isScreenSharing) {
        // Start screen sharing
        const screenStream = await navigator.mediaDevices.getDisplayMedia({
          video: true,
          audio: true
        });
        
        // Replace video track with screen share
        const videoTrack = screenStream.getVideoTracks()[0];
        const sender = peerConnection.current.getSenders().find(s => 
          s.track && s.track.kind === 'video'
        );
        
        if (sender) {
          await sender.replaceTrack(videoTrack);
        }
        
        setIsScreenSharing(true);
        
        // Handle screen share end
        videoTrack.onended = () => {
          setIsScreenSharing(false);
          // Switch back to camera
          if (localStream) {
            const cameraTrack = localStream.getVideoTracks()[0];
            if (sender && cameraTrack) {
              sender.replaceTrack(cameraTrack);
            }
          }
        };
        
      } else {
        // Stop screen sharing - switch back to camera
        if (localStream) {
          const cameraTrack = localStream.getVideoTracks()[0];
          const sender = peerConnection.current.getSenders().find(s => 
            s.track && s.track.kind === 'video'
          );
          
          if (sender && cameraTrack) {
            await sender.replaceTrack(cameraTrack);
          }
        }
        setIsScreenSharing(false);
      }
    } catch (error) {
      console.error('Screen share error:', error);
      alert('Screen sharing failed. Please try again.');
    }
  };

  const handleVoiceCall = async (contact) => {
    console.log('Voice call initiated for:', contact);
    
    const contactName = contact.other_user?.display_name || contact.other_user?.username || contact.name || 'Unknown Contact';
    
    if (window.confirm(`Start voice call with ${contactName}?`)) {
      await initiateCall('voice');
    }
  };

  const handleVideoCall = async (contact) => {
    console.log('Video call initiated for:', contact);
    
    const contactName = contact.other_user?.display_name || contact.other_user?.username || contact.name || 'Unknown Contact';
    
    if (window.confirm(`Start video call with ${contactName}?`)) {
      await initiateCall('video');
    }
  };

  // Message search functionality
  const handleMessageSearch = async () => {
    if (!searchQuery.trim() || !selectedChat) return;
    
    setIsSearching(true);
    try {
      const response = await axios.get(`${api}/chats/${selectedChat.chat_id}/search?q=${encodeURIComponent(searchQuery)}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setSearchResults(response.data.results || []);
      
    } catch (error) {
      console.error('Search failed:', error);
      alert('Search failed. Please try again.');
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  // Clear search results
  const clearSearch = () => {
    setSearchQuery('');
    setSearchResults([]);
    setShowMessageSearch(false);
  };

  // Jump to message in chat
  const jumpToMessage = (messageId) => {
    const messageElement = document.getElementById(`message-${messageId}`);
    if (messageElement) {
      messageElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      messageElement.classList.add('bg-yellow-100');
      setTimeout(() => {
        messageElement.classList.remove('bg-yellow-100');
      }, 2000);
    }
  };

  const renderMessage = (message) => {
    const isOwnMessage = message.sender_id === user.user_id;
    
    return (
      <div 
        key={message.message_id} 
        id={`message-${message.message_id}`}
        className={`flex ${isOwnMessage ? 'justify-end' : 'justify-start'} mb-3 transition-colors duration-500`}
      >
        <div className={`max-w-xs lg:max-w-md px-3 py-2 rounded-lg ${
          isOwnMessage 
            ? 'bg-blue-500 text-white' 
            : 'bg-white text-gray-900 border'
        }`}>
          {message.message_type === 'image' && message.file_data && (
            <img
              src={`data:image/jpeg;base64,${message.file_data}`}
              alt={message.file_name}
              className="max-w-full h-auto rounded mb-2"
            />
          )}
          
          {message.message_type === 'file' && (
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-2xl">📄</span>
              <div>
                <p className="font-medium">{message.file_name}</p>
                <p className="text-xs opacity-75">
                  {message.file_size ? `${(message.file_size / 1024).toFixed(1)} KB` : ''}
                </p>
              </div>
            </div>
          )}
          
          {message.content && (
            <p className="text-sm">{message.content}</p>
          )}
          
          <p className={`text-xs mt-1 ${isOwnMessage ? 'text-blue-100' : 'text-gray-500'}`}>
            {formatTime(message.created_at)}
          </p>
        </div>
      </div>
    );
  };

  // Mobile-first single view design
  if (viewMode === 'chat' && activeContact) {
    return (
      <div className="flex-1 flex flex-col bg-white">
        {/* Chat Header */}
        <div className="bg-white border-b border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <button
                onClick={handleBackToContacts}
                className="text-blue-500 hover:text-blue-700"
              >
                ←
              </button>
              <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                <span className="text-white font-medium">
                  {(activeContact.other_user?.display_name || activeContact.other_user?.username || activeContact.name || 'Unknown')?.[0]?.toUpperCase() || 'U'}
                </span>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">
                  {activeContact.other_user?.display_name || activeContact.other_user?.username || activeContact.name || 'Unknown'}
                </h3>
                <p className="text-sm text-gray-600">
                  {isConnected ? (
                    <span className="flex items-center">
                      <span className="w-2 h-2 bg-green-500 rounded-full mr-1"></span>
                      Online
                    </span>
                  ) : (
                    'Connecting...'
                  )}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button 
                onClick={() => setShowMessageSearch(!showMessageSearch)}
                className={`p-2 rounded-lg transition-all ${
                  showMessageSearch ? 'bg-blue-100 text-blue-600' : 'text-gray-500 hover:text-blue-600 hover:bg-gray-100'
                }`}
                title="Search messages"
              >
                🔍
              </button>
              <button 
                onClick={() => handleDoubleTapAction('voice', activeContact.chat_id, () => handleVoiceCall(activeContact))}
                className={`p-2 rounded-lg transition-all ${
                  doubleTapState[`voice_${activeContact.chat_id}`]
                    ? 'bg-green-100 text-green-600 animate-pulse'
                    : 'text-gray-500 hover:text-green-600 hover:bg-gray-100'
                }`}
                title={doubleTapState[`voice_${activeContact.chat_id}`] ? 'Tap again to call' : 'Voice call (double-tap)'}
              >
                📞
              </button>
              <button 
                onClick={() => handleDoubleTapAction('video', activeContact.chat_id, () => handleVideoCall(activeContact))}
                className={`p-2 rounded-lg transition-all ${
                  doubleTapState[`video_${activeContact.chat_id}`]
                    ? 'bg-blue-100 text-blue-600 animate-pulse'
                    : 'text-gray-500 hover:text-blue-600 hover:bg-gray-100'
                }`}
                title={doubleTapState[`video_${activeContact.chat_id}`] ? 'Tap again to video call' : 'Video call (double-tap)'}
              >
                📹
              </button>
              <button 
                onClick={() => handleDoubleTapAction('file', activeContact.chat_id, () => handleFileShare())}
                className={`p-2 rounded-lg transition-all ${
                  doubleTapState[`file_${activeContact.chat_id}`]
                    ? 'bg-purple-100 text-purple-600 animate-pulse'
                    : 'text-gray-500 hover:text-purple-600 hover:bg-gray-100'
                }`}
                title={doubleTapState[`file_${activeContact.chat_id}`] ? 'Tap again to share file' : 'Share file (double-tap)'}
              >
                📎
              </button>
            </div>
          </div>
          
          {/* Message Search Bar */}
          {showMessageSearch && (
            <div className="border-t border-gray-200 p-3">
              <div className="flex items-center space-x-2 mb-3">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleMessageSearch()}
                  placeholder={t('chat.searchMessages')}
                  className="flex-1 px-3 py-1 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                />
                <button
                  onClick={handleMessageSearch}
                  disabled={isSearching || !searchQuery.trim()}
                  className="bg-blue-500 text-white px-3 py-1 rounded-lg hover:bg-blue-600 disabled:opacity-50 text-sm"
                >
                  {isSearching ? '...' : 'Search'}
                </button>
                <button
                  onClick={clearSearch}
                  className="text-gray-500 hover:text-gray-700 px-2 py-1 rounded-lg text-sm"
                >
                  ✕
                </button>
              </div>
              
              {/* Search Results */}
              {searchResults.length > 0 && (
                <div className="max-h-40 overflow-y-auto border border-gray-200 rounded-lg bg-white">
                  <div className="p-2 bg-gray-50 border-b border-gray-200 text-xs text-gray-600 font-medium">
                    Found {searchResults.length} messages containing "{searchQuery}"
                  </div>
                  {searchResults.map((message) => (
                    <div
                      key={message.message_id}
                      onClick={() => jumpToMessage(message.message_id)}
                      className="p-2 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-b-0"
                    >
                      <div className="flex items-start space-x-2">
                        <div className="text-xs text-gray-500 font-medium">
                          {message.sender_name || 'Unknown'}
                        </div>
                        <div className="text-xs text-gray-400">
                          {new Date(message.created_at).toLocaleString()}
                        </div>
                      </div>
                      <div className="text-sm text-gray-700 mt-1 line-clamp-2">
                        {message.content}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              {searchResults.length === 0 && searchQuery && !isSearching && (
                <div className="text-xs text-gray-500 mt-2">
                  No messages found containing "{searchQuery}"
                </div>
              )}
            </div>
          )}
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 bg-gray-50">
          {chatMessages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="text-4xl mb-2">💬</div>
                <p className="text-gray-600">{t('chat.startConversation')}</p>
              </div>
            </div>
          ) : (
            <div>
              {chatMessages.map(renderMessage)}
              
              {/* Typing indicator */}
              {typingUsers[selectedChat?.chat_id]?.length > 0 && (
                <div className="flex justify-start mb-3">
                  <div className="bg-gray-200 px-3 py-2 rounded-lg">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          )}
          
          {/* Call Interface Overlay */}
          {isCallActive && (
            <div className="fixed inset-0 bg-black bg-opacity-90 z-50 flex flex-col">
              {/* Call Header */}
              <div className="bg-black text-white p-4 text-center">
                <h2 className="text-lg font-semibold">
                  {callType === 'video' ? '📹 Video Call' : '📞 Voice Call'}
                </h2>
                <p className="text-gray-300 text-sm">
                  {selectedChat?.other_user?.display_name || 'Contact'}
                </p>
              </div>
              
              {/* Video Area */}
              {callType === 'video' && (
                <div className="flex-1 relative">
                  {/* Remote Video */}
                  <video
                    ref={remoteVideoRef}
                    autoPlay
                    className="w-full h-full object-cover"
                    style={{ transform: 'scaleX(-1)' }}
                  />
                  
                  {/* Local Video (Picture-in-Picture) */}
                  <video
                    ref={localVideoRef}
                    autoPlay
                    muted
                    className="absolute top-4 right-4 w-32 h-24 object-cover rounded-lg border-2 border-white"
                    style={{ transform: 'scaleX(-1)' }}
                  />
                  
                  {/* No remote stream message */}
                  {!remoteStream && (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="text-white text-center">
                        <div className="text-6xl mb-4">📹</div>
                        <p>Waiting for connection...</p>
                        <p className="text-sm text-gray-300 mt-2">
                          In production, this would connect via signaling server
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              )}
              
              {/* Voice Call Display */}
              {callType === 'voice' && (
                <div className="flex-1 flex items-center justify-center">
                  <div className="text-white text-center">
                    <div className="text-8xl mb-4">📞</div>
                    <h3 className="text-2xl font-semibold mb-2">
                      {selectedChat?.other_user?.display_name || 'Contact'}
                    </h3>
                    <p className="text-gray-300">Voice call in progress...</p>
                    <p className="text-sm text-gray-400 mt-2">
                      Demo mode - In production connects via WebRTC
                    </p>
                  </div>
                </div>
              )}
              
              {/* Call Controls */}
              <div className="bg-black p-6 flex justify-center space-x-6">
                <button
                  onClick={endCall}
                  className="bg-red-500 hover:bg-red-600 text-white p-4 rounded-full transition-colors"
                  title="End Call"
                >
                  📞❌
                </button>
              </div>
            </div>
          )}

          {/* File Upload Progress */}
          {isUploadingFile && (
            <div className="fixed bottom-20 left-4 right-4 bg-white rounded-lg shadow-lg border p-4 z-50">
              <div className="flex items-center space-x-3">
                <div className="text-2xl">📤</div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">Uploading file...</p>
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                    <div 
                      className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    ></div>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">{Math.round(uploadProgress)}% complete</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Message Input */}
        <div className="bg-white border-t border-gray-200 p-4">
          <div className="flex items-center space-x-3">
            <input
              type="text"
              value={newMessage}
              onChange={(e) => {
                setNewMessage(e.target.value);
                handleTyping();
              }}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              placeholder={t('chat.typeMessage')}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <button
              onClick={sendMessage}
              disabled={!newMessage.trim()}
              className="bg-blue-500 text-white p-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              ➤
            </button>
          </div>
        </div>

        {/* Hidden file input */}
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileSelect}
          style={{ display: 'none' }}
          accept="image/*,.pdf,.doc,.docx,.txt"
        />
      </div>
    );
  }

  // Contacts List View (Default)
  return (
    <div className="flex-1 flex flex-col bg-white">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">{t('dashboard.chats')}</h2>
            <p className="text-sm text-gray-600">
              {isConnected ? (
                <span className="flex items-center">
                  <span className="w-2 h-2 bg-green-500 rounded-full mr-1"></span>
                  {t('chat.connected')}
                </span>
              ) : (
                t('common.loading')
              )}
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <button 
              onClick={() => setShowMyPin(true)}
              className="bg-green-500 text-white p-2 rounded-lg hover:bg-green-600"
              title="Share My PIN"
            >
              📤
            </button>
            <button 
              onClick={() => setShowAddContact(true)}
              className="bg-blue-500 text-white p-2 rounded-lg hover:bg-blue-600"
              title="Add Contact"
            >
              ➕
            </button>
          </div>
        </div>
      </div>

      {/* Chats List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full"></div>
          </div>
        ) : chats && chats.length > 0 ? (
          <div className="divide-y divide-gray-100">
            {chats.map(chat => (
              <div
                key={chat.chat_id}
                className="p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center space-x-3">
                  {/* Contact Avatar and Info */}
                  <button
                    onClick={() => handleContactTap(chat)}
                    className="flex items-center space-x-3 flex-1 text-left"
                  >
                    <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center relative">
                      <span className="text-white font-medium text-lg">
                        {(chat.other_user?.display_name || chat.other_user?.username || chat.name || 'Unknown')?.[0]?.toUpperCase() || 'U'}
                      </span>
                      {onlineUsers.has(chat.other_user?.user_id) && (
                        <span className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white"></span>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 truncate">
                        {chat.other_user?.display_name || chat.other_user?.username || chat.name || 'Unknown Contact'}
                      </p>
                      <p className="text-sm text-gray-600 truncate">
                        {chat.last_message?.content || t('chat.noMessages')}
                      </p>
                    </div>
                    <div className="text-xs text-gray-500">
                      {chat.last_message?.created_at && formatTime(chat.last_message.created_at)}
                    </div>
                  </button>

                  {/* Action Buttons with Double-Tap Protection */}
                  <div className="flex items-center space-x-1">
                    {/* Voice Call Button */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDoubleTapAction('voice', chat.chat_id, () => handleVoiceCall(chat));
                      }}
                      className={`p-2 rounded-lg transition-all ${
                        doubleTapState[`voice_${chat.chat_id}`]
                          ? 'bg-green-100 text-green-600 animate-pulse'
                          : 'text-gray-500 hover:text-green-600 hover:bg-gray-100'
                      }`}
                      title={doubleTapState[`voice_${chat.chat_id}`] ? 'Tap again to call' : 'Voice call (double-tap)'}
                    >
                      📞
                    </button>

                    {/* Video Call Button */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDoubleTapAction('video', chat.chat_id, () => handleVideoCall(chat));
                      }}
                      className={`p-2 rounded-lg transition-all ${
                        doubleTapState[`video_${chat.chat_id}`]
                          ? 'bg-blue-100 text-blue-600 animate-pulse'
                          : 'text-gray-500 hover:text-blue-600 hover:bg-gray-100'
                      }`}
                      title={doubleTapState[`video_${chat.chat_id}`] ? 'Tap again to video call' : 'Video call (double-tap)'}
                    >
                      📹
                    </button>

                    {/* File Share Button */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDoubleTapAction('file', chat.chat_id, () => {
                          setActiveContact(chat);
                          setViewMode('chat');
                          onSelectChat(chat);
                          setTimeout(() => handleFileShare(), 100);
                        });
                      }}
                      className={`p-2 rounded-lg transition-all ${
                        doubleTapState[`file_${chat.chat_id}`]
                          ? 'bg-purple-100 text-purple-600 animate-pulse'
                          : 'text-gray-500 hover:text-purple-600 hover:bg-gray-100'
                      }`}
                      title={doubleTapState[`file_${chat.chat_id}`] ? 'Tap again to share file' : 'Share file (double-tap)'}
                    >
                      📎
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center p-6">
            <div className="text-6xl mb-4">💬</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No chats yet</h3>
            <p className="text-gray-600 text-sm mb-6">
              Connect with people using PIN codes or email addresses to start authentic conversations.
            </p>
            <button 
              onClick={() => setShowAddContact(true)}
              className="bg-blue-500 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-600"
            >
              Add Your First Contact
            </button>
          </div>
        )}
      </div>

      {/* Add Contact Modal */}
      {showAddContact && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-sm w-full p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-bold text-gray-900">Add Contact</h2>
              <button
                onClick={() => {
                  setShowAddContact(false);
                  setContactPin('');
                  setContactEmail('');
                }}
                className="text-gray-500 hover:text-gray-700 text-xl"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              <div className="flex rounded-lg border border-gray-300 p-1">
                <button
                  onClick={() => setAddContactMethod('pin')}
                  className={`flex-1 py-2 px-3 rounded text-sm font-medium ${
                    addContactMethod === 'pin' 
                      ? 'bg-blue-500 text-white' 
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  PIN Code
                </button>
                <button
                  onClick={() => setAddContactMethod('email')}
                  className={`flex-1 py-2 px-3 rounded text-sm font-medium ${
                    addContactMethod === 'email' 
                      ? 'bg-blue-500 text-white' 
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  Email
                </button>
              </div>

              {addContactMethod === 'pin' ? (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Enter Connection PIN
                    </label>
                    <input
                      type="text"
                      value={contactPin}
                      onChange={(e) => setContactPin(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="PIN-XXXXX"
                    />
                  </div>
                  <button
                    onClick={sendConnectionRequest}
                    disabled={!contactPin.trim()}
                    className="w-full bg-blue-500 text-white py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50"
                  >
                    Send Connection Request
                  </button>
                </>
              ) : (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Email Address
                    </label>
                    <input
                      type="email"
                      value={contactEmail}
                      onChange={(e) => setContactEmail(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="friend@example.com"
                    />
                  </div>
                  <button
                    onClick={addContactByEmail}
                    disabled={!contactEmail.trim()}
                    className="w-full bg-blue-500 text-white py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50"
                  >
                    Add Contact
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Share PIN Modal */}
      {showMyPin && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-sm w-full p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-bold text-gray-900">Share My PIN</h2>
              <button
                onClick={() => setShowMyPin(false)}
                className="text-gray-500 hover:text-gray-700 text-xl"
              >
                ✕
              </button>
            </div>
            
            <div className="text-center">
              <div className="bg-gray-50 p-4 rounded-lg mb-4">
                <QRCode 
                  value={user.connection_pin || 'PIN-DEFAULT'} 
                  size={120}
                  className="mx-auto mb-3"
                />
                <p className="text-lg font-mono font-bold text-gray-900">
                  {user.connection_pin || 'Loading...'}
                </p>
              </div>
              
              <p className="text-sm text-gray-600 mb-4">
                Share this PIN with people you want to connect with
              </p>
              
              <button
                onClick={shareMyPin}
                className="w-full bg-blue-500 text-white py-2 rounded-lg hover:bg-blue-600"
              >
                Share PIN
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatsInterface;