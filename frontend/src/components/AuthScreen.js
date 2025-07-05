import React, { useState } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import LanguageSelector from './LanguageSelector';

const AuthScreen = ({ onAuthSuccess, api }) => {
  const { t } = useTranslation();
  const [isLogin, setIsLogin] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    username: ''
  });
  
  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError(''); // Clear error when user types
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    
    try {
      const endpoint = isLogin ? '/login' : '/register';
      const data = isLogin 
        ? { email: formData.email, password: formData.password }
        : { email: formData.email, password: formData.password, username: formData.username };
      
      const response = await axios.post(`${api}${endpoint}`, data);
      
      if (response.data.access_token) {
        onAuthSuccess(response.data.user || response.data, response.data.access_token);
      }
    } catch (error) {
      console.error('Authentication error:', error);
      
      // Handle different error types with better messaging
      if (error.response?.status === 401) {
        setError('Invalid email or password. Please check your credentials and try again.');
      } else if (error.response?.status === 400) {
        setError(error.response?.data?.detail || 'Invalid request. Please check your information.');
      } else if (error.response?.status === 404) {
        setError('Service not found. Please try again later.');
      } else if (error.response?.status >= 500) {
        setError('Server error. Please try again later.');
      } else {
        setError(error.response?.data?.detail || error.message || 'Authentication failed. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="min-h-screen bg-pulse-primary flex items-center justify-center px-4 py-8">
      {/* Language Selector - Top Right */}
      <div className="fixed top-4 right-4 z-50">
        <LanguageSelector />
      </div>
      
      <div className="w-full max-w-md">
        {/* Header with Pulse branding */}
        <div className="text-center mb-8 animate-fade-in-up">
          {/* Simple Text-Based Logo - Clean and Functional */}
          <div className="mb-6 flex flex-col items-center">
            <div className="text-6xl mb-2">🛡️💜</div>
            <div className="text-4xl font-bold bg-gradient-to-r from-orange-400 to-orange-500 bg-clip-text text-transparent mb-1 tracking-widest">
              {t('common.appName')}
            </div>
            <div className="text-sm font-semibold bg-gradient-to-r from-pink-400 to-purple-500 bg-clip-text text-transparent tracking-wider">
              {t('common.tagline')}
            </div>
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">{t('auth.welcomeBack')}</h1>
          <p className="text-white/80 font-medium">{t('auth.continueBuilding')}</p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}

        {/* Main Form Card */}
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
          <form onSubmit={handleSubmit} className="p-8">
            {/* Form Fields */}
            <div className="space-y-6">
              {!isLogin && (
                <div>
                  <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                    Username
                  </label>
                  <input
                    type="text"
                    id="username"
                    name="username"
                    value={formData.username}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                    placeholder="Choose a username"
                    required={!isLogin}
                  />
                </div>
              )}
              
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                  {t('auth.emailAddress')}
                </label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  placeholder={t('auth.email')}
                  required
                />
              </div>
              
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                  {t('auth.password')}
                </label>
                <input
                  type="password"
                  id="password"
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  placeholder={t('auth.password')}
                  required
                />
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-8 bg-pulse-accent text-white py-3 px-4 rounded-lg font-medium hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
{isLoading ? t('common.loading') : (isLogin ? t('auth.signIn') : t('auth.signUp'))}
            </button>

            {/* Toggle Auth Mode */}
            <div className="text-center mt-6">
              <button
                type="button"
                onClick={() => {
                  setIsLogin(!isLogin);
                  setError('');
                  setFormData({ email: '', password: '', username: '' });
                }}
                className="text-blue-600 hover:text-blue-800 font-medium transition-colors"
              >
                {isLogin 
                  ? t('auth.newToApp')
                  : t('auth.haveAccount')
                }
              </button>
            </div>
          </form>
        </div>

        {/* Features Section */}
        <div className="mt-12 bg-white/10 backdrop-blur-sm rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">{t('auth.whyChoose')}</h2>
          <div className="space-y-4">
            <div className="flex items-start space-x-3">
              <div className="text-orange-400 text-xl">🔒</div>
              <div className="text-white/90 text-sm">{t('auth.secureConnections')}</div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="text-orange-400 text-xl">✅</div>
              <div className="text-white/90 text-sm">{t('auth.verifiedUsers')}</div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="text-orange-400 text-xl">🛡️</div>
              <div className="text-white/90 text-sm">{t('auth.privacyFirst')}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthScreen;