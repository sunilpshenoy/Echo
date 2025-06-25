import React, { useState, useEffect } from 'react';
import axios from 'axios';

const WorkspaceSwitcher = ({ user, token, currentMode, onModeChange, onClose }) => {
  const [workspaceProfile, setWorkspaceProfile] = useState(null);
  const [showCreateProfile, setShowCreateProfile] = useState(false);
  const [workspaceForm, setWorkspaceForm] = useState({
    workspace_name: '',
    workspace_type: 'business',
    company_name: '',
    department: '',
    job_title: '',
    work_email: '',
    work_phone: ''
  });

  const API = process.env.REACT_APP_BACKEND_URL + '/api';

  const getAuthHeaders = () => ({
    headers: { Authorization: `Bearer ${token}` }
  });

  useEffect(() => {
    fetchWorkspaceProfile();
  }, []);

  const fetchWorkspaceProfile = async () => {
    try {
      const response = await axios.get(`${API}/workspace/profile`, getAuthHeaders());
      setWorkspaceProfile(response.data);
    } catch (error) {
      console.error('Error fetching workspace profile:', error);
    }
  };

  const switchMode = async (mode) => {
    try {
      await axios.put(`${API}/workspace/mode`, { mode }, getAuthHeaders());
      onModeChange(mode);
    } catch (error) {
      console.error('Error switching workspace mode:', error);
    }
  };

  const createWorkspaceProfile = async () => {
    try {
      await axios.post(`${API}/workspace/profile`, workspaceForm, getAuthHeaders());
      setShowCreateProfile(false);
      fetchWorkspaceProfile();
    } catch (error) {
      console.error('Error creating workspace profile:', error);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-96 max-w-[90vw]">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900">🏢 Workspace</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 p-2"
          >
            ✕
          </button>
        </div>

        {/* Current Mode Display */}
        <div className="mb-6">
          <p className="text-sm text-gray-600 mb-2">Current Mode:</p>
          <div className={`p-3 rounded-lg border-2 ${
            currentMode === 'personal' 
              ? 'bg-blue-50 border-blue-300 text-blue-800' 
              : 'bg-purple-50 border-purple-300 text-purple-800'
          }`}>
            <div className="flex items-center">
              <span className="text-2xl mr-3">
                {currentMode === 'personal' ? '🏠' : '🏢'}
              </span>
              <div>
                <p className="font-semibold capitalize">{currentMode} Mode</p>
                <p className="text-sm opacity-75">
                  {currentMode === 'personal' 
                    ? 'Personal chats, events, and tasks' 
                    : 'Work-related communications and projects'
                  }
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Mode Switch Buttons */}
        <div className="space-y-3 mb-6">
          <button
            onClick={() => switchMode('personal')}
            className={`w-full p-4 rounded-lg border-2 text-left transition-all ${
              currentMode === 'personal'
                ? 'bg-blue-50 border-blue-300 text-blue-800'
                : 'bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100'
            }`}
          >
            <div className="flex items-center">
              <span className="text-2xl mr-3">🏠</span>
              <div>
                <p className="font-semibold">Personal Mode</p>
                <p className="text-sm opacity-75">
                  Personal chats, family, friends, hobbies
                </p>
              </div>
            </div>
          </button>

          <button
            onClick={() => switchMode('business')}
            disabled={!workspaceProfile?.is_active}
            className={`w-full p-4 rounded-lg border-2 text-left transition-all ${
              currentMode === 'business'
                ? 'bg-purple-50 border-purple-300 text-purple-800'
                : workspaceProfile?.is_active
                ? 'bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100'
                : 'bg-gray-100 border-gray-300 text-gray-400 cursor-not-allowed'
            }`}
          >
            <div className="flex items-center">
              <span className="text-2xl mr-3">🏢</span>
              <div>
                <p className="font-semibold">Business Mode</p>
                <p className="text-sm opacity-75">
                  {workspaceProfile?.is_active 
                    ? `${workspaceProfile.company_name || 'Work'} - ${workspaceProfile.job_title || 'Professional'}`
                    : 'Set up your workspace profile to enable'
                  }
                </p>
              </div>
            </div>
          </button>
        </div>

        {/* Workspace Profile Section */}
        {workspaceProfile?.is_active ? (
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-3">Workspace Profile</h3>
            <div className="space-y-2 text-sm">
              <div><strong>Name:</strong> {workspaceProfile.workspace_name}</div>
              {workspaceProfile.company_name && (
                <div><strong>Company:</strong> {workspaceProfile.company_name}</div>
              )}
              {workspaceProfile.job_title && (
                <div><strong>Role:</strong> {workspaceProfile.job_title}</div>
              )}
              {workspaceProfile.department && (
                <div><strong>Department:</strong> {workspaceProfile.department}</div>
              )}
            </div>
            <button
              onClick={() => setShowCreateProfile(true)}
              className="mt-3 text-blue-600 hover:text-blue-800 text-sm"
            >
              Edit Profile
            </button>
          </div>
        ) : (
          <div className="text-center">
            <button
              onClick={() => setShowCreateProfile(true)}
              className="bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 transition-colors"
            >
              Set Up Workspace Profile
            </button>
          </div>
        )}

        {/* Create/Edit Workspace Profile Modal */}
        {showCreateProfile && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-96 max-w-[90vw] max-h-[80vh] overflow-y-auto">
              <h3 className="text-lg font-semibold mb-4">
                {workspaceProfile?.is_active ? 'Edit' : 'Create'} Workspace Profile
              </h3>
              <form onSubmit={(e) => { e.preventDefault(); createWorkspaceProfile(); }}>
                <div className="space-y-4">
                  <input
                    type="text"
                    placeholder="Workspace Name"
                    value={workspaceForm.workspace_name}
                    onChange={(e) => setWorkspaceForm({...workspaceForm, workspace_name: e.target.value})}
                    className="w-full p-3 border rounded-lg"
                    required
                  />
                  <select
                    value={workspaceForm.workspace_type}
                    onChange={(e) => setWorkspaceForm({...workspaceForm, workspace_type: e.target.value})}
                    className="w-full p-3 border rounded-lg"
                  >
                    <option value="business">Business</option>
                    <option value="team">Team</option>
                    <option value="organization">Organization</option>
                  </select>
                  <input
                    type="text"
                    placeholder="Company Name"
                    value={workspaceForm.company_name}
                    onChange={(e) => setWorkspaceForm({...workspaceForm, company_name: e.target.value})}
                    className="w-full p-3 border rounded-lg"
                  />
                  <input
                    type="text"
                    placeholder="Department"
                    value={workspaceForm.department}
                    onChange={(e) => setWorkspaceForm({...workspaceForm, department: e.target.value})}
                    className="w-full p-3 border rounded-lg"
                  />
                  <input
                    type="text"
                    placeholder="Job Title"
                    value={workspaceForm.job_title}
                    onChange={(e) => setWorkspaceForm({...workspaceForm, job_title: e.target.value})}
                    className="w-full p-3 border rounded-lg"
                  />
                  <input
                    type="email"
                    placeholder="Work Email"
                    value={workspaceForm.work_email}
                    onChange={(e) => setWorkspaceForm({...workspaceForm, work_email: e.target.value})}
                    className="w-full p-3 border rounded-lg"
                  />
                  <input
                    type="tel"
                    placeholder="Work Phone"
                    value={workspaceForm.work_phone}
                    onChange={(e) => setWorkspaceForm({...workspaceForm, work_phone: e.target.value})}
                    className="w-full p-3 border rounded-lg"
                  />
                </div>
                <div className="flex space-x-3 mt-6">
                  <button
                    type="button"
                    onClick={() => setShowCreateProfile(false)}
                    className="flex-1 py-2 border rounded-lg"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="flex-1 py-2 bg-purple-600 text-white rounded-lg"
                  >
                    {workspaceProfile?.is_active ? 'Update' : 'Create'} Profile
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkspaceSwitcher;