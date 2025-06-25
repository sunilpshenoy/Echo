import React, { useState, useEffect } from 'react';
import axios from 'axios';

const TaskManager = ({ user, token, workspaceMode, onClose }) => {
  const [tasks, setTasks] = useState([]);
  const [showCreateTask, setShowCreateTask] = useState(false);
  const [filter, setFilter] = useState('all');
  const [taskForm, setTaskForm] = useState({
    title: '',
    description: '',
    due_date: '',
    priority: 'medium',
    assigned_to: '',
    tags: [],
    estimated_hours: null
  });

  const API = process.env.REACT_APP_BACKEND_URL + '/api';

  const getAuthHeaders = () => ({
    headers: { Authorization: `Bearer ${token}` }
  });

  useEffect(() => {
    fetchTasks();
  }, [workspaceMode, filter]);

  const fetchTasks = async () => {
    try {
      const params = new URLSearchParams();
      if (filter !== 'all') params.append('status', filter);
      params.append('workspace_mode', workspaceMode);
      
      const response = await axios.get(
        `${API}/tasks?${params.toString()}`,
        getAuthHeaders()
      );
      setTasks(response.data);
    } catch (error) {
      console.error('Error fetching tasks:', error);
    }
  };

  const createTask = async () => {
    try {
      await axios.post(`${API}/tasks`, {
        ...taskForm,
        workspace_mode: workspaceMode
      }, getAuthHeaders());
      setTaskForm({
        title: '', description: '', due_date: '', priority: 'medium',
        assigned_to: '', tags: [], estimated_hours: null
      });
      setShowCreateTask(false);
      fetchTasks();
    } catch (error) {
      console.error('Error creating task:', error);
    }
  };

  const updateTaskStatus = async (taskId, status) => {
    try {
      await axios.put(`${API}/tasks/${taskId}`, { status }, getAuthHeaders());
      fetchTasks();
    } catch (error) {
      console.error('Error updating task:', error);
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'urgent': return 'bg-red-100 text-red-800 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'in_progress': return 'bg-blue-100 text-blue-800';
      case 'pending': return 'bg-gray-100 text-gray-800';
      case 'cancelled': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'No due date';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-5xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">
            ✅ Tasks ({workspaceMode === 'business' ? 'Work' : 'Personal'})
          </h2>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowCreateTask(true)}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
            >
              + New Task
            </button>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 p-2"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex space-x-2 mb-6">
          {[
            { key: 'all', label: 'All Tasks', count: tasks.length },
            { key: 'pending', label: 'Pending', count: tasks.filter(t => t.status === 'pending').length },
            { key: 'in_progress', label: 'In Progress', count: tasks.filter(t => t.status === 'in_progress').length },
            { key: 'completed', label: 'Completed', count: tasks.filter(t => t.status === 'completed').length }
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setFilter(tab.key)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                filter === tab.key
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {tab.label} ({tab.count})
            </button>
          ))}
        </div>

        {/* Tasks List */}
        <div className="space-y-4">
          {tasks.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <div className="text-6xl mb-4">📝</div>
              <p className="text-lg font-medium">No tasks found</p>
              <p>Create your first task to get started!</p>
            </div>
          ) : (
            tasks.map(task => (
              <div
                key={task.task_id}
                className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className={`font-semibold ${
                        task.status === 'completed' ? 'line-through text-gray-500' : 'text-gray-900'
                      }`}>
                        {task.title}
                      </h3>
                      <span className={`px-2 py-1 text-xs rounded-full border ${getPriorityColor(task.priority)}`}>
                        {task.priority}
                      </span>
                      <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(task.status)}`}>
                        {task.status.replace('_', ' ')}
                      </span>
                    </div>
                    
                    {task.description && (
                      <p className="text-gray-600 mb-3">{task.description}</p>
                    )}
                    
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <span>📅 Due: {formatDate(task.due_date)}</span>
                      {task.estimated_hours && (
                        <span>⏱️ Est: {task.estimated_hours}h</span>
                      )}
                      {task.tags && task.tags.length > 0 && (
                        <div className="flex space-x-1">
                          {task.tags.map(tag => (
                            <span key={tag} className="bg-gray-100 text-gray-600 px-2 py-1 rounded-full text-xs">
                              #{tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex space-x-2">
                    {task.status !== 'completed' && (
                      <>
                        {task.status === 'pending' && (
                          <button
                            onClick={() => updateTaskStatus(task.task_id, 'in_progress')}
                            className="bg-blue-100 text-blue-700 px-3 py-1 rounded-lg text-sm hover:bg-blue-200 transition-colors"
                          >
                            Start
                          </button>
                        )}
                        <button
                          onClick={() => updateTaskStatus(task.task_id, 'completed')}
                          className="bg-green-100 text-green-700 px-3 py-1 rounded-lg text-sm hover:bg-green-200 transition-colors"
                        >
                          Complete
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Create Task Modal */}
        {showCreateTask && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-96 max-w-[90vw]">
              <h3 className="text-lg font-semibold mb-4">Create New Task</h3>
              <form onSubmit={(e) => { e.preventDefault(); createTask(); }}>
                <div className="space-y-4">
                  <input
                    type="text"
                    placeholder="Task Title"
                    value={taskForm.title}
                    onChange={(e) => setTaskForm({...taskForm, title: e.target.value})}
                    className="w-full p-3 border rounded-lg"
                    required
                  />
                  <textarea
                    placeholder="Description"
                    value={taskForm.description}
                    onChange={(e) => setTaskForm({...taskForm, description: e.target.value})}
                    className="w-full p-3 border rounded-lg h-20"
                  />
                  <input
                    type="datetime-local"
                    value={taskForm.due_date}
                    onChange={(e) => setTaskForm({...taskForm, due_date: e.target.value})}
                    className="w-full p-3 border rounded-lg"
                  />
                  <select
                    value={taskForm.priority}
                    onChange={(e) => setTaskForm({...taskForm, priority: e.target.value})}
                    className="w-full p-3 border rounded-lg"
                  >
                    <option value="low">Low Priority</option>
                    <option value="medium">Medium Priority</option>
                    <option value="high">High Priority</option>
                    <option value="urgent">Urgent</option>
                  </select>
                  <input
                    type="number"
                    placeholder="Estimated Hours"
                    value={taskForm.estimated_hours || ''}
                    onChange={(e) => setTaskForm({...taskForm, estimated_hours: e.target.value ? parseFloat(e.target.value) : null})}
                    className="w-full p-3 border rounded-lg"
                  />
                </div>
                <div className="flex space-x-3 mt-6">
                  <button
                    type="button"
                    onClick={() => setShowCreateTask(false)}
                    className="flex-1 py-2 border rounded-lg"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="flex-1 py-2 bg-green-600 text-white rounded-lg"
                  >
                    Create Task
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

export default TaskManager;