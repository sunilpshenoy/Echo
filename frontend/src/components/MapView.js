import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const MapView = ({ user, token, api }) => {
  const [mapData, setMapData] = useState({ groups: [], activities: [] });
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [viewMode, setViewMode] = useState('groups'); // groups, activities, both
  const [userLocation, setUserLocation] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [searchRadius, setSearchRadius] = useState(25); // km

  // Get user's current location
  const getUserLocation = useCallback(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setUserLocation({
            lat: position.coords.latitude,
            lng: position.coords.longitude
          });
        },
        (error) => {
          console.warn('Location access denied, using default location');
          // Default to Mumbai coordinates
          setUserLocation({ lat: 19.0760, lng: 72.8777 });
        }
      );
    } else {
      setUserLocation({ lat: 19.0760, lng: 72.8777 });
    }
  }, []);

  // Fetch map data
  const fetchMapData = useCallback(async () => {
    if (!userLocation || !token || !api) return;
    
    setIsLoading(true);
    try {
      const promises = [];
      
      if (viewMode === 'groups' || viewMode === 'both') {
        const groupsParams = new URLSearchParams({
          lat: userLocation.lat.toString(),
          lng: userLocation.lng.toString(),
          radius: searchRadius.toString()
        });
        if (selectedCategory !== 'all') {
          groupsParams.append('category', selectedCategory);
        }
        
        promises.push(
          axios.get(`${api}/map/groups?${groupsParams}`, {
            headers: { Authorization: `Bearer ${token}` }
          })
        );
      } else {
        promises.push(Promise.resolve({ data: [] }));
      }
      
      if (viewMode === 'activities' || viewMode === 'both') {
        const activitiesParams = new URLSearchParams({
          lat: userLocation.lat.toString(),
          lng: userLocation.lng.toString(),
          radius: searchRadius.toString()
        });
        
        promises.push(
          axios.get(`${api}/map/activities?${activitiesParams}`, {
            headers: { Authorization: `Bearer ${token}` }
          })
        );
      } else {
        promises.push(Promise.resolve({ data: [] }));
      }
      
      const [groupsRes, activitiesRes] = await Promise.all(promises);
      
      setMapData({
        groups: groupsRes.data || [],
        activities: activitiesRes.data || []
      });
      
    } catch (error) {
      console.error('Failed to fetch map data:', error);
    } finally {
      setIsLoading(false);
    }
  }, [userLocation, token, api, viewMode, selectedCategory, searchRadius]);

  useEffect(() => {
    getUserLocation();
  }, [getUserLocation]);

  useEffect(() => {
    if (userLocation) {
      fetchMapData();
    }
  }, [userLocation, fetchMapData]);

  // Simple map implementation (placeholder for full map library)
  const MapContainer = () => (
    <div className="relative w-full h-96 bg-gray-200 rounded-lg overflow-hidden">
      {/* Map Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-100 to-green-100 flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-2">🗺️</div>
          <p className="text-gray-600">Interactive Map View</p>
          <p className="text-sm text-gray-500">
            {userLocation ? 
              `${userLocation.lat.toFixed(4)}, ${userLocation.lng.toFixed(4)}` : 
              'Getting location...'
            }
          </p>
        </div>
      </div>
      
      {/* Map Markers */}
      <div className="absolute inset-0">
        {/* Groups Markers */}
        {mapData.groups.map((group, index) => (
          <div
            key={group.id}
            className="absolute transform -translate-x-1/2 -translate-y-1/2 cursor-pointer"
            style={{
              left: `${50 + (index % 5 - 2) * 15}%`,
              top: `${50 + Math.floor(index / 5 - 2) * 15}%`
            }}
            onClick={() => setSelectedItem({...group, type: 'group'})}
          >
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold shadow-lg transition-transform hover:scale-110 ${
              group.is_joined ? 'bg-green-500' : 'bg-blue-500'
            }`}>
              {group.emoji || '👥'}
            </div>
            {group.health_score > 80 && (
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-yellow-400 rounded-full"></div>
            )}
          </div>
        ))}
        
        {/* Activities Markers */}
        {mapData.activities.map((activity, index) => (
          <div
            key={activity.id}
            className="absolute transform -translate-x-1/2 -translate-y-1/2 cursor-pointer"
            style={{
              left: `${40 + (index % 6 - 2.5) * 12}%`,
              top: `${60 + Math.floor(index / 6 - 1) * 12}%`
            }}
            onClick={() => setSelectedItem({...activity, type: 'activity'})}
          >
            <div className="w-6 h-6 bg-purple-500 rounded-full flex items-center justify-center text-white text-xs shadow-lg hover:scale-110 transition-transform">
              📅
            </div>
          </div>
        ))}
        
        {/* User Location */}
        {userLocation && (
          <div
            className="absolute transform -translate-x-1/2 -translate-y-1/2"
            style={{ left: '50%', top: '50%' }}
          >
            <div className="w-4 h-4 bg-red-500 rounded-full border-2 border-white shadow-lg animate-pulse"></div>
            <div className="absolute inset-0 w-4 h-4 bg-red-500 rounded-full opacity-30 animate-ping"></div>
          </div>
        )}
      </div>
    </div>
  );

  const InfoCard = ({ item }) => {
    if (!item) return null;
    
    return (
      <div className="bg-white rounded-lg shadow-lg p-4 border">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center space-x-3">
            <div className="text-2xl">{item.emoji || item.team_emoji || '📍'}</div>
            <div>
              <h3 className="font-semibold text-gray-900">
                {item.name || item.title}
              </h3>
              {item.type === 'group' && (
                <p className="text-sm text-gray-500">
                  {item.member_count} members • {item.address}
                </p>
              )}
              {item.type === 'activity' && (
                <p className="text-sm text-gray-500">
                  {item.team_name} • {new Date(item.start_time).toLocaleDateString()}
                </p>
              )}
            </div>
          </div>
          <button
            onClick={() => setSelectedItem(null)}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>
        
        <p className="text-gray-600 mb-3">{item.description}</p>
        
        {item.type === 'group' && (
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              {item.health_score && (
                <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
                  {item.health_score}% healthy
                </span>
              )}
            </div>
            <button className={`px-3 py-1 rounded text-sm font-medium ${
              item.is_joined 
                ? 'bg-green-100 text-green-700' 
                : 'bg-blue-500 text-white hover:bg-blue-600'
            }`}>
              {item.is_joined ? 'Joined' : 'Join'}
            </button>
          </div>
        )}
        
        {item.type === 'activity' && (
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              {item.attendee_count}/{item.max_attendees} attending
            </div>
            <button className={`px-3 py-1 rounded text-sm font-medium ${
              item.is_attending 
                ? 'bg-green-100 text-green-700' 
                : 'bg-purple-500 text-white hover:bg-purple-600'
            }`}>
              {item.is_attending ? 'Attending' : 'Join Activity'}
            </button>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="max-w-6xl mx-auto p-4">
      {/* Header Controls */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold text-gray-900">🗺️ Map Discovery</h1>
          <button
            onClick={getUserLocation}
            className="flex items-center px-3 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            <span className="mr-2">📍</span>
            Update Location
          </button>
        </div>
        
        {/* View Mode Tabs */}
        <div className="flex space-x-4 mb-4">
          {[
            { key: 'groups', label: '👥 Groups', count: mapData.groups.length },
            { key: 'activities', label: '📅 Activities', count: mapData.activities.length },
            { key: 'both', label: '🌟 Both', count: mapData.groups.length + mapData.activities.length }
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setViewMode(tab.key)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                viewMode === tab.key
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {tab.label} ({tab.count})
            </button>
          ))}
        </div>
        
        {/* Filters */}
        <div className="flex flex-wrap gap-4">
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Categories</option>
            <option value="food">🍛 Food & Dining</option>
            <option value="outdoor">🏔️ Outdoor & Sports</option>
            <option value="business">💻 Business & Tech</option>
            <option value="creative">🎨 Arts & Creative</option>
          </select>
          
          <div className="flex items-center space-x-2">
            <label className="text-sm text-gray-600">Radius:</label>
            <select
              value={searchRadius}
              onChange={(e) => setSearchRadius(parseInt(e.target.value))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value={5}>5 km</option>
              <option value={10}>10 km</option>
              <option value={25}>25 km</option>
              <option value={50}>50 km</option>
              <option value={100}>100 km</option>
            </select>
          </div>
        </div>
      </div>
      
      {/* Map and Info Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          {isLoading ? (
            <div className="w-full h-96 bg-gray-100 rounded-lg flex items-center justify-center">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                <p className="text-gray-600">Loading map data...</p>
              </div>
            </div>
          ) : (
            <MapContainer />
          )}
        </div>
        
        <div className="space-y-4">
          {selectedItem ? (
            <InfoCard item={selectedItem} />
          ) : (
            <div className="bg-gray-50 rounded-lg p-6 text-center">
              <div className="text-4xl mb-2">📍</div>
              <h3 className="font-semibold text-gray-900 mb-2">Explore the Map</h3>
              <p className="text-gray-600 text-sm">
                Click on markers to see details about groups and activities near you.
              </p>
            </div>
          )}
          
          {/* Quick Stats */}
          <div className="bg-white rounded-lg shadow p-4">
            <h4 className="font-semibold text-gray-900 mb-3">Nearby Discovery</h4>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Groups found</span>
                <span className="font-medium">{mapData.groups.length}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Activities found</span>
                <span className="font-medium">{mapData.activities.length}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Search radius</span>
                <span className="font-medium">{searchRadius} km</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MapView;