import React, { useState } from 'react';

const Dashboard = ({ user, token, api, onLogout }) => {
  const [activeTab, setActiveTab] = useState('profile');
  
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
                  <h2 className="heading-md mb-6">Your Profile</h2>
                  <div className="space-y-6">
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h3 className="font-semibold text-gray-900 mb-2">Basic Information</h3>
                      <p><strong>Age:</strong> {user?.age || 'Not set'}</p>
                      <p><strong>Location:</strong> {user?.location || 'Not set'}</p>
                      <p><strong>Bio:</strong> {user?.bio || 'Not set'}</p>
                    </div>
                    
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <h3 className="font-semibold text-gray-900 mb-2">Trust Level</h3>
                      <div className="flex items-center space-x-2">
                        <div className="trust-level-indicator trust-level-1">1</div>
                        <p className="text-gray-700">New Member - Building Your Authenticity</p>
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
