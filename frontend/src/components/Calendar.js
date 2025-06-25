import React, { useState, useEffect } from 'react';
import axios from 'axios';

const Calendar = ({ user, token, workspaceMode, onClose }) => {
  const [events, setEvents] = useState([]);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [view, setView] = useState('month');
  const [showCreateEvent, setShowCreateEvent] = useState(false);
  const [eventForm, setEventForm] = useState({
    title: '',
    description: '',
    start_time: '',
    end_time: '',
    event_type: 'meeting',
    location: '',
    attendees: [],
    reminder_minutes: 15,
    priority: 'medium'
  });

  const API = process.env.REACT_APP_BACKEND_URL + '/api';

  const getAuthHeaders = () => ({
    headers: { Authorization: `Bearer ${token}` }
  });

  useEffect(() => {
    fetchEvents();
  }, [workspaceMode]);

  const fetchEvents = async () => {
    try {
      const response = await axios.get(
        `${API}/calendar/events?workspace_mode=${workspaceMode}`,
        getAuthHeaders()
      );
      setEvents(response.data);
    } catch (error) {
      console.error('Error fetching events:', error);
    }
  };

  const createEvent = async () => {
    try {
      await axios.post(`${API}/calendar/events`, {
        ...eventForm,
        workspace_mode: workspaceMode
      }, getAuthHeaders());
      setEventForm({
        title: '', description: '', start_time: '', end_time: '',
        event_type: 'meeting', location: '', attendees: [],
        reminder_minutes: 15, priority: 'medium'
      });
      setShowCreateEvent(false);
      fetchEvents();
    } catch (error) {
      console.error('Error creating event:', error);
    }
  };

  const getDaysInMonth = (date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDay = firstDay.getDay();
    
    const days = [];
    
    // Previous month's trailing days
    for (let i = startingDay - 1; i >= 0; i--) {
      const day = new Date(year, month, -i);
      days.push({ date: day, isCurrentMonth: false });
    }
    
    // Current month's days
    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(year, month, day);
      days.push({ date, isCurrentMonth: true });
    }
    
    // Next month's leading days
    const remainingCells = 42 - days.length;
    for (let day = 1; day <= remainingCells; day++) {
      const date = new Date(year, month + 1, day);
      days.push({ date, isCurrentMonth: false });
    }
    
    return days;
  };

  const getEventsForDate = (date) => {
    return events.filter(event => {
      const eventDate = new Date(event.start_time);
      return eventDate.toDateString() === date.toDateString();
    });
  };

  const formatTime = (dateString) => {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-6xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">
            📅 Calendar ({workspaceMode === 'business' ? 'Work' : 'Personal'})
          </h2>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowCreateEvent(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              + New Event
            </button>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 p-2"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Calendar Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setSelectedDate(new Date(selectedDate.getFullYear(), selectedDate.getMonth() - 1))}
              className="text-gray-600 hover:text-gray-800 p-2"
            >
              ‹
            </button>
            <h3 className="text-xl font-semibold">
              {monthNames[selectedDate.getMonth()]} {selectedDate.getFullYear()}
            </h3>
            <button
              onClick={() => setSelectedDate(new Date(selectedDate.getFullYear(), selectedDate.getMonth() + 1))}
              className="text-gray-600 hover:text-gray-800 p-2"
            >
              ›
            </button>
          </div>
          <div className="flex space-x-2">
            {['month', 'week', 'day'].map(viewType => (
              <button
                key={viewType}
                onClick={() => setView(viewType)}
                className={`px-3 py-1 rounded-lg capitalize ${
                  view === viewType
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {viewType}
              </button>
            ))}
          </div>
        </div>

        {/* Calendar Grid */}
        {view === 'month' && (
          <div className="grid grid-cols-7 gap-1">
            {/* Week day headers */}
            {weekDays.map(day => (
              <div key={day} className="p-2 text-center font-medium text-gray-600 border-b">
                {day}
              </div>
            ))}
            
            {/* Calendar days */}
            {getDaysInMonth(selectedDate).map((day, index) => {
              const dayEvents = getEventsForDate(day.date);
              const isToday = day.date.toDateString() === new Date().toDateString();
              
              return (
                <div
                  key={index}
                  className={`min-h-[100px] p-2 border border-gray-200 ${
                    day.isCurrentMonth ? 'bg-white' : 'bg-gray-50'
                  } ${isToday ? 'bg-blue-50 border-blue-300' : ''}`}
                >
                  <div className={`text-sm ${
                    day.isCurrentMonth ? 'text-gray-900' : 'text-gray-400'
                  } ${isToday ? 'font-bold text-blue-600' : ''}`}>
                    {day.date.getDate()}
                  </div>
                  
                  {/* Events for this day */}
                  <div className="mt-1 space-y-1">
                    {dayEvents.slice(0, 3).map(event => (
                      <div
                        key={event.event_id}
                        className={`text-xs p-1 rounded truncate ${
                          event.event_type === 'meeting' ? 'bg-blue-100 text-blue-800' :
                          event.event_type === 'task' ? 'bg-green-100 text-green-800' :
                          'bg-purple-100 text-purple-800'
                        }`}
                        title={`${event.title} - ${formatTime(event.start_time)}`}
                      >
                        {event.title}
                      </div>
                    ))}
                    {dayEvents.length > 3 && (
                      <div className="text-xs text-gray-500">
                        +{dayEvents.length - 3} more
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Create Event Modal */}
        {showCreateEvent && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-96 max-w-[90vw]">
              <h3 className="text-lg font-semibold mb-4">Create New Event</h3>
              <form onSubmit={(e) => { e.preventDefault(); createEvent(); }}>
                <div className="space-y-4">
                  <input
                    type="text"
                    placeholder="Event Title"
                    value={eventForm.title}
                    onChange={(e) => setEventForm({...eventForm, title: e.target.value})}
                    className="w-full p-3 border rounded-lg"
                    required
                  />
                  <textarea
                    placeholder="Description"
                    value={eventForm.description}
                    onChange={(e) => setEventForm({...eventForm, description: e.target.value})}
                    className="w-full p-3 border rounded-lg h-20"
                  />
                  <div className="grid grid-cols-2 gap-4">
                    <input
                      type="datetime-local"
                      value={eventForm.start_time}
                      onChange={(e) => setEventForm({...eventForm, start_time: e.target.value})}
                      className="w-full p-3 border rounded-lg"
                      required
                    />
                    <input
                      type="datetime-local"
                      value={eventForm.end_time}
                      onChange={(e) => setEventForm({...eventForm, end_time: e.target.value})}
                      className="w-full p-3 border rounded-lg"
                      required
                    />
                  </div>
                  <select
                    value={eventForm.event_type}
                    onChange={(e) => setEventForm({...eventForm, event_type: e.target.value})}
                    className="w-full p-3 border rounded-lg"
                  >
                    <option value="meeting">Meeting</option>
                    <option value="task">Task</option>
                    <option value="reminder">Reminder</option>
                    <option value="personal">Personal</option>
                  </select>
                  <input
                    type="text"
                    placeholder="Location (optional)"
                    value={eventForm.location}
                    onChange={(e) => setEventForm({...eventForm, location: e.target.value})}
                    className="w-full p-3 border rounded-lg"
                  />
                </div>
                <div className="flex space-x-3 mt-6">
                  <button
                    type="button"
                    onClick={() => setShowCreateEvent(false)}
                    className="flex-1 py-2 border rounded-lg"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="flex-1 py-2 bg-blue-600 text-white rounded-lg"
                  >
                    Create Event
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

export default Calendar;