import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';

const TeamsInterface = ({ 
  user, 
  token, 
  api, 
  teams, 
  selectedTeam, 
  isLoading,
  onTeamSelect,
  onTeamsRefresh
}) => {
  const { t } = useTranslation();
  const [showCreateTeam, setShowCreateTeam] = useState(false);
  const [newTeamName, setNewTeamName] = useState('');
  const [newTeamDescription, setNewTeamDescription] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const handleCreateTeam = async () => {
    if (!newTeamName.trim()) return;
    
    setIsCreating(true);
    try {
      console.log('Creating team:', { name: newTeamName, description: newTeamDescription });
      
      // Call backend to create team
      const response = await axios.post(`${api}/teams`, {
        name: newTeamName,
        description: newTeamDescription,
        type: 'group'
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      alert(t('teams.teamCreatedSuccess'));
      console.log('Team created:', response.data);
      
      setNewTeamName('');
      setNewTeamDescription('');
      setShowCreateTeam(false);
      
      // Refresh teams list
      if (onTeamsRefresh) {
        onTeamsRefresh();
      }
      
    } catch (error) {
      console.error('Failed to create team:', error);
      const errorMessage = error.response?.data?.detail || t('teams.teamCreationFailed');
      alert(errorMessage);
    } finally {
      setIsCreating(false);
    }
  };

  const handleTeamClick = (team) => {
    if (onTeamSelect) {
      onTeamSelect(team);
    }
  };

  // For mobile, show single column layout
  if (selectedTeam) {
    return (
      <div className="flex-1 flex flex-col bg-white">
        {/* Team Header */}
        <div className="bg-white p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <button
              onClick={() => onTeamSelect ? onTeamSelect(null) : null}
              className="text-blue-500 hover:text-blue-700 text-sm font-medium"
            >
              ← {t('teams.backToTeams')}
            </button>
            <div className="flex items-center space-x-2">
              <button className="p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100">
                ⚙️
              </button>
              <button className="p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100">
                📞
              </button>
              <button className="p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100">
                📹
              </button>
            </div>
          </div>
          <div className="flex items-center space-x-3 mt-3">
            <div className="w-12 h-12 bg-purple-500 rounded-lg flex items-center justify-center">
              <span className="text-white font-medium text-lg">
                {selectedTeam.name?.[0]?.toUpperCase() || 'T'}
              </span>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                {selectedTeam.name || t('teams.unnamedTeam')}
              </h3>
              <p className="text-sm text-gray-600">
                {selectedTeam.member_count || selectedTeam.members?.length || 0} {t('teams.members')} • {selectedTeam.type || 'General'}
              </p>
            </div>
          </div>
        </div>

        {/* Team Messages Area */}
        <div className="flex-1 bg-gray-50 flex items-center justify-center p-4">
          <div className="text-center max-w-sm">
            <div className="text-4xl mb-4">💬</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {t('teams.welcomeTo')} {selectedTeam.name}
            </h3>
            <p className="text-gray-600 mb-4 text-sm">
              {selectedTeam.description || t('teams.startCollaborating')}
            </p>
            <button className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors text-sm">
              {t('teams.sendFirstMessage')}
            </button>
          </div>
        </div>

        {/* Message Input */}
        <div className="bg-white p-4 border-t border-gray-200">
          <div className="flex items-center space-x-3">
            <button className="p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100">
              📎
            </button>
            <input
              type="text"
              placeholder={`${t('teams.messageTeam')} ${selectedTeam.name}`}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            />
            <button className="bg-blue-500 text-white p-2 rounded-lg hover:bg-blue-600 transition-colors">
              ➤
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-white">
      {/* Teams Header */}
      <div className="bg-white p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">{t('teams.title')}</h2>
            <p className="text-sm text-gray-600">{t('teams.subtitle')}</p>
          </div>
          <button 
            onClick={() => setShowCreateTeam(true)}
            className="bg-blue-500 text-white p-2 rounded-lg hover:bg-blue-600 transition-colors"
            title={t('teams.createTeam')}
          >
            ➕
          </button>
        </div>
      </div>
      
      {/* Teams List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full"></div>
          </div>
        ) : teams && teams.length > 0 ? (
          <div className="p-4 space-y-3">
            {teams.map(team => (
              <button
                key={team.team_id || team.id}
                onClick={() => handleTeamClick(team)}
                className="w-full p-4 rounded-xl text-left hover:bg-gray-50 transition-colors border border-gray-100 bg-white shadow-sm"
              >
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-purple-500 rounded-lg flex items-center justify-center">
                    <span className="text-white font-medium text-lg">
                      {team.name?.[0]?.toUpperCase() || 'T'}
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 truncate">
                      {team.name || t('teams.unnamedTeam')}
                    </p>
                    <p className="text-sm text-gray-600 truncate">
                      {team.member_count || team.members?.length || 0} {t('teams.members')}
                    </p>
                    <p className="text-xs text-gray-500">
                      {team.last_activity ? new Date(team.last_activity).toLocaleDateString() : t('teams.noRecentActivity')}
                    </p>
                  </div>
                  <div className="text-gray-400">
                    →
                  </div>
                </div>
              </button>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center p-6">
            <div className="text-6xl mb-4">👥</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">{t('teams.noTeams')}</h3>
            <p className="text-gray-600 text-sm mb-6 max-w-sm">
              {t('teams.createTeamDescription')}
            </p>
            
            <div className="bg-gray-50 rounded-lg p-4 mb-6 max-w-sm">
              <h4 className="font-semibold text-gray-900 mb-2 text-sm">{t('teams.teamFeatures')}</h4>
              <div className="space-y-1 text-left text-xs text-gray-700">
                <div className="flex items-center space-x-2">
                  <span className="text-green-500">✓</span>
                  <span>{t('teams.groupMessaging')}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-green-500">✓</span>
                  <span>{t('teams.voiceVideoCalls')}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-green-500">✓</span>
                  <span>{t('teams.projectCollaboration')}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-green-500">✓</span>
                  <span>{t('teams.memberManagement')}</span>
                </div>
              </div>
            </div>

            <button 
              onClick={() => setShowCreateTeam(true)}
              className="bg-blue-500 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-600 transition-colors"
            >
              {t('teams.createFirstTeam')}
            </button>
          </div>
        )}
      </div>

      {/* Create Team Modal */}
      {showCreateTeam && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999] p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-sm w-full p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-bold text-gray-900">{t('teams.createTeam')}</h2>
              <button
                onClick={() => {
                  setShowCreateTeam(false);
                  setNewTeamName('');
                  setNewTeamDescription('');
                }}
                className="text-gray-500 hover:text-gray-700 text-xl"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('teams.teamNameRequired')}
                </label>
                <input
                  type="text"
                  value={newTeamName}
                  onChange={(e) => setNewTeamName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                  placeholder={t('teams.enterTeamName')}
                  maxLength={50}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('teams.description')}
                </label>
                <textarea
                  value={newTeamDescription}
                  onChange={(e) => setNewTeamDescription(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                  placeholder={t('teams.descriptionPlaceholder')}
                  rows={3}
                  maxLength={200}
                />
              </div>
            </div>
            
            <div className="flex space-x-3 mt-6">
              <button
                onClick={() => {
                  setShowCreateTeam(false);
                  setNewTeamName('');
                  setNewTeamDescription('');
                }}
                className="flex-1 bg-gray-100 text-gray-700 py-2 rounded-lg hover:bg-gray-200 transition-colors text-sm"
              >
                {t('common.cancel')}
              </button>
              <button
                onClick={handleCreateTeam}
                disabled={isCreating || !newTeamName.trim()}
                className="flex-1 bg-blue-500 text-white py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
              >
                {isCreating ? t('teams.creating') : t('teams.createTeamButton')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TeamsInterface;