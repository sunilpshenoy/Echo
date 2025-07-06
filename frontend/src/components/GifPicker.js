import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

const GifPicker = ({ onGifSelect, onClose }) => {
  const { t } = useTranslation();
  const [searchQuery, setSearchQuery] = useState('');
  const [gifs, setGifs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [trendingGifs, setTrendingGifs] = useState([]);
  const [recentGifs, setRecentGifs] = useState([]);
  const [favoriteGifs, setFavoriteGifs] = useState([]);
  const [activeTab, setActiveTab] = useState('trending');
  const pickerRef = useRef(null);
  const searchTimeoutRef = useRef(null);

  // Popular GIF categories for quick access
  const quickCategories = [
    { name: 'reactions', emoji: '😂', searches: ['funny', 'lol', 'laugh', 'reaction'] },
    { name: 'love', emoji: '❤️', searches: ['love', 'heart', 'kiss', 'romantic'] },
    { name: 'celebration', emoji: '🎉', searches: ['party', 'celebrate', 'happy', 'dance'] },
    { name: 'thumbsUp', emoji: '👍', searches: ['thumbs up', 'good', 'yes', 'approve'] },
    { name: 'animals', emoji: '🐱', searches: ['cat', 'dog', 'cute animals', 'pets'] },
    { name: 'sports', emoji: '⚽', searches: ['sports', 'football', 'basketball', 'goal'] }
  ];

  // Mock GIF data (in production, this would come from Giphy/Tenor API)
  const mockGifs = {
    trending: [
      {
        id: 'trending1',
        title: 'Excited Dance',
        url: 'https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif',
        preview: 'https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/200w.gif',
        width: 480,
        height: 270
      },
      {
        id: 'trending2',
        title: 'Thumbs Up',
        url: 'https://media.giphy.com/media/111ebonMs90YLu/giphy.gif',
        preview: 'https://media.giphy.com/media/111ebonMs90YLu/200w.gif',
        width: 480,
        height: 360
      },
      {
        id: 'trending3',
        title: 'Heart Eyes',
        url: 'https://media.giphy.com/media/3o6UB3VhArvomJHtdK/giphy.gif',
        preview: 'https://media.giphy.com/media/3o6UB3VhArvomJHtdK/200w.gif',
        width: 480,
        height: 270
      }
    ]
  };

  // Load saved GIFs from localStorage
  useEffect(() => {
    const savedRecent = localStorage.getItem('pulse_recent_gifs');
    const savedFavorites = localStorage.getItem('pulse_favorite_gifs');
    
    if (savedRecent) {
      setRecentGifs(JSON.parse(savedRecent));
    }
    if (savedFavorites) {
      setFavoriteGifs(JSON.parse(savedFavorites));
    }
    
    // Load trending GIFs
    setTrendingGifs(mockGifs.trending);
  }, []);

  // Debounced GIF search
  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (searchQuery.trim()) {
      searchTimeoutRef.current = setTimeout(() => {
        searchGifs(searchQuery);
      }, 500);
    } else {
      setGifs([]);
      setActiveTab('trending');
    }

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [searchQuery]);

  const searchGifs = async (query) => {
    setLoading(true);
    setError(null);
    
    try {
      // Mock search - in production, this would call Giphy/Tenor API
      await new Promise(resolve => setTimeout(resolve, 500)); // Simulate API delay
      
      // Filter mock data based on search
      const searchResults = mockGifs.trending.filter(gif => 
        gif.title.toLowerCase().includes(query.toLowerCase())
      );
      
      setGifs(searchResults);
      setActiveTab('search');
    } catch (err) {
      setError('Failed to search GIFs. Please try again.');
      console.error('GIF search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleGifSelect = (gif) => {
    // Add to recent GIFs
    const updatedRecent = [gif, ...recentGifs.filter(g => g.id !== gif.id)].slice(0, 20);
    setRecentGifs(updatedRecent);
    localStorage.setItem('pulse_recent_gifs', JSON.stringify(updatedRecent));

    // Call parent callback
    onGifSelect({
      type: 'gif',
      id: gif.id,
      title: gif.title,
      url: gif.url,
      preview: gif.preview,
      width: gif.width,
      height: gif.height
    });
    
    onClose();
  };

  const toggleFavorite = (gif) => {
    const isFavorite = favoriteGifs.some(f => f.id === gif.id);
    let updatedFavorites;
    
    if (isFavorite) {
      updatedFavorites = favoriteGifs.filter(f => f.id !== gif.id);
    } else {
      updatedFavorites = [gif, ...favoriteGifs];
    }
    
    setFavoriteGifs(updatedFavorites);
    localStorage.setItem('pulse_favorite_gifs', JSON.stringify(updatedFavorites));
  };

  const getCurrentGifs = () => {
    switch (activeTab) {
      case 'trending':
        return trendingGifs;
      case 'recent':
        return recentGifs;
      case 'favorites':
        return favoriteGifs;
      case 'search':
        return gifs;
      default:
        return trendingGifs;
    }
  };

  // Handle clicks outside to close
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (pickerRef.current && !pickerRef.current.contains(event.target)) {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  return (
    <div 
      ref={pickerRef}
      className="absolute bottom-12 left-0 bg-white rounded-2xl shadow-2xl border border-gray-200 w-96 h-[500px] z-50 flex flex-col"
    >
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
            <span>🎬</span>
            <span>{t('gifs.picker')}</span>
          </h3>
          <button 
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-lg"
          >
            ✕
          </button>
        </div>
        
        {/* Search */}
        <input
          type="text"
          placeholder={t('gifs.search')}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {/* Quick Categories */}
      {!searchQuery && (
        <div className="p-3 border-b border-gray-200">
          <div className="grid grid-cols-3 gap-2">
            {quickCategories.map((category) => (
              <button
                key={category.name}
                onClick={() => {
                  setSearchQuery(category.name);
                }}
                className="flex items-center space-x-2 px-3 py-2 text-sm bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <span>{category.emoji}</span>
                <span className="capitalize">{category.name}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-gray-200">
        {['trending', 'recent', 'favorites'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === tab
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {t(`gifs.${tab}`)}
          </button>
        ))}
      </div>

      {/* GIF Grid */}
      <div className="flex-1 overflow-y-auto p-3">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full"></div>
          </div>
        ) : error ? (
          <div className="text-center py-8 text-red-500">
            <div className="text-4xl mb-2">❌</div>
            <p className="text-sm">{error}</p>
          </div>
        ) : getCurrentGifs().length > 0 ? (
          <div className="grid grid-cols-2 gap-2">
            {getCurrentGifs().map((gif) => (
              <div 
                key={gif.id} 
                className="relative group cursor-pointer rounded-lg overflow-hidden bg-gray-100"
              >
                <div
                  className="w-full h-24 bg-gray-200 rounded flex items-center justify-center text-gray-500 text-xs hover:bg-gray-300 transition-colors"
                  onClick={() => handleGifSelect(gif)}
                >
                  🎬 {gif.title}
                </div>
                
                {/* Overlay */}
                <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-opacity flex items-center justify-center">
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity flex space-x-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleFavorite(gif);
                      }}
                      className="p-1 bg-white rounded-full shadow-lg"
                      title={favoriteGifs.some(f => f.id === gif.id) ? 'Remove from favorites' : 'Add to favorites'}
                    >
                      {favoriteGifs.some(f => f.id === gif.id) ? '❤️' : '🤍'}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-2">🎬</div>
            <p className="text-sm">
              {activeTab === 'recent' && 'No recent GIFs'}
              {activeTab === 'favorites' && 'No favorite GIFs yet'}
              {activeTab === 'search' && (searchQuery ? 'No GIFs found' : 'Search for GIFs')}
              {activeTab === 'trending' && 'Loading GIFs...'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default GifPicker;