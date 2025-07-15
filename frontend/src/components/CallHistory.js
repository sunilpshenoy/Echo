import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

const CallHistory = ({ user, token, api, onCallBack }) => {
  const { t } = useTranslation();
  const [callHistory, setCallHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedFilter, setSelectedFilter] = useState('all'); // all, missed, outgoing, incoming

  useEffect(() => {
    fetchCallHistory();
  }, []);

  const fetchCallHistory = async () => {
    try {
      const response = await axios.get(`${api}/calls/history`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCallHistory(response.data.calls || []);
    } catch (error) {
      console.error('Failed to fetch call history:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterCalls = (calls) => {
    if (selectedFilter === 'all') return calls;
    return calls.filter(call => call.type === selectedFilter);
  };

  const formatCallDuration = (seconds) => {
    if (!seconds) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatCallTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = (now - date) / (1000 * 60 * 60);
    
    if (diffInHours < 24) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (diffInHours < 168) { // 1 week
      return date.toLocaleDateString([], { weekday: 'short', hour: '2-digit', minute: '2-digit' });
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    }
  };

  const getCallIcon = (call) => {
    if (call.status === 'missed') return '📞❌';
    if (call.type === 'outgoing') return '📞📤';
    if (call.type === 'incoming') return '📞📥';
    return call.call_type === 'video' ? '📹' : '📞';
  };

  const getCallTypeColor = (call) => {
    if (call.status === 'missed') return 'text-red-500';
    if (call.type === 'outgoing') return 'text-blue-500';
    if (call.type === 'incoming') return 'text-green-500';
    return 'text-gray-500';
  };

  const handleCallBack = (contact) => {
    onCallBack(contact, 'voice');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-800">{t('calls.history')}</h2>
        <button
          onClick={fetchCallHistory}
          className="text-blue-500 hover:text-blue-700 text-sm"
        >
          {t('common.refresh')}
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex space-x-2 mb-4">
        {['all', 'missed', 'outgoing', 'incoming'].map((filter) => (
          <button
            key={filter}
            onClick={() => setSelectedFilter(filter)}
            className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
              selectedFilter === filter
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {t(`calls.${filter}`)}
          </button>
        ))}
      </div>

      {/* Call History List */}
      <div className="space-y-2">
        {filterCalls(callHistory).length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-2">📞</div>
            <p>{t('calls.noHistory')}</p>
          </div>
        ) : (
          filterCalls(callHistory).map((call) => (
            <div
              key={call.call_id}
              className="flex items-center p-3 hover:bg-gray-50 rounded-lg transition-colors"
            >
              <div className={`text-2xl mr-3 ${getCallTypeColor(call)}`}>
                {getCallIcon(call)}
              </div>
              
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium text-gray-800">
                    {call.other_user?.display_name || 'Unknown'}
                  </h3>
                  <span className="text-xs text-gray-500">
                    {formatCallTime(call.created_at)}
                  </span>
                </div>
                
                <div className="flex items-center justify-between text-sm text-gray-600">
                  <span>
                    {call.call_type === 'video' ? t('calls.video') : t('calls.voice')}
                    {call.duration && ` • ${formatCallDuration(call.duration)}`}
                  </span>
                  <span className={`text-xs ${getCallTypeColor(call)}`}>
                    {t(`calls.${call.status || call.type}`)}
                  </span>
                </div>
              </div>
              
              <button
                onClick={() => handleCallBack(call.other_user)}
                className="ml-3 p-2 text-blue-500 hover:bg-blue-50 rounded-full transition-colors"
                title={t('calls.callBack')}
              >
                📞
              </button>
            </div>
          ))
        )}
      </div>

      {/* Call Statistics */}
      {callHistory.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-gray-800">
                {callHistory.length}
              </div>
              <div className="text-xs text-gray-500">{t('calls.total')}</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">
                {callHistory.filter(c => c.status === 'completed').length}
              </div>
              <div className="text-xs text-gray-500">{t('calls.completed')}</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-red-600">
                {callHistory.filter(c => c.status === 'missed').length}
              </div>
              <div className="text-xs text-gray-500">{t('calls.missed')}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CallHistory;