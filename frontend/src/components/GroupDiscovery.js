import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';

const GroupDiscovery = ({ user, token, api }) => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('discover');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedLocation, setSelectedLocation] = useState('all');
  const [selectedSchedule, setSelectedSchedule] = useState('all');
  const [selectedCost, setSelectedCost] = useState('all');
  const [selectedLanguage, setSelectedLanguage] = useState('all');
  
  const [groups, setGroups] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [trendingGroups, setTrendingGroups] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [error, setError] = useState(null);
  
  // Create group modal state
  const [showCreateGroupModal, setShowCreateGroupModal] = useState(false);
  const [createGroupForm, setCreateGroupForm] = useState({
    name: '',
    description: '',
    category: 'business',
    location: 'online',
    privacy: 'public',
    emoji: '👥'
  });
  const [isCreatingGroup, setIsCreatingGroup] = useState(false);

  const categories = [
    { value: 'all', label: 'All Categories', icon: '🌟' },
    { value: 'food', label: 'Food & Dining', icon: '🍛' },
    { value: 'business', label: 'Business & Tech', icon: '💻' },
    { value: 'outdoor', label: 'Outdoor & Sports', icon: '🏔️' },
    { value: 'creative', label: 'Arts & Creative', icon: '🎨' },
    { value: 'education', label: 'Learning & Books', icon: '📚' },
    { value: 'sports', label: 'Sports & Fitness', icon: '⚽' },
    { value: 'music', label: 'Music & Arts', icon: '🎵' },
    { value: 'gaming', label: 'Gaming', icon: '🎮' },
    { value: 'lifestyle', label: 'Lifestyle', icon: '✨' }
  ];

  const locations = [
    { value: 'all', label: 'All Locations' },
    { value: 'mumbai', label: 'Mumbai' },
    { value: 'delhi', label: 'Delhi' },
    { value: 'bangalore', label: 'Bangalore' },
    { value: 'pune', label: 'Pune' },
    { value: 'hyderabad', label: 'Hyderabad' },
    { value: 'chennai', label: 'Chennai' },
    { value: 'kolkata', label: 'Kolkata' },
    { value: 'online', label: 'Online' }
  ];

  const scheduleOptions = [
    { value: 'all', label: 'Any Schedule' },
    { value: 'weekend', label: 'Weekends' },
    { value: 'weekday', label: 'Weekdays' },
    { value: 'evening', label: 'Evenings' }
  ];

  const costOptions = [
    { value: 'all', label: 'Any Cost' },
    { value: 'free', label: 'Free' },
    { value: 'paid', label: 'Paid Activities' },
    { value: 'premium', label: 'Premium' }
  ];

  const languageOptions = [
    { value: 'all', label: 'All Languages' },
    { value: 'english', label: 'English' },
    { value: 'hindi', label: 'Hindi' },
    { value: 'marathi', label: 'Marathi' },
    { value: 'gujarati', label: 'Gujarati' }
  ];

  // Fetch groups with advanced filtering
  const fetchGroups = useCallback(async () => {
    if (!token || !api) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      if (selectedCategory !== 'all') params.append('category', selectedCategory);
      if (selectedLocation !== 'all') params.append('location', selectedLocation);
      if (selectedSchedule !== 'all') params.append('schedule', selectedSchedule);
      if (selectedCost !== 'all') params.append('cost', selectedCost);
      if (selectedLanguage !== 'all') params.append('language', selectedLanguage);
      if (searchQuery) params.append('search', searchQuery);

      const response = await axios.get(`${api}/teams/discover?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const transformedGroups = response.data.map(team => ({
        id: team.team_id,
        name: team.name,
        description: team.description || 'No description available',
        category: team.category || 'general',
        location: team.location || 'Online',
        members: team.member_count || 0,
        image: team.emoji || '👥',
        tags: team.tags || [],
        activity: team.activity_level || 'quiet',
        isJoined: team.is_joined || false,
        healthScore: team.health_score || 0,
        isTrending: team.is_trending || false,
        mutualFriends: team.mutual_friends || 0,
        recentActivity: team.recent_activity || [],
        creator: team.creator
      }));
      
      setGroups(transformedGroups);
    } catch (error) {
      console.error('Failed to fetch groups:', error);
      setError('Failed to load groups. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, [api, token, selectedCategory, selectedLocation, selectedSchedule, selectedCost, selectedLanguage, searchQuery]);

  // Fetch smart recommendations
  const fetchRecommendations = useCallback(async () => {
    if (!token || !api) return;
    
    try {
      const response = await axios.get(`${api}/teams/recommendations`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setRecommendations(response.data);
    } catch (error) {
      console.error('Failed to fetch recommendations:', error);
    }
  }, [api, token]);

  // Fetch trending groups
  const fetchTrendingGroups = useCallback(async () => {
    if (!token || !api) return;
    
    try {
      const response = await axios.get(`${api}/teams/trending`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTrendingGroups(response.data);
    } catch (error) {
      console.error('Failed to fetch trending groups:', error);
    }
  }, [api, token]);

  // Join group with optimistic updates
  const joinGroup = useCallback(async (groupId) => {
    if (!token || !api) return;
    
    try {
      // Optimistic update
      const updateGroupInState = (groupsArray, setGroupsArray) => {
        setGroupsArray(prev => prev.map(group => 
          group.id === groupId 
            ? { ...group, isJoined: true, members: group.members + 1 }
            : group
        ));
      };

      updateGroupInState(groups, setGroups);
      updateGroupInState(recommendations, setRecommendations);
      updateGroupInState(trendingGroups, setTrendingGroups);

      await axios.post(`${api}/teams/${groupId}/join`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
    } catch (error) {
      console.error('Failed to join group:', error);
      // Revert optimistic update
      const revertGroupInState = (groupsArray, setGroupsArray) => {
        setGroupsArray(prev => prev.map(group => 
          group.id === groupId 
            ? { ...group, isJoined: false, members: group.members - 1 }
            : group
        ));
      };

      revertGroupInState(groups, setGroups);
      revertGroupInState(recommendations, setRecommendations);
      revertGroupInState(trendingGroups, setTrendingGroups);
      
      setError('Failed to join group. Please try again.');
    }
  }, [api, token, groups, recommendations, trendingGroups]);

  // Leave group with optimistic updates
  const leaveGroup = useCallback(async (groupId) => {
    if (!token || !api) return;
    
    try {
      // Optimistic update
      const updateGroupInState = (groupsArray, setGroupsArray) => {
        setGroupsArray(prev => prev.map(group => 
          group.id === groupId 
            ? { ...group, isJoined: false, members: Math.max(0, group.members - 1) }
            : group
        ));
      };

      updateGroupInState(groups, setGroups);
      updateGroupInState(recommendations, setRecommendations);
      updateGroupInState(trendingGroups, setTrendingGroups);

      await axios.post(`${api}/teams/${groupId}/leave`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
    } catch (error) {
      console.error('Failed to leave group:', error);
      // Revert optimistic update
      const revertGroupInState = (groupsArray, setGroupsArray) => {
        setGroupsArray(prev => prev.map(group => 
          group.id === groupId 
            ? { ...group, isJoined: true, members: group.members + 1 }
            : group
        ));
      };

      revertGroupInState(groups, setGroups);
      revertGroupInState(recommendations, setRecommendations);
      revertGroupInState(trendingGroups, setTrendingGroups);
      
      setError('Failed to leave group. Please try again.');
    }
  }, [api, token, groups, recommendations, trendingGroups]);

  useEffect(() => {
    fetchGroups();
  }, [fetchGroups]);

  useEffect(() => {
    if (activeTab === 'discover') {
      fetchRecommendations();
      fetchTrendingGroups();
    }
  }, [activeTab, fetchRecommendations, fetchTrendingGroups]);

  // Clear error after 5 seconds
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  const ActivityIndicator = ({ level }) => {
    const colors = {
      'very_high': 'bg-green-500',
      'high': 'bg-green-400', 
      'medium': 'bg-yellow-400',
      'low': 'bg-orange-400',
      'quiet': 'bg-gray-400'
    };
    
    const labels = {
      'very_high': 'Very Active',
      'high': 'Active',
      'medium': 'Moderate',
      'low': 'Light',
      'quiet': 'Quiet'
    };

    return (
      <div className="flex items-center space-x-1">
        <div className={`w-2 h-2 rounded-full ${colors[level] || 'bg-gray-400'}`}></div>
        <span className="text-xs text-gray-600">{labels[level] || 'Unknown'}</span>
      </div>
    );
  };

  const HealthScore = ({ score }) => {
    const getColor = (score) => {
      if (score >= 80) return 'text-green-600 bg-green-100';
      if (score >= 60) return 'text-yellow-600 bg-yellow-100';
      if (score >= 40) return 'text-orange-600 bg-orange-100';
      return 'text-red-600 bg-red-100';
    };

    return (
      <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getColor(score)}`}>
        <span className="mr-1">💚</span>
        {score}% healthy
      </div>
    );
  };

  const GroupCard = ({ group, showRecommendationReason = false }) => (
    <div className="bg-white rounded-xl shadow-md hover:shadow-lg transition-all duration-300 border border-gray-100 relative">
      {group.isTrending && (
        <div className="absolute top-2 right-2 bg-red-500 text-white text-xs px-2 py-1 rounded-full flex items-center">
          <span className="mr-1">🔥</span>
          Trending
        </div>
      )}
      
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="text-3xl">{group.image}</div>
            <div>
              <h3 className="font-semibold text-gray-900 text-lg">{group.name}</h3>
              <div className="flex items-center text-sm text-gray-500 mt-1">
                <span className="mr-1">📍</span>
                {group.location}
              </div>
              {group.creator && (
                <div className="flex items-center text-xs text-gray-400 mt-1">
                  <span className="mr-1">👑</span>
                  by {group.creator.display_name}
                </div>
              )}
            </div>
          </div>
        </div>
        
        <p className="text-gray-600 mb-4">{group.description}</p>
        
        {/* Health Score and Activity Level */}
        <div className="flex items-center space-x-3 mb-4">
          <HealthScore score={group.healthScore} />
          <ActivityIndicator level={group.activity} />
        </div>

        {/* Mutual Friends Indicator */}
        {group.mutualFriends > 0 && (
          <div className="bg-blue-50 text-blue-700 text-sm px-3 py-2 rounded-lg mb-4">
            <span className="mr-1">👥</span>
            {group.mutualFriends} mutual friend{group.mutualFriends > 1 ? 's' : ''} in this group
          </div>
        )}

        {/* Recommendation Reason */}
        {showRecommendationReason && group.recommendation_reason && (
          <div className="bg-purple-50 text-purple-700 text-sm px-3 py-2 rounded-lg mb-4">
            <span className="mr-1">✨</span>
            {group.recommendation_reason}
          </div>
        )}

        {/* Recent Activity Preview */}
        {group.recentActivity && group.recentActivity.length > 0 && (
          <div className="bg-gray-50 rounded-lg p-3 mb-4">
            <div className="text-xs text-gray-500 mb-2">Recent Activity:</div>
            {group.recentActivity.slice(0, 2).map((activity, index) => (
              <div key={index} className="text-xs text-gray-600 mb-1">
                <span className="font-medium">{activity.sender}:</span> {activity.content}
              </div>
            ))}
          </div>
        )}

        {group.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            {group.tags.map((tag, index) => (
              <span key={index} className="px-2 py-1 bg-blue-100 text-blue-600 text-xs rounded-full">
                {tag}
              </span>
            ))}
          </div>
        )}
        
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4 text-sm text-gray-500">
            <div className="flex items-center">
              <span className="mr-1">👥</span>
              {group.members} members
            </div>
          </div>
          
          <button 
            onClick={() => group.isJoined ? leaveGroup(group.id) : joinGroup(group.id)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              group.isJoined 
                ? 'bg-green-100 text-green-700 hover:bg-green-200' 
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {group.isJoined ? 'Joined' : 'Join Group'}
          </button>
        </div>
      </div>
    </div>
  );

  if (!token || !api) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">⚠️</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Authentication Required</h2>
          <p className="text-gray-600">Please log in to access group discovery features.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Error Message */}
      {error && (
        <div className="fixed top-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded z-50">
          <div className="flex items-center">
            <span className="mr-2">❌</span>
            {error}
          </div>
        </div>
      )}

      {/* Header */}
      <div className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-2xl font-bold text-gray-900">Smart Group Discovery</h1>
            <button 
              onClick={() => {/* TODO: Open create group modal */}}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <span className="mr-2">➕</span>
              Create Group
            </button>
          </div>
          
          {/* Tab Navigation */}
          <div className="flex space-x-6 border-b border-gray-200">
            {[
              { key: 'discover', label: '🔍 Discover', count: groups.length },
              { key: 'recommendations', label: '✨ For You', count: recommendations.length },
              { key: 'trending', label: '🔥 Trending', count: trendingGroups.length },
              { key: 'my-groups', label: '👥 My Groups', count: groups.filter(g => g.isJoined).length }
            ].map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`pb-2 px-1 font-medium text-sm transition-colors relative ${
                  activeTab === tab.key
                    ? 'text-blue-600 border-b-2 border-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.label}
                {tab.count > 0 && (
                  <span className="ml-1 bg-gray-200 text-gray-600 text-xs rounded-full px-2 py-1">
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-6">
        {activeTab === 'discover' && (
          <>
            {/* Enhanced Search and Filters */}
            <div className="mb-6 space-y-4">
              <div className="relative">
                <span className="absolute left-3 top-3 text-gray-400">🔍</span>
                <input
                  type="text"
                  placeholder="Search groups by name, description, or tags..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              
              <div className="flex flex-wrap gap-4">
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  {categories.map(cat => (
                    <option key={cat.value} value={cat.value}>
                      {cat.icon} {cat.label}
                    </option>
                  ))}
                </select>
                
                <select
                  value={selectedLocation}
                  onChange={(e) => setSelectedLocation(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  {locations.map(loc => (
                    <option key={loc.value} value={loc.value}>
                      📍 {loc.label}
                    </option>
                  ))}
                </select>

                <button
                  onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  🔧 Advanced Filters
                </button>
              </div>

              {/* Advanced Filters */}
              {showAdvancedFilters && (
                <div className="bg-gray-50 p-4 rounded-lg space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Schedule</label>
                      <select
                        value={selectedSchedule}
                        onChange={(e) => setSelectedSchedule(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      >
                        {scheduleOptions.map(opt => (
                          <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Cost</label>
                      <select
                        value={selectedCost}
                        onChange={(e) => setSelectedCost(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      >
                        {costOptions.map(opt => (
                          <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Language</label>
                      <select
                        value={selectedLanguage}
                        onChange={(e) => setSelectedLanguage(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      >
                        {languageOptions.map(opt => (
                          <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Results */}
            <div className="mb-4">
              <p className="text-gray-600">
                Found {groups.length} groups matching your criteria
              </p>
            </div>

            {/* Groups Grid */}
            {isLoading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-4 text-gray-600">Loading groups...</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {groups.map(group => (
                  <GroupCard key={group.id} group={group} />
                ))}
              </div>
            )}
          </>
        )}

        {activeTab === 'recommendations' && (
          <div>
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">✨ Recommended For You</h2>
              <p className="text-gray-600">Groups we think you'll love based on your interests and activity</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {recommendations.map(group => (
                <GroupCard key={group.team_id} group={{
                  id: group.team_id,
                  name: group.name,
                  description: group.description,
                  category: group.category,
                  location: group.location,
                  members: group.member_count || 0,
                  image: group.emoji || '👥',
                  tags: group.tags || [],
                  isJoined: group.is_joined,
                  recommendation_reason: group.recommendation_reason,
                  healthScore: 85 // Default for recommendations
                }} showRecommendationReason={true} />
              ))}
            </div>
            
            {recommendations.length === 0 && (
              <div className="text-center py-12">
                <span className="text-6xl">🤖</span>
                <h3 className="text-lg font-semibold text-gray-900 mb-2 mt-4">Building Your Recommendations</h3>
                <p className="text-gray-600">Join a few groups to get personalized recommendations</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'trending' && (
          <div>
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">🔥 Trending Groups</h2>
              <p className="text-gray-600">Hot groups gaining momentum in your area</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {trendingGroups.map(group => (
                <GroupCard key={group.team_id} group={{
                  id: group.team_id,
                  name: group.name,
                  description: group.description,
                  category: group.category,
                  location: group.location,
                  members: group.member_count || 0,
                  image: group.emoji || '👥',
                  tags: group.tags || [],
                  isJoined: group.is_joined,
                  isTrending: true,
                  healthScore: 90 // High for trending
                }} />
              ))}
            </div>
            
            {trendingGroups.length === 0 && (
              <div className="text-center py-12">
                <span className="text-6xl">📈</span>
                <h3 className="text-lg font-semibold text-gray-900 mb-2 mt-4">No Trending Groups Yet</h3>
                <p className="text-gray-600">Check back later for trending groups in your area</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'my-groups' && (
          <div>
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">👥 My Groups</h2>
              <p className="text-gray-600">Groups you've joined and communities you're part of</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {groups.filter(group => group.isJoined).map(group => (
                <GroupCard key={group.id} group={group} />
              ))}
            </div>
            
            {groups.filter(group => group.isJoined).length === 0 && (
              <div className="text-center py-12">
                <span className="text-6xl">👥</span>
                <h3 className="text-lg font-semibold text-gray-900 mb-2 mt-4">You haven't joined any groups yet</h3>
                <p className="text-gray-600 mb-6">Discover amazing communities and connect with like-minded people</p>
                <button 
                  onClick={() => setActiveTab('discover')}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Discover Groups
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default GroupDiscovery;