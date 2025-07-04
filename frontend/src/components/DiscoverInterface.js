import React, { useState } from 'react';

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

  if (!isPremium) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-purple-50 to-blue-50 p-4">
        <div className="text-center max-w-sm mx-auto">
          <div className="text-4xl mb-4">⭐</div>
          <h2 className="text-xl font-bold text-gray-900 mb-3">
            Discover Authentic Connections
          </h2>
          <p className="text-sm text-gray-600 mb-4">
            Unlock AI-powered compatibility matching and progressive trust building 
            to find genuine, meaningful relationships.
          </p>
          
          <div className="bg-white rounded-xl p-4 shadow-lg border mb-4">
            <h3 className="font-semibold text-gray-900 mb-3 text-sm">Premium Features:</h3>
            <div className="space-y-2 text-left">
              <div className="flex items-center space-x-2">
                <span className="text-green-500 text-sm">✓</span>
                <span className="text-xs text-gray-700">AI Compatibility Matching</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-green-500 text-sm">✓</span>
                <span className="text-xs text-gray-700">5-Layer Trust Progression</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-green-500 text-sm">✓</span>
                <span className="text-xs text-gray-700">Advanced Authenticity Ratings</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-green-500 text-sm">✓</span>
                <span className="text-xs text-gray-700">Anonymous Discovery</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-green-500 text-sm">✓</span>
                <span className="text-xs text-gray-700">Voice & Video Call Progression</span>
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
            Upgrade to Premium
          </button>
          
          <p className="text-xs text-gray-500 mt-3">
            First 50 searches included • Cancel anytime
          </p>
        </div>
        
        {/* Upgrade Modal */}
        {showUpgrade && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999] p-4">
            <div className="bg-white rounded-2xl shadow-2xl max-w-sm w-full p-6 relative">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-bold text-gray-900">Upgrade to Premium</h2>
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
                <div className="text-3xl mb-3">⭐</div>
                <h3 className="text-base font-semibold text-gray-900 mb-2">
                  Unlock Authentic Connections
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  Get access to AI-powered matching and progressive trust building
                </p>
                
                <div className="bg-gradient-to-r from-purple-50 to-blue-50 p-3 rounded-lg mb-4">
                  <div className="text-xl font-bold text-purple-600 mb-1">$9.99/month</div>
                  <p className="text-xs text-purple-700">First 50 searches included</p>
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
                    Start Premium Subscription
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
      {/* Header with Demo Mode */}
      <div className="bg-white border-b border-gray-200 p-3">
        <div className="flex items-center justify-between mb-2">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Discover</h2>
            <p className="text-sm text-gray-600">Find authentic connections</p>
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
      </div>

      {/* Main Content - Single Column for Mobile */}
      <div className="flex-1 overflow-y-auto p-4">
        {/* AI Discovery Section */}
        <div className="bg-white rounded-xl p-4 shadow-sm border mb-4">
          <div className="text-center mb-4">
            <h2 className="text-lg font-bold text-gray-900 mb-2">
              AI-Powered Discovery
            </h2>
            <p className="text-sm text-gray-600">
              Find people who share your values and interests through authentic compatibility
            </p>
          </div>

          <div className="bg-gray-50 rounded-lg p-3 mb-4">
            <h3 className="font-semibold text-gray-900 mb-2 text-sm">🧠 How AI Matching Works</h3>
            <div className="space-y-2 text-xs text-gray-700">
              <div className="flex items-start space-x-2">
                <span className="text-blue-500 mt-0.5 font-medium min-w-[12px]">1.</span>
                <span>Analyze your profile, interests, values, and connection preferences</span>
              </div>
              <div className="flex items-start space-x-2">
                <span className="text-blue-500 mt-0.5 font-medium min-w-[12px]">2.</span>
                <span>Calculate compatibility scores based on personality and goals</span>
              </div>
              <div className="flex items-start space-x-2">
                <span className="text-blue-500 mt-0.5 font-medium min-w-[12px]">3.</span>
                <span>Present anonymous profiles with high compatibility potential</span>
              </div>
              <div className="flex items-start space-x-2">
                <span className="text-blue-500 mt-0.5 font-medium min-w-[12px]">4.</span>
                <span>Facilitate progressive trust building through structured stages</span>
              </div>
            </div>
          </div>

          <div className="text-center">
            <button className="bg-blue-500 text-white px-6 py-2 rounded-full text-sm font-medium hover:bg-blue-600 transition-colors">
              Start AI Discovery
            </button>
            <p className="text-xs text-gray-500 mt-2">
              Your next authentic connection awaits
            </p>
          </div>
        </div>

        {/* Trust Level Progress */}
        <div className="bg-white rounded-xl p-4 shadow-sm border mb-4">
          <h3 className="font-medium text-gray-900 mb-3">Your Trust Journey</h3>
          <div className="space-y-2">
            {[
              { level: 1, title: "Anonymous Discovery", icon: "🔍" },
              { level: 2, title: "Text Chat", icon: "💬" },
              { level: 3, title: "Voice Call", icon: "🎙️" },
              { level: 4, title: "Video Call", icon: "📹" },
              { level: 5, title: "In-Person Meetup", icon: "🤝" }
            ].map(stage => (
              <div 
                key={stage.level}
                className={`flex items-center space-x-3 p-2 rounded-lg text-sm ${
                  (user?.trust_level || 1) >= stage.level 
                    ? 'bg-green-50 border border-green-200' 
                    : 'bg-gray-50 border border-gray-200'
                }`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm ${
                  (user?.trust_level || 1) >= stage.level 
                    ? 'bg-green-100' 
                    : 'bg-gray-100'
                }`}>
                  {(user?.trust_level || 1) >= stage.level ? '✓' : stage.icon}
                </div>
                <div className="flex-1">
                  <p className={`font-medium text-sm ${
                    (user?.trust_level || 1) >= stage.level ? 'text-green-700' : 'text-gray-600'
                  }`}>
                    {stage.title}
                  </p>
                  <p className="text-xs text-gray-500">Level {stage.level}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Authenticity Rating */}
        <div className="bg-white rounded-xl p-4 shadow-sm border mb-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-medium text-gray-900">Authenticity Rating</h3>
            <button
              onClick={fetchAuthenticityDetails}
              disabled={isLoadingAuthenticity}
              className="text-blue-600 hover:text-blue-800 text-sm"
            >
              {isLoadingAuthenticity ? '↻' : '🔄'}
            </button>
          </div>
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-3 rounded-lg">
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-sm">
                  {(user?.authenticity_rating || 0).toFixed(1)}
                </span>
              </div>
              <div className="flex-1">
                <p className="font-medium text-gray-900 text-sm">
                  {(user?.authenticity_rating || 0) < 3 ? 'Getting Started' :
                   (user?.authenticity_rating || 0) < 6 ? 'Building Trust' :
                   (user?.authenticity_rating || 0) < 8 ? 'Trusted Member' :
                   'Highly Authentic'}
                </p>
                <p className="text-xs text-gray-600">
                  {(user?.authenticity_rating || 0).toFixed(1)} / 10.0
                </p>
              </div>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all"
                style={{ width: `${((user?.authenticity_rating || 0) / 10) * 100}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Discovery Preferences */}
        <div className="bg-white rounded-xl p-4 shadow-sm border">
          <h3 className="font-medium text-gray-900 mb-3">Discovery Preferences</h3>
          <div className="space-y-3">
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
            <div>
              <label className="block text-sm text-gray-600 mb-1">Connection Type</label>
              <select className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2">
                <option>Friendship</option>
                <option>Romantic</option>
                <option>Professional</option>
                <option>Any</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DiscoverInterface;