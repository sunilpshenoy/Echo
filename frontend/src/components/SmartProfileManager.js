import React, { useState, useEffect } from 'react';
import ContextualProfileSetup from './ContextualProfileSetup';

const SmartProfileManager = ({ user, token, api }) => {
  const [profileCompleteness, setProfileCompleteness] = useState({});
  const [currentPrompt, setCurrentPrompt] = useState(null);
  const [showSetup, setShowSetup] = useState(false);

  // Check profile completeness for each context
  useEffect(() => {
    checkProfileCompleteness();
  }, [user]);

  const checkProfileCompleteness = async () => {
    if (!user || !token) return;

    try {
      const response = await fetch(`${api}/users/profile/completeness`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const completeness = await response.json();
      setProfileCompleteness(completeness);
    } catch (error) {
      console.error('Failed to check profile completeness:', error);
    }
  };

  // Get profile requirements for each tab
  const getTabRequirements = (tab) => {
    const requirements = {
      chats: {
        required: ['display_name'],
        nice_to_have: ['status_message', 'avatar'],
        impact: 'Better messaging experience'
      },
      groups: {
        required: ['interests', 'location'],
        nice_to_have: ['age_range', 'skills', 'availability'],
        impact: 'Personalized group suggestions'
      },
      marketplace: {
        required: ['full_name', 'phone_verification', 'location'],
        nice_to_have: ['id_verification', 'business_info'],
        impact: 'Ability to buy and sell safely'
      },
      premium: {
        required: ['premium_display_name', 'current_mood'],
        nice_to_have: ['personality_insights', 'relationship_goals'],
        impact: 'Enhanced social features'
      }
    };
    return requirements[tab] || { required: [], nice_to_have: [], impact: '' };
  };

  // Check if user can access tab
  const canAccessTab = (tab) => {
    const requirements = getTabRequirements(tab);
    const userProfile = profileCompleteness[tab] || {};
    
    // For chats, always allow access (minimal requirements)
    if (tab === 'chats') return true;
    
    // For other tabs, check if minimum requirements are met
    return requirements.required.every(field => userProfile[field]);
  };

  // Get completion percentage for a tab
  const getCompletionPercentage = (tab) => {
    const requirements = getTabRequirements(tab);
    const userProfile = profileCompleteness[tab] || {};
    const totalFields = [...requirements.required, ...requirements.nice_to_have];
    const completedFields = totalFields.filter(field => userProfile[field]);
    
    return totalFields.length > 0 ? (completedFields.length / totalFields.length) * 100 : 0;
  };

  // Smart prompt to complete profile based on usage
  const promptProfileCompletion = (tab, reason = 'access') => {
    const requirements = getTabRequirements(tab);
    let message = '';
    
    switch (reason) {
      case 'access':
        message = `To access ${tab} features, please complete your profile`;
        break;
      case 'enhance':
        message = `Complete your ${tab} profile for better experience`;
        break;
      case 'trust':
        message = `Build trust by completing your ${tab} profile`;
        break;
      default:
        message = `Update your ${tab} profile`;
    }

    setCurrentPrompt({
      tab,
      message,
      requirements,
      reason
    });
    setShowSetup(true);
  };

  // Render tab-specific profile completion card
  const renderTabProfileCard = (tab) => {
    const requirements = getTabRequirements(tab);
    const canAccess = canAccessTab(tab);
    const completion = getCompletionPercentage(tab);
    
    const tabIcons = {
      chats: '💬',
      groups: '👥', 
      marketplace: '🛒',
      premium: '⭐'
    };

    return (
      <div key={tab} className="bg-white rounded-lg shadow-md p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-gray-900 flex items-center">
            <span className="text-xl mr-2">{tabIcons[tab]}</span>
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </h3>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
            canAccess ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
          }`}>
            {canAccess ? 'Ready' : 'Setup Needed'}
          </span>
        </div>

        {/* Progress Bar */}
        <div className="mb-3">
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>Profile Complete</span>
            <span>{Math.round(completion)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full ${
                completion === 100 ? 'bg-green-500' : 
                completion >= 60 ? 'bg-blue-500' : 'bg-yellow-500'
              }`}
              style={{ width: `${completion}%` }}
            ></div>
          </div>
        </div>

        {/* Requirements */}
        <div className="space-y-2">
          <div>
            <h4 className="text-sm font-medium text-gray-700">Required:</h4>
            <div className="flex flex-wrap gap-1 mt-1">
              {requirements.required.map(field => (
                <span key={field} className={`px-2 py-1 rounded text-xs ${
                  profileCompleteness[tab]?.[field] 
                    ? 'bg-green-100 text-green-700' 
                    : 'bg-red-100 text-red-700'
                }`}>
                  {field.replace('_', ' ')}
                </span>
              ))}
            </div>
          </div>

          {requirements.nice_to_have.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700">Optional:</h4>
              <div className="flex flex-wrap gap-1 mt-1">
                {requirements.nice_to_have.map(field => (
                  <span key={field} className={`px-2 py-1 rounded text-xs ${
                    profileCompleteness[tab]?.[field] 
                      ? 'bg-blue-100 text-blue-700' 
                      : 'bg-gray-100 text-gray-600'
                  }`}>
                    {field.replace('_', ' ')}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Impact */}
        <p className="text-sm text-gray-600 mt-3 italic">
          Impact: {requirements.impact}
        </p>

        {/* Action Button */}
        <button
          onClick={() => promptProfileCompletion(tab, canAccess ? 'enhance' : 'access')}
          className={`w-full mt-3 px-4 py-2 rounded-md text-sm font-medium ${
            canAccess 
              ? 'bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100'
              : 'bg-red-50 text-red-700 border border-red-200 hover:bg-red-100'
          }`}
        >
          {canAccess ? 'Enhance Profile' : 'Complete Setup'}
        </button>
      </div>
    );
  };

  const handleSetupComplete = (data) => {
    setShowSetup(false);
    setCurrentPrompt(null);
    checkProfileCompleteness(); // Refresh completeness
  };

  const handleSetupSkip = () => {
    setShowSetup(false);
    setCurrentPrompt(null);
  };

  return (
    <div>
      {/* Profile Management Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {['chats', 'groups', 'marketplace', 'premium'].map(renderTabProfileCard)}
      </div>

      {/* Contextual Profile Setup Modal */}
      {showSetup && currentPrompt && (
        <ContextualProfileSetup
          user={user}
          token={token}
          api={api}
          context={currentPrompt.tab}
          onComplete={handleSetupComplete}
          onSkip={handleSetupSkip}
        />
      )}

      {/* Smart Suggestions */}
      <div className="mt-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4">
        <h3 className="font-semibold text-gray-900 mb-2">🎯 Smart Recommendations</h3>
        <div className="space-y-2">
          {/* Dynamic recommendations based on usage patterns */}
          {getCompletionPercentage('marketplace') < 50 && (
            <p className="text-sm text-gray-700">
              💡 Complete your marketplace profile to start selling and build trust with buyers
            </p>
          )}
          {getCompletionPercentage('groups') < 30 && (
            <p className="text-sm text-gray-700">
              🎯 Add your interests to discover groups that match your hobbies
            </p>
          )}
          {getCompletionPercentage('premium') === 0 && (
            <p className="text-sm text-gray-700">
              ⭐ Set up your premium profile to unlock advanced social features
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default SmartProfileManager;