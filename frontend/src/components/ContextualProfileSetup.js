import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';

const ContextualProfileSetup = ({ user, token, api, context, onComplete, onSkip }) => {
  const { t } = useTranslation();
  const [profileData, setProfileData] = useState({});
  const [currentStep, setCurrentStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Profile requirements based on context
  const getProfileConfig = (context) => {
    switch (context) {
      case 'chats':
        return {
          title: 'Chat Profile Setup',
          description: 'Basic info to start messaging',
          required: ['display_name'],
          optional: ['avatar', 'status_message'],
          canSkip: false,
          steps: [
            {
              title: 'Basic Info',
              fields: ['display_name', 'status_message']
            }
          ]
        };

      case 'groups':
        return {
          title: 'Groups Profile Setup',
          description: 'Help us suggest the perfect groups for you',
          required: ['interests', 'location', 'age_range'],
          optional: ['skills', 'availability', 'group_preferences'],
          canSkip: true,
          skipMessage: 'You can browse groups but won\'t get personalized suggestions',
          steps: [
            {
              title: 'Your Interests',
              fields: ['interests', 'skills']
            },
            {
              title: 'Location & Preferences',
              fields: ['location', 'age_range', 'group_preferences']
            }
          ]
        };

      case 'marketplace':
        return {
          title: 'Marketplace Profile Setup',
          description: 'Build trust for buying and selling',
          required: ['full_name', 'phone_verification', 'location'],
          optional: ['business_info', 'id_verification', 'payment_methods'],
          canSkip: true,
          skipMessage: 'You can browse but won\'t be able to buy or sell',
          steps: [
            {
              title: 'Personal Information',
              fields: ['full_name', 'phone_verification']
            },
            {
              title: 'Location & Verification',
              fields: ['location', 'id_verification']
            },
            {
              title: 'Business Profile (Optional)',
              fields: ['business_info', 'service_categories', 'portfolio']
            }
          ]
        };

      case 'premium':
        return {
          title: 'Premium Social Profile',
          description: 'Express yourself and connect meaningfully',
          required: ['premium_display_name', 'current_mood'],
          optional: ['personality_insights', 'relationship_goals', 'premium_interests'],
          canSkip: false,
          steps: [
            {
              title: 'Premium Identity',
              fields: ['premium_display_name', 'current_mood']
            },
            {
              title: 'Social Preferences',
              fields: ['premium_interests', 'discovery_preferences']
            }
          ]
        };

      default:
        return null;
    }
  };

  const config = getProfileConfig(context);
  if (!config) return null;

  const currentStepConfig = config.steps[currentStep];

  const renderField = (fieldName) => {
    switch (fieldName) {
      case 'display_name':
        return (
          <div key={fieldName}>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Display Name *
            </label>
            <input
              type="text"
              value={profileData[fieldName] || ''}
              onChange={(e) => setProfileData(prev => ({ ...prev, [fieldName]: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="How should others see your name?"
            />
          </div>
        );

      case 'interests':
        return (
          <div key={fieldName}>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Your Interests * 
            </label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {[
                '🏃 Fitness', '🎵 Music', '🎨 Art', '💻 Tech', '🍳 Cooking', 
                '📚 Reading', '🎮 Gaming', '🌍 Travel', '📷 Photography'
              ].map(interest => (
                <button
                  key={interest}
                  onClick={() => {
                    const current = profileData.interests || [];
                    const updated = current.includes(interest) 
                      ? current.filter(i => i !== interest)
                      : [...current, interest];
                    setProfileData(prev => ({ ...prev, interests: updated }));
                  }}
                  className={`p-2 text-sm rounded-lg border transition-colors ${
                    (profileData.interests || []).includes(interest)
                      ? 'bg-blue-500 text-white border-blue-500'
                      : 'bg-gray-50 text-gray-700 border-gray-300 hover:bg-gray-100'
                  }`}
                >
                  {interest}
                </button>
              ))}
            </div>
          </div>
        );

      case 'location':
        return (
          <div key={fieldName}>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Location *
            </label>
            <input
              type="text"
              value={profileData[fieldName] || ''}
              onChange={(e) => setProfileData(prev => ({ ...prev, [fieldName]: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="City, State/Region"
            />
          </div>
        );

      case 'full_name':
        return (
          <div key={fieldName}>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Full Name * 
              <span className="text-xs text-gray-500">(For marketplace transactions)</span>
            </label>
            <input
              type="text"
              value={profileData[fieldName] || ''}
              onChange={(e) => setProfileData(prev => ({ ...prev, [fieldName]: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Your legal name"
            />
          </div>
        );

      case 'premium_display_name':
        return (
          <div key={fieldName}>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Premium Display Name *
              <span className="text-xs text-gray-500">(Different from your real name)</span>
            </label>
            <input
              type="text"
              value={profileData[fieldName] || ''}
              onChange={(e) => setProfileData(prev => ({ ...prev, [fieldName]: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              placeholder="Your premium identity"
            />
          </div>
        );

      case 'current_mood':
        return (
          <div key={fieldName}>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Current Mood *
            </label>
            <div className="grid grid-cols-4 gap-2">
              {[
                '😊 Happy', '😴 Chill', '🚀 Energetic', '🤔 Thoughtful',
                '🎉 Excited', '😌 Peaceful', '💪 Motivated', '🎨 Creative'
              ].map(mood => (
                <button
                  key={mood}
                  onClick={() => setProfileData(prev => ({ ...prev, current_mood: mood }))}
                  className={`p-2 text-sm rounded-lg border transition-colors ${
                    profileData.current_mood === mood
                      ? 'bg-purple-500 text-white border-purple-500'
                      : 'bg-gray-50 text-gray-700 border-gray-300 hover:bg-gray-100'
                  }`}
                >
                  {mood}
                </button>
              ))}
            </div>
          </div>
        );

      case 'age_range':
        return (
          <div key={fieldName}>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Age Range *
            </label>
            <select
              value={profileData[fieldName] || ''}
              onChange={(e) => setProfileData(prev => ({ ...prev, [fieldName]: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select age range</option>
              <option value="18-25">18-25</option>
              <option value="26-35">26-35</option>
              <option value="36-45">36-45</option>
              <option value="46-60">46-60</option>
              <option value="60+">60+</option>
            </select>
          </div>
        );

      case 'phone_verification':
        return (
          <div key={fieldName}>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Phone Verification *
            </label>
            <input
              type="tel"
              value={profileData[fieldName] || ''}
              onChange={(e) => setProfileData(prev => ({ ...prev, [fieldName]: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="+1 (555) 123-4567"
            />
            <p className="text-xs text-gray-500 mt-1">Required for marketplace trust & safety</p>
          </div>
        );

      // Add more field types as needed...
      default:
        return (
          <div key={fieldName}>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {fieldName.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </label>
            <input
              type="text"
              value={profileData[fieldName] || ''}
              onChange={(e) => setProfileData(prev => ({ ...prev, [fieldName]: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder={`Enter ${fieldName.replace('_', ' ')}`}
            />
          </div>
        );
    }
  };

  const handleNext = () => {
    if (currentStep < config.steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleSubmit();
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      // Save contextual profile data
      await fetch(`${api}/users/profile/${context}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(profileData)
      });

      onComplete(profileData);
    } catch (error) {
      console.error('Profile setup error:', error);
      alert('Failed to save profile. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const isStepValid = () => {
    const requiredFields = currentStepConfig.fields.filter(field => 
      config.required.includes(field)
    );
    return requiredFields.every(field => profileData[field]);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full p-6">
        {/* Header */}
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">{config.title}</h2>
          <p className="text-gray-600">{config.description}</p>
          
          {/* Progress */}
          <div className="flex items-center justify-center mt-4 space-x-2">
            {config.steps.map((_, index) => (
              <div
                key={index}
                className={`w-3 h-3 rounded-full ${
                  index <= currentStep ? 'bg-blue-500' : 'bg-gray-300'
                }`}
              />
            ))}
          </div>
          <p className="text-sm text-gray-500 mt-2">
            Step {currentStep + 1} of {config.steps.length}: {currentStepConfig.title}
          </p>
        </div>

        {/* Form Fields */}
        <div className="space-y-4">
          {currentStepConfig.fields.map(renderField)}
        </div>

        {/* Actions */}
        <div className="flex justify-between items-center mt-8">
          {/* Skip Button */}
          {config.canSkip && (
            <button
              onClick={onSkip}
              className="text-gray-500 hover:text-gray-700 text-sm"
              title={config.skipMessage}
            >
              Skip for now
            </button>
          )}
          
          <div className="flex space-x-3 ml-auto">
            {/* Back Button */}
            {currentStep > 0 && (
              <button
                onClick={() => setCurrentStep(currentStep - 1)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Back
              </button>
            )}
            
            {/* Next/Submit Button */}
            <button
              onClick={handleNext}
              disabled={!isStepValid() || isSubmitting}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Saving...' : 
               currentStep === config.steps.length - 1 ? 'Complete Setup' : 'Next'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContextualProfileSetup;