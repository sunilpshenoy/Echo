import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import QRCode from 'react-qr-code';
import { useTranslation } from 'react-i18next';
import CallInterface from './CallInterface';
import EmojiPicker from './EmojiPicker';
import MessageReactions from './MessageReactions';
import GifPicker from './GifPicker';

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

  // Enhanced WebSocket message handling with emoji reactions
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

      // Emoji reaction WebSocket messages
      case 'reaction_added':
        fetchMessageReactions(message.data.message_id);
        break;
        
      case 'reaction_removed':
        fetchMessageReactions(message.data.message_id);
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

  // Enhanced file sharing state and functionality
  const [isUploadingFile, setIsUploadingFile] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadQueue, setUploadQueue] = useState([]);
  const [dragActive, setDragActive] = useState(false);
  const [filePreview, setFilePreview] = useState(null);
  const [showFilePreview, setShowFilePreview] = useState(false);
  
  // Emoji functionality state
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [customEmojis, setCustomEmojis] = useState([]);
  const [messageReactions, setMessageReactions] = useState({});
  const [showCustomEmojiModal, setShowCustomEmojiModal] = useState(false);
  
  // GIF functionality state
  const [showGifPicker, setShowGifPicker] = useState(false);

  // Enhanced file validation with better feedback
  const validateFile = (file) => {
    const maxSize = 25 * 1024 * 1024; // Increased to 25MB
    const allowedTypes = {
      // Images
      'image/jpeg': { category: 'Image', icon: '🖼️', maxSize: 10 * 1024 * 1024 },
      'image/png': { category: 'Image', icon: '🖼️', maxSize: 10 * 1024 * 1024 },
      'image/gif': { category: 'Image', icon: '🖼️', maxSize: 5 * 1024 * 1024 },
      'image/webp': { category: 'Image', icon: '🖼️', maxSize: 10 * 1024 * 1024 },
      // Documents
      'application/pdf': { category: 'Document', icon: '📄', maxSize: 25 * 1024 * 1024 },
      'text/plain': { category: 'Text', icon: '📝', maxSize: 5 * 1024 * 1024 },
      'application/msword': { category: 'Document', icon: '📝', maxSize: 25 * 1024 * 1024 },
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': { category: 'Document', icon: '📝', maxSize: 25 * 1024 * 1024 },
      // Spreadsheets
      'application/vnd.ms-excel': { category: 'Spreadsheet', icon: '📊', maxSize: 25 * 1024 * 1024 },
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': { category: 'Spreadsheet', icon: '📊', maxSize: 25 * 1024 * 1024 },
      // Audio
      'audio/mpeg': { category: 'Audio', icon: '🎵', maxSize: 15 * 1024 * 1024 },
      'audio/wav': { category: 'Audio', icon: '🎵', maxSize: 15 * 1024 * 1024 },
      'audio/ogg': { category: 'Audio', icon: '🎵', maxSize: 15 * 1024 * 1024 },
      // Video (limited size)
      'video/mp4': { category: 'Video', icon: '🎬', maxSize: 50 * 1024 * 1024 },
      'video/webm': { category: 'Video', icon: '🎬', maxSize: 50 * 1024 * 1024 },
      // Archives
      'application/zip': { category: 'Archive', icon: '📦', maxSize: 25 * 1024 * 1024 },
      'application/x-rar-compressed': { category: 'Archive', icon: '📦', maxSize: 25 * 1024 * 1024 }
    };
    
    const fileInfo = allowedTypes[file.type];
    
    if (!fileInfo) {
      return {
        valid: false,
        error: `File type not supported!\n\nSupported types:\n• Images: JPG, PNG, GIF, WebP\n• Documents: PDF, Word, Excel, Text\n• Media: Audio (MP3, WAV), Video (MP4, WebM)\n• Archives: ZIP, RAR\n\nYour file: ${file.type || 'Unknown type'}`
      };
    }
    
    if (file.size > fileInfo.maxSize) {
      return {
        valid: false,
        error: `File too large for ${fileInfo.category}!\n\nMaximum size for ${fileInfo.category}: ${(fileInfo.maxSize / (1024 * 1024)).toFixed(1)}MB\nYour file: ${(file.size / (1024 * 1024)).toFixed(1)}MB`
      };
    }
    
    return { valid: true, fileInfo };
  };

  // Enhanced file preview generation
  const generateFilePreview = (file) => {
    return new Promise((resolve) => {
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => resolve({
          type: 'image',
          url: e.target.result,
          name: file.name,
          size: file.size
        });
        reader.readAsDataURL(file);
      } else {
        // For non-images, create a preview card
        const validation = validateFile(file);
        resolve({
          type: 'file',
          icon: validation.fileInfo?.icon || '📄',
          name: file.name,
          size: file.size,
          category: validation.fileInfo?.category || 'Unknown'
        });
      }
    });
  };

  // Chunked upload implementation
  const uploadFileInChunks = async (file, chatId) => {
    const chunkSize = 1024 * 1024; // 1MB chunks
    const totalChunks = Math.ceil(file.size / chunkSize);
    const fileId = `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    let uploadedChunks = 0;
    
    // Read entire file as base64 for current implementation
    // In production, you'd upload chunks separately
    const reader = new FileReader();
    
    return new Promise((resolve, reject) => {
      reader.onprogress = (e) => {
        if (e.lengthComputable) {
          const progress = (e.loaded / e.total) * 80; // Reserve 20% for upload
          setUploadProgress(progress);
        }
      };
      
      reader.onload = async () => {
        try {
          setUploadProgress(80); // Reading complete
          
          const base64Data = reader.result.split(',')[1];
          const validation = validateFile(file);
          const messageType = file.type.startsWith('image/') ? 'image' : 'file';
          
          const response = await axios.post(`${api}/chats/${chatId}/messages`, {
            content: file.name,
            message_type: messageType,
            file_name: file.name,
            file_size: file.size,
            file_data: base64Data
          }, {
            headers: { Authorization: `Bearer ${token}` },
            onUploadProgress: (progressEvent) => {
              const uploadProgress = 80 + (progressEvent.loaded / progressEvent.total) * 20;
              setUploadProgress(uploadProgress);
            }
          });
          
          resolve(response);
          
        } catch (error) {
          reject(error);
        }
      };
      
      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsDataURL(file);
    });
  };

  // Enhanced file selection handler
  const handleFileSelect = async (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0 || !selectedChat) return;
    
    // Process multiple files
    for (const file of files) {
      await processFileUpload(file);
    }
    
    // Clear file input
    event.target.value = '';
  };

  // Process individual file upload
  const processFileUpload = async (file) => {
    // Validate file
    const validation = validateFile(file);
    if (!validation.valid) {
      alert(validation.error);
      return;
    }
    
    // Generate preview
    const preview = await generateFilePreview(file);
    setFilePreview(preview);
    setShowFilePreview(true);
    
    // Wait for user confirmation or auto-proceed after 2 seconds
    const proceed = await new Promise((resolve) => {
      const timer = setTimeout(() => {
        setShowFilePreview(false);
        resolve(true);
      }, 2000);
      
      // User can click to proceed immediately
      window.confirmFileUpload = () => {
        clearTimeout(timer);
        setShowFilePreview(false);
        resolve(true);
      };
      
      window.cancelFileUpload = () => {
        clearTimeout(timer);
        setShowFilePreview(false);
        resolve(false);
      };
    });
    
    if (!proceed) return;
    
    setIsUploadingFile(true);
    setUploadProgress(0);
    
    try {
      await uploadFileInChunks(file, selectedChat.chat_id);
      
      setUploadProgress(100);
      
      // Show success notification
      const fileIcon = validation.fileInfo.icon;
      const notification = document.createElement('div');
      notification.className = 'fixed top-4 right-4 bg-green-500 text-white p-3 rounded-lg shadow-lg z-50 flex items-center space-x-2';
      notification.innerHTML = `
        <span>${fileIcon}</span>
        <span>File "${file.name}" shared successfully!</span>
      `;
      document.body.appendChild(notification);
      
      setTimeout(() => {
        document.body.removeChild(notification);
      }, 3000);
      
      // Refresh messages
      onSelectChat(selectedChat);
      
    } catch (error) {
      console.error('Failed to send file:', error);
      const errorMsg = error.response?.data?.detail || 'Failed to send file. Please try again.';
      
      // Show error notification
      const notification = document.createElement('div');
      notification.className = 'fixed top-4 right-4 bg-red-500 text-white p-3 rounded-lg shadow-lg z-50 flex items-center space-x-2';
      notification.innerHTML = `
        <span>❌</span>
        <span>Upload failed: ${errorMsg}</span>
      `;
      document.body.appendChild(notification);
      
      setTimeout(() => {
        document.body.removeChild(notification);
      }, 5000);
      
    } finally {
      setIsUploadingFile(false);
      setUploadProgress(0);
    }
  };

  // Drag and drop handlers
  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    const files = Array.from(e.dataTransfer.files);
    files.forEach(file => processFileUpload(file));
  };

  // Emoji functionality
  const fetchCustomEmojis = async () => {
    try {
      const response = await axios.get(`${api}/emojis/custom`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCustomEmojis(response.data.custom_emojis || []);
    } catch (error) {
      console.error('Failed to fetch custom emojis:', error);
    }
  };

  const fetchMessageReactions = async (messageId) => {
    try {
      const response = await axios.get(`${api}/messages/${messageId}/reactions`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMessageReactions(prev => ({
        ...prev,
        [messageId]: response.data.reactions || []
      }));
    } catch (error) {
      console.error('Failed to fetch message reactions:', error);
    }
  };

  const addEmojiReaction = async (messageId, emoji) => {
    try {
      await axios.post(`${api}/messages/${messageId}/reactions`, {
        emoji: typeof emoji === 'object' ? `:${emoji.name}:` : emoji
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Reactions will be updated via WebSocket
    } catch (error) {
      console.error('Failed to add emoji reaction:', error);
    }
  };

  const removeEmojiReaction = async (messageId, emoji) => {
    // This is handled by the toggle behavior in the backend
    await addEmojiReaction(messageId, emoji);
  };

  const handleEmojiSelect = (emoji) => {
    if (typeof emoji === 'object') {
      // Custom emoji
      setNewMessage(prev => prev + `:${emoji.name}:`);
    } else {
      // Standard emoji
      setNewMessage(prev => prev + emoji);
    }
    setShowEmojiPicker(false);
  };

  const handleGifSelect = async (gif) => {
    if (!selectedChat) return;
    
    try {
      // Send GIF as a message
      const response = await axios.post(`${api}/chats/${selectedChat.chat_id}/messages`, {
        content: gif.title,
        message_type: 'gif',
        gif_data: {
          id: gif.id,
          url: gif.url,
          preview: gif.preview,
          width: gif.width,
          height: gif.height,
          title: gif.title
        }
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Refresh messages
      onSelectChat(selectedChat);
      
    } catch (error) {
      console.error('Failed to send GIF:', error);
      // Show error notification
      const notification = document.createElement('div');
      notification.className = 'fixed top-4 right-4 bg-red-500 text-white p-3 rounded-lg shadow-lg z-50 flex items-center space-x-2';
      notification.innerHTML = `
        <span>❌</span>
        <span>Failed to send GIF. Please try again.</span>
      `;
      document.body.appendChild(notification);
      
      setTimeout(() => {
        if (document.body.contains(notification)) {
          document.body.removeChild(notification);
        }
      }, 3000);
    }
    
    setShowGifPicker(false);
  };

  const uploadCustomEmoji = async (file, name, category = 'custom') => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('name', name);
      formData.append('category', category);

      await axios.post(`${api}/emojis/custom`, formData, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });

      // Refresh custom emojis
      await fetchCustomEmojis();
      
      return true;
    } catch (error) {
      console.error('Failed to upload custom emoji:', error);
      return false;
    }
  };

  const deleteCustomEmoji = async (emojiId) => {
    try {
      await axios.delete(`${api}/emojis/custom/${emojiId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      // Refresh custom emojis
      await fetchCustomEmojis();
      
      return true;
    } catch (error) {
      console.error('Failed to delete custom emoji:', error);
      return false;
    }
  };

  // Load custom emojis and message reactions when chat is selected
  useEffect(() => {
    if (user && token) {
      fetchCustomEmojis();
    }
  }, [user, token]);

  useEffect(() => {
    if (selectedChat && messages.length > 0) {
      // Fetch reactions for all messages
      messages.forEach(message => {
        fetchMessageReactions(message.message_id);
      });
    }
  }, [selectedChat, messages]);

  // Message search state
  const [showMessageSearch, setShowMessageSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

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
    const reactions = messageReactions[message.message_id] || [];
    
    return (
      <div 
        key={message.message_id} 
        id={`message-${message.message_id}`}
        className={`group flex ${isOwnMessage ? 'justify-end' : 'justify-start'} mb-3 transition-colors duration-500`}
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

          {/* Message Reactions */}
          <MessageReactions
            messageId={message.message_id}
            reactions={reactions}
            onAddReaction={addEmojiReaction}
            onRemoveReaction={removeEmojiReaction}
            currentUserId={user.user_id}
          />
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

        {/* Messages Area with Drag & Drop Support */}
        <div 
          className="flex-1 overflow-y-auto p-4 bg-gray-50"
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
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
          
          {/* Enhanced Call Interface */}
          {isCallActive && (
            <CallInterface
              call={currentCall}
              callType={callType}
              localStream={localStream}
              remoteStream={remoteStream}
              onEndCall={endCall}
              onToggleMute={toggleMute}
              onToggleVideo={toggleVideo}
              onToggleScreenShare={toggleScreenShare}
              isMuted={isMuted}
              isVideoOff={isVideoOff}
              isScreenSharing={isScreenSharing}
              api={api}
              token={token}
            />
          )}

          {/* Incoming Call Modal */}
          {incomingCall && !isCallActive && (
            <div className="fixed inset-0 bg-black bg-opacity-90 z-50 flex items-center justify-center">
              <div className="bg-white rounded-2xl shadow-2xl max-w-sm w-full mx-4 p-6">
                <div className="text-center">
                  <div className="w-24 h-24 bg-purple-500 rounded-full mx-auto mb-4 flex items-center justify-center">
                    <span className="text-white text-3xl">
                      {incomingCall.call_type === 'video' ? '📹' : '📞'}
                    </span>
                  </div>
                  
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {incomingCall.call_type === 'video' ? t('calls.videoCall') : t('calls.voiceCall')}
                  </h3>
                  
                  <p className="text-gray-600 mb-6">
                    {selectedChat?.other_user?.display_name || 'Contact'} {t('calls.incomingCall')}
                  </p>
                  
                  <div className="flex space-x-4">
                    <button
                      onClick={() => declineCall(incomingCall)}
                      className="flex-1 bg-red-500 text-white py-3 px-4 rounded-lg hover:bg-red-600 transition-colors flex items-center justify-center space-x-2"
                    >
                      <span>📞❌</span>
                      <span>{t('calls.decline')}</span>
                    </button>
                    
                    <button
                      onClick={() => acceptCall(incomingCall)}
                      className="flex-1 bg-green-500 text-white py-3 px-4 rounded-lg hover:bg-green-600 transition-colors flex items-center justify-center space-x-2"
                    >
                      <span>📞✅</span>
                      <span>{t('calls.accept')}</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Enhanced File Upload Progress */}
          {isUploadingFile && (
            <div className="fixed bottom-20 left-4 right-4 bg-white rounded-lg shadow-lg border p-4 z-50">
              <div className="flex items-center space-x-3">
                <div className="text-2xl">
                  {uploadProgress < 80 ? '📖' : uploadProgress < 100 ? '📤' : '✅'}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">
                    {uploadProgress < 80 ? 'Reading file...' : uploadProgress < 100 ? 'Uploading...' : 'Complete!'}
                  </p>
                  <div className="w-full bg-gray-200 rounded-full h-3 mt-1 overflow-hidden">
                    <div 
                      className={`h-3 rounded-full transition-all duration-500 ${
                        uploadProgress < 100 
                          ? 'bg-gradient-to-r from-blue-500 to-purple-500' 
                          : 'bg-gradient-to-r from-green-500 to-emerald-500'
                      }`}
                      style={{ width: `${uploadProgress}%` }}
                    ></div>
                  </div>
                  <div className="flex justify-between items-center mt-1">
                    <p className="text-xs text-gray-500">{Math.round(uploadProgress)}% complete</p>
                    <p className="text-xs text-gray-400">
                      {uploadProgress < 80 ? 'Processing...' : uploadProgress < 100 ? 'Sending...' : 'Done!'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* File Preview Modal */}
          {showFilePreview && filePreview && (
            <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
              <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Send File</h3>
                
                <div className="bg-gray-50 rounded-lg p-4 mb-4">
                  {filePreview.type === 'image' ? (
                    <img 
                      src={filePreview.url} 
                      alt={filePreview.name}
                      className="w-full h-48 object-cover rounded-lg mb-3"
                    />
                  ) : (
                    <div className="flex items-center justify-center h-24 mb-3">
                      <span className="text-4xl">{filePreview.icon}</span>
                    </div>
                  )}
                  
                  <div className="text-center">
                    <p className="font-medium text-gray-900 truncate">{filePreview.name}</p>
                    <p className="text-sm text-gray-500">
                      {filePreview.category} • {(filePreview.size / 1024 / 1024).toFixed(1)} MB
                    </p>
                  </div>
                </div>
                
                <div className="flex space-x-3">
                  <button
                    onClick={() => window.cancelFileUpload && window.cancelFileUpload()}
                    className="flex-1 bg-gray-100 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => window.confirmFileUpload && window.confirmFileUpload()}
                    className="flex-1 bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 transition-colors"
                  >
                    Send File
                  </button>
                </div>
                
                <p className="text-xs text-gray-400 text-center mt-2">
                  Auto-sending in 2 seconds...
                </p>
              </div>
            </div>
          )}

          {/* Drag and Drop Overlay */}
          {dragActive && (
            <div className="fixed inset-0 bg-blue-500 bg-opacity-90 z-40 flex items-center justify-center">
              <div className="text-center text-white">
                <div className="text-6xl mb-4">📁</div>
                <h3 className="text-2xl font-semibold mb-2">Drop files here</h3>
                <p className="text-blue-100">Release to upload files to this chat</p>
              </div>
            </div>
          )}
        </div>

        {/* Message Input with Emoji & GIF Support */}
        <div className="bg-white border-t border-gray-200 p-4 relative">
          <div className="flex items-center space-x-3">
            {/* File Upload Button */}
            <button
              onClick={() => fileInputRef.current?.click()}
              className="p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100"
              title={t('chat.attachFile')}
            >
              📎
            </button>

            {/* GIF Picker Button */}
            <button
              onClick={() => {
                setShowGifPicker(!showGifPicker);
                setShowEmojiPicker(false);
              }}
              className="p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100"
              title={t('gifs.picker')}
            >
              🎬
            </button>

            {/* Emoji Picker Button */}
            <button
              onClick={() => {
                setShowEmojiPicker(!showEmojiPicker);
                setShowGifPicker(false);
              }}
              className="p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100"
              title={t('emojis.picker')}
            >
              😀
            </button>

            {/* Message Input */}
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

            {/* Send Button */}
            <button
              onClick={sendMessage}
              disabled={!newMessage.trim()}
              className="bg-blue-500 text-white p-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              ➤
            </button>
          </div>

          {/* GIF Picker */}
          {showGifPicker && (
            <GifPicker
              onGifSelect={handleGifSelect}
              onClose={() => setShowGifPicker(false)}
            />
          )}

          {/* Emoji Picker */}
          {showEmojiPicker && (
            <EmojiPicker
              onEmojiSelect={handleEmojiSelect}
              onClose={() => setShowEmojiPicker(false)}
              customEmojis={customEmojis}
            />
          )}
        </div>

        {/* Hidden file input - supports multiple files */}
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileSelect}
          multiple
          accept="image/*,application/pdf,text/plain,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,audio/*,video/*,application/zip,application/x-rar-compressed"
          style={{ display: 'none' }}
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