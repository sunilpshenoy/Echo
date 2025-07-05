import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import ChatsInterface from './ChatsInterface';
import TeamsInterface from './TeamsInterface';
import DiscoverInterface from './DiscoverInterface';
import TrustSystem from './TrustSystem';
import LanguageSelector from './LanguageSelector';

const Dashboard = ({ user, token, api, onLogout, onUserUpdate }) => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('chats');
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [editProfileData, setEditProfileData] = useState({
    display_name: user?.display_name || user?.username || '',
    age: user?.age || '',
    gender: user?.gender || '',
    location: user?.location || '',
    bio: user?.bio || '',
    interests: user?.interests?.join(', ') || '',
    values: user?.values?.join(', ') || '',
    current_mood: user?.current_mood || '',
    seeking_type: user?.seeking_type || '',
    connection_purpose: user?.connection_purpose || ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [updateMessage, setUpdateMessage] = useState('');
  const [authenticityDetails, setAuthenticityDetails] = useState(null);
  const [isLoadingAuthenticity, setIsLoadingAuthenticity] = useState(false);
  
  // Connection management state
  const [connections, setConnections] = useState([]);
  const [isLoadingConnections, setIsLoadingConnections] = useState(false);
  const [connectionFilter, setConnectionFilter] = useState('all');
  const [selectedConnection, setSelectedConnection] = useState(null);
  
  // Chat state
  const [selectedChat, setSelectedChat] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoadingChats, setIsLoadingChats] = useState(false);
  const [chats, setChats] = useState([]);
  
  // Teams state
  const [teams, setTeams] = useState([]);
  const [selectedTeam, setSelectedTeam] = useState(null);
  const [isLoadingTeams, setIsLoadingTeams] = useState(false);
  
  // Premium state (check for both user premium and demo mode)
  const [isPremium, setIsPremium] = useState(
    user?.premium || localStorage.getItem('demo_premium') === 'true'
  );
  
  // Listen for storage changes to update premium status
  useEffect(() => {
    const handleStorageChange = () => {
      setIsPremium(user?.premium || localStorage.getItem('demo_premium') === 'true');
    };
    
    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [user?.premium]);
  
  // Fetch authenticity details
  const fetchAuthenticityDetails = async () => {
    setIsLoadingAuthenticity(true);
    try {
      const response = await axios.get(`${api}/authenticity/details`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAuthenticityDetails(response.data);
    } catch (error) {
      console.error('Failed to fetch authenticity details:', error);
    } finally {
      setIsLoadingAuthenticity(false);
    }
  };

  const updateAuthenticityRating = async () => {
    try {
      await axios.put(`${api}/authenticity/update`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      await fetchAuthenticityDetails();
      setUpdateMessage('Authenticity rating updated! 🎉');
    } catch (error) {
      console.error('Failed to update authenticity rating:', error);
    }
  };
  
  // Chat management functions
  const fetchChats = async () => {
    setIsLoadingChats(true);
    try {
      const response = await axios.get(`${api}/chats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setChats(response.data);
    } catch (error) {
      console.error('Failed to fetch chats:', error);
    } finally {
      setIsLoadingChats(false);
    }
  };

  const selectChat = async (chat) => {
    setSelectedChat(chat);
    try {
      const response = await axios.get(`${api}/chats/${chat.chat_id}/messages`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setChatMessages(response.data);
    } catch (error) {
      console.error('Failed to fetch messages:', error);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !selectedChat) return;
    
    try {
      await axios.post(`${api}/chats/${selectedChat.chat_id}/messages`, {
        content: newMessage,
        message_type: 'text'
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setNewMessage('');
      // Real-time updates will be handled by WebSocket, but refresh as fallback
      await selectChat(selectedChat);
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const fetchTeams = async () => {
    setIsLoadingTeams(true);
    try {
      const response = await axios.get(`${api}/teams`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTeams(response.data);
    } catch (error) {
      console.error('Failed to fetch teams:', error);
    } finally {
      setIsLoadingTeams(false);
    }
  };

  const fetchConnections = async () => {
    setIsLoadingConnections(true);
    try {
      const response = await axios.get(`${api}/connections`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setConnections(response.data);
    } catch (error) {
      console.error('Failed to fetch connections:', error);
    } finally {
      setIsLoadingConnections(false);
    }
  };

  const respondToConnection = async (connectionId, action) => {
    try {
      await axios.put(`${api}/connections/${connectionId}/respond`, {
        action: action
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUpdateMessage(`Connection ${action}ed successfully! 🎉`);
      await fetchConnections();
    } catch (error) {
      console.error(`Failed to ${action} connection:`, error);
      setUpdateMessage(`Failed to ${action} connection. Please try again.`);
    }
  };
  
  // Profile editing functions
  const handleEditProfileChange = (field, value) => {
    setEditProfileData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSaveProfile = async () => {
    setIsLoading(true);
    setUpdateMessage('');
    
    try {
      const updateData = {
        ...editProfileData,
        interests: editProfileData.interests.split(',').map(item => item.trim()).filter(item => item),
        values: editProfileData.values.split(',').map(item => item.trim()).filter(item => item),
        age: editProfileData.age ? parseInt(editProfileData.age) : null
      };

      const response = await axios.put(`${api}/profile/complete`, updateData, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setUpdateMessage('Profile updated successfully! 🎉');
      setIsEditingProfile(false);
      
      if (onUserUpdate && response.data) {
        onUserUpdate(response.data);
      }
      
      setTimeout(() => {
        setUpdateMessage('');
      }, 3000);
      
    } catch (error) {
      setUpdateMessage('Failed to update profile. Please try again.');
      console.error('Profile update error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'chats') {
      fetchChats();
    } else if (activeTab === 'teams') {
      fetchTeams();
    } else if (activeTab === 'discover') {
      // Fetch authenticity details when discover tab is opened
      if (!authenticityDetails) {
        fetchAuthenticityDetails();
      }
      // Fetch connections for discover tab
      fetchConnections();
    }
  }, [activeTab]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50 relative">
      {/* Pulse Logo Background - Exact Match */}
      <div className="fixed inset-0 flex items-center justify-center pointer-events-none z-0">
        <div className="opacity-8 transform scale-125">
          <svg width="150" height="195" viewBox="0 0 120 160">
            <defs>
              <linearGradient id="bgShieldGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#D946EF"/>
                <stop offset="30%" stopColor="#EC4899"/>
                <stop offset="70%" stopColor="#F97316"/>
                <stop offset="100%" stopColor="#FB923C"/>
              </linearGradient>
            </defs>
            
            {/* Hexagonal shield - exactly like your design */}
            <path d="M25 35 C20 30, 20 30, 25 30 L95 30 C100 30, 100 30, 95 35 L105 50 L100 80 C100 85, 95 85, 90 85 L60 90 L30 85 C25 85, 20 85, 20 80 L15 50 Z" 
                  fill="url(#bgShieldGradient)" 
                  opacity="0.4"/>
            
            {/* Interlocked hearts */}
            <g transform="translate(60, 55)">
              <path d="M-12 -8 C-18 -15, -28 -15, -28 -5 C-28 5, -12 18, 0 25 C6 20, 12 15, 18 10" 
                    fill="#2D1B69" 
                    opacity="0.3"/>
              <path d="M12 -8 C18 -15, 28 -15, 28 -5 C28 5, 12 18, 0 25 C-6 20, -12 15, -18 10" 
                    fill="#2D1B69" 
                    opacity="0.3"/>
              <path d="M-8 0 C-5 -5, 5 -5, 8 0 C5 5, -5 5, -8 0" 
                    fill="#2D1B69" 
                    opacity="0.2"/>
            </g>
          </svg>
        </div>
      </div>
      
      {/* Main content with higher z-index */}
      <div className="relative z-10">
      {/* WhatsApp-style Header */}
      <div className="bg-white border-b shadow-sm">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <div className="w-10 h-10 bg-pulse-secondary rounded-full flex items-center justify-center shadow-md">
                <span className="text-white font-bold text-lg">
                  {user?.display_name?.[0]?.toUpperCase() || user?.username?.[0]?.toUpperCase() || '?'}
                </span>
              </div>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">
                  {user?.display_name || user?.username || 'User'}
                </h1>
                <p className="text-sm text-gray-700 font-medium">
                  {t('profile.trustLevel')} {user?.trust_level || 1} • {t('profile.authenticity')} {(user?.authenticity_rating || 0).toFixed(1)}
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setIsEditingProfile(true)}
                className="text-gray-600 hover:text-gray-800 p-2"
                title={t('common.edit')}
              >
                ⚙️
              </button>
              <button
                onClick={onLogout}
                className="text-gray-600 hover:text-gray-800 p-2"
                title={t('dashboard.signOut')}
              >
                🚪
              </button>
            </div>
          </div>
          
          {/* Top Tabs - WhatsApp Style */}
          <div className="flex border-b">
            {[
              { id: 'chats', label: t('dashboard.chats'), icon: '💬', description: t('dashboard.directMessages') },
              { id: 'teams', label: t('dashboard.teams'), icon: '👥', description: t('dashboard.groupsWorkspaces') },
              { 
                id: 'discover', 
                label: t('dashboard.premium'), 
                icon: '⭐', 
                description: t('dashboard.findPeopleSafely'),
                premium: true 
              }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-6 py-3 text-sm font-medium border-b-2 transition-all ${
                  activeTab === tab.id
                    ? 'border-purple-500 text-purple-700 bg-purple-50 font-semibold'
                    : 'border-transparent text-gray-700 hover:text-purple-600 hover:bg-purple-50'
                }`}
              >
                <span className="text-lg">{tab.icon}</span>
                <span>{tab.label}</span>
                {tab.premium && !isPremium && (
                  <span className="bg-yellow-100 text-yellow-700 px-2 py-1 rounded-full text-xs font-medium">
                    Premium
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="max-w-7xl mx-auto flex h-[calc(100vh-120px)]">
        <div className="flex-1 flex">
          {activeTab === 'chats' && (
            <ChatsInterface 
              user={user}
              token={token}
              api={api}
              chats={chats}
              selectedChat={selectedChat}
              chatMessages={chatMessages}
              newMessage={newMessage}
              setNewMessage={setNewMessage}
              onSelectChat={selectChat}
              onSendMessage={sendMessage}
              isLoading={isLoadingChats}
            />
          )}
          
          {activeTab === 'teams' && (
            <TeamsInterface 
              user={user}
              token={token}
              api={api}
              teams={teams}
              selectedTeam={selectedTeam}
              isLoading={isLoadingTeams}
            />
          )}
          
          {activeTab === 'discover' && (
            <DiscoverInterface 
              user={user}
              token={token}
              api={api}
              isPremium={isPremium}
              authenticityDetails={authenticityDetails}
              fetchAuthenticityDetails={fetchAuthenticityDetails}
              isLoadingAuthenticity={isLoadingAuthenticity}
              connections={connections}
              fetchConnections={fetchConnections}
            />
          )}
        </div>
      </div>

      {/* Profile Editing Modal */}
      {isEditingProfile && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b px-6 py-4 rounded-t-2xl">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-bold text-gray-900">Edit Your Profile</h2>
                <button
                  onClick={() => setIsEditingProfile(false)}
                  className="text-gray-500 hover:text-gray-700 text-2xl leading-none"
                >
                  ✕
                </button>
              </div>
            </div>
            
            <div className="p-6 space-y-8">
              {updateMessage && (
                <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
                  {updateMessage}
                </div>
              )}
              
              {/* Basic Information */}
              <div>
                <h3 className="font-semibold text-gray-900 mb-4">Basic Information</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Display Name
                    </label>
                    <input
                      type="text"
                      value={editProfileData.display_name}
                      onChange={(e) => handleEditProfileChange('display_name', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="How should others see your name?"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Age
                    </label>
                    <input
                      type="number"
                      min="18"
                      max="100"
                      value={editProfileData.age}
                      onChange={(e) => handleEditProfileChange('age', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Your age"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Gender
                    </label>
                    <select
                      value={editProfileData.gender}
                      onChange={(e) => handleEditProfileChange('gender', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select your gender</option>
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                      <option value="non-binary">Non-binary</option>
                      <option value="prefer-not-to-say">Prefer not to say</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Location
                    </label>
                    <input
                      type="text"
                      value={editProfileData.location}
                      onChange={(e) => handleEditProfileChange('location', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="City, Country"
                    />
                  </div>
                </div>
                
                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Bio
                  </label>
                  <textarea
                    value={editProfileData.bio}
                    onChange={(e) => handleEditProfileChange('bio', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 h-24"
                    placeholder="Tell others about yourself..."
                    maxLength="500"
                  />
                  <p className="text-gray-500 text-sm mt-1">
                    {editProfileData.bio.length}/500 characters
                  </p>
                </div>
              </div>
              
              {/* Interests & Values */}
              <div>
                <h3 className="font-semibold text-gray-900 mb-4">Interests & Values</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Interests (comma-separated)
                    </label>
                    <input
                      type="text"
                      value={editProfileData.interests}
                      onChange={(e) => handleEditProfileChange('interests', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g., photography, hiking, cooking"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Values (comma-separated)
                    </label>
                    <input
                      type="text"
                      value={editProfileData.values}
                      onChange={(e) => handleEditProfileChange('values', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g., honesty, creativity, kindness"
                    />
                  </div>
                </div>
              </div>
              
              {/* Connection Preferences */}
              <div>
                <h3 className="font-semibold text-gray-900 mb-4">Connection Preferences</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Current Mood
                    </label>
                    <textarea
                      value={editProfileData.current_mood}
                      onChange={(e) => handleEditProfileChange('current_mood', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 h-20"
                      placeholder="How are you feeling today?"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      What are you seeking?
                    </label>
                    <select
                      value={editProfileData.seeking_type}
                      onChange={(e) => handleEditProfileChange('seeking_type', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select what you're looking for</option>
                      <option value="friendship">New friends</option>
                      <option value="romantic">Romantic connection</option>
                      <option value="activity-partner">Activity partners</option>
                      <option value="professional">Professional networking</option>
                      <option value="open">Open to anything genuine</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Connection Purpose
                    </label>
                    <textarea
                      value={editProfileData.connection_purpose}
                      onChange={(e) => handleEditProfileChange('connection_purpose', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 h-20"
                      placeholder="What do you hope to achieve through new connections?"
                    />
                  </div>
                </div>
              </div>
            </div>
            
            {/* Modal Footer */}
            <div className="sticky bottom-0 bg-gray-50 px-6 py-4 rounded-b-2xl border-t">
              <div className="flex justify-end space-x-4">
                <button
                  onClick={() => setIsEditingProfile(false)}
                  className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300"
                  disabled={isLoading}
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveProfile}
                  disabled={isLoading}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400"
                >
                  {isLoading ? (
                    <div className="flex items-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Saving...
                    </div>
                  ) : (
                    'Save Changes'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      </div> {/* Close main content wrapper */}
    </div>
  );
};

export default Dashboard;