import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

const AdvancedMessaging = ({ 
  user, 
  token, 
  api, 
  selectedChat, 
  messages, 
  onSendMessage, 
  onUpdateMessage, 
  onDeleteMessage 
}) => {
  const { t } = useTranslation();
  const [editingMessageId, setEditingMessageId] = useState(null);
  const [editingText, setEditingText] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedMessages, setSelectedMessages] = useState([]);
  const [showMessageActions, setShowMessageActions] = useState(false);
  const [messageToDelete, setMessageToDelete] = useState(null);
  const [disappearingTimer, setDisappearingTimer] = useState(null);

  // Message editing functionality
  const startEditingMessage = (message) => {
    setEditingMessageId(message.id);
    setEditingText(message.content);
  };

  const cancelEditing = () => {
    setEditingMessageId(null);
    setEditingText('');
  };

  const saveEditedMessage = async () => {
    if (!editingText.trim() || !editingMessageId) return;

    try {
      const response = await axios.put(
        `${api}/chats/${selectedChat.chat_id}/messages/${editingMessageId}`,
        { content: editingText.trim() },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      onUpdateMessage(response.data);
      setEditingMessageId(null);
      setEditingText('');
    } catch (error) {
      console.error('Failed to edit message:', error);
    }
  };

  // Message deletion functionality
  const deleteMessage = async (messageId) => {
    try {
      await axios.delete(
        `${api}/chats/${selectedChat.chat_id}/messages/${messageId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      onDeleteMessage(messageId);
      setMessageToDelete(null);
    } catch (error) {
      console.error('Failed to delete message:', error);
    }
  };

  // Message search functionality
  const searchMessages = useCallback(async (query) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    try {
      const response = await axios.get(
        `${api}/chats/${selectedChat.chat_id}/messages/search`,
        {
          params: { query },
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setSearchResults(response.data);
    } catch (error) {
      console.error('Failed to search messages:', error);
    } finally {
      setIsSearching(false);
    }
  }, [api, selectedChat?.chat_id, token]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      searchMessages(searchQuery);
    }, 500);

    return () => clearTimeout(timer);
  }, [searchQuery, searchMessages]);

  // Disappearing messages
  const sendDisappearingMessage = async (content, timer = 60) => {
    try {
      const response = await axios.post(
        `${api}/chats/${selectedChat.chat_id}/messages`,
        {
          content,
          message_type: 'text',
          disappearing_timer: timer
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      onSendMessage(response.data);
    } catch (error) {
      console.error('Failed to send disappearing message:', error);
    }
  };

  // Message forwarding
  const forwardMessage = async (messageId, targetChatId) => {
    try {
      await axios.post(
        `${api}/chats/${targetChatId}/messages/forward`,
        { message_id: messageId },
        { headers: { Authorization: `Bearer ${token}` } }
      );
    } catch (error) {
      console.error('Failed to forward message:', error);
    }
  };

  // Message selection for bulk actions
  const toggleMessageSelection = (messageId) => {
    setSelectedMessages(prev => 
      prev.includes(messageId) 
        ? prev.filter(id => id !== messageId)
        : [...prev, messageId]
    );
  };

  const clearSelection = () => {
    setSelectedMessages([]);
    setShowMessageActions(false);
  };

  // Bulk delete messages
  const bulkDeleteMessages = async () => {
    try {
      await axios.delete(
        `${api}/chats/${selectedChat.chat_id}/messages/bulk`,
        {
          data: { message_ids: selectedMessages },
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      selectedMessages.forEach(messageId => onDeleteMessage(messageId));
      clearSelection();
    } catch (error) {
      console.error('Failed to bulk delete messages:', error);
    }
  };

  // Message context menu
  const MessageContextMenu = ({ message, onClose }) => {
    const isOwnMessage = message.sender_id === user.id;

    return (
      <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
        <div className="py-1">
          <button
            onClick={() => {
              navigator.clipboard.writeText(message.content);
              onClose();
            }}
            className="w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center space-x-2"
            aria-label="Copy message text"
          >
            <span>📋</span>
            <span>Copy</span>
          </button>
          
          {isOwnMessage && (
            <>
              <button
                onClick={() => {
                  startEditingMessage(message);
                  onClose();
                }}
                className="w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center space-x-2"
                aria-label="Edit message"
              >
                <span>✏️</span>
                <span>Edit</span>
              </button>
              
              <button
                onClick={() => {
                  setMessageToDelete(message);
                  onClose();
                }}
                className="w-full px-4 py-2 text-left hover:bg-gray-100 text-red-600 flex items-center space-x-2"
                aria-label="Delete message"
              >
                <span>🗑️</span>
                <span>Delete</span>
              </button>
            </>
          )}
          
          <button
            onClick={() => {
              // Forward message logic
              onClose();
            }}
            className="w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center space-x-2"
            aria-label="Forward message"
          >
            <span>📤</span>
            <span>Forward</span>
          </button>
          
          <button
            onClick={() => {
              toggleMessageSelection(message.id);
              onClose();
            }}
            className="w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center space-x-2"
            aria-label="Select message"
          >
            <span>☑️</span>
            <span>Select</span>
          </button>
        </div>
      </div>
    );
  };

  // Enhanced message component
  const EnhancedMessage = ({ message, onContextMenu }) => {
    const [showContextMenu, setShowContextMenu] = useState(false);
    const [timeLeft, setTimeLeft] = useState(null);
    const isOwnMessage = message.sender_id === user.id;
    const isSelected = selectedMessages.includes(message.id);

    // Handle disappearing message countdown
    useEffect(() => {
      if (message.disappearing_timer) {
        const createdAt = new Date(message.created_at);
        const expiresAt = new Date(createdAt.getTime() + message.disappearing_timer * 1000);
        
        const updateTimer = () => {
          const now = new Date();
          const remaining = Math.max(0, expiresAt - now);
          setTimeLeft(remaining);
          
          if (remaining <= 0) {
            // Message expired, trigger deletion
            onDeleteMessage(message.id);
          }
        };

        updateTimer();
        const interval = setInterval(updateTimer, 1000);
        return () => clearInterval(interval);
      }
    }, [message, onDeleteMessage]);

    const formatTimeLeft = (ms) => {
      const seconds = Math.floor(ms / 1000);
      const minutes = Math.floor(seconds / 60);
      const hours = Math.floor(minutes / 60);
      
      if (hours > 0) return `${hours}h ${minutes % 60}m`;
      if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
      return `${seconds}s`;
    };

    return (
      <div 
        className={`flex mb-4 ${isOwnMessage ? 'justify-end' : 'justify-start'} ${isSelected ? 'bg-blue-50' : ''}`}
        onContextMenu={(e) => {
          e.preventDefault();
          setShowContextMenu(true);
        }}
      >
        <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
          isOwnMessage 
            ? 'bg-blue-500 text-white' 
            : 'bg-gray-200 text-gray-800'
        } relative`}>
          
          {/* Selection checkbox */}
          {selectedMessages.length > 0 && (
            <input
              type="checkbox"
              checked={isSelected}
              onChange={() => toggleMessageSelection(message.id)}
              className="absolute top-1 right-1 w-4 h-4"
              aria-label={`Select message: ${message.content}`}
            />
          )}

          {/* Message content */}
          {editingMessageId === message.id ? (
            <div className="space-y-2">
              <textarea
                value={editingText}
                onChange={(e) => setEditingText(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded resize-none text-black"
                rows={2}
                aria-label="Edit message content"
              />
              <div className="flex space-x-2">
                <button
                  onClick={saveEditedMessage}
                  className="text-xs bg-green-500 text-white px-2 py-1 rounded hover:bg-green-600"
                  aria-label="Save edited message"
                >
                  Save
                </button>
                <button
                  onClick={cancelEditing}
                  className="text-xs bg-gray-500 text-white px-2 py-1 rounded hover:bg-gray-600"
                  aria-label="Cancel editing"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <>
              <p className="text-sm">{message.content}</p>
              
              {/* Message metadata */}
              <div className="flex items-center justify-between mt-1 text-xs opacity-75">
                <span>
                  {new Date(message.created_at).toLocaleTimeString([], { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                  })}
                  {message.edited && (
                    <span className="ml-1 italic" aria-label="Message was edited">
                      (edited)
                    </span>
                  )}
                </span>
                
                {/* Disappearing timer */}
                {timeLeft && (
                  <span className="text-orange-400 flex items-center space-x-1">
                    <span>⏰</span>
                    <span>{formatTimeLeft(timeLeft)}</span>
                  </span>
                )}
              </div>
            </>
          )}

          {/* Context menu */}
          {showContextMenu && (
            <MessageContextMenu 
              message={message} 
              onClose={() => setShowContextMenu(false)} 
            />
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full">
      {/* Search Bar */}
      <div className="p-4 border-b border-gray-200">
        <div className="relative">
          <input
            type="text"
            placeholder={t('messages.searchPlaceholder')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            aria-label="Search messages"
          />
          <div className="absolute left-3 top-2.5 text-gray-400">
            <span aria-hidden="true">🔍</span>
          </div>
          {isSearching && (
            <div className="absolute right-3 top-2.5">
              <div className="animate-spin w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full"></div>
            </div>
          )}
        </div>
      </div>

      {/* Search Results */}
      {searchQuery && searchResults.length > 0 && (
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <h3 className="text-sm font-medium text-gray-700 mb-2">
            {t('messages.searchResults')} ({searchResults.length})
          </h3>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {searchResults.map((result) => (
              <div
                key={result.id}
                className="p-2 bg-white rounded border cursor-pointer hover:bg-gray-100"
                onClick={() => {
                  // Jump to message
                  const messageElement = document.getElementById(`message-${result.id}`);
                  if (messageElement) {
                    messageElement.scrollIntoView({ behavior: 'smooth' });
                  }
                }}
                aria-label={`Jump to message: ${result.content}`}
              >
                <p className="text-sm text-gray-600 truncate">{result.content}</p>
                <p className="text-xs text-gray-400">
                  {new Date(result.created_at).toLocaleString()}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Bulk Actions Bar */}
      {selectedMessages.length > 0 && (
        <div className="p-4 border-b border-gray-200 bg-blue-50">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-blue-700">
              {selectedMessages.length} {t('messages.selected')}
            </span>
            <div className="flex space-x-2">
              <button
                onClick={bulkDeleteMessages}
                className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 text-sm"
                aria-label={`Delete ${selectedMessages.length} selected messages`}
              >
                {t('messages.delete')}
              </button>
              <button
                onClick={clearSelection}
                className="px-3 py-1 bg-gray-500 text-white rounded hover:bg-gray-600 text-sm"
                aria-label="Clear selection"
              >
                {t('common.cancel')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Messages List */}
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map((message) => (
          <EnhancedMessage
            key={message.id}
            message={message}
            onContextMenu={() => {}}
          />
        ))}
      </div>

      {/* Enhanced Message Input */}
      <div className="p-4 border-t border-gray-200 bg-white">
        <div className="flex items-center space-x-2">
          {/* Disappearing Timer Toggle */}
          <button
            onClick={() => setDisappearingTimer(disappearingTimer ? null : 60)}
            className={`p-2 rounded-lg transition-colors ${
              disappearingTimer ? 'bg-orange-500 text-white' : 'bg-gray-200 text-gray-600'
            }`}
            aria-label={`${disappearingTimer ? 'Disable' : 'Enable'} disappearing messages`}
            title={disappearingTimer ? `Messages will disappear after ${disappearingTimer}s` : 'Enable disappearing messages'}
          >
            <span aria-hidden="true">⏰</span>
          </button>
          
          {/* Timer options */}
          {disappearingTimer && (
            <select
              value={disappearingTimer}
              onChange={(e) => setDisappearingTimer(parseInt(e.target.value))}
              className="px-2 py-1 border border-gray-300 rounded text-sm"
              aria-label="Select disappearing timer duration"
            >
              <option value={10}>10s</option>
              <option value={30}>30s</option>
              <option value={60}>1m</option>
              <option value={300}>5m</option>
              <option value={3600}>1h</option>
            </select>
          )}
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {messageToDelete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" role="dialog" aria-modal="true">
          <div className="bg-white rounded-lg p-6 max-w-sm w-full mx-4">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              {t('messages.deleteConfirmation')}
            </h3>
            <p className="text-gray-600 mb-4">
              {t('messages.deleteWarning')}
            </p>
            <div className="flex space-x-3">
              <button
                onClick={() => setMessageToDelete(null)}
                className="flex-1 px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
                aria-label="Cancel message deletion"
              >
                {t('common.cancel')}
              </button>
              <button
                onClick={() => deleteMessage(messageToDelete.id)}
                className="flex-1 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
                aria-label="Confirm message deletion"
              >
                {t('messages.delete')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdvancedMessaging;