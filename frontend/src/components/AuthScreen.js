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
      console.error('Error response:', error.response);
      console.error('Error status:', error.response?.status);
      console.error('Error data:', error.response?.data);
      setError(error.response?.data?.detail || error.message || 'Authentication failed');
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-md">
        {/* Header with authentic connection messaging */}
        <div className="text-center mb-8 animate-fade-in-up">
          <div className="w-20 h-20 mx-auto mb-6 bg-trust-gradient rounded-full flex items-center justify-center">
            <span className="text-3xl text-white">💫</span>
          </div>
          <h1 className="heading-xl mb-4">Authentic Connections</h1>
          <p className="text-subtle text-lg leading-relaxed">
            Where genuine friendships begin through trust, patience, and real conversation.
          </p>
        </div>
        
        {/* Auth Form Card */}
        <div className="card animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
          <div className="text-center mb-6">
            <h2 className="heading-md">
              {isLogin ? 'Welcome Back' : 'Begin Your Journey'}
            </h2>
            <p className="text-subtle">
              {isLogin 
                ? 'Continue building authentic connections' 
                : 'Join others seeking genuine friendships'
              }
            </p>
          </div>
          
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
              {error}
            </div>
          )}
          
          <form onSubmit={handleSubmit} className="space-y-6">
            {!isLogin && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Display Name
                </label>
                <input
                  type="text"
                  name="username"
                  value={formData.username}
                  onChange={handleInputChange}
                  className="input-field"
                  placeholder="What should we call you?"
                  required={!isLogin}
                />
              </div>
            )}
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email Address
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                className="input-field"
                placeholder="your@email.com"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                className="input-field"
                placeholder={isLogin ? "Enter your password" : "Choose a secure password"}
                required
              />
            </div>
            
            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full relative"
            >
              {isLoading ? (
                <div className="flex items-center justify-center">
                  <div className="loading-spinner w-5 h-5 mr-2"></div>
                  {isLogin ? 'Signing In...' : 'Creating Account...'}
                </div>
              ) : (
                isLogin ? 'Sign In' : 'Create Account'
              )}
            </button>
          </form>
          
          <div className="mt-6 text-center">
            <button
              onClick={() => {
                setIsLogin(!isLogin);
                setError('');
                setFormData({ email: '', password: '', username: '' });
              }}
              className="text-emphasis hover:underline transition-all"
            >
              {isLogin 
                ? "New to authentic connections? Create an account" 
                : "Already have an account? Sign in"
              }
            </button>
          </div>
        </div>
        
        {/* Trust Messaging */}
        <div className="mt-8 text-center animate-fade-in-up" style={{ animationDelay: '0.4s' }}>
          <div className="card-glass">
            <h3 className="heading-md mb-4">Why Choose Authentic Connections?</h3>
            <div className="grid grid-cols-1 gap-4 text-left">
              <div className="flex items-start space-x-3">
                <div className="trust-level-indicator trust-level-1 text-sm">1</div>
                <div>
                  <p className="font-medium text-gray-800">Progressive Trust</p>
                  <p className="text-subtle text-sm">Build connections gradually, at your own pace</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-warm-gradient rounded-full flex items-center justify-center">
                  <span className="text-white text-sm">✓</span>
                </div>
                <div>
                  <p className="font-medium text-gray-800">Authentic People Only</p>
                  <p className="text-subtle text-sm">Verified users seeking genuine connections</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-gentle-gradient rounded-full flex items-center justify-center">
                  <span className="text-white text-sm">🛡️</span>
                </div>
                <div>
                  <p className="font-medium text-gray-800">Your Privacy Matters</p>
                  <p className="text-subtle text-sm">Share only what you're comfortable with</p>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Footer */}
        <div className="mt-8 text-center text-subtle text-sm">
          <p>Building genuine friendships, one authentic conversation at a time.</p>
        </div>
      </div>
    </div>
  );
};

export default AuthScreen;