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
    if (!contactPin.trim()) return;
    
    try {
      await axios.post(`${api}/connections/request-by-pin`, {
        target_pin: contactPin,
        message: "Hi! I'd like to connect with you."
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setContactPin('');
      setShowAddContact(false);
      alert('Connection request sent! 🎉');
    } catch (error) {
      console.error('Failed to send connection request:', error);
      alert('Failed to send request. Please check the PIN.');
    }
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
                        onClick={() => setShowContactOptions(null)}
                        className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center space-x-2"
                      >
                        <span>📎</span>
                        <span>Share Files</span>
                      </button>
                      <button
                        onClick={() => setShowContactOptions(null)}
                        className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center space-x-2"
                      >
                        <span>🎙️</span>
                        <span>Voice Call</span>
                      </button>
                      <button
                        onClick={() => setShowContactOptions(null)}
                        className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center space-x-2"
                      >
                        <span>📹</span>
                        <span>Video Call</span>
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
              <div className="bg-gray-100 p-8 rounded-2xl mb-4">
                <div className="text-6xl mb-4">📷</div>
                <p className="text-gray-600 mb-4">
                  Camera access is required to scan QR codes
                </p>
                <button
                  onClick={() => {
                    // Try to access camera
                    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                      navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
                        .then(stream => {
                          alert('Camera access granted! QR scanning will be implemented soon. 📷');
                          stream.getTracks().forEach(track => track.stop());
                          setShowQRScanner(false);
                        })
                        .catch(error => {
                          console.error('Camera access error:', error);
                          alert('Camera access denied. Please enable camera permissions and try again.');
                        });
                    } else {
                      alert('Camera not supported on this device/browser.');
                    }
                  }}
                  className="bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600"
                >
                  📷 Enable Camera
                </button>
              </div>
              
              <p className="text-xs text-gray-500">
                Point your camera at a QR code to scan
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatsInterface;