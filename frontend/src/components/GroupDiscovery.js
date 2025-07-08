import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';

const GroupDiscovery = ({ user, token, api }) => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('discover');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedLocation, setSelectedLocation] = useState('all');
  const [groups, setGroups] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const categories = [
    { value: 'all', label: t('groups.categories.all'), icon: '🌟' },
    { value: 'food', label: t('groups.categories.food'), icon: '🍛' },
    { value: 'business', label: t('groups.categories.business'), icon: '💻' },
    { value: 'outdoor', label: t('groups.categories.outdoor'), icon: '🏔️' },
    { value: 'creative', label: t('groups.categories.creative'), icon: '🎨' },
    { value: 'education', label: t('groups.categories.education'), icon: '📚' },
    { value: 'sports', label: t('groups.categories.sports'), icon: '⚽' },
    { value: 'music', label: t('groups.categories.music'), icon: '🎵' },
    { value: 'gaming', label: t('groups.categories.gaming'), icon: '🎮' },
    { value: 'lifestyle', label: t('groups.categories.lifestyle'), icon: '✨' }
  ];

  const locations = [
    { value: 'all', label: t('groups.locations.all') },
    { value: 'mumbai', label: 'Mumbai' },
    { value: 'delhi', label: 'Delhi' },
    { value: 'bangalore', label: 'Bangalore' },
    { value: 'pune', label: 'Pune' },
    { value: 'hyderabad', label: 'Hyderabad' },
    { value: 'chennai', label: 'Chennai' },
    { value: 'kolkata', label: 'Kolkata' },
    { value: 'online', label: t('groups.locations.online') }
  ];

  // Fetch groups from backend
  const fetchGroups = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get(`${api}/teams/discover`, {
        headers: { Authorization: `Bearer ${token}` },
        params: {
          category: selectedCategory !== 'all' ? selectedCategory : undefined,
          location: selectedLocation !== 'all' ? selectedLocation : undefined,
          search: searchQuery || undefined
        }
      });
      
      // Transform teams data to match group structure
      const transformedGroups = response.data.map(team => ({
        id: team.team_id,
        name: team.name,
        description: team.description || 'No description available',
        category: team.category || 'general',
        location: team.location || 'Online',
        members: team.member_count || 0,
        image: team.emoji || '👥',
        tags: team.tags || [],
        activity: 'Recently active',
        isJoined: team.is_joined || false,
        created_at: team.created_at,
        privacy: team.settings?.is_public ? 'public' : 'private'
      }));
      
      setGroups(transformedGroups);
    } catch (error) {
      console.error('Failed to fetch groups:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Join group
  const joinGroup = async (groupId) => {
    try {
      await axios.post(`${api}/teams/${groupId}/join`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Update local state
      setGroups(groups.map(group => 
        group.id === groupId 
          ? { ...group, isJoined: true, members: group.members + 1 }
          : group
      ));
    } catch (error) {
      console.error('Failed to join group:', error);
    }
  };

  // Leave group
  const leaveGroup = async (groupId) => {
    try {
      await axios.post(`${api}/teams/${groupId}/leave`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Update local state
      setGroups(groups.map(group => 
        group.id === groupId 
          ? { ...group, isJoined: false, members: Math.max(0, group.members - 1) }
          : group
      ));
    } catch (error) {
      console.error('Failed to leave group:', error);
    }
  };

  useEffect(() => {
    fetchGroups();
  }, [selectedCategory, selectedLocation, searchQuery]);

  // Filter groups based on search and filters
  const filteredGroups = groups.filter(group => {
    const matchesSearch = searchQuery === '' || 
                         group.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         group.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         group.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesSearch;
  });

  const GroupCard = ({ group }) => (
    <div className="bg-white rounded-xl shadow-md hover:shadow-lg transition-all duration-300 border border-gray-100">
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
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-gray-400 hover:text-red-500 cursor-pointer">❤️</span>
            <span className="text-gray-400 hover:text-yellow-500 cursor-pointer">⭐</span>
          </div>
        </div>
        
        <p className="text-gray-600 mb-4">{group.description}</p>
        
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
            <div className="flex items-center">
              <span className="mr-1">🕒</span>
              {group.activity}
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

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-2xl font-bold text-gray-900">Groups & Communities</h1>
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
            <button
              onClick={() => setActiveTab('discover')}
              className={`pb-2 px-1 font-medium text-sm transition-colors ${
                activeTab === 'discover'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Discover Groups
            </button>
            <button
              onClick={() => setActiveTab('activities')}
              className={`pb-2 px-1 font-medium text-sm transition-colors ${
                activeTab === 'activities'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Activities
            </button>
            <button
              onClick={() => setActiveTab('my-groups')}
              className={`pb-2 px-1 font-medium text-sm transition-colors ${
                activeTab === 'my-groups'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              My Groups
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-6">
        {activeTab === 'discover' && (
          <>
            {/* Search and Filters */}
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
                <div className="flex items-center space-x-2">
                  <span className="text-gray-500">🔽</span>
                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    {categories.map(cat => (
                      <option key={cat.value} value={cat.value}>
                        {cat.icon} {cat.label}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div className="flex items-center space-x-2">
                  <span className="text-gray-500">📍</span>
                  <select
                    value={selectedLocation}
                    onChange={(e) => setSelectedLocation(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    {locations.map(loc => (
                      <option key={loc.value} value={loc.value}>
                        {loc.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Results */}
            <div className="mb-4">
              <p className="text-gray-600">
                Found {filteredGroups.length} groups matching your criteria
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
                {filteredGroups.map(group => (
                  <GroupCard key={group.id} group={group} />
                ))}
              </div>
            )}
          </>
        )}

        {activeTab === 'activities' && (
          <div className="text-center py-12">
            <span className="text-6xl">📅</span>
            <h3 className="text-lg font-semibold text-gray-900 mb-2 mt-4">Activities Coming Soon</h3>
            <p className="text-gray-600">Group activities and events will be available here soon</p>
          </div>
        )}

        {activeTab === 'my-groups' && (
          <div>
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">My Groups</h2>
              <p className="text-gray-600">Groups you've joined will appear here</p>
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