import React, { useState, useEffect } from 'react';
import axios from 'axios';

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
      
      alert(`Team "${newTeamName}" created successfully! 👥`);
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
      const errorMessage = error.response?.data?.detail || 'Failed to create team. Please try again.';
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

  return (
    <div className="flex w-full h-full">
      {/* Teams List Sidebar */}
      <div className="w-1/3 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Teams</h2>
              <p className="text-sm text-gray-600">Groups & workspaces</p>
            </div>
            <button 
              onClick={() => setShowCreateTeam(true)}
              className="bg-blue-500 text-white p-2 rounded-lg hover:bg-blue-600 transition-colors"
              title="Create New Team"
            >
              ➕
            </button>
          </div>
        </div>
        
        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="loading-spinner w-6 h-6"></div>
            </div>
          ) : teams && teams.length > 0 ? (
            <div className="space-y-1 p-2">
              {teams.map(team => (
                <button
                  key={team.team_id || team.id}
                  onClick={() => handleTeamClick(team)}
                  className={`w-full p-3 rounded-lg text-left hover:bg-gray-50 transition-colors ${
                    selectedTeam?.team_id === team.team_id || selectedTeam?.id === team.id ? 'bg-blue-50 border border-blue-200' : ''
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-purple-500 rounded-lg flex items-center justify-center">
                      <span className="text-white font-medium text-sm">
                        {team.name?.[0]?.toUpperCase() || 'T'}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 truncate">
                        {team.name || 'Unnamed Team'}
                      </p>
                      <p className="text-sm text-gray-600 truncate">
                        {team.member_count || team.members?.length || 0} members
                      </p>
                    </div>
                    <div className="text-xs text-gray-500">
                      {team.last_activity && 
                        new Date(team.last_activity).toLocaleDateString()
                      }
                    </div>
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-64 text-center p-4">
              <div className="text-6xl mb-4">👥</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No teams yet</h3>
              <p className="text-gray-600 text-sm mb-4">
                Create or join teams to collaborate with groups
              </p>
              <button 
                onClick={() => setShowCreateTeam(true)}
                className="btn-primary bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors"
              >
                Create Your First Team
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Team Content Area */}
      <div className="flex-1 flex flex-col">
        {selectedTeam ? (
          <>
            {/* Team Header */}
            <div className="bg-white p-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-purple-500 rounded-lg flex items-center justify-center">
                    <span className="text-white font-medium text-lg">
                      {selectedTeam.name?.[0]?.toUpperCase() || 'T'}
                    </span>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {selectedTeam.name || 'Unnamed Team'}
                    </h3>
                    <p className="text-sm text-gray-600">
                      {selectedTeam.member_count || selectedTeam.members?.length || 0} members • {selectedTeam.type || 'General'}
                    </p>
                  </div>
                </div>
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
            </div>

            {/* Team Messages Area */}
            <div className="flex-1 bg-gray-50 flex items-center justify-center">
              <div className="text-center">
                <div className="text-4xl mb-4">💬</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Welcome to {selectedTeam.name}
                </h3>
                <p className="text-gray-600 mb-4">
                  {selectedTeam.description || 'Start collaborating with your team members'}
                </p>
                <button className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors">
                  Send First Message
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
                  placeholder={`Message ${selectedTeam.name}`}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <button className="bg-blue-500 text-white p-2 rounded-lg hover:bg-blue-600 transition-colors">
                  ➤
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center bg-gray-50">
            <div className="text-center max-w-md">
              <div className="text-6xl mb-6">🚀</div>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Collaborate in Teams
              </h2>
              <p className="text-gray-600 mb-6">
                Create teams for work projects, interest groups, or friend circles. 
                Share files, have group calls, and build together.
              </p>
              
              <div className="bg-white rounded-lg p-6 shadow-sm border mb-6">
                <h3 className="font-semibold text-gray-900 mb-3">Team Features:</h3>
                <div className="space-y-2 text-left text-sm text-gray-700">
                  <div className="flex items-center space-x-2">
                    <span className="text-green-500">✓</span>
                    <span>Group messaging and file sharing</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-green-500">✓</span>
                    <span>Voice and video group calls</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-green-500">✓</span>
                    <span>Project collaboration tools</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-green-500">✓</span>
                    <span>Member management and roles</span>
                  </div>
                </div>
              </div>

              <button 
                onClick={() => setShowCreateTeam(true)}
                className="bg-blue-500 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-600 transition-colors"
              >
                Create Your First Team
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Create Team Modal */}
      {showCreateTeam && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999] p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold text-gray-900">Create New Team</h2>
              <button
                onClick={() => {
                  setShowCreateTeam(false);
                  setNewTeamName('');
                  setNewTeamDescription('');
                }}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Team Name *
                </label>
                <input
                  type="text"
                  value={newTeamName}
                  onChange={(e) => setNewTeamName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter team name"
                  maxLength={50}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  value={newTeamDescription}
                  onChange={(e) => setNewTeamDescription(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="What's this team about?"
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
                className="flex-1 bg-gray-100 text-gray-700 py-2 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateTeam}
                disabled={isCreating || !newTeamName.trim()}
                className="flex-1 bg-blue-500 text-white py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isCreating ? 'Creating...' : 'Create Team'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TeamsInterface;