import React, { useState } from 'react';
import axios from 'axios';

const TeamsInterface = ({ 
  user, 
  token, 
  api, 
  teams, 
  selectedTeam, 
  isLoading 
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
      
      // Refresh teams list (if parent provides refresh function)
      if (window.location.reload) {
        setTimeout(() => window.location.reload(), 1000);
      }
      
    } catch (error) {
      console.error('Failed to create team:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to create team. Please try again.';
      alert(errorMessage);
    } finally {
      setIsCreating(false);
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
                  key={team.team_id}
                  className={`w-full p-3 rounded-lg text-left hover:bg-gray-50 transition-colors ${
                    selectedTeam?.team_id === team.team_id ? 'bg-blue-50 border border-blue-200' : ''
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
                        {team.member_count || 0} members
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
                Create or join teams to collaborate
              </p>
              <button 
                onClick={() => setShowCreateTeam(true)}
                className="btn-primary"
              >
                Create Team
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
                      {selectedTeam.member_count || 0} members • {selectedTeam.type || 'General'}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button className="text-gray-600 hover:text-gray-800 p-2">
                    🔍
                  </button>
                  <button className="text-gray-600 hover:text-gray-800 p-2">
                    ⚙️
                  </button>
                </div>
              </div>
            </div>

            {/* Team Content */}
            <div className="flex-1 bg-gray-50 p-6">
              <div className="max-w-2xl mx-auto text-center">
                <div className="text-6xl mb-4">🚧</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  Teams Coming Soon
                </h3>
                <p className="text-gray-600 mb-6">
                  Team collaboration features are being developed. You'll be able to:
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
                  <div className="bg-white p-4 rounded-lg border">
                    <div className="text-2xl mb-2">💬</div>
                    <h4 className="font-medium text-gray-900 mb-1">Group Chats</h4>
                    <p className="text-sm text-gray-600">Team messaging with channels</p>
                  </div>
                  <div className="bg-white p-4 rounded-lg border">
                    <div className="text-2xl mb-2">📅</div>
                    <h4 className="font-medium text-gray-900 mb-1">Shared Calendar</h4>
                    <p className="text-sm text-gray-600">Team events and scheduling</p>
                  </div>
                  <div className="bg-white p-4 rounded-lg border">
                    <div className="text-2xl mb-2">📋</div>
                    <h4 className="font-medium text-gray-900 mb-1">Task Management</h4>
                    <p className="text-sm text-gray-600">Collaborative project tracking</p>
                  </div>
                  <div className="bg-white p-4 rounded-lg border">
                    <div className="text-2xl mb-2">📁</div>
                    <h4 className="font-medium text-gray-900 mb-1">File Sharing</h4>
                    <p className="text-sm text-gray-600">Team document repository</p>
                  </div>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center h-full bg-gray-50">
            <div className="text-center">
              <div className="text-6xl mb-4">👥</div>
              <h3 className="text-xl font-medium text-gray-900 mb-2">
                Select a team to collaborate
              </h3>
              <p className="text-gray-600">
                Choose a team from the sidebar to start collaborating
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Create Team Modal */}
      {showCreateTeam && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold text-gray-900">Create New Team</h2>
              <button
                onClick={() => setShowCreateTeam(false)}
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
                  placeholder="Enter team name"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description (Optional)
                </label>
                <textarea
                  value={newTeamDescription}
                  onChange={(e) => setNewTeamDescription(e.target.value)}
                  placeholder="Describe what this team is for"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent h-24 resize-none"
                />
              </div>
              
              <div className="flex space-x-3 pt-4">
                <button
                  onClick={() => setShowCreateTeam(false)}
                  className="flex-1 bg-gray-200 text-gray-800 py-2 px-4 rounded-lg hover:bg-gray-300"
                  disabled={isCreating}
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateTeam}
                  disabled={!newTeamName.trim() || isCreating}
                  className="flex-1 bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  {isCreating ? (
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Creating...
                    </div>
                  ) : (
                    'Create Team'
                  )}
                </button>
              </div>
              
              <p className="text-xs text-gray-500 text-center pt-2">
                💡 Team features are coming soon! This is a preview of the creation flow.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TeamsInterface;