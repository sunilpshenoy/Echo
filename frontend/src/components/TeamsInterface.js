import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import ChannelsInterface from './ChannelsInterface';

const TeamsInterface = ({ 
  user, 
  token, 
  api, 
  teams, 
  selectedTeam, 
  isLoading,
  onTeamSelect,
  onTeamsRefresh
}) => {
  const { t } = useTranslation();
  const [showCreateTeam, setShowCreateTeam] = useState(false);
  const [newTeamName, setNewTeamName] = useState('');
  const [newTeamDescription, setNewTeamDescription] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  
  // Team chat functionality
  const [teamMessages, setTeamMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isSendingMessage, setIsSendingMessage] = useState(false);
  
  // WebSocket functionality
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [typingUsers, setTypingUsers] = useState({});
  const [isTyping, setIsTyping] = useState(false);
  const typingTimeoutRef = useRef(null);
  const messagesEndRef = useRef(null);

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
        console.log('WebSocket connected for Teams');
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
    console.log('Received WebSocket message in Teams:', message);
    
    switch (message.type) {
      case 'new_message':
        // Real-time message received - refresh messages if it's for current team
        if (selectedTeam && message.data.team_id === selectedTeam.team_id) {
          fetchTeamMessages();
        }
        break;
        
      case 'typing':
        if (selectedTeam && message.data.team_id === selectedTeam.team_id) {
          setTypingUsers(prev => ({
            ...prev,
            [selectedTeam.team_id]: message.data.typing_users || []
          }));
        }
        break;
        
      default:
        console.log('Unknown message type:', message.type);
    }
  };

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom();
  }, [teamMessages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Typing indicator functionality
  const handleTyping = () => {
    if (!socket || !selectedTeam) return;
    
    if (!isTyping) {
      setIsTyping(true);
      socket.send(JSON.stringify({
        type: 'typing',
        team_id: selectedTeam.team_id,
        is_typing: true
      }));
    }
    
    // Clear existing timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
    
    // Set new timeout to stop typing indicator
    typingTimeoutRef.current = setTimeout(() => {
      if (socket && selectedTeam) {
        socket.send(JSON.stringify({
          type: 'typing',
          team_id: selectedTeam.team_id,
          is_typing: false
        }));
      }
      setIsTyping(false);
    }, 2000);
  };

  // Fetch team messages when a team is selected
  useEffect(() => {
    if (selectedTeam?.team_id) {
      fetchTeamMessages();
    }
  }, [selectedTeam]);

  const fetchTeamMessages = async () => {
    if (!selectedTeam?.team_id) return;
    
    setIsLoadingMessages(true);
    try {
      const response = await axios.get(`${api}/teams/${selectedTeam.team_id}/messages`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTeamMessages(response.data);
    } catch (error) {
      console.error('Failed to fetch team messages:', error);
      // If endpoint doesn't exist, start with empty messages
      setTeamMessages([]);
    } finally {
      setIsLoadingMessages(false);
    }
  };

  const sendTeamMessage = async () => {
    if (!newMessage.trim() || !selectedTeam?.team_id || isSendingMessage) return;
    
    setIsSendingMessage(true);
    try {
      const response = await axios.post(`${api}/teams/${selectedTeam.team_id}/messages`, {
        content: newMessage,
        message_type: 'text'
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setNewMessage('');
      // The message will be added via WebSocket or we'll refresh
      await fetchTeamMessages();
      
    } catch (error) {
      console.error('Failed to send team message:', error);
      
      // If API doesn't exist yet, add message locally for demo
      const messageData = {
        message_id: Date.now(),
        content: newMessage,
        sender: user,
        timestamp: new Date().toISOString(),
        message_type: 'text'
      };
      
      setTeamMessages(prev => [...prev, messageData]);
      setNewMessage('');
    } finally {
      setIsSendingMessage(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendTeamMessage();
    } else {
      handleTyping();
    }
  };

  const handleCreateTeam = async () => {
    if (!newTeamName.trim()) return;
    
    setIsCreating(true);
    try {
      console.log('Creating team:', { name: newTeamName, description: newTeamDescription });
      
      // Call backend to create team
      const response = await axios.post(`${api}/teams`, {
        name: newTeamName,
        description: newTeamDescription,
        type: 'group'
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      alert(t('teams.teamCreatedSuccess'));
      console.log('Team created:', response.data);
      
      setNewTeamName('');
      setNewTeamDescription('');
      setShowCreateTeam(false);
      
      // Refresh teams list
      if (onTeamsRefresh) {
        onTeamsRefresh();
      }
      
    } catch (error) {
      console.error('Failed to create team:', error);
      const errorMessage = error.response?.data?.detail || t('teams.teamCreationFailed');
      alert(errorMessage);
    } finally {
      setIsCreating(false);
    }
  };

  const handleTeamClick = (team) => {
    if (onTeamSelect) {
      onTeamSelect(team);
    }
  };

  // For mobile, show single column layout
  if (selectedTeam) {
    return (
      <div className="flex-1 flex flex-col bg-white">
        {/* Team Header */}
        <div className="bg-white p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <button
              onClick={() => onTeamSelect ? onTeamSelect(null) : null}
              className="text-blue-500 hover:text-blue-700 text-sm font-medium"
            >
              ← {t('teams.backToTeams')}
            </button>
            <div className="flex items-center space-x-2">
              <button className="p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100">
                ⚙️
              </button>
              <button className="p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100">
                📞
              </button>
              <button className="p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100">
                📹
              </button>
            </div>
          </div>
          <div className="flex items-center space-x-3 mt-3">
            <div className="w-12 h-12 bg-purple-500 rounded-lg flex items-center justify-center">
              <span className="text-white font-medium text-lg">
                {selectedTeam.name?.[0]?.toUpperCase() || 'T'}
              </span>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                {selectedTeam.name || t('teams.unnamedTeam')}
              </h3>
              <p className="text-sm text-gray-600">
                {selectedTeam.member_count || selectedTeam.members?.length || 0} {t('teams.members')} • {selectedTeam.type || 'General'}
              </p>
            </div>
          </div>
        </div>

        {/* Team Content Area */}
        {selectedTeam ? (
          <div className="flex-1 flex flex-col">
            {/* Team Header */}
            <div className="bg-white border-b border-gray-200 px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-purple-500 rounded-lg flex items-center justify-center">
                    <span className="text-white text-xl font-bold">
                      {selectedTeam.name?.[0]?.toUpperCase()}
            <div className="p-4 space-y-4">
              {teamMessages.map((msg, index) => (
                <div key={msg.message_id || index} className="flex items-start space-x-3">
                  <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-medium">
                      {msg.sender?.display_name?.[0]?.toUpperCase() || 
                       msg.sender?.username?.[0]?.toUpperCase() || 'U'}
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-medium text-gray-900">
                        {msg.sender?.display_name || msg.sender?.username || 'Unknown User'}
                      </span>
                      <span className="text-xs text-gray-500">
                        {new Date(msg.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="mt-1 text-sm text-gray-700">
                      {msg.content}
                    </div>
                  </div>
                </div>
              ))}
              
              {/* Typing indicator */}
              {typingUsers[selectedTeam?.team_id] && typingUsers[selectedTeam.team_id].length > 0 && (
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                  </div>
                  <span>
                    {typingUsers[selectedTeam.team_id].map(user => user.display_name || user.username).join(', ')} 
                    {typingUsers[selectedTeam.team_id].length === 1 ? ' is' : ' are'} typing...
                  </span>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-sm">
                <div className="text-4xl mb-4">💬</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  {t('teams.welcomeTo')} {selectedTeam.name}
                </h3>
                <p className="text-gray-600 mb-4 text-sm">
                  {selectedTeam.description || t('teams.startCollaborating')}
                </p>
                <button 
                  onClick={() => document.getElementById('team-message-input').focus()}
                  className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors text-sm"
                >
                  {t('teams.sendFirstMessage')}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Message Input */}
        <div className="bg-white p-4 border-t border-gray-200">
          <div className="flex items-center space-x-3">
            <button className="p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100">
              📎
            </button>
            <input
              id="team-message-input"
              type="text"
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={`${t('teams.messageTeam')} ${selectedTeam.name}`}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
              disabled={isSendingMessage}
            />
            <button 
              onClick={sendTeamMessage}
              disabled={!newMessage.trim() || isSendingMessage}
              className="bg-blue-500 text-white p-2 rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSendingMessage ? (
                <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
              ) : (
                '➤'
              )}
            </button>
          </div>
          
          {/* Connection status */}
          {!isConnected && (
            <div className="text-xs text-red-500 mt-2">
              {t('teams.connectionIssue')}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-white">
      {/* Teams Header */}
      <div className="bg-white p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">{t('teams.title')}</h2>
            <p className="text-sm text-gray-600">{t('teams.subtitle')}</p>
          </div>
          <button 
            onClick={() => setShowCreateTeam(true)}
            className="bg-blue-500 text-white p-2 rounded-lg hover:bg-blue-600 transition-colors"
            title={t('teams.createTeam')}
          >
            ➕
          </button>
        </div>
      </div>
      
      {/* Teams List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full"></div>
          </div>
        ) : teams && teams.length > 0 ? (
          <div className="p-4 space-y-3">
            {teams.map(team => (
              <button
                key={team.team_id || team.id}
                onClick={() => handleTeamClick(team)}
                className="w-full p-4 rounded-xl text-left hover:bg-gray-50 transition-colors border border-gray-100 bg-white shadow-sm"
              >
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-purple-500 rounded-lg flex items-center justify-center">
                    <span className="text-white font-medium text-lg">
                      {team.name?.[0]?.toUpperCase() || 'T'}
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 truncate">
                      {team.name || t('teams.unnamedTeam')}
                    </p>
                    <p className="text-sm text-gray-600 truncate">
                      {team.member_count || team.members?.length || 0} {t('teams.members')}
                    </p>
                    <p className="text-xs text-gray-500">
                      {team.last_activity ? new Date(team.last_activity).toLocaleDateString() : t('teams.noRecentActivity')}
                    </p>
                  </div>
                  <div className="text-gray-400">
                    →
                  </div>
                </div>
              </button>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center p-6">
            <div className="text-6xl mb-4">👥</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">{t('teams.noTeams')}</h3>
            <p className="text-gray-600 text-sm mb-6 max-w-sm">
              {t('teams.createTeamDescription')}
            </p>
            
            <div className="bg-gray-50 rounded-lg p-4 mb-6 max-w-sm">
              <h4 className="font-semibold text-gray-900 mb-2 text-sm">{t('teams.teamFeatures')}</h4>
              <div className="space-y-1 text-left text-xs text-gray-700">
                <div className="flex items-center space-x-2">
                  <span className="text-green-500">✓</span>
                  <span>{t('teams.groupMessaging')}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-green-500">✓</span>
                  <span>{t('teams.voiceVideoCalls')}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-green-500">✓</span>
                  <span>{t('teams.projectCollaboration')}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-green-500">✓</span>
                  <span>{t('teams.memberManagement')}</span>
                </div>
              </div>
            </div>

            <button 
              onClick={() => setShowCreateTeam(true)}
              className="bg-blue-500 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-600 transition-colors"
            >
              {t('teams.createFirstTeam')}
            </button>
          </div>
        )}
      </div>

      {/* Create Team Modal */}
      {showCreateTeam && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999] p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-sm w-full p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-bold text-gray-900">{t('teams.createTeam')}</h2>
              <button
                onClick={() => {
                  setShowCreateTeam(false);
                  setNewTeamName('');
                  setNewTeamDescription('');
                }}
                className="text-gray-500 hover:text-gray-700 text-xl"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('teams.teamNameRequired')}
                </label>
                <input
                  type="text"
                  value={newTeamName}
                  onChange={(e) => setNewTeamName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                  placeholder={t('teams.enterTeamName')}
                  maxLength={50}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('teams.description')}
                </label>
                <textarea
                  value={newTeamDescription}
                  onChange={(e) => setNewTeamDescription(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                  placeholder={t('teams.descriptionPlaceholder')}
                  rows={3}
                  maxLength={200}
                />
              </div>
            </div>
            
            <div className="flex space-x-3 mt-6">
              <button
                onClick={() => {
                  setShowCreateTeam(false);
                  setNewTeamName('');
                  setNewTeamDescription('');
                }}
                className="flex-1 bg-gray-100 text-gray-700 py-2 rounded-lg hover:bg-gray-200 transition-colors text-sm"
              >
                {t('common.cancel')}
              </button>
              <button
                onClick={handleCreateTeam}
                disabled={isCreating || !newTeamName.trim()}
                className="flex-1 bg-blue-500 text-white py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
              >
                {isCreating ? t('teams.creating') : t('teams.createTeamButton')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TeamsInterface;