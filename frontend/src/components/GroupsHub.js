import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import GroupDiscovery from './GroupDiscovery';
import MapView from './MapView';
import CalendarView from './CalendarView';

const GroupsHub = ({ user, token, api }) => {
  const { t } = useTranslation();
  const [activeSubTab, setActiveSubTab] = useState('discover');

  const subTabs = [
    {
      id: 'discover',
      label: 'Discover Groups',
      icon: '🔍',
      description: 'Find groups that match your interests'
    },
    {
      id: 'map',
      label: 'Map View',
      icon: '🗺️',
      description: 'Explore groups and activities nearby'
    },
    {
      id: 'calendar',
      label: 'Events Calendar',
      icon: '📅',
      description: 'View group events and activities'
    }
  ];

  return (
    <div className="flex-1 flex flex-col bg-white">
      {/* Groups Hub Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center space-x-2">
              <span>👥</span>
              <span>Groups Hub</span>
            </h1>
            <p className="text-gray-600 mt-1">
              Discover, explore, and connect with groups that share your interests
            </p>
          </div>
        </div>

        {/* Sub-tabs Navigation */}
        <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
          {subTabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveSubTab(tab.id)}
              className={`flex-1 flex items-center justify-center space-x-2 px-4 py-3 rounded-md text-sm font-medium transition-all ${
                activeSubTab === tab.id
                  ? 'bg-white text-purple-700 shadow-sm border border-purple-200'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
              title={tab.description}
            >
              <span className="text-lg">{tab.icon}</span>
              <span className="hidden sm:inline">{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Active Tab Description */}
        <div className="mt-3 text-sm text-gray-500">
          {subTabs.find(tab => tab.id === activeSubTab)?.description}
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-hidden">
        {activeSubTab === 'discover' && (
          <div className="h-full">
            <GroupDiscovery 
              user={user}
              token={token}
              api={api}
            />
          </div>
        )}

        {activeSubTab === 'map' && (
          <div className="h-full overflow-auto">
            <div className="p-4">
              <MapView 
                user={user}
                token={token}
                api={api}
              />
            </div>
          </div>
        )}

        {activeSubTab === 'calendar' && (
          <div className="h-full overflow-auto">
            <div className="p-4">
              <CalendarView 
                user={user}
                token={token}
                api={api}
              />
            </div>
          </div>
        )}
      </div>

      {/* Quick Stats Footer */}
      <div className="bg-gray-50 border-t border-gray-200 px-6 py-3">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 bg-green-400 rounded-full"></span>
              <span>Discovering groups worldwide</span>
            </div>
            <div className="hidden sm:flex items-center space-x-2">
              <span>📍</span>
              <span>Location-based recommendations</span>
            </div>
          </div>
          
          <div className="flex items-center space-x-4 text-xs">
            <div className="flex items-center space-x-1">
              <span>🔍</span>
              <span>Smart Discovery</span>
            </div>
            <div className="flex items-center space-x-1">
              <span>🗺️</span>
              <span>Map Explorer</span>
            </div>
            <div className="flex items-center space-x-1">
              <span>📅</span>
              <span>Event Calendar</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GroupsHub;
