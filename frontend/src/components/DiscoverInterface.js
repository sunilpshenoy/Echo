import React, { useState, useEffect } from 'react';
import axios from 'axios';
import TrustSystem from './TrustSystem';

const DiscoverInterface = ({ 
  user, 
  token, 
  api, 
  isPremium,
  authenticityDetails,
  fetchAuthenticityDetails,
  isLoadingAuthenticity,
  connections,
  fetchConnections
}) => {
  const [showUpgrade, setShowUpgrade] = useState(false);
  const [activeDiscoverTab, setActiveDiscoverTab] = useState('discovery');

  if (!isPremium) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-purple-50 to-blue-50 p-4">
        <div className="text-center max-w-sm mx-auto">
          <div className="text-4xl mb-4">🔒</div>
          <h2 className="text-xl font-bold text-gray-900 mb-3">
            Safely Discover New Friends
          </h2>
          <p className="text-sm text-gray-600 mb-4">
            Our 5-Layer Trust System helps you discover new people safely, 
            building secure connections with strangers through verified progression.
          </p>
          
          <div className="bg-white rounded-xl p-4 shadow-lg border mb-4">
            <h3 className="font-semibold text-gray-900 mb-3 text-sm">Safe Discovery Features:</h3>
            <div className="space-y-2 text-left">
              <div className="flex items-center space-x-2">
                <span className="text-green-500 text-sm">✓</span>
                <span className="text-xs text-gray-700">5-Layer Trust Progression</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-green-500 text-sm">✓</span>
                <span className="text-xs text-gray-700">AI Compatibility Matching</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-green-500 text-sm">✓</span>
                <span className="text-xs text-gray-700">Anonymous Discovery</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-green-500 text-sm">✓</span>
                <span className="text-xs text-gray-700">Verified User Matching</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-green-500 text-sm">✓</span>
                <span className="text-xs text-gray-700">Safe Meetup Planning</span>
              </div>
            </div>
          </div>

          <button 
            onClick={() => {
              console.log('Upgrade button clicked');
              setShowUpgrade(true);
            }}
            className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-2 rounded-full text-sm font-medium hover:from-purple-700 hover:to-blue-700 transition-all transform hover:scale-105"
          >
            Upgrade for Safe Discovery
          </button>
          
          <p className="text-xs text-gray-500 mt-3">
            Meet new people safely • Cancel anytime
          </p>
        </div>
        
        {/* Upgrade Modal */}
        {showUpgrade && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999] p-4">
            <div className="bg-white rounded-2xl shadow-2xl max-w-sm w-full p-6 relative">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-bold text-gray-900">Safe Discovery Premium</h2>
                <button
                  onClick={() => {
                    console.log('Closing upgrade modal');
                    setShowUpgrade(false);
                  }}
                  className="text-gray-500 hover:text-gray-700 text-xl"
                >
                  ✕
                </button>
              </div>
              
              <div className="text-center">
                <div className="text-3xl mb-3">🔒</div>
                <h3 className="text-base font-semibold text-gray-900 mb-2">
                  Discover New Friends Safely
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  Get access to our 5-Layer Trust System for meeting new people with confidence
                </p>
                
                <div className="bg-gradient-to-r from-purple-50 to-blue-50 p-3 rounded-lg mb-4">
                  <div className="text-xl font-bold text-purple-600 mb-1">$9.99/month</div>
                  <p className="text-xs text-purple-700">Safe discovery with trust verification</p>
                </div>
                
                <div className="space-y-2">
                  <button 
                    onClick={() => {
                      // TODO: Implement payment processing
                      alert('Payment processing will be implemented soon! 💳');
                      setShowUpgrade(false);
                    }}
                    className="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white py-2 rounded-lg text-sm font-medium hover:from-purple-700 hover:to-blue-700"
                  >
                    Start Safe Discovery
                  </button>
                  <button
                    onClick={() => {
                      // Enable demo premium mode for testing
                      if (window.confirm('Enable Premium Demo Mode? This is for testing purposes only.')) {
                        localStorage.setItem('demo_premium', 'true');
                        setShowUpgrade(false);
                        // Trigger a state update instead of page reload
                        window.dispatchEvent(new Event('storage'));
                      }
                    }}
                    className="w-full bg-gradient-to-r from-yellow-500 to-orange-500 text-white py-2 rounded-lg text-sm font-medium hover:from-yellow-600 hover:to-orange-600"
                  >
                    🚀 Enable Demo Mode (Testing)
                  </button>
                  <button
                    onClick={() => setShowUpgrade(false)}
                    className="w-full bg-gray-100 text-gray-700 py-2 rounded-lg text-sm hover:bg-gray-200"
                  >
                    Maybe Later
                  </button>
                </div>
                
                <p className="text-xs text-gray-500 mt-3">
                  Cancel anytime • No hidden fees
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-gray-50">
      {/* Header with Demo Mode and Navigation */}
      <div className="bg-white border-b border-gray-200 p-3">
        <div className="flex items-center justify-between mb-2">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Discover New Friends</h2>
            <p className="text-sm text-gray-600">Find secure connections safely</p>
          </div>
        </div>
        {localStorage.getItem('demo_premium') === 'true' && (
          <button
            onClick={() => {
              if (window.confirm('Disable Demo Premium Mode?')) {
                localStorage.removeItem('demo_premium');
                window.dispatchEvent(new Event('storage'));
              }
            }}
            className="bg-yellow-100 text-yellow-700 px-3 py-1 rounded-full text-xs font-medium hover:bg-yellow-200 border border-yellow-200"
            title="You are in Demo Premium Mode"
          >
            🚀 Demo Mode • Click to Disable
          </button>
        )}

        {/* Discovery Sub-Tabs */}
        <div className="flex mt-3 border-b">
          {[
            { id: 'discovery', label: 'Find People', icon: '🔍' },
            { id: 'trust', label: 'Safety System', icon: '🔒' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveDiscoverTab(tab.id)}
              className={`flex items-center space-x-2 px-4 py-2 text-sm font-medium border-b-2 transition-all ${
                activeDiscoverTab === tab.id
                  ? 'border-blue-500 text-blue-600 bg-blue-50'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
              }`}
            >
              <span className="text-base">{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Content based on active sub-tab */}
      {activeDiscoverTab === 'discovery' && (
        <div className="flex-1 overflow-y-auto p-4">
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-6">
              <h2 className="text-xl font-bold text-gray-900 mb-2">
                AI-Powered Safe Discovery
              </h2>
              <p className="text-sm text-gray-600">
                Find new friends through our trust-based matching system
              </p>
            </div>

            <div className="bg-white rounded-xl p-4 shadow-sm border mb-4">
              <h3 className="font-semibold text-gray-900 mb-3 text-sm">🔒 How Safe Discovery Works</h3>
              <div className="space-y-2 text-xs text-gray-700">
                <div className="flex items-start space-x-2">
                  <span className="text-blue-500 mt-0.5 font-medium min-w-[12px]">1.</span>
                  <span>Anonymous matching based on interests and values (no personal info shared)</span>
                </div>
                <div className="flex items-start space-x-2">
                  <span className="text-blue-500 mt-0.5 font-medium min-w-[12px]">2.</span>
                  <span>Start with text chat only - no calls or meetups until trust builds</span>
                </div>
                <div className="flex items-start space-x-2">
                  <span className="text-blue-500 mt-0.5 font-medium min-w-[12px]">3.</span>
                  <span>Gradual progression through 5 trust levels as you get to know each other</span>
                </div>
                <div className="flex items-start space-x-2">
                  <span className="text-blue-500 mt-0.5 font-medium min-w-[12px]">4.</span>
                  <span>Only meet in person after building trust through conversations and calls</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl p-4 shadow-sm border mb-4">
              <h3 className="font-semibold text-gray-900 mb-3 text-sm">🎯 Discovery Preferences</h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm text-gray-600 mb-1">Looking for</label>
                  <select className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2">
                    <option>New friends</option>
                    <option>Activity partners</option>
                    <option>Study buddies</option>
                    <option>Travel companions</option>
                    <option>Professional connections</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">Age Range</label>
                  <select className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2">
                    <option>18-25</option>
                    <option>26-35</option>
                    <option>36-45</option>
                    <option>46+</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">Location</label>
                  <select className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2">
                    <option>Within 10 miles</option>
                    <option>Within 25 miles</option>
                    <option>Within 50 miles</option>
                    <option>Anywhere</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="text-center">
              <button className="bg-blue-500 text-white px-6 py-2 rounded-full text-sm font-medium hover:bg-blue-600 transition-colors">
                Start Safe Discovery
              </button>
              <p className="text-xs text-gray-500 mt-2">
                All matches start with anonymous chat for your safety
              </p>
            </div>
          </div>
        </div>
      )}

      {activeDiscoverTab === 'trust' && (
        <TrustSystem 
          user={user}
          token={token}
          api={api}
        />
      )}
    </div>
  );
};

export default DiscoverInterface;