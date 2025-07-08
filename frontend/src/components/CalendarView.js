import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const CalendarView = ({ user, token, api }) => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [events, setEvents] = useState([]);
  const [selectedDate, setSelectedDate] = useState(null);
  const [showCreateEvent, setShowCreateEvent] = useState(false);
  const [viewMode, setViewMode] = useState('month'); // month, week, day
  const [isLoading, setIsLoading] = useState(false);

  // Fetch calendar events
  const fetchEvents = useCallback(async () => {
    if (!token || !api) return;
    
    setIsLoading(true);
    try {
      // Calculate date range based on view mode
      const startDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
      const endDate = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
      
      const response = await axios.get(`${api}/calendar/events`, {
        headers: { Authorization: `Bearer ${token}` },
        params: {
          start_date: startDate.toISOString(),
          end_date: endDate.toISOString()
        }
      });
      
      setEvents(response.data);
    } catch (error) {
      console.error('Failed to fetch calendar events:', error);
    } finally {
      setIsLoading(false);
    }
  }, [currentDate, token, api]);

  // Create new event
  const createEvent = async (eventData) => {
    if (!token || !api) return;
    
    try {
      const response = await axios.post(`${api}/calendar/events`, eventData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setEvents(prev => [...prev, response.data]);
      setShowCreateEvent(false);
    } catch (error) {
      console.error('Failed to create event:', error);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  // Calendar utility functions
  const getDaysInMonth = (date) => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (date) => {
    return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
  };

  const getEventsForDate = (date) => {
    return events.filter(event => {
      const eventDate = new Date(event.start_time);
      return eventDate.toDateString() === date.toDateString();
    });
  };

  const navigateMonth = (direction) => {
    setCurrentDate(prev => {
      const newDate = new Date(prev);
      newDate.setMonth(prev.getMonth() + direction);
      return newDate;
    });
  };

  const CreateEventModal = () => {
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [startTime, setStartTime] = useState('');
    const [endTime, setEndTime] = useState('');
    const [location, setLocation] = useState('');
    const [isAllDay, setIsAllDay] = useState(false);

    const handleSubmit = (e) => {
      e.preventDefault();
      if (!title.trim() || !startTime || !endTime) return;
      
      createEvent({
        title: title.trim(),
        description: description.trim(),
        start_time: startTime,
        end_time: endTime,
        location: location.trim(),
        is_all_day: isAllDay
      });
    };

    // Set default times if date is selected
    useEffect(() => {
      if (selectedDate) {
        const dateStr = selectedDate.toISOString().split('T')[0];
        if (!startTime) setStartTime(`${dateStr}T09:00`);
        if (!endTime) setEndTime(`${dateStr}T10:00`);
      }
    }, [selectedDate, startTime, endTime]);

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-screen overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Create New Event</h3>
            <button
              onClick={() => setShowCreateEvent(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Event Title *
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Team meeting, workout, lunch..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="What's this event about?"
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <div className="flex items-center mb-4">
              <input
                type="checkbox"
                id="allDay"
                checked={isAllDay}
                onChange={(e) => setIsAllDay(e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="allDay" className="ml-2 text-sm text-gray-700">
                All day event
              </label>
            </div>
            
            {!isAllDay && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Start Time *
                  </label>
                  <input
                    type="datetime-local"
                    value={startTime}
                    onChange={(e) => setStartTime(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    End Time *
                  </label>
                  <input
                    type="datetime-local"
                    value={endTime}
                    onChange={(e) => setEndTime(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
              </div>
            )}
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Location
              </label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="Meeting room, restaurant, online..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <div className="flex space-x-3 pt-4">
              <button
                type="button"
                onClick={() => setShowCreateEvent(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Create Event
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  const EventCard = ({ event }) => (
    <div className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs mb-1 truncate cursor-pointer hover:bg-blue-200">
      <div className="font-medium">{event.title}</div>
      {!event.is_all_day && (
        <div className="text-blue-600">
          {new Date(event.start_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
        </div>
      )}
    </div>
  );

  const CalendarGrid = () => {
    const daysInMonth = getDaysInMonth(currentDate);
    const firstDay = getFirstDayOfMonth(currentDate);
    const days = [];
    
    // Previous month days
    for (let i = 0; i < firstDay; i++) {
      days.push(null);
    }
    
    // Current month days
    for (let day = 1; day <= daysInMonth; day++) {
      days.push(day);
    }
    
    const weeks = [];
    for (let i = 0; i < days.length; i += 7) {
      weeks.push(days.slice(i, i + 7));
    }
    
    return (
      <div className="bg-white rounded-lg shadow">
        {/* Calendar Header */}
        <div className="grid grid-cols-7 border-b">
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
            <div key={day} className="p-3 text-center text-sm font-medium text-gray-500 border-r last:border-r-0">
              {day}
            </div>
          ))}
        </div>
        
        {/* Calendar Body */}
        {weeks.map((week, weekIndex) => (
          <div key={weekIndex} className="grid grid-cols-7 border-b last:border-b-0">
            {week.map((day, dayIndex) => {
              const date = day ? new Date(currentDate.getFullYear(), currentDate.getMonth(), day) : null;
              const dayEvents = date ? getEventsForDate(date) : [];
              const isToday = date && date.toDateString() === new Date().toDateString();
              const isSelected = date && selectedDate && date.toDateString() === selectedDate.toDateString();
              
              return (
                <div
                  key={dayIndex}
                  className={`min-h-[100px] p-2 border-r last:border-r-0 cursor-pointer hover:bg-gray-50 ${
                    !day ? 'bg-gray-50' : ''
                  } ${isSelected ? 'bg-blue-50' : ''}`}
                  onClick={() => day && setSelectedDate(date)}
                >
                  {day && (
                    <>
                      <div className={`text-sm font-medium mb-1 ${
                        isToday ? 'text-blue-600 font-bold' : 'text-gray-900'
                      }`}>
                        {day}
                        {isToday && (
                          <div className="w-2 h-2 bg-blue-600 rounded-full inline-block ml-1"></div>
                        )}
                      </div>
                      <div className="space-y-1">
                        {dayEvents.slice(0, 3).map(event => (
                          <EventCard key={event.event_id} event={event} />
                        ))}
                        {dayEvents.length > 3 && (
                          <div className="text-xs text-gray-500">
                            +{dayEvents.length - 3} more
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="max-w-6xl mx-auto p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-bold text-gray-900">📅 Calendar</h1>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => navigateMonth(-1)}
              className="p-2 hover:bg-gray-100 rounded-lg"
            >
              ←
            </button>
            <h2 className="text-lg font-medium text-gray-900 min-w-[180px] text-center">
              {currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
            </h2>
            <button
              onClick={() => navigateMonth(1)}
              className="p-2 hover:bg-gray-100 rounded-lg"
            >
              →
            </button>
          </div>
        </div>
        
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setCurrentDate(new Date())}
            className="px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Today
          </button>
          <button
            onClick={() => setShowCreateEvent(true)}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <span className="mr-2">+</span>
            New Event
          </button>
        </div>
      </div>
      
      {/* View Mode Tabs */}
      <div className="flex space-x-4 mb-6">
        {[
          { key: 'month', label: 'Month' },
          { key: 'week', label: 'Week' },
          { key: 'day', label: 'Day' }
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
            {tab.label}
          </button>
        ))}
      </div>
      
      {/* Calendar Content */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-3">
            {viewMode === 'month' && <CalendarGrid />}
            {viewMode === 'week' && (
              <div className="bg-white rounded-lg shadow p-4">
                <p className="text-center text-gray-500">Week view coming soon</p>
              </div>
            )}
            {viewMode === 'day' && (
              <div className="bg-white rounded-lg shadow p-4">
                <p className="text-center text-gray-500">Day view coming soon</p>
              </div>
            )}
          </div>
          
          {/* Sidebar */}
          <div className="space-y-4">
            {/* Selected Date Info */}
            {selectedDate && (
              <div className="bg-white rounded-lg shadow p-4">
                <h3 className="font-semibold text-gray-900 mb-3">
                  {selectedDate.toLocaleDateString('en-US', { 
                    weekday: 'long', 
                    month: 'long', 
                    day: 'numeric' 
                  })}
                </h3>
                <div className="space-y-2">
                  {getEventsForDate(selectedDate).map(event => (
                    <div key={event.event_id} className="p-3 bg-blue-50 rounded-lg">
                      <div className="font-medium text-blue-900">{event.title}</div>
                      {!event.is_all_day && (
                        <div className="text-sm text-blue-700">
                          {new Date(event.start_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} - 
                          {new Date(event.end_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                        </div>
                      )}
                      {event.location && (
                        <div className="text-sm text-blue-600">📍 {event.location}</div>
                      )}
                    </div>
                  ))}
                  {getEventsForDate(selectedDate).length === 0 && (
                    <p className="text-gray-500 text-sm">No events scheduled</p>
                  )}
                </div>
                <button
                  onClick={() => setShowCreateEvent(true)}
                  className="w-full mt-3 px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Add Event
                </button>
              </div>
            )}
            
            {/* Quick Stats */}
            <div className="bg-white rounded-lg shadow p-4">
              <h4 className="font-semibold text-gray-900 mb-3">This Month</h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Total events</span>
                  <span className="font-medium">{events.length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Team events</span>
                  <span className="font-medium">
                    {events.filter(e => e.team_id).length}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Personal events</span>
                  <span className="font-medium">
                    {events.filter(e => !e.team_id).length}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {showCreateEvent && <CreateEventModal />}
    </div>
  );
};

export default CalendarView;