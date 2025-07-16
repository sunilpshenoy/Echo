import React, { useState } from 'react';
import axios from 'axios';

const ProfileSetup = ({ user, token, api, onProfileComplete }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  
  // AI Compatibility Questionnaire Data
  const [profileData, setProfileData] = useState({
    // Basic Info
    age: '',
    gender: '',
    location: '',
    
    // Compatibility Questions
    current_mood: '',
    mood_reason: '',
    seeking_type: '',
    seeking_age_range: '',
    seeking_gender: '',
    seeking_location_preference: '',
    connection_purpose: '',
    additional_requirements: '',
    
    // Profile Details
    bio: '',
    interests: [],
    values: []
  });
  
  const getAuthHeaders = () => ({
    headers: { Authorization: `Bearer ${token}` }
  });
  
  const handleInputChange = (field, value) => {
    setProfileData(prev => ({
      ...prev,
      [field]: value
    }));
    setError('');
  };
  
  const handleArrayChange = (field, value) => {
    setProfileData(prev => ({
      ...prev,
      [field]: value.split(',').map(item => item.trim()).filter(item => item)
    }));
  };
  
  const handleSubmit = async () => {
    setIsLoading(true);
    setError('');
    
    try {
      const response = await axios.put(`${api}/profile/complete`, {
        ...profileData,
        profile_completed: true
      }, getAuthHeaders());
      
      onProfileComplete(response.data);
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to save profile');
    } finally {
      setIsLoading(false);
    }
  };
  
  const nextStep = () => {
    if (currentStep < 3) {
      setCurrentStep(currentStep + 1);
    } else {
      handleSubmit();
    }
  };
  
  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };
  
  const isStepValid = () => {
    switch (currentStep) {
      case 1:
        return profileData.age && profileData.gender && profileData.location;
      case 2:
        return profileData.seeking_type && profileData.connection_purpose;
      case 3:
        return profileData.bio.trim().length > 0;
      default:
        return false;
    }
  };
  
  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-8 animate-fade-in-up">
          <h1 className="heading-xl mb-4">Let's Get to Know You</h1>
          <p className="text-subtle text-lg">
            This helps us connect you with people who truly understand you.
          </p>
          
          {/* Progress Indicator */}
          <div className="flex justify-center mt-6 space-x-4" role="progressbar" aria-valuenow={currentStep} aria-valuemin="1" aria-valuemax="3" aria-label="Profile setup progress">
            {[1, 2, 3].map((step) => (
              <div
                key={step}
                className={`trust-level-indicator ${
                  step <= currentStep ? 'trust-level-3' : 'bg-gray-200'
                } ${step === currentStep ? 'animate-pulse-gentle' : ''}`}
                aria-current={step === currentStep ? 'step' : undefined}
              >
                {step}
              </div>
            ))}
          </div>
          <p className="text-subtle text-sm mt-2">
            Step {currentStep} of 3
          </p>
        </div>
        
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6" role="alert">
            {error}
          </div>
        )}
        
        <div className="card animate-fade-in-up">
          {/* Step 1: Basic Information */}
          {currentStep === 1 && (
            <div>
              <h2 className="heading-md mb-6">Basic Information</h2>
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="age">
                    What's your age?
                  </label>
                  <input
                    type="number"
                    id="age"
                    min="18"
                    max="100"
                    value={profileData.age}
                    onChange={(e) => handleInputChange('age', e.target.value)}
                    className="input-field"
                    placeholder="e.g., 25"
                    aria-describedby="age-help"
                  />
                  <p id="age-help" className="text-xs text-gray-500 mt-1">Must be 18 or older</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="gender">
                    Gender
                  </label>
                  <select
                    id="gender"
                    value={profileData.gender}
                    onChange={(e) => handleInputChange('gender', e.target.value)}
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
                  <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="location">
                    Where are you located?
                  </label>
                  <input
                    type="text"
                    id="location"
                    value={profileData.location}
                    onChange={(e) => handleInputChange('location', e.target.value)}
                    className="input-field"
                    placeholder="e.g., New York, NY or London, UK"
                    aria-describedby="location-help"
                  />
                  <p id="location-help" className="text-xs text-gray-500 mt-1">City and country/state</p>
                </div>
              </div>
            </div>
          )}
          
          {/* Step 2: Compatibility Questions */}
          {currentStep === 2 && (
            <div>
              <h2 className="heading-md mb-6">What You're Looking For</h2>
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="current_mood">
                    What's your current mood and why?
                  </label>
                  <textarea
                    id="current_mood"
                    value={profileData.current_mood}
                    onChange={(e) => handleInputChange('current_mood', e.target.value)}
                    className="input-field h-20"
                    placeholder="e.g., Feeling optimistic because I just started a new hobby..."
                    aria-describedby="mood-help"
                  />
                  <p id="mood-help" className="text-xs text-gray-500 mt-1">Help others understand your current state of mind</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="seeking_type">
                    What kind of person would you like to meet?
                  </label>
                  <select
                    id="seeking_type"
                    value={profileData.seeking_type}
                    onChange={(e) => handleInputChange('seeking_type', e.target.value)}
                    className="input-field"
                  >
                    <option value="">Select connection type</option>
                    <option value="friendship">New friends</option>
                    <option value="romantic">Romantic connection</option>
                    <option value="activity-partner">Activity partners</option>
                    <option value="professional">Professional networking</option>
                    <option value="open">Open to anything genuine</option>
                  </select>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="seeking_age_range">
                      Preferred Age Range
                    </label>
                    <input
                      type="text"
                      id="seeking_age_range"
                      value={profileData.seeking_age_range}
                      onChange={(e) => handleInputChange('seeking_age_range', e.target.value)}
                      className="input-field"
                      placeholder="e.g., 22-30"
                      aria-describedby="age-range-help"
                    />
                    <p id="age-range-help" className="text-xs text-gray-500 mt-1">Optional preference</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="seeking_gender">
                      Gender Preference
                    </label>
                    <select
                      id="seeking_gender"
                      value={profileData.seeking_gender}
                      onChange={(e) => handleInputChange('seeking_gender', e.target.value)}
                      className="input-field"
                    >
                      <option value="">Any gender</option>
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                      <option value="non-binary">Non-binary</option>
                    </select>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="connection_purpose">
                    What's the purpose of this connection?
                  </label>
                  <textarea
                    id="connection_purpose"
                    value={profileData.connection_purpose}
                    onChange={(e) => handleInputChange('connection_purpose', e.target.value)}
                    className="input-field h-20"
                    placeholder="e.g., Looking for someone to explore the city with, deep conversations, shared hobbies..."
                    aria-describedby="purpose-help"
                  />
                  <p id="purpose-help" className="text-xs text-gray-500 mt-1">Be specific about what you're hoping to find</p>
                </div>
              </div>
            </div>
          )}
          
          {/* Step 3: Personal Details */}
          {currentStep === 3 && (
            <div>
              <h2 className="heading-md mb-6">Tell Us About Yourself</h2>
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="bio">
                    Bio - Share what makes you unique
                  </label>
                  <textarea
                    id="bio"
                    value={profileData.bio}
                    onChange={(e) => handleInputChange('bio', e.target.value)}
                    className="input-field h-32"
                    placeholder="What do you love? What drives you? What kind of conversations excite you? Be authentic..."
                    aria-describedby="bio-help"
                  />
                  <p id="bio-help" className="text-subtle text-sm mt-1">
                    {profileData.bio.length}/500 characters
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="interests">
                    Interests (comma-separated)
                  </label>
                  <input
                    type="text"
                    id="interests"
                    onChange={(e) => handleArrayChange('interests', e.target.value)}
                    className="input-field"
                    placeholder="e.g., photography, hiking, cooking, philosophy, sci-fi books"
                    aria-describedby="interests-help"
                  />
                  <p id="interests-help" className="text-xs text-gray-500 mt-1">Separate multiple interests with commas</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="values">
                    Values that matter to you (comma-separated)
                  </label>
                  <input
                    type="text"
                    id="values"
                    onChange={(e) => handleArrayChange('values', e.target.value)}
                    className="input-field"
                    placeholder="e.g., honesty, creativity, kindness, adventure, growth"
                    aria-describedby="values-help"
                  />
                  <p id="values-help" className="text-xs text-gray-500 mt-1">What principles guide your life?</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="additional_requirements">
                    Any other requirements or preferences?
                  </label>
                  <textarea
                    id="additional_requirements"
                    value={profileData.additional_requirements}
                    onChange={(e) => handleInputChange('additional_requirements', e.target.value)}
                    className="input-field h-20"
                    placeholder="Anything specific you'd like potential connections to know?"
                    aria-describedby="requirements-help"
                  />
                  <p id="requirements-help" className="text-xs text-gray-500 mt-1">Optional additional information</p>
                </div>
              </div>
            </div>
          )}
          
          {/* Navigation Buttons */}
          <div className="flex justify-between mt-8">
            <button
              onClick={prevStep}
              disabled={currentStep === 1}
              className={`btn-secondary ${currentStep === 1 ? 'opacity-50 cursor-not-allowed' : ''}`}
              aria-label="Go to previous step"
            >
              Previous
            </button>
            
            <button
              onClick={nextStep}
              disabled={!isStepValid() || isLoading}
              className={`btn-primary ${!isStepValid() ? 'opacity-50 cursor-not-allowed' : ''}`}
              aria-label={currentStep === 3 ? 'Complete profile setup' : 'Go to next step'}
            >
              {isLoading ? (
                <div className="flex items-center">
                  <div className="loading-spinner w-5 h-5 mr-2"></div>
                  Saving...
                </div>
              ) : (
                currentStep === 3 ? 'Complete Profile' : 'Next'
              )}
            </button>
          </div>
        </div>
        
        {/* Privacy Notice */}
        <div className="mt-6 text-center">
          <div className="card-glass">
            <p className="text-subtle text-sm">
              🔒 Your information is kept private and secure. You control what you share and when.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfileSetup;