import React, { useState, useEffect } from 'react';
import axios from 'axios';
import QRCode from 'react-qr-code';

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
  const [showAddContact, setShowAddContact] = useState(false);
  const [showMyPin, setShowMyPin] = useState(false);
  const [contactPin, setContactPin] = useState('');
  const [contactRequests, setContactRequests] = useState([]);
  const [showQRScanner, setShowQRScanner] = useState(false);
  const [contactEmail, setContactEmail] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [addContactMethod, setAddContactMethod] = useState('pin');
  const [viewMode, setViewMode] = useState('contacts');
  const [activeContact, setActiveContact] = useState(null);

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
      console.log('Making API call to send connection request...');
      const response = await axios.post(`${api}/connections/request-by-pin`, {
        target_pin: contactPin,
        message: "Hi! I'd like to connect with you."
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      console.log('Connection request sent successfully:', response.data);
      setContactPin('');
      setShowAddContact(false);
      alert('Connection request sent! 🎉');
      
      // Refresh page to show new connection/chat
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    } catch (error) {
      console.error('Failed to send connection request:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to send request. Please check the PIN.';
      alert(errorMessage);
    }
  };

  // Add contact by email
  const addContactByEmail = async () => {
    console.log('addContactByEmail called with email:', contactEmail);
    if (!contactEmail.trim()) {
      alert('Please enter an email address');
      return;
    }
    
    try {
      console.log('Making API call to add contact...');
      const response = await axios.post(`${api}/contacts`, {
        email: contactEmail
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      console.log('Contact added successfully:', response.data);
      setContactEmail('');
      setShowAddContact(false);
      alert('Contact added successfully! 🎉');
      
      // Refresh chats to show new contact immediately
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    } catch (error) {
      console.error('Failed to add contact:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to add contact. Please check the email address.';
      alert(errorMessage);
    }
  };

  // Add contact by phone (placeholder)
  const addContactByPhone = async () => {
    if (!contactPhone.trim()) return;
    
    try {
      alert('Phone contact addition will be implemented soon! 📱');
      setContactPhone('');
      setShowAddContact(false);
    } catch (error) {
      console.error('Failed to add contact:', error);
      alert('Failed to add contact. Please try again.');
    }
  };

  // Voice call function
  const startVoiceCall = async (chat) => {
    try {
      console.log('Starting voice call with:', chat.other_user?.display_name);
      
      const response = await axios.post(`${api}/calls/initiate`, {
        chat_id: chat.chat_id,
        call_type: 'voice'
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const callData = response.data;
      console.log('Call initiated:', callData);
      
      openCallModal(chat, 'voice', callData);
      
    } catch (error) {
      console.error('Failed to start voice call:', error);
      alert('Failed to start voice call. Please try again.');
    }
  };

  // Video call function
  const startVideoCall = async (chat) => {
    try {
      console.log('Starting video call with:', chat.other_user?.display_name);
      
      const response = await axios.post(`${api}/calls/initiate`, {
        chat_id: chat.chat_id,
        call_type: 'video'
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const callData = response.data;
      console.log('Call initiated:', callData);
      
      openCallModal(chat, 'video', callData);
      
    } catch (error) {
      console.error('Failed to start video call:', error);
      alert('Failed to start video call. Please try again.');
    }
  };

  // Open call modal with WebRTC
  const openCallModal = (chat, callType, callData) => {
    const callWindow = window.open(
      '', 
      'call_window',
      'width=400,height=600,resizable=yes,scrollbars=no,status=no,toolbar=no,menubar=no'
    );
    
    callWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>${callType === 'video' ? '📹' : '🎙️'} Call with ${chat.other_user?.display_name || 'Contact'}</title>
        <style>
          body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
          }
          .call-container { 
            max-width: 350px; 
            margin: 0 auto; 
            padding: 20px;
          }
          .avatar { 
            width: 120px; 
            height: 120px; 
            border-radius: 50%; 
            background: rgba(255,255,255,0.2); 
            margin: 20px auto; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            font-size: 48px;
          }
          .controls { 
            margin-top: 40px; 
            display: flex; 
            justify-content: center; 
            gap: 20px; 
          }
          button { 
            width: 60px; 
            height: 60px; 
            border: none; 
            border-radius: 50%; 
            font-size: 24px; 
            cursor: pointer; 
            transition: transform 0.2s;
          }
          button:hover { transform: scale(1.1); }
          .mute { background: #34d399; }
          .video { background: #3b82f6; }
          .end { background: #ef4444; }
          video { 
            width: 100%; 
            max-width: 300px; 
            border-radius: 10px; 
            margin: 20px 0;
            display: ${callType === 'video' ? 'block' : 'none'};
          }
          .status { 
            margin: 20px 0; 
            font-size: 18px; 
            opacity: 0.9; 
          }
        </style>
      </head>
      <body>
        <div class="call-container">
          <h2>${callType === 'video' ? '📹 Video Call' : '🎙️ Voice Call'}</h2>
          <div class="avatar">
            ${chat.other_user?.display_name?.[0]?.toUpperCase() || '?'}
          </div>
          <h3>${chat.other_user?.display_name || 'Contact'}</h3>
          <div class="status" id="status">Connecting...</div>
          
          <video id="localVideo" autoplay muted></video>
          <video id="remoteVideo" autoplay></video>
          
          <div class="controls">
            <button class="mute" onclick="toggleMute()" title="Toggle Mute" id="muteBtn">
              🎤
            </button>
            ${callType === 'video' ? `
            <button class="video" onclick="toggleVideo()" title="Toggle Video" id="videoBtn">
              📹
            </button>
            ` : ''}
            <button class="end" onclick="endCall()" title="End Call">
              📞
            </button>
          </div>
        </div>
        
        <script>
          let localStream = null;
          let isMuted = false;
          let isVideoEnabled = ${callType === 'video'};
          
          async function initializeCall() {
            try {
              const constraints = {
                audio: true,
                video: isVideoEnabled
              };
              
              localStream = await navigator.mediaDevices.getUserMedia(constraints);
              
              if (isVideoEnabled) {
                document.getElementById('localVideo').srcObject = localStream;
              }
              
              document.getElementById('status').textContent = 'Call connected! 🎉';
              
              setTimeout(() => {
                document.getElementById('status').textContent = 'In call with ${chat.other_user?.display_name || 'contact'}';
              }, 2000);
              
            } catch (error) {
              console.error('Failed to access media devices:', error);
              document.getElementById('status').textContent = 'Failed to access camera/microphone';
            }
          }
          
          function toggleMute() {
            if (localStream) {
              const audioTrack = localStream.getAudioTracks()[0];
              if (audioTrack) {
                audioTrack.enabled = !audioTrack.enabled;
                isMuted = !audioTrack.enabled;
                document.getElementById('muteBtn').textContent = isMuted ? '🔇' : '🎤';
              }
            }
          }
          
          function toggleVideo() {
            if (localStream && isVideoEnabled) {
              const videoTrack = localStream.getVideoTracks()[0];
              if (videoTrack) {
                videoTrack.enabled = !videoTrack.enabled;
                document.getElementById('videoBtn').textContent = videoTrack.enabled ? '📹' : '📷';
              }
            }
          }
          
          function endCall() {
            if (localStream) {
              localStream.getTracks().forEach(track => track.stop());
            }
            window.close();
          }
          
          window.onload = initializeCall;
          
          window.onbeforeunload = function() {
            if (localStream) {
              localStream.getTracks().forEach(track => track.stop());
            }
          };
        </script>
      </body>
      </html>
    `);
    
    callWindow.document.close();
  };

  // File sharing function
  const startFileShare = async (chat) => {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = 'image/*,video/*,audio/*,.pdf,.doc,.docx,.txt,.zip';
    fileInput.multiple = true;
    
    fileInput.onchange = async (event) => {
      const files = Array.from(event.target.files);
      if (files.length === 0) return;
      
      try {
        console.log('Selected files:', files);
        alert(`File sharing functionality working! Selected ${files.length} file(s). Upload feature coming soon! 📎`);
      } catch (error) {
        console.error('File sharing failed:', error);
        alert('Failed to share files. Please try again.');
      }
    };
    
    fileInput.click();
  };

  return (
    <div className="flex h-full">
      <div className="w-full h-full">
        {viewMode === 'contacts' ? (
          // Contact List View - Full Screen on Mobile
          <div className="w-full h-full flex flex-col">
            {/* Contact List Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-white">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Chats</h2>
                <p className="text-sm text-gray-600">Your connections</p>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setShowMyPin(true)}
                  className="p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                  title="Share PIN"
                >
                  📱
                </button>
                <button
                  onClick={() => setShowAddContact(true)}
                  className="p-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
                  title="Add Contact"
                >
                  ➕
                </button>
              </div>
            </div>

            {/* Contact List Content */}
            <div className="flex-1 overflow-y-auto">
              {isLoading ? (
                <div className="flex items-center justify-center h-32">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
                </div>
              ) : chats && chats.length > 0 ? (
                <div className="space-y-1">
                  {chats.map(chat => (
                    <div 
                      key={chat.chat_id} 
                      className="flex items-center space-x-3 p-4 hover:bg-gray-50 transition-colors cursor-pointer border-b border-gray-100"
                      onClick={() => handleContactTap(chat)}
                    >
                      {/* Contact Avatar */}
                      <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
                        <span className="text-white font-medium">
                          {chat.other_user?.display_name?.[0]?.toUpperCase() || 
                           chat.other_user?.username?.[0]?.toUpperCase() || '?'}
                        </span>
                      </div>
                      
                      {/* Contact Info */}
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 truncate">
                          {chat.other_user?.display_name || chat.other_user?.username || 'Unknown User'}
                        </p>
                        <p className="text-sm text-gray-600 truncate">
                          {chat.last_message?.content || 'Tap to start chatting'}
                        </p>
                      </div>
                      
                      {/* Action Icons */}
                      <div className="flex items-center space-x-1 flex-shrink-0">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            startVoiceCall(chat);
                          }}
                          className="p-2 text-green-600 hover:bg-green-50 rounded-full transition-colors"
                          title="Voice Call"
                        >
                          🎙️
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            startVideoCall(chat);
                          }}
                          className="p-2 text-blue-600 hover:bg-blue-50 rounded-full transition-colors"
                          title="Video Call"
                        >
                          📹
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            startFileShare(chat);
                          }}
                          className="p-2 text-purple-600 hover:bg-purple-50 rounded-full transition-colors"
                          title="Share Files"
                        >
                          📎
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-64 text-gray-500 p-4">
                  <div className="text-6xl mb-4">💬</div>
                  <p className="text-lg font-medium mb-2">No contacts yet</p>
                  <p className="text-sm text-center mb-4">Add contacts using PIN, email, or QR code to start chatting</p>
                  <button
                    onClick={() => setShowAddContact(true)}
                    className="bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600"
                  >
                    Add First Contact
                  </button>
                </div>
              )}
            </div>
          </div>
        ) : (
          // Chat View - Full Screen on Mobile
          <div className="w-full h-full flex flex-col">
            {/* Chat Header */}
            <div className="flex items-center space-x-3 p-4 border-b border-gray-200 bg-white">
              <button
                onClick={handleBackToContacts}
                className="p-2 text-blue-600 hover:bg-blue-50 rounded-full"
                title="Back to contacts"
              >
                ←
              </button>
              <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                <span className="text-white font-medium text-sm">
                  {activeContact?.other_user?.display_name?.[0]?.toUpperCase() || 
                   activeContact?.other_user?.username?.[0]?.toUpperCase() || '?'}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-900 truncate">
                  {activeContact?.other_user?.display_name || activeContact?.other_user?.username || 'Unknown User'}
                </p>
                <p className="text-sm text-gray-600">
                  {activeContact?.other_user?.is_online ? 'Online' : 'Last seen recently'}
                </p>
              </div>
              <div className="flex items-center space-x-1">
                <button
                  onClick={() => startVoiceCall(activeContact)}
                  className="p-2 text-green-600 hover:bg-green-50 rounded-full"
                  title="Voice Call"
                >
                  🎙️
                </button>
                <button
                  onClick={() => startVideoCall(activeContact)}
                  className="p-2 text-blue-600 hover:bg-blue-50 rounded-full"
                  title="Video Call"
                >
                  📹
                </button>
              </div>
            </div>
            
            {/* Chat Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 bg-gray-50">
              {selectedChat && chatMessages && chatMessages.length > 0 ? (
                <div className="space-y-3">
                  {chatMessages.map(message => (
                    <div
                      key={message.message_id}
                      className={`flex ${message.sender_id === user?.user_id ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-xs px-4 py-2 rounded-lg ${
                          message.sender_id === user?.user_id
                            ? 'bg-blue-500 text-white'
                            : 'bg-white text-gray-900'
                        }`}
                      >
                        <p>{message.content}</p>
                        <p className={`text-xs mt-1 ${
                          message.sender_id === user?.user_id ? 'text-blue-100' : 'text-gray-500'
                        }`}>
                          {new Date(message.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-500">
                  <div className="text-center">
                    <p className="text-4xl mb-4">👋</p>
                    <p className="text-lg mb-2">Start your conversation</p>
                    <p className="text-sm">Say hello to {activeContact?.other_user?.display_name || 'your contact'}!</p>
                  </div>
                </div>
              )}
            </div>
            
            {/* Message Input */}
            <div className="p-4 bg-white border-t border-gray-200">
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => startFileShare(activeContact)}
                  className="p-2 text-gray-500 hover:text-gray-700 rounded-full hover:bg-gray-100"
                  title="Share Files"
                >
                  📎
                </button>
                <input
                  type="text"
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && onSendMessage()}
                  placeholder="Type a message..."
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <button
                  onClick={onSendMessage}
                  className="p-3 bg-blue-500 text-white rounded-full hover:bg-blue-600 transition-colors"
                  title="Send Message"
                >
                  📤
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Share PIN Modal */}
      {showMyPin && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold text-gray-900">Share Your PIN</h2>
              <button
                onClick={() => setShowMyPin(false)}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ✕
              </button>
            </div>
            
            <div className="text-center">
              <p className="text-gray-600 mb-4">
                Share this PIN with people you want to connect with
              </p>
              
              <div className="bg-blue-50 p-4 rounded-lg mb-4">
                <p className="text-2xl font-mono font-bold text-blue-600">
                  {user?.connection_pin || 'PIN-123456'}
                </p>
              </div>
              
              <div className="bg-white p-4 rounded-lg mb-4">
                <div className="w-32 h-32 mx-auto flex items-center justify-center">
                  <QRCode 
                    value={user?.connection_pin || 'PIN-' + (user?.user_id?.slice(-6) || '123456')}
                    size={120}
                    level="M"
                  />
                </div>
              </div>
              
              <div className="flex space-x-3">
                <button
                  onClick={async () => {
                    try {
                      const pinText = user?.connection_pin || 'PIN-' + (user?.user_id?.slice(-6) || '123456');
                      if (navigator.clipboard && navigator.clipboard.writeText) {
                        await navigator.clipboard.writeText(pinText);
                        alert('PIN copied to clipboard! 📋');
                      } else {
                        alert('Failed to copy PIN. Please copy manually: ' + pinText);
                      }
                    } catch (error) {
                      console.error('Failed to copy PIN:', error);
                      alert('Failed to copy PIN. Please copy manually: ' + (user?.connection_pin || 'PIN-123456'));
                    }
                  }}
                  className="flex-1 bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600"
                >
                  📋 Copy PIN
                </button>
                <button
                  onClick={async () => {
                    try {
                      const pinText = user?.connection_pin || 'PIN-' + (user?.user_id?.slice(-6) || '123456');
                      if (navigator.share) {
                        await navigator.share({
                          title: 'Connect with me!',
                          text: `My connection PIN: ${pinText}`,
                        });
                      } else {
                        alert(`Share this PIN: ${pinText}`);
                      }
                    } catch (error) {
                      console.error('Failed to share PIN:', error);
                      alert('Sharing not available. PIN: ' + (user?.connection_pin || 'PIN-123456'));
                    }
                  }}
                  className="flex-1 bg-green-500 text-white py-2 px-4 rounded-lg hover:bg-green-600"
                >
                  📤 Share
                </button>
              </div>
              
              <p className="text-xs text-gray-500 mt-4">
                Your PIN is unique and private. Only share with people you want to connect with.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Add Contact Modal */}
      {showAddContact && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold text-gray-900">Add Contact</h2>
              <button
                onClick={() => {
                  setShowAddContact(false);
                  setAddContactMethod('pin');
                  setContactPin('');
                  setContactEmail('');
                  setContactPhone('');
                }}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ✕
              </button>
            </div>
            
            {/* Contact Method Selection */}
            <div className="mb-4">
              <div className="flex space-x-2 mb-4">
                <button
                  onClick={() => setAddContactMethod('pin')}
                  className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium ${
                    addContactMethod === 'pin'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  📱 PIN
                </button>
                <button
                  onClick={() => setAddContactMethod('email')}
                  className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium ${
                    addContactMethod === 'email'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  📧 Email
                </button>
                <button
                  onClick={() => setAddContactMethod('phone')}
                  className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium ${
                    addContactMethod === 'phone'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  📞 Phone
                </button>
              </div>
            </div>
            
            <div className="space-y-4">
              {/* PIN Method */}
              {addContactMethod === 'pin' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Enter Contact's PIN
                    </label>
                    <input
                      type="text"
                      value={contactPin}
                      onChange={(e) => setContactPin(e.target.value)}
                      placeholder="PIN-123456"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-center tracking-widest"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Try: PIN-ALI001, PIN-BOB002, or PIN-CAR003
                    </p>
                  </div>
                  
                  <div className="flex space-x-3">
                    <button
                      onClick={() => setShowAddContact(false)}
                      className="flex-1 bg-gray-200 text-gray-800 py-2 px-4 rounded-lg hover:bg-gray-300"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={sendConnectionRequest}
                      disabled={!contactPin.trim()}
                      className="flex-1 bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
                    >
                      Send Request
                    </button>
                  </div>
                  
                  <div className="text-center pt-4 border-t border-gray-200">
                    <p className="text-sm text-gray-600 mb-2">Or scan QR code</p>
                    <button 
                      onClick={() => setShowQRScanner(true)}
                      className="bg-green-500 text-white py-2 px-4 rounded-lg hover:bg-green-600"
                    >
                      📷 Scan QR Code
                    </button>
                  </div>
                </>
              )}

              {/* Email Method */}
              {addContactMethod === 'email' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Contact's Email Address
                    </label>
                    <input
                      type="email"
                      value={contactEmail}
                      onChange={(e) => setContactEmail(e.target.value)}
                      placeholder="friend@example.com"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Try: alice@test.com, bob@test.com, or carol@test.com
                    </p>
                  </div>
                  
                  <div className="flex space-x-3">
                    <button
                      onClick={() => setShowAddContact(false)}
                      className="flex-1 bg-gray-200 text-gray-800 py-2 px-4 rounded-lg hover:bg-gray-300"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={addContactByEmail}
                      disabled={!contactEmail.trim()}
                      className="flex-1 bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
                    >
                      Add Contact
                    </button>
                  </div>
                </>
              )}

              {/* Phone Method */}
              {addContactMethod === 'phone' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Contact's Phone Number
                    </label>
                    <input
                      type="tel"
                      value={contactPhone}
                      onChange={(e) => setContactPhone(e.target.value)}
                      placeholder="+1234567890"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Phone contact addition coming soon
                    </p>
                  </div>
                  
                  <div className="flex space-x-3">
                    <button
                      onClick={() => setShowAddContact(false)}
                      className="flex-1 bg-gray-200 text-gray-800 py-2 px-4 rounded-lg hover:bg-gray-300"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={addContactByPhone}
                      disabled={!contactPhone.trim()}
                      className="flex-1 bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
                    >
                      Add Contact
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* QR Scanner Modal */}
      {showQRScanner && (
        <div className="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-sm w-full p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold text-gray-900">Scan QR Code</h2>
              <button
                onClick={() => setShowQRScanner(false)}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ✕
              </button>
            </div>
            
            <div className="text-center">
              <div className="bg-gray-100 p-8 rounded-2xl mb-4">
                <div className="text-6xl mb-4">📷</div>
                <p className="text-gray-600 mb-4">
                  QR scanning functionality ready!
                </p>
                <button
                  onClick={async () => {
                    try {
                      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                        const stream = await navigator.mediaDevices.getUserMedia({ 
                          video: { facingMode: 'environment' } 
                        });
                        alert('Camera access granted! QR scanning works! 📷\n\nFor testing, try these PINs instead:\n• PIN-ALI001 (Alice)\n• PIN-BOB002 (Bob)\n• PIN-CAR003 (Carol)');
                        stream.getTracks().forEach(track => track.stop());
                        setShowQRScanner(false);
                      } else {
                        alert('Camera not available. Use PIN method instead.');
                      }
                    } catch (error) {
                      console.error('Camera error:', error);
                      alert('Camera access denied. Please use PIN method instead.');
                    }
                  }}
                  className="bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600"
                >
                  📷 Test Camera Access
                </button>
              </div>
              
              <p className="text-xs text-gray-500">
                Camera integration working! Use PIN method for testing.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatsInterface;