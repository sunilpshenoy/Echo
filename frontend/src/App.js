import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import AuthScreen from './components/AuthScreen';
import ProfileSetup from './components/ProfileSetup';
import Dashboard from './components/Dashboard';
import { useTranslation } from 'react-i18next';

const App = () => {
  const { i18n } = useTranslation();
  
  // Core authentication state
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [isLoading, setIsLoading] = useState(true);
  
  // App flow state
  const [currentStep, setCurrentStep] = useState('auth'); // 'auth', 'profile_setup', 'dashboard'
  
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
  const API = `${BACKEND_URL}/api`;
  
  // Check authentication on app load
  useEffect(() => {
    const checkAuth = async () => {
      const savedToken = localStorage.getItem('token');
      if (savedToken) {
        try {
          const response = await axios.get(`${API}/users/me`, {
            headers: { Authorization: `Bearer ${savedToken}` }
          });
          setUser(response.data);
          setToken(savedToken);
          
          // Check if user has completed profile setup
          if (response.data.profile_completed) {
            setCurrentStep('dashboard');
          } else {
            setCurrentStep('profile_setup');
          }
        } catch (error) {
          console.error('Token validation failed:', error);
          localStorage.removeItem('token');
          setToken(null);
          setCurrentStep('auth');
        }
      } else {
        setCurrentStep('auth');
      }
      setIsLoading(false);
    };
    
    checkAuth();
  }, [API]);
  
  // Authentication handlers
  const handleAuthSuccess = (userData, authToken) => {
    setUser(userData);
    setToken(authToken);
    localStorage.setItem('token', authToken);
    
    // Check if profile is complete
    if (userData.profile_completed) {
      setCurrentStep('dashboard');
    } else {
      setCurrentStep('profile_setup');
    }
  };
  
  const handleProfileComplete = (updatedUser) => {
    setUser(updatedUser);
    setCurrentStep('dashboard');
  };
  
  const handleLogout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    setCurrentStep('auth');
  };

  const handleUserUpdate = (updatedUserData) => {
    setUser(prevUser => ({
      ...prevUser,
      ...updatedUserData
    }));
  };
  
  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-indigo-600 font-medium">Loading your secure connections...</p>
        </div>
      </div>
    );
  }
  
  // Render appropriate screen based on current step
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {currentStep === 'auth' && (
        <AuthScreen onAuthSuccess={handleAuthSuccess} api={API} />
      )}
      
      {currentStep === 'profile_setup' && (
        <ProfileSetup
          user={user}
          token={token}
          api={API}
          onProfileComplete={handleProfileComplete}
        />
      )}
      
      {currentStep === 'dashboard' && (
        <Dashboard
          user={user}
          token={token}
          api={API}
          onLogout={handleLogout}
          onUserUpdate={handleUserUpdate}
        />
      )}
    </div>
  );
};

export default App;