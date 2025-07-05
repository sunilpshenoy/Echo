import React, { useState } from 'react';
import axios from 'axios';

const AuthScreen = ({ onAuthSuccess, api }) => {
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
      <div className="w-full max-w-md">
        {/* Header with Pulse branding */}
        <div className="text-center mb-8 animate-fade-in-up">
          {/* Pulse Logo - Recreated to match your exact design */}
          <div className="mb-6 flex justify-center">
            <svg width="100" height="120" viewBox="0 0 100 120" className="drop-shadow-lg">
              <defs>
                <linearGradient id="shieldGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#D946EF"/>
                  <stop offset="50%" stopColor="#EC4899"/>
                  <stop offset="100%" stopColor="#F97316"/>
                </linearGradient>
                <linearGradient id="textGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#F97316"/>
                  <stop offset="100%" stopColor="#FB923C"/>
                </linearGradient>
              </defs>
              
              {/* Hexagonal shield - geometric, angular design */}
              <path d="M50 10 L75 25 L75 55 L50 70 L25 55 L25 25 Z" 
                    fill="url(#shieldGradient)" 
                    stroke="none"/>
              
              {/* Interlocked heart/chain design - simplified and cleaner */}
              <g transform="translate(50, 40)">
                {/* Left loop */}
                <path d="M-8 -5 C-12 -10, -18 -10, -18 -3 C-18 4, -8 10, 0 15 C8 10, 18 4, 18 -3 C18 -10, 12 -10, 8 -5" 
                      fill="#2D1B69" 
                      opacity="0.9"/>
                {/* Connection/chain effect */}
                <circle cx="-10" cy="0" r="3" fill="#2D1B69" opacity="0.8"/>
                <circle cx="10" cy="0" r="3" fill="#2D1B69" opacity="0.8"/>
                <rect x="-10" y="-1" width="20" height="2" fill="#2D1B69" opacity="0.6"/>
              </g>
              
              {/* PULSE text - matching your font style */}
              <text x="50" y="90" 
                    textAnchor="middle" 
                    fill="url(#textGradient)" 
                    fontSize="14" 
                    fontWeight="bold" 
                    fontFamily="system-ui, -apple-system, sans-serif" 
                    letterSpacing="3px">PULSE</text>
              
              {/* CONNECT SECURELY text */}
              <text x="50" y="105" 
                    textAnchor="middle" 
                    fill="#EC4899" 
                    fontSize="8" 
                    fontWeight="600" 
                    fontFamily="system-ui, -apple-system, sans-serif" 
                    letterSpacing="2px">CONNECT SECURELY</text>
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Welcome Back</h1>
          <p className="text-white/80 font-medium">Continue building secure connections</p>
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
                  Email Address
                </label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  placeholder="Enter your email"
                  required
                />
              </div>
              
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                  Password
                </label>
                <input
                  type="password"
                  id="password"
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  placeholder="Enter your password"
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
              {isLoading ? (
                <div className="flex items-center justify-center">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  {isLogin ? 'Signing In...' : 'Creating Account...'}
                </div>
              ) : (
                isLogin ? 'Sign In' : 'Create Account'
              )}
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
                  ? 'New to Pulse? Create an account' 
                  : 'Already have an account? Sign in'
                }
              </button>
            </div>
          </form>
        </div>

        {/* Value Proposition */}
        <div className="mt-8 text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Why Choose Pulse?</h2>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 border border-gray-100">
              <div className="text-2xl mb-2">🔒</div>
              <h3 className="font-medium text-gray-900 mb-1">5-Layer Trust</h3>
              <p className="text-gray-600">Progressive relationship building</p>
            </div>
            <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 border border-gray-100">
              <div className="text-2xl mb-2">🧠</div>
              <h3 className="font-medium text-gray-900 mb-1">AI Matching</h3>
              <p className="text-gray-600">Authentic compatibility scores</p>
            </div>
            <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 border border-gray-100">
              <div className="text-2xl mb-2">✨</div>
              <h3 className="font-medium text-gray-900 mb-1">Genuine Bonds</h3>
              <p className="text-gray-600">Quality over quantity</p>
            </div>
            <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 border border-gray-100">
              <div className="text-2xl mb-2">🎯</div>
              <h3 className="font-medium text-gray-900 mb-1">Purpose-Driven</h3>
              <p className="text-gray-600">Meaningful connections</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthScreen;