import React, { useState } from 'react';
import axios from 'axios';

const Dashboard = ({ user, token, api, onLogout, onUserUpdate }) => {
  const [activeTab, setActiveTab] = useState('profile');
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
  
  // Connection management functions
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
      await fetchConnections(); // Refresh connections
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
      // Prepare data for API
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
      
      // Refresh the page to get updated user data
      setTimeout(() => {
        window.location.reload();
      }, 1500);
      
    } catch (error) {
      setUpdateMessage('Failed to update profile. Please try again.');
      console.error('Profile update error:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="min-h-screen">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-trust-gradient rounded-full flex items-center justify-center">
                <span className="text-white font-bold">
                  {user?.username?.[0]?.toUpperCase() || '?'}
                </span>
              </div>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">
                  Welcome, {user?.display_name || user?.username}
                </h1>
                <p className="text-subtle text-sm">Ready for authentic connections</p>
              </div>
            </div>
            
            <button
              onClick={onLogout}
              className="btn-secondary"
            >
              Sign Out
            </button>
          </div>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Sidebar Navigation */}
          <div className="lg:col-span-1">
            <div className="card">
              <h2 className="heading-md mb-4">Your Journey</h2>
              <nav className="space-y-2">
                {[
                  { id: 'profile', label: 'Profile', icon: '👤' },
                  { id: 'authenticity', label: 'Authenticity', icon: '⭐' },
                  { id: 'discover', label: 'Discover People', icon: '🔍' },
                  { id: 'connections', label: 'Connections', icon: '💫' },
                  { id: 'settings', label: 'Settings', icon: '⚙️' }
                ].map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full text-left p-3 rounded-lg transition-all ${
                      activeTab === tab.id
                        ? 'bg-trust-gradient text-white'
                        : 'text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <span className="mr-3">{tab.icon}</span>
                    {tab.label}
                  </button>
                ))}
              </nav>
            </div>
          </div>
          
          {/* Main Content Area */}
          <div className="lg:col-span-2">
            <div className="card">
              {activeTab === 'profile' && (
                <div>
                  <div className="flex justify-between items-center mb-6">
                    <h2 className="heading-md">Your Profile</h2>
                    <button
                      onClick={() => setIsEditingProfile(true)}
                      className="btn-primary"
                    >
                      ✏️ Edit Profile
                    </button>
                  </div>
                  
                  {updateMessage && (
                    <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-6">
                      {updateMessage}
                    </div>
                  )}
                  
                  <div className="space-y-6">
                    {/* Basic Information */}
                    <div className="bg-gray-50 p-6 rounded-lg">
                      <h3 className="font-semibold text-gray-900 mb-4">Basic Information</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <p className="text-gray-600 text-sm">Display Name</p>
                          <p className="font-medium">{user?.display_name || user?.username || 'Not set'}</p>
                        </div>
                        <div>
                          <p className="text-gray-600 text-sm">Age</p>
                          <p className="font-medium">{user?.age || 'Not set'}</p>
                        </div>
                        <div>
                          <p className="text-gray-600 text-sm">Gender</p>
                          <p className="font-medium">{user?.gender || 'Not set'}</p>
                        </div>
                        <div>
                          <p className="text-gray-600 text-sm">Location</p>
                          <p className="font-medium">{user?.location || 'Not set'}</p>
                        </div>
                      </div>
                      <div className="mt-4">
                        <p className="text-gray-600 text-sm">Bio</p>
                        <p className="font-medium">{user?.bio || 'Tell us about yourself...'}</p>
                      </div>
                    </div>
                    
                    {/* Interests & Values */}
                    <div className="bg-purple-50 p-6 rounded-lg">
                      <h3 className="font-semibold text-gray-900 mb-4">Interests & Values</h3>
                      <div className="space-y-3">
                        <div>
                          <p className="text-gray-600 text-sm">Interests</p>
                          <div className="flex flex-wrap gap-2 mt-2">
                            {user?.interests?.length > 0 ? user.interests.map((interest, index) => (
                              <span key={index} className="bg-purple-100 text-purple-700 px-3 py-1 rounded-full text-sm">
                                {interest}
                              </span>
                            )) : <p className="text-gray-500 italic">No interests added yet</p>}
                          </div>
                        </div>
                        <div>
                          <p className="text-gray-600 text-sm">Values</p>
                          <div className="flex flex-wrap gap-2 mt-2">
                            {user?.values?.length > 0 ? user.values.map((value, index) => (
                              <span key={index} className="bg-indigo-100 text-indigo-700 px-3 py-1 rounded-full text-sm">
                                {value}
                              </span>
                            )) : <p className="text-gray-500 italic">No values added yet</p>}
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Connection Preferences */}
                    <div className="bg-green-50 p-6 rounded-lg">
                      <h3 className="font-semibold text-gray-900 mb-4">Connection Preferences</h3>
                      <div className="space-y-3">
                        <div>
                          <p className="text-gray-600 text-sm">Current Mood</p>
                          <p className="font-medium">{user?.current_mood || 'Not shared'}</p>
                        </div>
                        <div>
                          <p className="text-gray-600 text-sm">Seeking</p>
                          <p className="font-medium">{user?.seeking_type || 'Not specified'}</p>
                        </div>
                        <div>
                          <p className="text-gray-600 text-sm">Connection Purpose</p>
                          <p className="font-medium">{user?.connection_purpose || 'Not specified'}</p>
                        </div>
                      </div>
                    </div>
                    
                    {/* Trust & Authenticity */}
                    <div className="bg-blue-50 p-6 rounded-lg">
                      <h3 className="font-semibold text-gray-900 mb-6">Trust & Authenticity</h3>
                      
                      {/* 5-Layer Progressive Trust System */}
                      <div className="mb-8">
                        <h4 className="font-medium text-gray-900 mb-4">5-Layer Progressive Trust System</h4>
                        <div className="space-y-4">
                          {[
                            {
                              level: 1,
                              title: "Anonymous Discovery",
                              description: "Find compatible people through AI matching",
                              icon: "🔍",
                              status: (user?.trust_level || 1) >= 1 ? "unlocked" : "locked"
                            },
                            {
                              level: 2,
                              title: "Text Chat",
                              description: "Start conversations with matched users",
                              icon: "💬",
                              status: (user?.trust_level || 1) >= 2 ? "unlocked" : "locked"
                            },
                            {
                              level: 3,
                              title: "Voice Call",
                              description: "Hear each other's voices",
                              icon: "🎙️",
                              status: (user?.trust_level || 1) >= 3 ? "unlocked" : "locked"
                            },
                            {
                              level: 4,
                              title: "Video Call",
                              description: "See each other face-to-face",
                              icon: "📹",
                              status: (user?.trust_level || 1) >= 4 ? "unlocked" : "locked"
                            },
                            {
                              level: 5,
                              title: "In-Person Meetup",
                              description: "Meet in real life",
                              icon: "🤝",
                              status: (user?.trust_level || 1) >= 5 ? "unlocked" : "locked"
                            }
                          ].map((layer, index) => (
                            <div
                              key={layer.level}
                              className={`flex items-center space-x-4 p-4 rounded-lg border-2 transition-all ${
                                layer.status === "unlocked"
                                  ? "border-green-200 bg-green-50"
                                  : (user?.trust_level || 1) === layer.level - 1
                                  ? "border-yellow-200 bg-yellow-50"
                                  : "border-gray-200 bg-gray-50"
                              }`}
                            >
                              <div className={`trust-level-indicator ${
                                layer.status === "unlocked" 
                                  ? `trust-level-${layer.level}` 
                                  : "bg-gray-300"
                              }`}>
                                {layer.status === "unlocked" ? layer.icon : "🔒"}
                              </div>
                              <div className="flex-1">
                                <div className="flex items-center space-x-2">
                                  <h5 className="font-medium text-gray-900">
                                    Level {layer.level}: {layer.title}
                                  </h5>
                                  {layer.status === "unlocked" && (
                                    <span className="bg-green-100 text-green-700 px-2 py-1 rounded-full text-xs font-medium">
                                      Unlocked
                                    </span>
                                  )}
                                  {(user?.trust_level || 1) === layer.level - 1 && layer.status === "locked" && (
                                    <span className="bg-yellow-100 text-yellow-700 px-2 py-1 rounded-full text-xs font-medium">
                                      Next Level
                                    </span>
                                  )}
                                </div>
                                <p className="text-gray-600 text-sm">{layer.description}</p>
                                {layer.status === "locked" && (user?.trust_level || 1) === layer.level - 1 && (
                                  <p className="text-yellow-700 text-xs mt-1 font-medium">
                                    Complete more profile sections and build authentic connections to unlock
                                  </p>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                      
                      {/* Current Progress */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <p className="text-gray-600 text-sm mb-2">Current Trust Level</p>
                          <div className="flex items-center space-x-3">
                            <div className={`trust-level-indicator trust-level-${user?.trust_level || 1}`}>
                              {user?.trust_level || 1}
                            </div>
                            <div>
                              <p className="font-medium">
                                {user?.trust_level === 1 ? "Anonymous Discovery" :
                                 user?.trust_level === 2 ? "Text Chat Unlocked" :
                                 user?.trust_level === 3 ? "Voice Call Unlocked" :
                                 user?.trust_level === 4 ? "Video Call Unlocked" :
                                 user?.trust_level === 5 ? "Full Trust Achieved" :
                                 "New Member"}
                              </p>
                              <p className="text-gray-600 text-sm">
                                {user?.trust_level === 1 ? "Start by discovering compatible people" :
                                 user?.trust_level === 2 ? "You can now chat with connections" :
                                 user?.trust_level === 3 ? "Voice calls are now available" :
                                 user?.trust_level === 4 ? "Video calls are now available" :
                                 user?.trust_level === 5 ? "All features unlocked" :
                                 "Building Your Authenticity"}
                              </p>
                            </div>
                          </div>
                        </div>
                        <div>
                          <p className="text-gray-600 text-sm mb-2">Authenticity Rating</p>
                          <div className="flex items-center space-x-3">
                            <div className="w-16 h-16 bg-trust-gradient rounded-full flex items-center justify-center">
                              <span className="text-white font-bold text-lg">
                                {(user?.authenticity_rating || 0).toFixed(1)}
                              </span>
                            </div>
                            <div>
                              <p className="font-medium">
                                {(user?.authenticity_rating || 0) < 3 ? "Getting Started" :
                                 (user?.authenticity_rating || 0) < 6 ? "Building Trust" :
                                 (user?.authenticity_rating || 0) < 8 ? "Trusted Member" :
                                 "Highly Authentic"}
                              </p>
                              <p className="text-gray-600 text-sm">
                                {(user?.authenticity_rating || 0) < 3 ? "Complete your profile to improve" :
                                 (user?.authenticity_rating || 0) < 6 ? "Keep engaging authentically" :
                                 (user?.authenticity_rating || 0) < 8 ? "Well-established member" :
                                 "Exemplary community member"}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      {/* Progress Tips */}
                      <div className="mt-6 p-4 bg-indigo-50 rounded-lg border border-indigo-200">
                        <h5 className="font-medium text-indigo-900 mb-2">💡 How to Progress</h5>
                        <ul className="text-indigo-800 text-sm space-y-1">
                          <li>• Complete all sections of your profile</li>
                          <li>• Engage in meaningful conversations</li>
                          <li>• Be authentic and genuine in your interactions</li>
                          <li>• Take time to build real connections</li>
                          <li>• Both users must agree to progress to the next level</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              {activeTab === 'authenticity' && (
                <div>
                  <div className="flex justify-between items-center mb-6">
                    <h2 className="heading-md">Authenticity Details</h2>
                    <button
                      onClick={() => {
                        fetchAuthenticityDetails();
                        updateAuthenticityRating();
                      }}
                      disabled={isLoadingAuthenticity}
                      className="btn-primary"
                    >
                      {isLoadingAuthenticity ? (
                        <div className="flex items-center">
                          <div className="loading-spinner w-5 h-5 mr-2"></div>
                          Updating...
                        </div>
                      ) : (
                        '🔄 Refresh Rating'
                      )}
                    </button>
                  </div>
                  
                  {updateMessage && (
                    <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-6">
                      {updateMessage}
                    </div>
                  )}
                  
                  {authenticityDetails ? (
                    <div className="space-y-6">
                      {/* Overall Rating */}
                      <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-lg border border-blue-200">
                        <div className="flex items-center justify-between mb-4">
                          <h3 className="font-semibold text-gray-900">Overall Authenticity Rating</h3>
                          <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm font-medium">
                            {authenticityDetails.level}
                          </span>
                        </div>
                        <div className="flex items-center space-x-6">
                          <div className="w-24 h-24 bg-trust-gradient rounded-full flex items-center justify-center">
                            <span className="text-white font-bold text-2xl">
                              {authenticityDetails.total_rating}
                            </span>
                          </div>
                          <div className="flex-1">
                            <div className="flex justify-between text-sm text-gray-600 mb-2">
                              <span>Progress</span>
                              <span>{authenticityDetails.total_rating} / {authenticityDetails.max_rating}</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-3">
                              <div 
                                className="bg-trust-gradient h-3 rounded-full transition-all duration-500"
                                style={{ width: `${(authenticityDetails.total_rating / authenticityDetails.max_rating) * 100}%` }}
                              ></div>
                            </div>
                            <p className="text-gray-600 text-sm mt-2">
                              Next milestone: {authenticityDetails.next_milestone} points
                            </p>
                          </div>
                        </div>
                      </div>
                      
                      {/* Factor Breakdown */}
                      <div className="bg-white p-6 rounded-lg border">
                        <h3 className="font-semibold text-gray-900 mb-4">Rating Breakdown</h3>
                        <div className="space-y-4">
                          {Object.entries(authenticityDetails.factors).map(([key, factor]) => (
                            <div key={key} className="border-l-4 border-blue-200 pl-4">
                              <div className="flex justify-between items-center mb-2">
                                <h4 className="font-medium text-gray-900 capitalize">
                                  {key.replace('_', ' ')}
                                </h4>
                                <span className="text-sm font-medium text-gray-600">
                                  {factor.score} / {factor.max_score}
                                </span>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                                <div 
                                  className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                                  style={{ width: `${(factor.score / factor.max_score) * 100}%` }}
                                ></div>
                              </div>
                              <p className="text-gray-600 text-sm mb-2">{factor.description}</p>
                              {factor.tips && factor.tips.length > 0 && (
                                <details className="mt-2">
                                  <summary className="text-blue-600 cursor-pointer text-sm hover:text-blue-800">
                                    💡 Tips to improve
                                  </summary>
                                  <ul className="mt-2 text-sm text-gray-600 list-disc list-inside space-y-1">
                                    {factor.tips.map((tip, index) => (
                                      <li key={index}>{tip}</li>
                                    ))}
                                  </ul>
                                </details>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                      
                      {/* Improvement Guide */}
                      <div className="bg-yellow-50 p-6 rounded-lg border border-yellow-200">
                        <h3 className="font-semibold text-gray-900 mb-4">🌟 How to Improve Your Rating</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                          <div>
                            <h4 className="font-medium text-gray-900 mb-2">Quick Wins:</h4>
                            <ul className="text-gray-700 space-y-1">
                              <li>• Complete all profile sections</li>
                              <li>• Add detailed bio and interests</li>
                              <li>• Upload a profile photo</li>
                            </ul>
                          </div>
                          <div>
                            <h4 className="font-medium text-gray-900 mb-2">Long-term Growth:</h4>
                            <ul className="text-gray-700 space-y-1">
                              <li>• Engage in meaningful conversations</li>
                              <li>• Build genuine connections</li>
                              <li>• Be consistent and authentic</li>
                            </ul>
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <div className="text-6xl mb-4">⭐</div>
                      <h3 className="text-xl font-semibold text-gray-900 mb-2">
                        Authenticity Rating
                      </h3>
                      <p className="text-subtle mb-4">
                        Click "Refresh Rating" to see your detailed authenticity breakdown.
                      </p>
                      <button
                        onClick={fetchAuthenticityDetails}
                        className="btn-primary"
                      >
                        View My Rating
                      </button>
                    </div>
                  )}
                </div>
              )}
              
              {activeTab === 'authenticity' && (
                <div>
                  <div className="flex justify-between items-center mb-6">
                    <h2 className="heading-md">Authenticity Details</h2>
                    <button
                      onClick={() => {
                        fetchAuthenticityDetails();
                        updateAuthenticityRating();
                      }}
                      disabled={isLoadingAuthenticity}
                      className="btn-primary"
                    >
                      {isLoadingAuthenticity ? (
                        <div className="flex items-center">
                          <div className="loading-spinner w-5 h-5 mr-2"></div>
                          Updating...
                        </div>
                      ) : (
                        '🔄 Refresh Rating'
                      )}
                    </button>
                  </div>
                  
                  {updateMessage && (
                    <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-6">
                      {updateMessage}
                    </div>
                  )}
                  
                  {authenticityDetails ? (
                    <div className="space-y-6">
                      {/* Overall Rating */}
                      <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-lg border border-blue-200">
                        <div className="flex items-center justify-between mb-4">
                          <h3 className="font-semibold text-gray-900">Overall Authenticity Rating</h3>
                          <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm font-medium">
                            {authenticityDetails.level}
                          </span>
                        </div>
                        <div className="flex items-center space-x-6">
                          <div className="w-24 h-24 bg-trust-gradient rounded-full flex items-center justify-center">
                            <span className="text-white font-bold text-2xl">
                              {authenticityDetails.total_rating}
                            </span>
                          </div>
                          <div className="flex-1">
                            <div className="flex justify-between text-sm text-gray-600 mb-2">
                              <span>Progress</span>
                              <span>{authenticityDetails.total_rating} / {authenticityDetails.max_rating}</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-3">
                              <div 
                                className="bg-trust-gradient h-3 rounded-full transition-all duration-500"
                                style={{ width: `${(authenticityDetails.total_rating / authenticityDetails.max_rating) * 100}%` }}
                              ></div>
                            </div>
                            <p className="text-gray-600 text-sm mt-2">
                              Next milestone: {authenticityDetails.next_milestone} points
                            </p>
                          </div>
                        </div>
                      </div>
                      
                      {/* Factor Breakdown */}
                      <div className="bg-white p-6 rounded-lg border">
                        <h3 className="font-semibold text-gray-900 mb-4">Rating Breakdown</h3>
                        <div className="space-y-4">
                          {Object.entries(authenticityDetails.factors).map(([key, factor]) => (
                            <div key={key} className="border-l-4 border-blue-200 pl-4">
                              <div className="flex justify-between items-center mb-2">
                                <h4 className="font-medium text-gray-900 capitalize">
                                  {key.replace('_', ' ')}
                                </h4>
                                <span className="text-sm font-medium text-gray-600">
                                  {factor.score} / {factor.max_score}
                                </span>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                                <div 
                                  className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                                  style={{ width: `${(factor.score / factor.max_score) * 100}%` }}
                                ></div>
                              </div>
                              <p className="text-gray-600 text-sm mb-2">{factor.description}</p>
                              {factor.tips && factor.tips.length > 0 && (
                                <details className="mt-2">
                                  <summary className="text-blue-600 cursor-pointer text-sm hover:text-blue-800">
                                    💡 Tips to improve
                                  </summary>
                                  <ul className="mt-2 text-sm text-gray-600 list-disc list-inside space-y-1">
                                    {factor.tips.map((tip, index) => (
                                      <li key={index}>{tip}</li>
                                    ))}
                                  </ul>
                                </details>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                      
                      {/* Improvement Guide */}
                      <div className="bg-yellow-50 p-6 rounded-lg border border-yellow-200">
                        <h3 className="font-semibold text-gray-900 mb-4">🌟 How to Improve Your Rating</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                          <div>
                            <h4 className="font-medium text-gray-900 mb-2">Quick Wins:</h4>
                            <ul className="text-gray-700 space-y-1">
                              <li>• Complete all profile sections</li>
                              <li>• Add detailed bio and interests</li>
                              <li>• Upload a profile photo</li>
                            </ul>
                          </div>
                          <div>
                            <h4 className="font-medium text-gray-900 mb-2">Long-term Growth:</h4>
                            <ul className="text-gray-700 space-y-1">
                              <li>• Engage in meaningful conversations</li>
                              <li>• Build genuine connections</li>
                              <li>• Be consistent and authentic</li>
                            </ul>
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <div className="text-6xl mb-4">⭐</div>
                      <h3 className="text-xl font-semibold text-gray-900 mb-2">
                        Authenticity Rating
                      </h3>
                      <p className="text-subtle mb-4">
                        Click "Refresh Rating" to see your detailed authenticity breakdown.
                      </p>
                      <button
                        onClick={fetchAuthenticityDetails}
                        className="btn-primary"
                      >
                        View My Rating
                      </button>
                    </div>
                  )}
                </div>
              )}
              
              {activeTab === 'discover' && (
                <div>
                  <h2 className="heading-md mb-6">Discover Authentic People</h2>
                  <div className="text-center py-12">
                    <div className="text-6xl mb-4">🚧</div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">
                      Coming Soon
                    </h3>
                    <p className="text-subtle">
                      We're building the AI-powered matching system that will connect you with people who truly understand you.
                    </p>
                  </div>
                </div>
              )}
              
              {activeTab === 'connections' && (
                <div>
                  <div className="flex justify-between items-center mb-6">
                    <h2 className="heading-md">Your Connections</h2>
                    <button
                      onClick={fetchConnections}
                      disabled={isLoadingConnections}
                      className="btn-secondary"
                    >
                      {isLoadingConnections ? (
                        <div className="flex items-center">
                          <div className="loading-spinner w-4 h-4 mr-2"></div>
                          Loading...
                        </div>
                      ) : (
                        '🔄 Refresh'
                      )}
                    </button>
                  </div>
                  
                  {updateMessage && (
                    <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-6">
                      {updateMessage}
                    </div>
                  )}
                  
                  {/* Connection Status Tabs */}
                  <div className="flex space-x-4 mb-6">
                    {['all', 'connected', 'pending'].map(status => (
                      <button
                        key={status}
                        onClick={() => setConnectionFilter(status)}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                          connectionFilter === status
                            ? 'bg-trust-gradient text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        {status.charAt(0).toUpperCase() + status.slice(1)}
                        {connections.filter(c => status === 'all' || c.status === status).length > 0 && (
                          <span className="ml-2 bg-white bg-opacity-30 px-2 py-1 rounded-full text-xs">
                            {connections.filter(c => status === 'all' || c.status === status).length}
                          </span>
                        )}
                      </button>
                    ))}
                  </div>
                  
                  {connections && connections.length > 0 ? (
                    <div className="space-y-4">
                      {connections
                        .filter(connection => connectionFilter === 'all' || connection.status === connectionFilter)
                        .map(connection => (
                        <div key={connection.connection_id} className="bg-white p-6 rounded-lg border hover:border-blue-200 transition-all">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-4">
                              <div className="w-12 h-12 bg-trust-gradient rounded-full flex items-center justify-center">
                                <span className="text-white font-bold">
                                  {connection.other_user?.display_name?.[0]?.toUpperCase() || 
                                   connection.other_user?.username?.[0]?.toUpperCase() || '?'}
                                </span>
                              </div>
                              <div>
                                <h3 className="font-semibold text-gray-900">
                                  {connection.other_user?.display_name || connection.other_user?.username || 'Unknown User'}
                                </h3>
                                <p className="text-gray-600 text-sm">
                                  {connection.other_user?.status_message || 'No status message'}
                                </p>
                                <div className="flex items-center space-x-2 mt-1">
                                  <span className={`w-2 h-2 rounded-full ${
                                    connection.other_user?.is_online ? 'bg-green-400' : 'bg-gray-400'
                                  }`}></span>
                                  <span className="text-xs text-gray-500">
                                    {connection.other_user?.is_online ? 'Online' : 'Offline'}
                                  </span>
                                  <span className="text-xs text-gray-400">•</span>
                                  <span className="text-xs text-gray-500">
                                    Authenticity: {(connection.other_user?.authenticity_rating || 0).toFixed(1)}
                                  </span>
                                </div>
                              </div>
                            </div>
                            
                            <div className="flex items-center space-x-4">
                              {/* Connection Status */}
                              <div className="text-center">
                                <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                                  connection.status === 'connected' 
                                    ? 'bg-green-100 text-green-700'
                                    : connection.status === 'pending'
                                    ? 'bg-yellow-100 text-yellow-700'
                                    : 'bg-gray-100 text-gray-700'
                                }`}>
                                  {connection.status === 'connected' ? 'Connected' :
                                   connection.status === 'pending' ? 'Pending' : connection.status}
                                </span>
                                {connection.status === 'connected' && (
                                  <p className="text-xs text-gray-500 mt-1">
                                    Since {new Date(connection.connected_at).toLocaleDateString()}
                                  </p>
                                )}
                              </div>
                              
                              {/* Trust Level Indicator */}
                              {connection.status === 'connected' && (
                                <div className="text-center">
                                  <div className={`trust-level-indicator trust-level-${connection.trust_level || 1} mx-auto`}>
                                    {connection.trust_level || 1}
                                  </div>
                                  <p className="text-xs text-gray-500 mt-1">
                                    {[
                                      'Anonymous',
                                      'Chat',
                                      'Voice',
                                      'Video',
                                      'Meetup'
                                    ][connection.trust_level - 1] || 'Unknown'}
                                  </p>
                                </div>
                              )}
                              
                              {/* Action Buttons */}
                              <div className="flex space-x-2">
                                {connection.status === 'pending' && 
                                 connection.connected_user_id === user?.user_id && (
                                  <>
                                    <button
                                      onClick={() => respondToConnection(connection.connection_id, 'accept')}
                                      className="bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600"
                                    >
                                      Accept
                                    </button>
                                    <button
                                      onClick={() => respondToConnection(connection.connection_id, 'decline')}
                                      className="bg-red-500 text-white px-3 py-1 rounded text-sm hover:bg-red-600"
                                    >
                                      Decline
                                    </button>
                                  </>
                                )}
                                
                                {connection.status === 'connected' && (
                                  <button
                                    onClick={() => setSelectedConnection(connection)}
                                    className="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600"
                                  >
                                    Manage
                                  </button>
                                )}
                              </div>
                            </div>
                          </div>
                          
                          {/* Connection Message */}
                          {connection.message && (
                            <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                              <p className="text-gray-700 text-sm italic">"{connection.message}"</p>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <div className="text-6xl mb-4">💫</div>
                      <h3 className="text-xl font-semibold text-gray-900 mb-2">
                        No Connections Yet
                      </h3>
                      <p className="text-subtle mb-4">
                        Start discovering people and build your first authentic connection.
                      </p>
                      <button 
                        onClick={() => setActiveTab('discover')}
                        className="btn-primary"
                      >
                        Start Discovering
                      </button>
                    </div>
                  )}
                </div>
              )}
              
              {activeTab === 'settings' && (
                <div>
                  <h2 className="heading-md mb-6">Settings</h2>
                  <div className="space-y-6">
                    <div className="border-b pb-6">
                      <h3 className="font-semibold text-gray-900 mb-4">Privacy & Safety</h3>
                      <div className="space-y-3">
                        <label className="flex items-center">
                          <input type="checkbox" className="mr-3" defaultChecked />
                          <span>Allow others to find me</span>
                        </label>
                        <label className="flex items-center">
                          <input type="checkbox" className="mr-3" defaultChecked />
                          <span>Show my location to matches</span>
                        </label>
                        <label className="flex items-center">
                          <input type="checkbox" className="mr-3" defaultChecked />
                          <span>Send me connection suggestions</span>
                        </label>
                      </div>
                    </div>
                    
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-4">Account</h3>
                      <button 
                        onClick={() => setIsEditingProfile(true)}
                        className="btn-secondary mr-4"
                      >
                        Edit Profile
                      </button>
                      <button className="text-red-600 hover:text-red-800">
                        Delete Account
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      
      {/* Profile Editing Modal */}
      {isEditingProfile && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b px-6 py-4 rounded-t-2xl">
              <div className="flex justify-between items-center">
                <h2 className="heading-md">Edit Your Profile</h2>
                <button
                  onClick={() => setIsEditingProfile(false)}
                  className="text-gray-500 hover:text-gray-700 text-2xl"
                >
                  ✕
                </button>
              </div>
            </div>
            
            <div className="p-6 space-y-8">
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
                      className="input-field"
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
                      className="input-field"
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
                      className="input-field"
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
                      className="input-field"
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
                    className="input-field h-24"
                    placeholder="Tell others about yourself, your passions, what makes you unique..."
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
                      className="input-field"
                      placeholder="e.g., photography, hiking, cooking, philosophy, music"
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
                      className="input-field"
                      placeholder="e.g., honesty, creativity, kindness, adventure, growth"
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
                      Current Mood & Why
                    </label>
                    <textarea
                      value={editProfileData.current_mood}
                      onChange={(e) => handleEditProfileChange('current_mood', e.target.value)}
                      className="input-field h-20"
                      placeholder="How are you feeling today and what's influencing that mood?"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      What are you seeking?
                    </label>
                    <select
                      value={editProfileData.seeking_type}
                      onChange={(e) => handleEditProfileChange('seeking_type', e.target.value)}
                      className="input-field"
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
                      className="input-field h-20"
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
                  className="btn-secondary"
                  disabled={isLoading}
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveProfile}
                  disabled={isLoading}
                  className="btn-primary"
                >
                  {isLoading ? (
                    <div className="flex items-center">
                      <div className="loading-spinner w-5 h-5 mr-2"></div>
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
    </div>
  );
};

export default Dashboard;
