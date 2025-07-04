import React, { useState, useEffect } from 'react';
import axios from 'axios';

const TrustSystem = ({ user, token, api }) => {
  const [trustProgress, setTrustProgress] = useState(null);
  const [achievements, setAchievements] = useState([]);
  const [showLevelUpModal, setShowLevelUpModal] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadTrustProgress();
    loadAchievements();
  }, []);

  const loadTrustProgress = async () => {
    try {
      const response = await axios.get(`${api}/trust/progress`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTrustProgress(response.data);
    } catch (error) {
      console.error('Failed to load trust progress:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadAchievements = async () => {
    try {
      const response = await axios.get(`${api}/trust/achievements`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAchievements(response.data);
    } catch (error) {
      console.error('Failed to load achievements:', error);
    }
  };

  const handleLevelUp = async () => {
    try {
      await axios.post(`${api}/trust/level-up`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setShowLevelUpModal(true);
      setTimeout(() => {
        setShowLevelUpModal(false);
        loadTrustProgress();
        loadAchievements();
      }, 3000);
      
    } catch (error) {
      console.error('Failed to level up:', error);
      alert(error.response?.data?.detail || 'Failed to level up');
    }
  };

  const getProgressPercentage = (current, required) => {
    if (required === 0) return 100;
    return Math.min((current / required) * 100, 100);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  if (!trustProgress) {
    return (
      <div className="text-center p-8">
        <p className="text-gray-600">Failed to load trust progress</p>
      </div>
    );
  }

  const currentLevel = trustProgress.current_level_info;
  const nextLevel = trustProgress.next_level_info;
  const canLevelUp = trustProgress.can_level_up;

  return (
    <div className="flex-1 bg-gray-50 p-4 overflow-y-auto">
      <div className="max-w-4xl mx-auto space-y-6">
        
        {/* Current Trust Level */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border">
          <div className="text-center mb-6">
            <div className="text-6xl mb-3">
              {currentLevel.icon}
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Trust Level {trustProgress.current_level}
            </h2>
            <h3 className="text-lg font-semibold text-gray-700 mb-2">
              {currentLevel.name}
            </h3>
            <p className="text-gray-600">
              {currentLevel.description}
            </p>
          </div>

          {/* Available Features */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-semibold text-gray-900 mb-3">Available Features:</h4>
            <div className="flex flex-wrap gap-2">
              {currentLevel.features.map(feature => (
                <span
                  key={feature}
                  className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium"
                >
                  {feature.replace(/_/g, ' ').toUpperCase()}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Progress to Next Level */}
        {nextLevel && (
          <div className="bg-white rounded-2xl p-6 shadow-sm border">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Progress to Level {trustProgress.next_level}
              </h3>
              {canLevelUp && (
                <button
                  onClick={handleLevelUp}
                  className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-4 py-2 rounded-lg font-medium hover:from-blue-600 hover:to-purple-600 transform hover:scale-105 transition-all"
                >
                  🚀 Level Up!
                </button>
              )}
            </div>

            <div className="flex items-center mb-4">
              <div className="text-3xl mr-4">{nextLevel.icon}</div>
              <div>
                <h4 className="font-semibold text-gray-900">{nextLevel.name}</h4>
                <p className="text-sm text-gray-600">{nextLevel.description}</p>
              </div>
            </div>

            {/* Progress Bars */}
            <div className="space-y-4">
              {Object.entries(trustProgress.progress).map(([key, progress]) => (
                <div key={key}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="font-medium text-gray-700">
                      {key.replace(/_/g, ' ').toUpperCase()}
                    </span>
                    <span className={`font-medium ${progress.completed ? 'text-green-600' : 'text-gray-500'}`}>
                      {progress.current} / {progress.required}
                      {progress.completed && ' ✓'}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full transition-all ${
                        progress.completed ? 'bg-green-500' : 'bg-blue-500'
                      }`}
                      style={{ width: `${getProgressPercentage(progress.current, progress.required)}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>

            {/* Next Level Features Preview */}
            <div className="mt-4 bg-blue-50 rounded-lg p-4">
              <h5 className="font-semibold text-blue-900 mb-2">Unlock at Level {trustProgress.next_level}:</h5>
              <div className="flex flex-wrap gap-2">
                {nextLevel.features.map(feature => (
                  <span
                    key={feature}
                    className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium"
                  >
                    {feature.replace(/_/g, ' ').toUpperCase()}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Trust Metrics */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Trust Metrics</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {trustProgress.metrics.total_connections}
              </div>
              <div className="text-sm text-gray-600">Total Connections</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {trustProgress.metrics.days_since_registration}
              </div>
              <div className="text-sm text-gray-600">Days Active</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {trustProgress.metrics.total_interactions}
              </div>
              <div className="text-sm text-gray-600">Interactions</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {trustProgress.metrics.messages_sent}
              </div>
              <div className="text-sm text-gray-600">Messages Sent</div>
            </div>
          </div>
        </div>

        {/* Recent Achievements */}
        {achievements.length > 0 && (
          <div className="bg-white rounded-2xl p-6 shadow-sm border">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Achievements</h3>
            <div className="space-y-3">
              {achievements.slice(0, 3).map(achievement => (
                <div key={achievement.achievement_id} className="flex items-center space-x-3 p-3 bg-yellow-50 rounded-lg">
                  <div className="text-2xl">🏆</div>
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{achievement.title}</p>
                    <p className="text-sm text-gray-600">{achievement.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Trust Milestones */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Trust Milestones</h3>
          <div className="space-y-3">
            {trustProgress.milestones.slice(0, 5).map((milestone, index) => (
              <div key={index} className="flex items-center justify-between p-3 rounded-lg border">
                <div className="flex items-center space-x-3">
                  <div className={`w-4 h-4 rounded-full ${
                    milestone.completed ? 'bg-green-500' : 'bg-gray-300'
                  }`}></div>
                  <div>
                    <p className="font-medium text-gray-900">{milestone.title}</p>
                    <p className="text-sm text-gray-600">{milestone.description}</p>
                  </div>
                </div>
                <div className="text-sm text-gray-500">
                  {milestone.current} / {milestone.target}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Level Up Celebration Modal */}
      {showLevelUpModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8 text-center">
            <div className="text-6xl mb-4">🎉</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Congratulations!
            </h2>
            <p className="text-gray-600 mb-4">
              You've reached Trust Level {trustProgress.current_level + 1}!
            </p>
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4">
              <div className="text-3xl mb-2">{nextLevel?.icon}</div>
              <h3 className="font-semibold text-gray-900">{nextLevel?.name}</h3>
              <p className="text-sm text-gray-600">{nextLevel?.description}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TrustSystem;