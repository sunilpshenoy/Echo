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
  const [showContactOptions, setShowContactOptions] = useState(null);
  const [showQRScanner, setShowQRScanner] = useState(false);
  const [contactEmail, setContactEmail] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [addContactMethod, setAddContactMethod] = useState('pin'); // 'pin', 'email', 'phone'

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

  // Add contact by phone (placeholder - would need phone lookup)
  const addContactByPhone = async () => {
    if (!contactPhone.trim()) return;
    
    try {
      // For now, show placeholder message
      alert('Phone contact addition will be implemented soon! 📱');
      setContactPhone('');
      setShowAddContact(false);
    } catch (error) {
      console.error('Failed to add contact:', error);
      alert('Failed to add contact. Please try again.');
    }
  };

  // Handle QR code scan result
  const handleQRScan = (result) => {
    if (result) {
      setContactPin(result);
      setShowQRScanner(false);
      sendConnectionRequest();
    }
  };

  // Handle QR scan error
  const handleQRError = (error) => {
    console.error('QR Scan Error:', error);
    alert('Camera access denied or QR scan failed. Please enter PIN manually.');
    setShowQRScanner(false);
  };

  // Delete contact function
  const deleteContact = async (chat) => {
    if (!window.confirm(`Are you sure you want to delete ${chat.other_user?.display_name || chat.other_user?.username || 'this contact'}? This will also delete your chat history.`)) {
      return;
    }
    
    try {
      // Find the contact by user ID (since we don't have contact_id in chat object)
      const contactsResponse = await axios.get(`${api}/contacts`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const contact = contactsResponse.data.find(c => c.contact_user_id === chat.other_user?.user_id);
      
      if (contact) {
        await axios.delete(`${api}/contacts/${contact.contact_id}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        alert('Contact deleted successfully! 🗑️');
        setShowContactOptions(null);
        
        // Refresh page to update contact list
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      } else {
        alert('Contact not found');
      }
    } catch (error) {
      console.error('Failed to delete contact:', error);
      alert('Failed to delete contact. Please try again.');
    }
  };

  // Voice call function
  const startVoiceCall = async (chat) => {
    setShowContactOptions(null);
    
    try {
      console.log('Starting voice call with:', chat.other_user?.display_name);
      
      // Initiate call in backend
      const response = await axios.post(`${api}/calls/initiate`, {
        chat_id: chat.chat_id,
        call_type: 'voice'
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const callData = response.data;
      console.log('Call initiated:', callData);
      
      // Open simple call modal
      openCallModal(chat, 'voice', callData);
      
    } catch (error) {
      console.error('Failed to start voice call:', error);
      alert('Failed to start voice call. Please try again.');
    }
  };

  // Video call function
  const startVideoCall = async (chat) => {
    setShowContactOptions(null);
    
    try {
      console.log('Starting video call with:', chat.other_user?.display_name);
      
      // Initiate call in backend
      const response = await axios.post(`${api}/calls/initiate`, {
        chat_id: chat.chat_id,
        call_type: 'video'
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const callData = response.data;
      console.log('Call initiated:', callData);
      
      // Open simple call modal
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
          let peerConnection = null;
          let isMuted = false;
          let isVideoEnabled = ${callType === 'video'};
          
          // Initialize call
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
              
              // In a real implementation, this would establish WebRTC connection
              // For now, we simulate a successful connection
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
          
          // Initialize when page loads
          window.onload = initializeCall;
          
          // Cleanup when window closes
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
    setShowContactOptions(null);
    
    // Create file input element
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = 'image/*,video/*,audio/*,.pdf,.doc,.docx,.txt,.zip';
    fileInput.multiple = true;
    
    fileInput.onchange = async (event) => {
      const files = Array.from(event.target.files);
      if (files.length === 0) return;
      
      try {
        console.log('Selected files:', files);
        
        // Show upload progress
        const uploadWindow = window.open(
          '', 
          'file_upload',
          'width=450,height=300,resizable=yes,scrollbars=no'
        );
        
        uploadWindow.document.write(`
          <!DOCTYPE html>
          <html>
          <head>
            <title>📎 Sharing Files</title>
            <style>
              body { 
                font-family: Arial, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: #f8fafc;
              }
              .container { max-width: 400px; margin: 0 auto; }
              .file-item { 
                background: white; 
                border: 1px solid #e2e8f0; 
                border-radius: 8px; 
                padding: 12px; 
                margin: 8px 0;
              }
              .progress-bar { 
                width: 100%; 
                height: 8px; 
                background: #e2e8f0; 
                border-radius: 4px; 
                overflow: hidden;
              }
              .progress-fill { 
                height: 100%; 
                background: #3b82f6; 
                transition: width 0.3s;
              }
              .status { margin: 8px 0; font-size: 14px; }
              button { 
                background: #10b981; 
                color: white; 
                border: none; 
                padding: 8px 16px; 
                border-radius: 4px; 
                cursor: pointer; 
                margin-top: 16px;
              }
            </style>
          </head>
          <body>
            <div class="container">
              <h3>📎 Sharing with ${chat.other_user?.display_name || 'Contact'}</h3>
              <div id="fileList"></div>
              <button onclick="window.close()">Close</button>
            </div>
          </body>
          </html>
        `);
        
        const fileListDiv = uploadWindow.document.getElementById('fileList');
        
        for (const file of files) {
          // Create file item UI
          const fileDiv = uploadWindow.document.createElement('div');
          fileDiv.className = 'file-item';
          fileDiv.innerHTML = `
            <div><strong>${file.name}</strong> (${(file.size / 1024 / 1024).toFixed(2)} MB)</div>
            <div class="status">Preparing...</div>
            <div class="progress-bar">
              <div class="progress-fill" style="width: 0%"></div>
            </div>
          `;
          fileListDiv.appendChild(fileDiv);
          
          // Simulate file upload (in real implementation, use FormData)
          const progressFill = fileDiv.querySelector('.progress-fill');
          const statusDiv = fileDiv.querySelector('.status');
          
          // Convert file to base64 for storage (simple implementation)
          const reader = new FileReader();
          reader.onload = async function(e) {
            try {
              const fileData = {
                filename: file.name,
                size: file.size,
                type: file.type,
                data: e.target.result, // base64 data
                chat_id: chat.chat_id
              };
              
              // Simulate upload progress
              for (let i = 0; i <= 100; i += 10) {
                progressFill.style.width = i + '%';
                statusDiv.textContent = `Uploading... ${i}%`;
                await new Promise(resolve => setTimeout(resolve, 100));
              }
              
              // Send file data to backend
              await axios.post(`${api}/chats/${chat.chat_id}/files`, fileData, {
                headers: { Authorization: `Bearer ${token}` }
              });
              
              statusDiv.textContent = '✅ Sent successfully!';
              statusDiv.style.color = '#10b981';
              
            } catch (error) {
              console.error('File upload failed:', error);
              statusDiv.textContent = '❌ Upload failed';
              statusDiv.style.color = '#ef4444';
            }
          };
          
          reader.readAsDataURL(file);
        }
        
        uploadWindow.document.close();
        
      } catch (error) {
        console.error('File sharing failed:', error);
        alert('Failed to share files. Please try again.');
      }
    };
    
    // Trigger file selection
    fileInput.click();
  };

  // Fetch pending connection requests
  const fetchConnectionRequests = async () => {
    try {
      const response = await axios.get(`${api}/connections/requests`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setContactRequests(response.data);
    } catch (error) {
      console.error('Failed to fetch connection requests:', error);
    }
  };

  // Handle connection request response
  const handleConnectionRequest = async (requestId, action) => {
    try {
      await axios.put(`${api}/connections/requests/${requestId}`, {
        action: action
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      fetchConnectionRequests();
      alert(`Connection request ${action}ed! ${action === 'accept' ? '🎉' : '👋'}`);
    } catch (error) {
      console.error(`Failed to ${action} connection request:`, error);
    }
  };

  useEffect(() => {
    fetchConnectionRequests();
  }, []);

  return (
    <div className="flex w-full h-full">
      {/* Chat List Sidebar */}
      <div className="w-1/3 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Chats</h2>
              <p className="text-sm text-gray-600">Your connections</p>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setShowMyPin(true)}
                className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                title="My PIN & QR Code"
              >
                📱
              </button>
              <button
                onClick={() => setShowAddContact(true)}
                className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                title="Add Contact"
              >
                ➕
              </button>
            </div>
          </div>

          {/* Connection Requests */}
          {contactRequests && contactRequests.length > 0 && (
            <div className="mb-4">
              <h3 className="text-sm font-medium text-gray-900 mb-2">
                Connection Requests ({contactRequests.length})
              </h3>
              <div className="space-y-2">
                {contactRequests.map(request => (
                  <div key={request.request_id} className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                          <span className="text-yellow-700 text-sm font-medium">
                            {request.sender?.display_name?.[0] || request.sender?.username?.[0] || '?'}
                          </span>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            {request.sender?.display_name || request.sender?.username}
                          </p>
                          <p className="text-xs text-gray-600">{request.message}</p>
                        </div>
                      </div>
                      <div className="flex space-x-1">
                        <button
                          onClick={() => handleConnectionRequest(request.request_id, 'accept')}
                          className="bg-green-500 text-white px-2 py-1 rounded text-xs hover:bg-green-600"
                        >
                          ✓
                        </button>
                        <button
                          onClick={() => handleConnectionRequest(request.request_id, 'decline')}
                          className="bg-red-500 text-white px-2 py-1 rounded text-xs hover:bg-red-600"
                        >
                          ✕
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
        
        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
            </div>
          ) : chats && chats.length > 0 ? (
            <div className="space-y-1 p-2">
              {chats.map(chat => (
                <div key={chat.chat_id} className="relative">
                  <button
                    onClick={() => onSelectChat(chat)}
                    className={`w-full p-3 rounded-lg text-left hover:bg-gray-50 transition-colors ${
                      selectedChat?.chat_id === chat.chat_id ? 'bg-blue-50 border border-blue-200' : ''
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                        <span className="text-white font-medium text-sm">
                          {chat.other_user?.display_name?.[0]?.toUpperCase() || 
                           chat.other_user?.username?.[0]?.toUpperCase() || '?'}
                        </span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <p className="font-medium text-gray-900 truncate">
                            {chat.other_user?.display_name || chat.other_user?.username || 'Unknown User'}
                          </p>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setShowContactOptions(showContactOptions === chat.chat_id ? null : chat.chat_id);
                            }}
                            className="p-1 text-gray-400 hover:text-gray-600"
                          >
                            ⋯
                          </button>
                        </div>
                        <p className="text-sm text-gray-600 truncate">
                          {chat.last_message?.content || 'No messages yet'}
                        </p>
                        <div className="flex items-center justify-between mt-1">
                          <span className="text-xs text-gray-500">
                            {chat.last_message?.timestamp && 
                              new Date(chat.last_message.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
                            }
                          </span>
                          <div className="flex items-center space-x-1">
                            {chat.other_user?.is_online && (
                              <span className="w-2 h-2 bg-green-400 rounded-full"></span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </button>

                  {/* Contact Options Dropdown */}
                  {showContactOptions === chat.chat_id && (
                    <div className="absolute right-2 top-12 bg-white border border-gray-200 rounded-lg shadow-lg z-10 w-48">
                      <button
                        onClick={() => {
                          onSelectChat(chat);
                          setShowContactOptions(null);
                        }}
                        className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center space-x-2"
                      >
                        <span>💬</span>
                        <span>Chat</span>
                      </button>
                      <button
                        onClick={() => startFileShare(chat)}
                        className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center space-x-2"
                      >
                        <span>📎</span>
                        <span>Share Files</span>
                      </button>
                      <button
                        onClick={() => startVoiceCall(chat)}
                        className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center space-x-2"
                      >
                        <span>🎙️</span>
                        <span>Voice Call</span>
                      </button>
                      <button
                        onClick={() => startVideoCall(chat)}
                        className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center space-x-2"
                      >
                        <span>📹</span>
                        <span>Video Call</span>
                      </button>
                      <button
                        onClick={() => deleteContact(chat)}
                        className="w-full px-4 py-2 text-left hover:bg-red-50 text-red-600 flex items-center space-x-2 border-t border-gray-200"
                      >
                        <span>🗑️</span>
                        <span>Delete Contact</span>
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-64 text-center p-4">
              <div className="text-6xl mb-4">💬</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No chats yet</h3>
              <p className="text-gray-600 text-sm mb-4">
                Add contacts using PIN or QR code to start chatting
              </p>
              <button
                onClick={() => setShowAddContact(true)}
                className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600"
              >
                Add First Contact
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Chat Messages Area */}
      <div className="flex-1 flex flex-col">
        {selectedChat ? (
          <>
            {/* Chat Header */}
            <div className="bg-white p-4 border-b border-gray-200">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                  <span className="text-white font-medium">
                    {selectedChat.other_user?.display_name?.[0]?.toUpperCase() || 
                     selectedChat.other_user?.username?.[0]?.toUpperCase() || '?'}
                  </span>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">
                    {selectedChat.other_user?.display_name || selectedChat.other_user?.username || 'Unknown User'}
                  </h3>
                  <p className="text-sm text-gray-600">
                    {selectedChat.other_user?.is_online ? (
                      <span className="flex items-center">
                        <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                        Online
                      </span>
                    ) : (
                      `Last seen ${selectedChat.other_user?.last_seen ? 
                        new Date(selectedChat.other_user.last_seen).toLocaleDateString() : 'recently'}`
                    )}
                  </p>
                </div>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 bg-gray-50">
              {chatMessages && chatMessages.length > 0 ? (
                <div className="space-y-4">
                  {chatMessages.map((message, index) => (
                    <div
                      key={message.message_id || index}
                      className={`flex ${message.sender_id === user.user_id ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-xs lg:max-w-md px-4 py-2 rounded-2xl ${
                          message.sender_id === user.user_id
                            ? 'bg-blue-500 text-white'
                            : 'bg-white text-gray-900 border'
                        }`}
                      >
                        <p className="text-sm">{message.content}</p>
                        <p className={`text-xs mt-1 ${
                          message.sender_id === user.user_id ? 'text-blue-100' : 'text-gray-500'
                        }`}>
                          {new Date(message.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="text-4xl mb-2">👋</div>
                    <p className="text-gray-600">Start your conversation!</p>
                  </div>
                </div>
              )}
            </div>

            {/* Message Input */}
            <div className="bg-white p-4 border-t border-gray-200">
              <div className="flex items-center space-x-3">
                <input
                  type="text"
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && onSendMessage()}
                  placeholder="Type a message..."
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <button
                  onClick={onSendMessage}
                  disabled={!newMessage.trim()}
                  className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors ${
                    newMessage.trim()
                      ? 'bg-blue-500 hover:bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  }`}
                >
                  ➤
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center h-full bg-gray-50">
            <div className="text-center">
              <div className="text-6xl mb-4">💬</div>
              <h3 className="text-xl font-medium text-gray-900 mb-2">
                Select a chat to start messaging
              </h3>
              <p className="text-gray-600">
                Choose a conversation from the sidebar to begin
              </p>
            </div>
          </div>
        )}
      </div>

      {/* My PIN & QR Code Modal */}
      {showMyPin && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold text-gray-900">My Connection PIN</h2>
              <button
                onClick={() => setShowMyPin(false)}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ✕
              </button>
            </div>
            
            <div className="text-center">
              <div className="bg-gray-100 p-6 rounded-2xl mb-6">
                <div className="text-3xl font-mono font-bold text-blue-600 tracking-widest mb-4">
                  {user?.connection_pin || 'PIN-' + (user?.user_id?.slice(-6) || '123456')}
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
                <p className="text-sm text-gray-600">
                  Share this PIN or QR code for others to connect with you
                </p>
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
                        // Fallback for older browsers
                        const textArea = document.createElement('textarea');
                        textArea.value = pinText;
                        document.body.appendChild(textArea);
                        textArea.select();
                        document.execCommand('copy');
                        document.body.removeChild(textArea);
                        alert('PIN copied to clipboard! 📋');
                      }
                    } catch (error) {
                      console.error('Failed to copy PIN:', error);
                      alert('Failed to copy PIN. Please copy manually: ' + (user?.connection_pin || 'PIN-' + (user?.user_id?.slice(-6) || '123456')));
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
                        // Fallback for browsers without native sharing
                        if (navigator.clipboard && navigator.clipboard.writeText) {
                          await navigator.clipboard.writeText(`My connection PIN: ${pinText}`);
                          alert('PIN copied to clipboard for sharing! 📤');
                        } else {
                          alert(`Share this PIN: ${pinText}`);
                        }
                      }
                    } catch (error) {
                      console.error('Failed to share PIN:', error);
                      alert('Sharing not available. PIN: ' + (user?.connection_pin || 'PIN-' + (user?.user_id?.slice(-6) || '123456')));
                    }
                  }}
                  className="flex-1 bg-green-500 text-white py-2 px-4 rounded-lg hover:bg-green-600"
                >
                  📤 Share
                </button>
              </div>
              
              <p className="text-xs text-gray-500 mt-4">
                💡 Your PIN is unique and private. Only share with people you want to connect with.
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
                      Enter the PIN they shared with you
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
                      Enter their registered email address
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
                      Enter their registered phone number
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
              <div className="bg-gray-900 rounded-2xl mb-4 relative overflow-hidden">
                <video
                  id="qr-video"
                  className="w-full h-64 object-cover"
                  autoPlay
                  playsInline
                ></video>
                <div className="absolute inset-0 border-2 border-blue-500 rounded-2xl pointer-events-none">
                  <div className="absolute top-4 left-4 w-6 h-6 border-l-4 border-t-4 border-blue-500"></div>
                  <div className="absolute top-4 right-4 w-6 h-6 border-r-4 border-t-4 border-blue-500"></div>
                  <div className="absolute bottom-4 left-4 w-6 h-6 border-l-4 border-b-4 border-blue-500"></div>
                  <div className="absolute bottom-4 right-4 w-6 h-6 border-r-4 border-b-4 border-blue-500"></div>
                </div>
              </div>
              
              <div className="space-y-3">
                <button
                  onClick={async () => {
                    try {
                      const QrScanner = (await import('qr-scanner')).default;
                      const video = document.getElementById('qr-video');
                      
                      const qrScanner = new QrScanner(
                        video,
                        (result) => {
                          console.log('QR Code scanned:', result.data);
                          
                          // Check if it's a PIN format
                          if (result.data.startsWith('PIN-') || result.data.includes('PIN')) {
                            setContactPin(result.data);
                            setShowQRScanner(false);
                            
                            // Auto-send connection request
                            setTimeout(() => {
                              sendConnectionRequest();
                            }, 500);
                            
                            alert(`QR Code scanned! 📱\nPIN: ${result.data}\nSending connection request...`);
                          } else {
                            alert(`QR Code scanned: ${result.data}\n\nThis doesn't appear to be a contact PIN. Please scan a contact's QR code.`);
                          }
                        },
                        {
                          returnDetailedScanResult: true,
                          highlightScanRegion: true,
                          highlightCodeOutline: true,
                        }
                      );
                      
                      await qrScanner.start();
                      document.getElementById('scan-status').textContent = '📷 Camera active - Point at QR code';
                      
                      // Store scanner reference for cleanup
                      window.currentQrScanner = qrScanner;
                      
                    } catch (error) {
                      console.error('QR Scanner error:', error);
                      document.getElementById('scan-status').textContent = '❌ Camera access failed';
                      alert('Camera access denied or QR scanner failed to start.\\n\\nPlease:\\n1. Enable camera permissions\\n2. Try again\\n3. Use PIN method instead');
                    }
                  }}
                  className="w-full bg-blue-500 text-white py-3 px-4 rounded-lg hover:bg-blue-600"
                >
                  📷 Start Camera Scanning
                </button>
                
                <button
                  onClick={() => {
                    // Stop scanner if running
                    if (window.currentQrScanner) {
                      window.currentQrScanner.stop();
                      window.currentQrScanner = null;
                    }
                    setShowQRScanner(false);
                  }}
                  className="w-full bg-gray-200 text-gray-800 py-2 px-4 rounded-lg hover:bg-gray-300"
                >
                  Cancel
                </button>
              </div>
              
              <p className="text-xs text-gray-500 mt-4" id="scan-status">
                Click "Start Camera Scanning" to begin
              </p>
              
              <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                <p className="text-xs text-blue-700">
                  💡 <strong>Tip:</strong> Ask your contact to show their PIN QR code from their Chats tab
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatsInterface;