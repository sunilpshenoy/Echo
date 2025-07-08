import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const ChannelsInterface = ({ team, user, token, api, onChannelSelect }) => {
  const [channels, setChannels] = useState([]);
  const [selectedChannel, setSelectedChannel] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [showCreateChannel, setShowCreateChannel] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Fetch team channels
  const fetchChannels = useCallback(async () => {
    if (!team?.team_id || !token || !api) return;
    
    try {
      const response = await axios.get(`${api}/teams/${team.team_id}/channels`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setChannels(response.data);
      
      // Auto-select first channel if none selected
      if (response.data.length > 0 && !selectedChannel) {
        setSelectedChannel(response.data[0]);
      }
    } catch (error) {
      console.error('Failed to fetch channels:', error);
    }
  }, [team?.team_id, token, api, selectedChannel]);

  // Fetch channel messages
  const fetchMessages = useCallback(async (channelId) => {
    if (!channelId || !token || !api) return;
    
    setIsLoading(true);
    try {
      const response = await axios.get(`${api}/channels/${channelId}/messages`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMessages(response.data);
    } catch (error) {
      console.error('Failed to fetch messages:', error);
    } finally {
      setIsLoading(false);
    }
  }, [token, api]);

  // Send message to channel
  const sendMessage = async () => {
    if (!newMessage.trim() || !selectedChannel || !token || !api) return;
    
    try {
      const response = await axios.post(
        `${api}/channels/${selectedChannel.channel_id}/messages`,
        { content: newMessage.trim() },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setMessages(prev => [...prev, response.data]);
      setNewMessage('');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  // Create new channel
  const createChannel = async (channelData) => {
    if (!team?.team_id || !token || !api) return;
    
    try {
      const response = await axios.post(
        `${api}/teams/${team.team_id}/channels`,
        channelData,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setChannels(prev => [...prev, response.data]);
      setShowCreateChannel(false);
      setSelectedChannel(response.data);
    } catch (error) {
      console.error('Failed to create channel:', error);
    }
  };

  useEffect(() => {
    fetchChannels();
  }, [fetchChannels]);

  useEffect(() => {
    if (selectedChannel) {
      fetchMessages(selectedChannel.channel_id);
      if (onChannelSelect) {
        onChannelSelect(selectedChannel);
      }
    }
  }, [selectedChannel, fetchMessages, onChannelSelect]);

  const CreateChannelModal = () => {
    const [channelName, setChannelName] = useState('');
    const [channelDescription, setChannelDescription] = useState('');
    const [channelType, setChannelType] = useState('general');
    const [isPrivate, setIsPrivate] = useState(false);

    const handleSubmit = (e) => {
      e.preventDefault();
      if (!channelName.trim()) return;
      
      createChannel({
        name: channelName.trim(),
        description: channelDescription.trim(),
        type: channelType,
        is_private: isPrivate
      });
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-md">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Create New Channel</h3>
            <button
              onClick={() => setShowCreateChannel(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Channel Name
              </label>
              <input
                type="text"
                value={channelName}
                onChange={(e) => setChannelName(e.target.value)}
                placeholder="general, announcements, etc."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={channelDescription}
                onChange={(e) => setChannelDescription(e.target.value)}
                placeholder="What's this channel about?"
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Channel Type
              </label>
              <select
                value={channelType}
                onChange={(e) => setChannelType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="general">General Discussion</option>
                <option value="announcements">Announcements</option>
                <option value="activities">Activities</option>
                <option value="social">Social</option>
                <option value="help">Help & Support</option>
              </select>
            </div>
            
            <div className="flex items-center">
              <input
                type="checkbox"
                id="isPrivate"
                checked={isPrivate}
                onChange={(e) => setIsPrivate(e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="isPrivate" className="ml-2 text-sm text-gray-700">
                Make this channel private
              </label>
            </div>
            
            <div className="flex space-x-3 pt-4">
              <button
                type="button"
                onClick={() => setShowCreateChannel(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Create Channel
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  const ChannelIcon = ({ type, isPrivate }) => {
    if (isPrivate) return '🔒';
    switch (type) {
      case 'announcements': return '📢';
      case 'activities': return '📅';
      case 'social': return '💬';
      case 'help': return '❓';
      default: return '#';
    }
  };

  return (
    <div className="flex h-full">
      {/* Channels Sidebar */}
      <div className="w-64 bg-gray-50 border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">{team?.name}</h2>
            <button
              onClick={() => setShowCreateChannel(true)}
              className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm hover:bg-blue-600"
              title="Create Channel"
            >
              +
            </button>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            {channels.length} channel{channels.length !== 1 ? 's' : ''}
          </p>
        </div>
        
        <div className="flex-1 overflow-y-auto">
          <div className="p-2">
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 px-2">
              Channels
            </div>
            {channels.map(channel => (
              <button
                key={channel.channel_id}
                onClick={() => setSelectedChannel(channel)}
                className={`w-full text-left px-2 py-2 rounded-lg mb-1 transition-colors ${
                  selectedChannel?.channel_id === channel.channel_id
                    ? 'bg-blue-100 text-blue-900'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <span className="text-sm">
                    <ChannelIcon type={channel.type} isPrivate={channel.is_private} />
                  </span>
                  <span className="truncate text-sm font-medium">{channel.name}</span>
                  {channel.unread_count > 0 && (
                    <span className="bg-red-500 text-white text-xs rounded-full px-1 min-w-[16px] h-4 flex items-center justify-center">
                      {channel.unread_count}
                    </span>
                  )}
                </div>
                {channel.description && (
                  <p className="text-xs text-gray-500 truncate mt-1 ml-6">
                    {channel.description}
                  </p>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>
      
      {/* Messages Area */}
      <div className="flex-1 flex flex-col">
        {selectedChannel ? (
          <>
            {/* Channel Header */}
            <div className="px-6 py-4 border-b border-gray-200 bg-white">
              <div className="flex items-center space-x-3">
                <span className="text-lg">
                  <ChannelIcon type={selectedChannel.type} isPrivate={selectedChannel.is_private} />
                </span>
                <div>
                  <h3 className="font-semibold text-gray-900">{selectedChannel.name}</h3>
                  {selectedChannel.description && (
                    <p className="text-sm text-gray-500">{selectedChannel.description}</p>
                  )}
                </div>
              </div>
              <div className="mt-2 flex items-center space-x-4 text-sm text-gray-500">
                <span>{selectedChannel.member_count} members</span>
                <span>•</span>
                <span>Created by {selectedChannel.created_by}</span>
              </div>
            </div>
            
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {isLoading ? (
                <div className="flex items-center justify-center h-32">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                </div>
              ) : messages.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-4xl mb-2">💬</div>
                  <h3 className="font-semibold text-gray-900 mb-1">Start the conversation</h3>
                  <p className="text-gray-500 text-sm">
                    Be the first to send a message in #{selectedChannel.name}
                  </p>
                </div>
              ) : (
                messages.map(message => (
                  <div key={message.message_id} className="flex space-x-3">
                    <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center text-sm">
                      {message.sender_name?.charAt(0)?.toUpperCase() || '?'}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="font-medium text-gray-900 text-sm">
                          {message.sender_name || 'Unknown'}
                        </span>
                        <span className="text-xs text-gray-500">
                          {new Date(message.created_at).toLocaleTimeString()}
                        </span>
                      </div>
                      <p className="text-gray-700 text-sm">{message.content}</p>
                    </div>
                  </div>
                ))
              )}
            </div>
            
            {/* Message Input */}
            <div className="p-4 border-t border-gray-200 bg-white">
              <div className="flex items-center space-x-3">
                <input
                  type="text"
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                  placeholder={`Message #${selectedChannel.name}`}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={sendMessage}
                  disabled={!newMessage.trim()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Send
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <div className="text-4xl mb-4">📢</div>
              <h3 className="font-semibold text-gray-900 mb-2">Select a Channel</h3>
              <p className="text-gray-500">Choose a channel from the sidebar to start chatting</p>
            </div>
          </div>
        )}
      </div>
      
      {showCreateChannel && <CreateChannelModal />}
    </div>
  );
};

export default ChannelsInterface;