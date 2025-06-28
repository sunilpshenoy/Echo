import React, { useState } from 'react';
import axios from 'axios';

const Dashboard = ({ user, token, api, onLogout }) => {
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
                      <h3 className="font-semibold text-gray-900 mb-4">Trust & Authenticity</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <p className="text-gray-600 text-sm mb-2">Trust Level</p>
                          <div className="flex items-center space-x-3">
                            <div className="trust-level-indicator trust-level-1">{user?.trust_level || 1}</div>
                            <div>
                              <p className="font-medium">New Member</p>
                              <p className="text-gray-600 text-sm">Building Your Authenticity</p>
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
                              <p className="font-medium">Getting Started</p>
                              <p className="text-gray-600 text-sm">Complete your profile to improve</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
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
                  <h2 className="heading-md mb-6">Your Connections</h2>
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
                      <button className="btn-secondary mr-4">
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
    </div>
  );
};

export default Dashboard;
