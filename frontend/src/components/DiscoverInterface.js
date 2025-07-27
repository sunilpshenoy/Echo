import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
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
  const { t } = useTranslation();
  const [showUpgrade, setShowUpgrade] = useState(false);
  const [activeDiscoverTab, setActiveDiscoverTab] = useState('discovery');
  
  // Check if profile is complete for premium features
  const isProfileComplete = user && (
    user.profile_completed || 
    (user.display_name && user.age && user.location)
  );

  if (!isPremium) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-purple-50 to-blue-50 p-4">
        <div className="text-center max-w-sm mx-auto">
          <div className="text-4xl mb-4">🔒</div>
          <h2 className="text-xl font-bold text-gray-900 mb-3">
            {t('premium.title')}
          </h2>
          <p className="text-sm text-gray-600 mb-4">
            {t('premium.subtitle')}
          </p>
          
          <div className="bg-white rounded-xl p-4 shadow-lg border mb-4">
            <h3 className="font-semibold text-gray-900 mb-3 text-sm">{t('premium.safeDiscoveryFeatures')}</h3>
            <div className="space-y-2 text-left">
              <div className="flex items-center space-x-2">
                <span className="text-green-500 text-sm">✓</span>
                <span className="text-xs text-gray-700">{t('premium.fiveLayerTrust')}</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-green-500 text-sm">✓</span>
                <span className="text-xs text-gray-700">{t('premium.aiCompatibility')}</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-green-500 text-sm">✓</span>
                <span className="text-xs text-gray-700">{t('premium.anonymousDiscovery')}</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-green-500 text-sm">✓</span>
                <span className="text-xs text-gray-700">{t('premium.verifiedMatching')}</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-green-500 text-sm">✓</span>
                <span className="text-xs text-gray-700">{t('premium.safeMeetup')}</span>
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
            {t('premium.upgradeButton')}
          </button>
          
          <p className="text-xs text-gray-500 mt-3">
            {t('premium.meetSafely')} • {t('premium.cancelAnytime')}
          </p>
        </div>
        
        {/* Upgrade Modal */}
        {showUpgrade && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999] p-4">
            <div className="bg-white rounded-2xl shadow-2xl max-w-sm w-full p-6 relative">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-bold text-gray-900">{t('premium.premiumTitle')}</h2>
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
                  {t('premium.discoverSafely')}
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  {t('premium.trustVerification')}
                </p>
                
                <div className="bg-gradient-to-r from-purple-50 to-blue-50 p-3 rounded-lg mb-4">
                  <div className="text-xl font-bold text-purple-600 mb-1">{t('premium.monthlyPrice')}</div>
                  <p className="text-xs text-purple-700">{t('premium.priceDescription')}</p>
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
                    {t('premium.startSafeDiscovery')}
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
                    🚀 {t('premium.enableDemo')}
                  </button>
                  <button
                    onClick={() => setShowUpgrade(false)}
                    className="w-full bg-gray-100 text-gray-700 py-2 rounded-lg text-sm hover:bg-gray-200"
                  >
                    {t('premium.maybeLater')}
                  </button>
                </div>
                
                <p className="text-xs text-gray-500 mt-3">
                  {t('premium.cancelAnytime')} • {t('premium.noHiddenFees')}
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
            <h2 className="text-lg font-semibold text-gray-900">{t('premium.discoverSafely')}</h2>
            <p className="text-sm text-gray-600">{t('dashboard.findPeopleSafely')}</p>
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
            🚀 {t('premium.demoMode')} • {t('premium.clickToDisable')}
          </button>
        )}

        {/* Profile Setup Message for Premium Users */}
        {isPremium && !isProfileComplete && (
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mt-3">
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0">
                <span className="text-purple-500 text-lg">⚠️</span>
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-medium text-purple-800 mb-1">
                  Complete Your Profile to Access Premium Features
                </h3>
                <p className="text-sm text-purple-700 mb-3">
                  To discover people safely and access advanced trust features, please complete your profile with basic information.
                </p>
                <button
                  onClick={() => {
                    // This would trigger profile setup - integrate with existing profile setup
                    alert('Profile setup functionality - integrate with existing profile setup system');
                  }}
                  className="bg-purple-500 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-purple-600 transition-colors"
                >
                  Complete Profile
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Discovery Sub-Tabs */}
        <div className="flex mt-3 border-b">
          {[
            { id: 'discovery', label: t('premium.findPeople'), icon: '🔍' },
            { id: 'trust', label: t('premium.safetySystem'), icon: '🔒' }
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
                {t('premium.aiPoweredDiscovery')}
              </h2>
              <p className="text-sm text-gray-600">
                {t('premium.trustBasedMatching')}
              </p>
            </div>

            <div className="bg-white rounded-xl p-4 shadow-sm border mb-4">
              <h3 className="font-semibold text-gray-900 mb-3 text-sm">🔒 {t('premium.howItWorks')}</h3>
              <div className="space-y-2 text-xs text-gray-700">
                <div className="flex items-start space-x-2">
                  <span className="text-blue-500 mt-0.5 font-medium min-w-[12px]">1.</span>
                  <span>{t('premium.step1')}</span>
                </div>
                <div className="flex items-start space-x-2">
                  <span className="text-blue-500 mt-0.5 font-medium min-w-[12px]">2.</span>
                  <span>{t('premium.step2')}</span>
                </div>
                <div className="flex items-start space-x-2">
                  <span className="text-blue-500 mt-0.5 font-medium min-w-[12px]">3.</span>
                  <span>{t('premium.step3')}</span>
                </div>
                <div className="flex items-start space-x-2">
                  <span className="text-blue-500 mt-0.5 font-medium min-w-[12px]">4.</span>
                  <span>{t('premium.step4')}</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl p-4 shadow-sm border mb-4">
              <h3 className="font-semibold text-gray-900 mb-3 text-sm">🎯 {t('premium.discoveryPreferences')}</h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm text-gray-600 mb-1">{t('premium.lookingFor')}</label>
                  <select className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2">
                    <option>{t('premium.newFriends')}</option>
                    <option>{t('premium.activityPartners')}</option>
                    <option>{t('premium.studyBuddies')}</option>
                    <option>{t('premium.travelCompanions')}</option>
                    <option>{t('premium.professionalConnections')}</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">{t('premium.ageRange')}</label>
                  <select className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2">
                    <option>{t('premium.age18to25')}</option>
                    <option>{t('premium.age26to35')}</option>
                    <option>{t('premium.age36to45')}</option>
                    <option>{t('premium.age46plus')}</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">{t('premium.location')}</label>
                  <select className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2">
                    <option>{t('premium.within10miles')}</option>
                    <option>{t('premium.within25miles')}</option>
                    <option>{t('premium.within50miles')}</option>
                    <option>{t('premium.anywhere')}</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="text-center">
              <button className="bg-blue-500 text-white px-6 py-2 rounded-full text-sm font-medium hover:bg-blue-600 transition-colors">
                {t('premium.startDiscovery')}
              </button>
              <p className="text-xs text-gray-500 mt-2">
                {t('premium.anonymousChat')}
              </p>
            </div>
          </div>
        </div>
      )}

      {activeDiscoverTab === 'trust' && (
        <div className="flex-1 overflow-y-auto p-4">
          <div className="max-w-2xl mx-auto space-y-6">
            
            {/* Trust & Authenticity Display */}
            <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
              <div className="text-center mb-6">
                <h3 className="text-xl font-bold text-gray-900 mb-2">Your Trust & Authenticity Profile</h3>
                <p className="text-gray-600">Your premium ratings that help others trust you</p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Trust Level */}
                <div className="text-center">
                  <div className="w-20 h-20 mx-auto mb-4 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center shadow-lg">
                    <span className="text-white font-bold text-2xl">
                      {user?.trust_level || 1}
                    </span>
                  </div>
                  <h4 className="font-semibold text-gray-900 mb-1">{t('profile.trustLevel')}</h4>
                  <p className="text-sm text-gray-600 mb-2">Level {user?.trust_level || 1} of 5</p>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${((user?.trust_level || 1) / 5) * 100}%` }}
                    ></div>
                  </div>
                </div>
                
                {/* Authenticity Rating */}
                <div className="text-center">
                  <div className="w-20 h-20 mx-auto mb-4 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-full flex items-center justify-center shadow-lg">
                    <span className="text-white font-bold text-lg">
                      {(user?.authenticity_rating || 0).toFixed(1)}
                    </span>
                  </div>
                  <h4 className="font-semibold text-gray-900 mb-1">{t('profile.authenticity')}</h4>
                  <p className="text-sm text-gray-600 mb-2">Out of 10.0</p>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-gradient-to-r from-emerald-500 to-teal-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${((user?.authenticity_rating || 0) / 10) * 100}%` }}
                    ></div>
                  </div>
                </div>
              </div>
              
              <div className="mt-6 pt-6 border-t border-gray-200 text-center">
                <p className="text-sm text-gray-600">
                  🔒 These ratings are visible to other premium users and help build trust in the community
                </p>
              </div>
            </div>
            
            {/* Trust System Component */}
            <TrustSystem 
              user={user}
              token={token}
              api={api}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default DiscoverInterface;