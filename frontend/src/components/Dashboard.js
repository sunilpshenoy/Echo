import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import ChatsInterface from './ChatsInterface';
import TeamsInterface from './TeamsInterface';
import GroupDiscovery from './GroupDiscovery';
import DiscoverInterface from './DiscoverInterface';
import TrustSystem from './TrustSystem';
import LanguageSelector from './LanguageSelector';
import ThemeCustomizer from './ThemeCustomizer';
import GroupsHub from './GroupsHub';
import ChannelsInterface from './ChannelsInterface';
import SimpleMarketplace from './SimpleMarketplace';
import SmartProfileManager from './SmartProfileManager';
import ContextualProfileSetup from './ContextualProfileSetup';
import GamesInterface from './GamesInterface';

const Dashboard = ({ user, token, api, onLogout, onUserUpdate }) => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('games'); // Test: Default to games
  const [showProfilePrompt, setShowProfilePrompt] = useState(false);
  const [attemptedTab, setAttemptedTab] = useState(null);
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [showSmartProfileManager, setShowSmartProfileManager] = useState(false);
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
  
  // Calendar and Calculator Modal States
  const [showCalendarModal, setShowCalendarModal] = useState(false);
  const [showCalculatorModal, setShowCalculatorModal] = useState(false);
  
  // Theme customization state
  const [showThemeCustomizer, setShowThemeCustomizer] = useState(false);
  const [currentTheme, setCurrentTheme] = useState('default');
  const [appliedTheme, setAppliedTheme] = useState(null);
  const [profileCompleteness, setProfileCompleteness] = useState({});
  const [showContextualSetup, setShowContextualSetup] = useState(false);
  const [currentContext, setCurrentContext] = useState(null);
  
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
  
  // Check profile completeness on component mount
  useEffect(() => {
    checkProfileCompleteness();
  }, [user, token, api]);
  
  // Cleanup loading states on component unmount
  useEffect(() => {
    return () => {
      setIsLoadingChats(false);
      setIsLoadingTeams(false);
      setIsLoadingConnections(false);
    };
  }, []);

  const checkProfileCompleteness = async () => {
    if (!user || !token) return;
    
    try {
      const response = await axios.get(`${api}/users/profile/completeness`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProfileCompleteness(response.data.profiles || {});
    } catch (error) {
      console.error('Failed to check profile completeness:', error);
    }
  };

  // Check if user can access tab
  const canAccessTab = (tab) => {
    const requirements = {
      chats: { required: ['display_name'] },
      teams: { required: ['interests', 'location'] },
      marketplace: { required: ['full_name', 'phone_verification', 'location'] },
      premium: { required: ['premium_display_name', 'current_mood'] }
    };

    if (tab === 'chats') return true; // Always allow chats

    const tabRequirements = requirements[tab];
    if (!tabRequirements) return true;

    const userProfile = profileCompleteness[tab] || {};
    return tabRequirements.required.every(field => userProfile[field]);
  };

  // Function to check if profile is required for a tab
  const requiresProfile = (tabId) => {
    return tabId === 'teams' || tabId === 'premium';
  };

  // Handle tab selection with profile requirement check
  const handleTabSelection = (tabId) => {
    if (canAccessTab(tabId)) {
      setActiveTab(tabId);
    } else {
      // Show contextual profile setup
      setCurrentContext(tabId);
      setShowContextualSetup(true);
    }
  };

  // Handle profile completion
  const handleProfileComplete = () => {
    setShowProfilePrompt(false);
    if (attemptedTab) {
      setActiveTab(attemptedTab);
      setAttemptedTab(null);
    }
  };

  // Handle profile prompt dismissal
  const handleProfilePromptDismiss = () => {
    setShowProfilePrompt(false);
    setAttemptedTab(null);
  };

  // Handle contextual profile setup completion
  const handleContextualSetupComplete = (data) => {
    setShowContextualSetup(false);
    checkProfileCompleteness(); // Refresh completeness
    if (currentContext) {
      setActiveTab(currentContext); // Switch to the tab they wanted
      setCurrentContext(null);
    }
  };

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
    if (isLoadingChats) {
      console.log('⚠️ Already loading chats, skipping duplicate request');
      return;
    }
    
    setIsLoadingChats(true);
    console.log('🔄 Fetching chats...');
    
    // Add timeout mechanism to prevent indefinite loading
    const fetchTimeout = setTimeout(() => {
      console.log('⏰ Chat fetch timeout - resetting loading state');
      setIsLoadingChats(false);
    }, 10000); // 10 second timeout
    
    try {
      const response = await axios.get(`${api}/chats`, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 8000 // 8 second axios timeout
      });
      console.log('✅ Chats response:', response.data);
      setChats(response.data);
      clearTimeout(fetchTimeout); // Clear timeout on success
    } catch (error) {
      console.error('❌ Failed to fetch chats:', error);
      setChats([]); // Set empty array on error
      clearTimeout(fetchTimeout); // Clear timeout on error
    } finally {
      setIsLoadingChats(false);
      console.log('🏁 Chat loading completed');
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

  const selectTeam = (team) => {
    setSelectedTeam(team);
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

  // Calculator functionality
  const calculatorAction = (action) => {
    const display = document.getElementById('calculator-display');
    if (!display) return;
    
    const currentValue = display.textContent;
    
    switch (action) {
      case 'clear':
        display.textContent = '0';
        break;
      case '=':
        try {
          // Replace display symbols with JavaScript operators
          const expression = currentValue
            .replace(/×/g, '*')
            .replace(/÷/g, '/')
            .replace(/−/g, '-');
          const result = eval(expression);
          display.textContent = result.toString();
        } catch (error) {
          display.textContent = 'Error';
        }
        break;
      case '±':
        if (currentValue !== '0') {
          display.textContent = currentValue.startsWith('-') 
            ? currentValue.slice(1) 
            : '-' + currentValue;
        }
        break;
      case '%':
        try {
          const result = parseFloat(currentValue) / 100;
          display.textContent = result.toString();
        } catch (error) {
          display.textContent = 'Error';
        }
        break;
      default:
        if (currentValue === '0' && !isNaN(action)) {
          display.textContent = action;
        } else if (currentValue === 'Error') {
          display.textContent = action;
        } else {
          display.textContent = currentValue + action;
        }
        break;
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
    
    // Cleanup function to reset loading states when switching tabs
    return () => {
      if (activeTab !== 'chats') {
        setIsLoadingChats(false);
      }
      if (activeTab !== 'teams') {
        setIsLoadingTeams(false);
      }
    };
  }, [activeTab]); // Only depend on activeTab to prevent infinite loops

  // Theme application function
  const applyThemeStyles = (theme) => {
    if (!theme || typeof theme === 'string') return;
    
    // Apply CSS custom properties for theming
    const root = document.documentElement;
    
    if (theme.colors) {
      root.style.setProperty('--color-primary', theme.colors.primary);
      root.style.setProperty('--color-secondary', theme.colors.secondary);
      root.style.setProperty('--color-accent', theme.colors.accent);
      root.style.setProperty('--color-background', theme.colors.background);
      root.style.setProperty('--color-surface', theme.colors.surface);
      root.style.setProperty('--color-text', theme.colors.text);
      root.style.setProperty('--color-text-secondary', theme.colors.textSecondary);
    }
    
    if (theme.chatBubbles) {
      root.style.setProperty('--chat-own-bubble', theme.chatBubbles.ownBubbleColor);
      root.style.setProperty('--chat-other-bubble', theme.chatBubbles.otherBubbleColor);
      root.style.setProperty('--chat-own-text', theme.chatBubbles.textColor);
      root.style.setProperty('--chat-other-text', theme.chatBubbles.otherTextColor);
    }
    
    // Save theme to localStorage
    localStorage.setItem('pulse_current_theme', JSON.stringify(theme));
    localStorage.setItem('pulse_theme_name', theme.name || 'custom');
  };

  // Load saved theme on component mount
  useEffect(() => {
    const savedTheme = localStorage.getItem('pulse_current_theme');
    const savedThemeName = localStorage.getItem('pulse_theme_name');
    
    if (savedTheme) {
      try {
        const theme = JSON.parse(savedTheme);
        setAppliedTheme(theme);
        setCurrentTheme(savedThemeName || 'custom');
        applyThemeStyles(theme);
      } catch (error) {
        console.error('Failed to load saved theme:', error);
      }
    }
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50 relative">
      
      {/* Main content with higher z-index */}
      <div className="relative z-10">
      {/* WhatsApp-style Header */}
      <div className="bg-white border-b shadow-sm">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setIsEditingProfile(true)}
                className="flex items-center space-x-3 hover:bg-gray-100 rounded-lg p-1 transition-colors"
                title={t('common.edit')}
                aria-label={`Edit profile for ${user?.display_name || user?.username || 'user'}`}
              >
                <div className="w-10 h-10 bg-pulse-secondary rounded-full flex items-center justify-center shadow-md">
                  <span className="text-white font-bold text-lg">
                    {user?.display_name?.[0]?.toUpperCase() || user?.username?.[0]?.toUpperCase() || '?'}
                  </span>
                </div>
                <div>
                  <h1 className="text-xl font-semibold text-gray-900">
                    {user?.display_name || user?.username || 'User'}
                  </h1>
                  <p className="text-sm text-gray-500">
                    {t('dashboard.clickToEdit')}
                  </p>
                </div>
              </button>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Calendar with Planner Icon */}
              <button
                onClick={() => setShowCalendarModal(true)}
                className="text-gray-600 hover:text-blue-600 p-2 transition-colors"
                title="Calendar & Planner"
                aria-label="Open calendar and planner"
              >
                📅
              </button>
              
              {/* Calculator Icon */}
              <button
                onClick={() => setShowCalculatorModal(true)}
                className="text-gray-600 hover:text-green-600 p-2 transition-colors"
                title="Calculator"
                aria-label="Open calculator"
              >
                🧮
              </button>
              
              {/* Logout Button */}
              <button
                onClick={onLogout}
                className="text-gray-600 hover:text-gray-800 p-2"
                title={t('dashboard.signOut')}
                aria-label="Sign out of your account"
              >
                🚪
              </button>
            </div>
          </div>
          
          {/* Top Tabs - Streamlined Navigation */}
          <div className="flex border-b overflow-x-auto">
            {[
              { id: 'chats', label: t('dashboard.chats'), icon: '💬', description: 'Direct messages & conversations' },
              { id: 'teams', label: 'Groups', icon: '👥', description: 'Discover groups, map view & events' },
              { id: 'games', label: 'Games', icon: '🎮', description: 'Multiplayer games & tournaments' },
              { id: 'marketplace', label: 'Marketplace', icon: '🛒', description: 'Buy, sell & trade items and services' },
              { 
                id: 'premium', 
                label: t('dashboard.premium'), 
                icon: '⭐', 
                description: t('dashboard.findPeopleSafely'),
                premium: true 
              }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => handleTabSelection(tab.id)}
                className={`flex items-center space-x-2 px-6 py-3 text-sm font-medium border-b-2 transition-all whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'border-purple-500 text-purple-700 bg-purple-50 font-semibold'
                    : canAccessTab(tab.id) 
                      ? 'border-transparent text-gray-700 hover:text-purple-600 hover:bg-purple-50'
                      : 'border-transparent text-gray-400 hover:text-orange-500 hover:bg-orange-50'
                } ${!canAccessTab(tab.id) ? 'cursor-help' : 'cursor-pointer'}`}
                aria-label={`Switch to ${tab.label} tab - ${tab.description}`}
                aria-current={activeTab === tab.id ? 'page' : undefined}
                title={!canAccessTab(tab.id) ? `Complete profile to access ${tab.label}` : `Switch to ${tab.label} tab - ${tab.description}`}
              >
                <span className="text-lg">{tab.icon}</span>
                <span>{tab.label}</span>
                {tab.premium && !isPremium && (
                  <span className="bg-yellow-100 text-yellow-700 px-2 py-1 rounded-full text-xs font-medium">
                    ⭐
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="max-w-7xl mx-auto flex h-[calc(100vh-120px)]">
        <div className="flex-1 flex relative">
          {/* Tab Content */}
          <div className="relative z-10 flex-1 flex">
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

            {activeTab === 'marketplace' && (
              <SimpleMarketplace 
                user={user}
                token={token}
                api={api}
              />
            )}
            
            {activeTab === 'games' && (
              <GamesInterface 
                user={user}
                token={token}
                api={api}
              />
            )}
            
            {activeTab === 'teams' && (
              <GroupsHub 
                user={user}
                token={token}
                api={api}
              />
            )}
            
            {activeTab === 'premium' && (
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
      </div>

      {/* Profile Editing Modal */}
      {isEditingProfile && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" role="dialog" aria-labelledby="profile-modal-title" aria-modal="true">
          <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b px-6 py-4 rounded-t-2xl">
              <div className="flex justify-between items-center">
                <h2 id="profile-modal-title" className="text-xl font-bold text-gray-900">Edit Your Profile</h2>
                <button
                  onClick={() => setIsEditingProfile(false)}
                  className="text-gray-500 hover:text-gray-700 text-2xl leading-none"
                  aria-label="Close profile edit modal"
                >
                  ✕
                </button>
              </div>
            </div>
            
            <div className="p-6 space-y-8">
              {updateMessage && (
                <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg" role="alert">
                  {updateMessage}
                </div>
              )}
              
              {/* Basic Information */}
              <div>
                <h3 className="font-semibold text-gray-900 mb-4">Basic Information</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="display_name">
                      Display Name
                    </label>
                    <input
                      type="text"
                      id="display_name"
                      value={editProfileData.display_name}
                      onChange={(e) => handleEditProfileChange('display_name', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="How should others see your name?"
                      aria-describedby="display_name-help"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="age">
                      Age
                    </label>
                    <input
                      type="number"
                      id="age"
                      min="18"
                      max="100"
                      value={editProfileData.age}
                      onChange={(e) => handleEditProfileChange('age', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Your age"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="gender">
                      Gender
                    </label>
                    <select
                      id="gender"
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
                    <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="location">
                      Location
                    </label>
                    <input
                      type="text"
                      id="location"
                      value={editProfileData.location}
                      onChange={(e) => handleEditProfileChange('location', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="City, Country"
                    />
                  </div>
                </div>
                
                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="bio">
                    Bio
                  </label>
                  <textarea
                    id="bio"
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
                    <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="interests">
                      Interests (comma-separated)
                    </label>
                    <input
                      type="text"
                      id="interests"
                      value={editProfileData.interests}
                      onChange={(e) => handleEditProfileChange('interests', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g., photography, hiking, cooking"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="values">
                      Values (comma-separated)
                    </label>
                    <input
                      type="text"
                      id="values"
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
                    <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="current_mood">
                      Current Mood
                    </label>
                    <textarea
                      id="current_mood"
                      value={editProfileData.current_mood}
                      onChange={(e) => handleEditProfileChange('current_mood', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 h-20"
                      placeholder="How are you feeling today?"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="seeking_type">
                      What are you seeking?
                    </label>
                    <select
                      id="seeking_type"
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
                    <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="connection_purpose">
                      Connection Purpose
                    </label>
                    <textarea
                      id="connection_purpose"
                      value={editProfileData.connection_purpose}
                      onChange={(e) => handleEditProfileChange('connection_purpose', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 h-20"
                      placeholder="What do you hope to achieve through new connections?"
                    />
                  </div>
                </div>
              </div>
              
              {/* Language Settings */}
              <div>
                <h3 className="font-semibold text-gray-900 mb-4">{t('languages.changeLanguage')}</h3>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t('languages.changeLanguage')}
                  </label>
                  <LanguageSelector className="w-full" />
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
                  aria-label="Cancel profile editing"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveProfile}
                  disabled={isLoading}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400"
                  aria-label="Save profile changes"
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

              {/* Theme Customization Section */}
              <div className="border-t border-gray-200 pt-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center space-x-2">
                  <span>🎨</span>
                  <span>{t('themes.title')}</span>
                </h3>
                <button
                  onClick={() => setShowThemeCustomizer(true)}
                  className="w-full bg-gradient-to-r from-purple-500 to-blue-500 text-white py-3 px-4 rounded-lg hover:from-purple-600 hover:to-blue-600 transition-all duration-200 flex items-center justify-center space-x-2"
                  aria-label="Open theme customization panel"
                >
                  <span>🎨</span>
                  <span>{t('themes.title')}</span>
                </button>
                <p className="text-sm text-gray-500 mt-2 text-center">
                  {t('themes.currentTheme')}: {currentTheme === 'default' ? t('themes.defaultTheme') : currentTheme}
                </p>
              </div>

              {/* Smart Profile Management */}
              <div className="bg-gradient-to-br from-green-50 to-teal-50 rounded-xl p-6 border border-green-100">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
                  <span>👤</span>
                  <span>Smart Profile Management</span>
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  Manage your profiles for different app sections. Each tab has specific requirements for the best experience.
                </p>
                <button
                  onClick={() => setShowSmartProfileManager(true)}
                  className="w-full bg-gradient-to-r from-green-500 to-teal-500 text-white py-3 px-4 rounded-lg hover:from-green-600 hover:to-teal-600 transition-all duration-200 flex items-center justify-center space-x-2"
                  aria-label="Open smart profile management"
                >
                  <span>🎯</span>
                  <span>Manage Profiles</span>
                </button>
                <p className="text-sm text-gray-500 mt-2 text-center">
                  Contextual profiles for Chats, Groups, Marketplace & Premium
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Contextual Profile Setup Modal */}
      {showContextualSetup && currentContext && (
        <ContextualProfileSetup
          user={user}
          token={token}
          api={api}
          context={currentContext}
          onComplete={handleContextualSetupComplete}
          onSkip={() => {
            setShowContextualSetup(false);
            setCurrentContext(null);
          }}
        />
      )}

      {/* Smart Profile Manager Modal */}
      {showSmartProfileManager && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900">Smart Profile Management</h2>
                <button
                  onClick={() => setShowSmartProfileManager(false)}
                  className="text-gray-500 hover:text-gray-700 text-xl"
                >
                  ✕
                </button>
              </div>
              
              <SmartProfileManager 
                user={user}
                token={token}
                api={api}
              />
            </div>
          </div>
        </div>
      )}

      {/* Calendar & Planner Modal */}
      {showCalendarModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                  📅 Calendar & Planner
                </h2>
                <button
                  onClick={() => setShowCalendarModal(false)}
                  className="text-gray-500 hover:text-gray-700 text-xl"
                  aria-label="Close calendar"
                >
                  ✕
                </button>
              </div>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Calendar Section */}
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-800 flex items-center">
                    📆 Calendar
                  </h3>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-800">
                        {new Date().toLocaleDateString('en-US', { 
                          weekday: 'long', 
                          year: 'numeric', 
                          month: 'long', 
                          day: 'numeric' 
                        })}
                      </div>
                      <div className="text-sm text-gray-600 mt-2">
                        {new Date().toLocaleTimeString('en-US', { 
                          hour: '2-digit', 
                          minute: '2-digit' 
                        })}
                      </div>
                    </div>
                    
                    {/* Quick Date Navigation */}
                    <div className="grid grid-cols-7 gap-1 mt-4 text-xs">
                      {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                        <div key={day} className="text-center p-2 font-medium text-gray-600">
                          {day}
                        </div>
                      ))}
                      {Array.from({length: 35}, (_, i) => {
                        const date = new Date();
                        const firstDay = new Date(date.getFullYear(), date.getMonth(), 1);
                        const startingDay = firstDay.getDay();
                        const daysInMonth = new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
                        const currentDay = i - startingDay + 1;
                        const isCurrentMonth = currentDay > 0 && currentDay <= daysInMonth;
                        const isToday = isCurrentMonth && currentDay === date.getDate();
                        
                        return (
                          <div 
                            key={i} 
                            className={`text-center p-2 hover:bg-blue-100 cursor-pointer rounded ${
                              isToday ? 'bg-blue-500 text-white' : ''
                            } ${isCurrentMonth ? 'text-gray-800' : 'text-gray-300'}`}
                          >
                            {isCurrentMonth ? currentDay : ''}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                  
                  {/* Quick Actions */}
                  <div className="space-y-2">
                    <button className="w-full bg-blue-500 text-white p-3 rounded-lg hover:bg-blue-600 transition-colors">
                      📅 Schedule Event
                    </button>
                    <button className="w-full bg-green-500 text-white p-3 rounded-lg hover:bg-green-600 transition-colors">
                      🔔 Set Reminder
                    </button>
                  </div>
                </div>

                {/* Planner Section */}
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-800 flex items-center">
                    📝 Today's Tasks
                  </h3>
                  <div className="bg-gray-50 rounded-lg p-4 min-h-[300px]">
                    <div className="space-y-3">
                      <div className="flex items-center space-x-2">
                        <input type="checkbox" className="w-4 h-4" />
                        <span className="text-gray-700">Review chat messages</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <input type="checkbox" className="w-4 h-4" />
                        <span className="text-gray-700">Plan weekend activities</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <input type="checkbox" className="w-4 h-4" />
                        <span className="text-gray-700">Update profile information</span>
                      </div>
                      
                      {/* Add Task Input */}
                      <div className="border-t pt-3 mt-4">
                        <div className="flex space-x-2">
                          <input 
                            type="text" 
                            placeholder="Add new task..." 
                            className="flex-1 p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          />
                          <button className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors">
                            ➕
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Planner Actions */}
                  <div className="space-y-2">
                    <button className="w-full bg-purple-500 text-white p-3 rounded-lg hover:bg-purple-600 transition-colors">
                      📋 Create Task List
                    </button>
                    <button className="w-full bg-orange-500 text-white p-3 rounded-lg hover:bg-orange-600 transition-colors">
                      🎯 Set Goals
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Calculator Modal */}
      {showCalculatorModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                  🧮 Calculator
                </h2>
                <button
                  onClick={() => setShowCalculatorModal(false)}
                  className="text-gray-500 hover:text-gray-700 text-xl"
                  aria-label="Close calculator"
                >
                  ✕
                </button>
              </div>
              
              <div className="bg-gray-50 rounded-lg p-4">
                {/* Calculator Display */}
                <div className="bg-black text-white text-right text-2xl p-4 rounded-lg mb-4 font-mono">
                  <div id="calculator-display">0</div>
                </div>
                
                {/* Calculator Buttons */}
                <div className="grid grid-cols-4 gap-2">
                  {/* Row 1 */}
                  <button className="bg-gray-300 hover:bg-gray-400 p-4 rounded-lg font-semibold transition-colors" onClick={() => calculatorAction('clear')}>C</button>
                  <button className="bg-gray-300 hover:bg-gray-400 p-4 rounded-lg font-semibold transition-colors" onClick={() => calculatorAction('±')}>±</button>
                  <button className="bg-gray-300 hover:bg-gray-400 p-4 rounded-lg font-semibold transition-colors" onClick={() => calculatorAction('%')}>%</button>
                  <button className="bg-orange-500 hover:bg-orange-600 text-white p-4 rounded-lg font-semibold transition-colors" onClick={() => calculatorAction('÷')}>÷</button>
                  
                  {/* Row 2 */}
                  <button className="bg-gray-200 hover:bg-gray-300 p-4 rounded-lg font-semibold transition-colors" onClick={() => calculatorAction('7')}>7</button>
                  <button className="bg-gray-200 hover:bg-gray-300 p-4 rounded-lg font-semibold transition-colors" onClick={() => calculatorAction('8')}>8</button>
                  <button className="bg-gray-200 hover:bg-gray-300 p-4 rounded-lg font-semibold transition-colors" onClick={() => calculatorAction('9')}>9</button>
                  <button className="bg-orange-500 hover:bg-orange-600 text-white p-4 rounded-lg font-semibold transition-colors" onClick={() => calculatorAction('×')}>×</button>
                  
                  {/* Row 3 */}
                  <button className="bg-gray-200 hover:bg-gray-300 p-4 rounded-lg font-semibold transition-colors" onClick={() => calculatorAction('4')}>4</button>
                  <button className="bg-gray-200 hover:bg-gray-300 p-4 rounded-lg font-semibold transition-colors" onClick={() => calculatorAction('5')}>5</button>
                  <button className="bg-gray-200 hover:bg-gray-300 p-4 rounded-lg font-semibold transition-colors" onClick={() => calculatorAction('6')}>6</button>
                  <button className="bg-orange-500 hover:bg-orange-600 text-white p-4 rounded-lg font-semibold transition-colors" onClick={() => calculatorAction('-')}>-</button>
                  
                  {/* Row 4 */}
                  <button className="bg-gray-200 hover:bg-gray-300 p-4 rounded-lg font-semibold transition-colors" onClick={() => calculatorAction('1')}>1</button>
                  <button className="bg-gray-200 hover:bg-gray-300 p-4 rounded-lg font-semibold transition-colors" onClick={() => calculatorAction('2')}>2</button>
                  <button className="bg-gray-200 hover:bg-gray-300 p-4 rounded-lg font-semibold transition-colors" onClick={() => calculatorAction('3')}>3</button>
                  <button className="bg-orange-500 hover:bg-orange-600 text-white p-4 rounded-lg font-semibold transition-colors" onClick={() => calculatorAction('+')}>+</button>
                  
                  {/* Row 5 */}
                  <button className="bg-gray-200 hover:bg-gray-300 p-4 rounded-lg font-semibold col-span-2 transition-colors" onClick={() => calculatorAction('0')}>0</button>
                  <button className="bg-gray-200 hover:bg-gray-300 p-4 rounded-lg font-semibold transition-colors" onClick={() => calculatorAction('.')}>.</button>
                  <button className="bg-orange-500 hover:bg-orange-600 text-white p-4 rounded-lg font-semibold transition-colors" onClick={() => calculatorAction('=')}>=</button>
                </div>
                
                {/* Quick Actions */}
                <div className="mt-4 space-y-2">
                  <button className="w-full bg-blue-500 text-white p-2 rounded-lg hover:bg-blue-600 transition-colors text-sm">
                    💬 Share Result in Chat
                  </button>
                  <button className="w-full bg-green-500 text-white p-2 rounded-lg hover:bg-green-600 transition-colors text-sm">
                    💰 Split Bill Calculator
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Theme Customizer Modal */}
      {showThemeCustomizer && (
        <ThemeCustomizer
          onClose={() => setShowThemeCustomizer(false)}
          onApplyTheme={(theme) => {
            setAppliedTheme(theme);
            setCurrentTheme(theme.name || theme);
            setShowThemeCustomizer(false);
            // Apply theme styles to the app
            applyThemeStyles(theme);
          }}
          currentTheme={currentTheme}
        />
      )}
      
      {/* Profile Setup Prompt Modal */}
      {showProfilePrompt && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" role="dialog" aria-labelledby="profile-prompt-title" aria-modal="true">
          <div className="bg-white rounded-lg p-6 max-w-md mx-4 shadow-xl">
            <div className="text-center">
              <div className="text-4xl mb-4">👤</div>
              <h3 id="profile-prompt-title" className="text-xl font-bold text-gray-900 mb-2">
                Complete Your Profile
              </h3>
              <p className="text-gray-600 mb-6">
                To access {attemptedTab === 'teams' ? 'Groups' : 'Premium features'}, please complete your profile setup first.
              </p>
              
              <div className="flex space-x-3">
                <button
                  onClick={handleProfilePromptDismiss}
                  className="flex-1 px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                  aria-label="Cancel profile setup"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    setShowProfilePrompt(false);
                    // You can integrate with ProfileSetup component here
                    // For now, we'll just mark as completed
                    onUserUpdate({ ...user, profile_completed: true });
                    handleProfileComplete();
                  }}
                  className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                  aria-label="Start profile setup process"
                >
                  Setup Profile
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