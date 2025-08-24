import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import './App.css';
import AuthScreen from './components/AuthScreen';
import ProfileSetup from './components/ProfileSetup';
import Dashboard from './components/Dashboard';
import ErrorBoundary from './components/ErrorBoundary';
import { ThemeProvider } from './contexts/ThemeContext';
import { PerformanceMonitor, BundleAnalyzer, PerformanceOptimizer } from './components/PerformanceMonitor';
import { useTranslation } from 'react-i18next';
import './i18n';

const App = () => {
  const { i18n } = useTranslation();
  
  // Core authentication state
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [isLoading, setIsLoading] = useState(true);
  
  // App flow state
  const [currentStep, setCurrentStep] = useState('auth'); // 'auth', 'profile_setup', 'dashboard'
  
  // Stable API URL to prevent useEffect loops
  const API = useMemo(() => {
    const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
    return `${BACKEND_URL}/api`;
  }, []);
  
  // Check authentication on app load
  // Token refresh mechanism
  const refreshToken = async () => {
    try {
      const currentToken = localStorage.getItem('token');
      if (!currentToken) return false;

      const response = await axios.post(`${API}/auth/refresh`, {}, {
        headers: { Authorization: `Bearer ${currentToken}` },
        timeout: 5000
      });

      if (response.data.access_token) {
        localStorage.setItem('token', response.data.access_token);
        setToken(response.data.access_token);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return false;
    }
  };

  useEffect(() => {
    // Initialize language from localStorage with multiple fallbacks
    const savedLanguage = localStorage.getItem('i18nextLng') || localStorage.getItem('pulse-language');
    if (savedLanguage && savedLanguage !== i18n.language) {
      i18n.changeLanguage(savedLanguage);
      document.documentElement.lang = savedLanguage;
      // Set text direction for RTL languages
      if (savedLanguage === 'ur') {
        document.documentElement.dir = 'rtl';
      } else {
        document.documentElement.dir = 'ltr';
      }
    }
    
    // Enhanced auth check with retry mechanism
    const checkAuth = async (retryCount = 0) => {
      const savedToken = localStorage.getItem('token');
      if (savedToken) {
        try {
          // Set the token in axios defaults for all requests
          axios.defaults.headers.common['Authorization'] = `Bearer ${savedToken}`;
          
          const response = await axios.get(`${API}/users/me`, {
            timeout: 10000
          });
          
          const userData = response.data;
          setUser(userData);
          setToken(savedToken);
          
          // Check if user has completed profile setup
          if (userData.profile_completed) {
            setCurrentStep('dashboard');
          } else {
            setCurrentStep('profile_setup');
          }
          
          console.log('✅ Token validation successful:', userData.user_id);
        } catch (error) {
          console.error('❌ Token validation failed:', error.response?.status, error.response?.data);
          
          // Try token refresh on 401 errors
          if (error.response?.status === 401 && retryCount < 2) {
            console.log('🔄 Attempting token refresh...');
            const refreshSuccess = await refreshToken();
            if (refreshSuccess) {
              console.log('✅ Token refresh successful, retrying auth check...');
              return checkAuth(retryCount + 1);
            }
          }
          
          // Clear invalid token and reset axios defaults
          console.log('🧹 Clearing invalid token...');
          localStorage.removeItem('token');
          delete axios.defaults.headers.common['Authorization'];
          setToken(null);
          setUser(null);
          setCurrentStep('auth');
        }
      } else {
        console.log('📝 No token found, redirecting to auth...');
        delete axios.defaults.headers.common['Authorization'];
        setCurrentStep('auth');
      }
      setIsLoading(false);
    };
    
    checkAuth();
  }, [i18n]);

  // Listen for language changes and persist them
  useEffect(() => {
    const handleLanguageChange = (lng) => {
      localStorage.setItem('i18nextLng', lng);
      localStorage.setItem('pulse-language', lng);
      document.documentElement.lang = lng;
      document.documentElement.dir = lng === 'ur' ? 'rtl' : 'ltr';
      
      // Force a re-render by updating loading state
      setIsLoading(true);
      setTimeout(() => setIsLoading(false), 100);
    };

    i18n.on('languageChanged', handleLanguageChange);
    
    return () => {
      i18n.off('languageChanged', handleLanguageChange);
    };
  }, [i18n]);
  
  // Authentication handlers
  const handleAuthSuccess = (userData, authToken) => {
    console.log('🎉 Authentication successful for user:', userData.user_id);
    
    // Set user data and token in state
    setUser(userData);
    setToken(authToken);
    
    // Persist token in localStorage
    localStorage.setItem('token', authToken);
    
    // Set token in axios defaults for all future requests
    axios.defaults.headers.common['Authorization'] = `Bearer ${authToken}`;
    
    // Always go to dashboard - profile setup is now optional for basic chat
    // Profile will be required only when accessing Groups or Premium tabs
    setCurrentStep('dashboard');
  };
  
  const handleProfileComplete = (updatedUser) => {
    setUser(updatedUser);
    setCurrentStep('dashboard');
  };
  
  const handleLogout = () => {
    console.log('👋 Logging out user...');
    
    // Clear state
    setUser(null);
    setToken(null);
    
    // Clear localStorage
    localStorage.removeItem('token');
    
    // Clear axios defaults
    delete axios.defaults.headers.common['Authorization'];
    
    // Redirect to auth
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
    <ThemeProvider>
      <ErrorBoundary>
        <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 transition-colors duration-200">
          {currentStep === 'auth' && (
            <ErrorBoundary>
              <AuthScreen onAuthSuccess={handleAuthSuccess} api={API} />
            </ErrorBoundary>
          )}
          
          {currentStep === 'profile_setup' && (
            <ErrorBoundary>
              <ProfileSetup
                user={user}
                token={token}
                api={API}
                onProfileComplete={handleProfileComplete}
              />
            </ErrorBoundary>
          )}
          
          {currentStep === 'dashboard' && (
            <ErrorBoundary>
              <Dashboard
                user={user}
                token={token}
                api={API}
                onLogout={handleLogout}
                onUserUpdate={handleUserUpdate}
              />
            </ErrorBoundary>
          )}
        </div>
      </ErrorBoundary>
    </ThemeProvider>
  );
};

export default App;