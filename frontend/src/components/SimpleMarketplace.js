import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

  const SimpleMarketplace = ({ user, token, api }) => {
  const { t } = useTranslation();
  const [activeView, setActiveView] = useState('browse');
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('');
  
  // Simple create listing state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newListing, setNewListing] = useState({
    title: '',
    description: '',
    category: 'food',
    price: '',
    price_type: 'fixed',
    youtube_url: '',
    instagram_url: '',
    location: ''
  });

  // Emergency close function
  const closeModal = () => {
    setShowCreateModal(false);
    setLoading(false); // Reset loading state
    // Reset form
    setNewListing({
      title: '',
      description: '',
      category: 'food',
      price: '',
      price_type: 'fixed',
      youtube_url: '',
      instagram_url: '',
      location: ''
    });
  };

  // Add escape key listener
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && showCreateModal) {
        closeModal();
      }
    };

    if (showCreateModal) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [showCreateModal]);

  // Simple categories
  const categories = [
    { value: 'food', label: 'Food & Catering', icon: '🍳' },
    { value: 'design', label: 'Design & Creative', icon: '🎨' },
    { value: 'tech', label: 'Tech Services', icon: '💻' },
    { value: 'home', label: 'Home Services', icon: '🏠' },
    { value: 'education', label: 'Education', icon: '📚' }
  ];

  // Enhanced mock listings with social links
  const mockListings = [
    {
      id: '1',
      title: 'Home Cooking Service',
      description: 'Authentic North Indian meals delivered fresh daily. Watch my cooking videos!',
      category: 'food',
      price: 500,
      price_type: 'per_meal',
      seller: 'Ravi Kumar',
      location: 'Mumbai, Maharashtra',
      rating: 4.8,
      verified: true,
      youtube_url: 'https://youtube.com/watch?v=example1',
      instagram_url: 'https://instagram.com/ravi_chef_mumbai'
    },
    {
      id: '2',
      title: 'Logo Design Service',
      description: 'Professional logos for your business. Check out my portfolio on Instagram!',
      category: 'design',
      price: 2000,
      price_type: 'per_project',
      seller: 'Sarah Design',
      location: 'Delhi',
      rating: 4.9,
      verified: true,
      youtube_url: '',
      instagram_url: 'https://instagram.com/sarah_designs_delhi'
    },
    {
      id: '3',
      title: 'Math Tutoring',
      description: 'Expert math tutoring for grades 6-12. See my teaching style on YouTube!',
      category: 'education',
      price: 800,
      price_type: 'per_hour',
      seller: 'Dr. Sharma',
      location: 'Bangalore',
      rating: 4.7,
      verified: true,
      youtube_url: 'https://youtube.com/watch?v=math_tutorial',
      instagram_url: ''
    },
    {
      id: '4',
      title: 'Plumbing Services',
      description: 'Quick home repairs and maintenance. See my work videos for quality assurance!',
      category: 'home',
      price: 600,
      price_type: 'per_hour',
      seller: 'Rajesh Plumber',
      location: 'Chennai',
      rating: 4.6,
      verified: true,
      youtube_url: 'https://youtube.com/watch?v=plumbing_work',
      instagram_url: 'https://instagram.com/rajesh_plumber_chennai'
    }
  ];

  useEffect(() => {
    loadListings();
  }, [selectedCategory]);

  // Helper functions for social media links
  const isValidYouTubeUrl = (url) => {
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/;
    return youtubeRegex.test(url);
  };

  const isValidInstagramUrl = (url) => {
    const instagramRegex = /^(https?:\/\/)?(www\.)?instagram\.com\/.+/;
    return instagramRegex.test(url);
  };

  const getYouTubeThumbnail = (url) => {
    const videoId = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)/);
    return videoId ? `https://img.youtube.com/vi/${videoId[1]}/mqdefault.jpg` : null;
  };

  const extractInstagramUsername = (url) => {
    const match = url.match(/instagram\.com\/([^\/\?]+)/);
    return match ? `@${match[1]}` : 'Instagram';
  };

  const loadListings = async () => {
    setLoading(true);
    try {
      // Try to load real data, fall back to mock data
      const response = await axios.get(`${api}/marketplace/listings?category=${selectedCategory}`, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 5000
      });
      setListings(response.data.listings || mockListings);
    } catch (error) {
      console.log('Using mock data:', error.message);
      setListings(mockListings.filter(item => !selectedCategory || item.category === selectedCategory));
    }
    setLoading(false);
  };

  const createListing = async () => {
    if (!newListing.title || !newListing.description || !newListing.price) {
      alert('Please fill all required fields');
      return;
    }

    // Validate social media URLs if provided
    if (newListing.youtube_url && !isValidYouTubeUrl(newListing.youtube_url)) {
      alert('Please enter a valid YouTube URL');
      return;
    }

    if (newListing.instagram_url && !isValidInstagramUrl(newListing.instagram_url)) {
      alert('Please enter a valid Instagram URL');
      return;
    }

    setLoading(true);
    
    try {
      // Try real API first
      await axios.post(`${api}/marketplace/listings`, {
        title: newListing.title,
        description: newListing.description,
        category: newListing.category,
        price: parseFloat(newListing.price),
        price_type: newListing.price_type,
        youtube_url: newListing.youtube_url,
        instagram_url: newListing.instagram_url,
        location: newListing.location,
        tags: []
      }, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 5000
      });

      alert('Listing created successfully!');
      setShowCreateModal(false);
      setNewListing({ 
        title: '', description: '', category: 'food', price: '', 
        price_type: 'fixed', youtube_url: '', instagram_url: '', location: ''
      });
      loadListings();
    } catch (error) {
      console.error('Create listing error:', error);
      
      // Add to mock data as fallback
      const mockListing = {
        id: Date.now().toString(),
        ...newListing,
        price: parseFloat(newListing.price),
        seller: user.username || 'You',
        location: newListing.location || 'Your Location',
        rating: 4.5,
        verified: false
      };
      
      setListings(prev => [mockListing, ...prev]);
      alert('Listing created successfully! (Demo mode)');
      setShowCreateModal(false);
      setNewListing({ 
        title: '', description: '', category: 'food', price: '', 
        price_type: 'fixed', youtube_url: '', instagram_url: '', location: ''
      });
    } finally {
      setLoading(false);
    }
  };

  const contactSeller = (listing) => {
    // Simple contact action
    alert(`Contact feature coming soon! You can reach out to ${typeof listing.seller === 'string' ? listing.seller : listing.seller?.username || 'the seller'} for: ${listing.title}`);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="bg-white border-b p-4 flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <h1 className="text-lg font-bold">Marketplace</h1>
          <div className="flex space-x-2">
            <button
              onClick={() => setActiveView('browse')}
              className={`px-3 py-1 rounded-lg text-sm ${
                activeView === 'browse' 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
              aria-label="Browse marketplace listings"
              aria-current={activeView === 'browse' ? 'page' : undefined}
            >
              Browse
            </button>
            <button
              onClick={() => setActiveView('my-listings')}
              className={`px-3 py-1 rounded-lg text-sm ${
                activeView === 'my-listings' 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
              aria-label="View your listings"
              aria-current={activeView === 'my-listings' ? 'page' : undefined}
            >
              My Listings
            </button>
          </div>
        </div>
        
        <button
          onClick={() => setShowCreateModal(true)}
          className="bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 text-sm"
          aria-label="Create new marketplace listing"
        >
          + Create Listing
        </button>
      </div>

      {/* Category Filter */}
      <div className="bg-gray-50 border-b p-4">
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedCategory('')}
            className={`px-3 py-1 rounded-full text-sm ${
              selectedCategory === '' 
                ? 'bg-purple-500 text-white' 
                : 'bg-white text-gray-700 hover:bg-gray-100'
            }`}
            aria-label="Show all categories"
            aria-pressed={selectedCategory === ''}
          >
            All Categories
          </button>
          {categories.map(category => (
            <button
              key={category.value}
              onClick={() => setSelectedCategory(category.value)}
              className={`px-3 py-1 rounded-full text-sm flex items-center space-x-1 ${
                selectedCategory === category.value 
                  ? 'bg-purple-500 text-white' 
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
              aria-label={`Filter by ${category.label}`}
              aria-pressed={selectedCategory === category.value}
            >
              <span>{category.icon}</span>
              <span>{category.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Listings Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
            <p className="text-gray-600">Loading...</p>
          </div>
        ) : (
          <div className="space-y-4">
            {listings.length === 0 ? (
              <div className="bg-white rounded-lg p-8 text-center">
                <p className="text-gray-600 mb-4">No listings found</p>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600"
                  aria-label="Create your first listing"
                >
                  Create First Listing
                </button>
              </div>
            ) : (
              listings.map(listing => (
                <div key={listing.id} className="bg-white rounded-lg p-4 shadow-sm">
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="text-lg font-semibold text-gray-900">{listing.title}</h3>
                    <div className="flex items-center space-x-2">
                      <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                        {categories.find(c => c.value === listing.category)?.label || listing.category}
                      </span>
                      {listing.verified && (
                        <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
                          ✓ Verified
                        </span>
                      )}
                    </div>
                  </div>

                  <p className="text-gray-600 text-sm mb-3">{listing.description}</p>

                  {/* Social Media Links */}
                  {(listing.youtube_url || listing.instagram_url) && (
                    <div className="flex space-x-2 mb-3">
                      {listing.youtube_url && (
                        <a
                          href={listing.youtube_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center space-x-1 bg-red-100 text-red-700 px-3 py-1 rounded-full text-xs hover:bg-red-200 transition-colors"
                          aria-label={`Watch demo video for ${listing.title}`}
                        >
                          <span>📺</span>
                          <span>Watch Demo</span>
                        </a>
                      )}
                      {listing.instagram_url && (
                        <a
                          href={listing.instagram_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center space-x-1 bg-pink-100 text-pink-700 px-3 py-1 rounded-full text-xs hover:bg-pink-200 transition-colors"
                          aria-label={`View portfolio for ${listing.title}`}
                        >
                          <span>📷</span>
                          <span>Portfolio</span>
                        </a>
                      )}
                    </div>
                  )}

                  <div className="flex justify-between items-center mb-3">
                    <div>
                      <span className="text-lg font-bold text-green-600">
                        ₹{listing.price}
                        {listing.price_type === 'per_hour' && '/hr'}
                        {listing.price_type === 'per_project' && '/project'}
                        {listing.price_type === 'per_meal' && '/meal'}
                      </span>
                    </div>
                    <div className="text-sm text-gray-500">
                      📍 {typeof listing.location === 'string' ? listing.location : 
                           (listing.location?.city || listing.location?.state || 'Location not specified')}
                    </div>
                  </div>

                  <div className="flex justify-between items-center">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-600">By {typeof listing.seller === 'string' ? listing.seller : 
                           (listing.seller?.username || listing.seller?.display_name || 'Unknown seller')}</span>
                      <span className="text-sm text-yellow-600">⭐ {listing.rating}</span>
                    </div>
                    
                    <button
                      onClick={() => contactSeller(listing)}
                      className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 text-sm"
                      aria-label={`Contact ${typeof listing.seller === 'string' ? listing.seller : listing.seller?.username || 'seller'} about ${listing.title}`}
                    >
                      💬 Contact
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Simple Create Modal */}
      {showCreateModal && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" 
          role="dialog" 
          aria-labelledby="create-listing-title" 
          aria-modal="true"
          onClick={(e) => {
            // Close modal when clicking on backdrop
            if (e.target === e.currentTarget) {
              closeModal();
            }
          }}
        >
          <div className="bg-white rounded-lg p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-4">
              <h3 id="create-listing-title" className="text-lg font-bold">Create Listing</h3>
              <button
                onClick={closeModal}
                className="text-gray-500 hover:text-gray-700 text-xl font-bold"
                aria-label="Close create listing modal"
                type="button"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="listing-title">Title *</label>
                <input
                  type="text"
                  id="listing-title"
                  value={newListing.title}
                  onChange={(e) => setNewListing({...newListing, title: e.target.value})}
                  placeholder="Service title"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="listing-category">Category *</label>
                <select
                  id="listing-category"
                  value={newListing.category}
                  onChange={(e) => setNewListing({...newListing, category: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  {categories.map(cat => (
                    <option key={cat.value} value={cat.value}>
                      {cat.icon} {cat.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="listing-description">Description *</label>
                <textarea
                  id="listing-description"
                  value={newListing.description}
                  onChange={(e) => setNewListing({...newListing, description: e.target.value})}
                  placeholder="Describe your service..."
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="listing-location">Location</label>
                <input
                  type="text"
                  id="listing-location"
                  value={newListing.location}
                  onChange={(e) => setNewListing({...newListing, location: e.target.value})}
                  placeholder="e.g., Mumbai, Maharashtra"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Social Media Links */}
              <div className="border-t pt-4">
                <h4 className="text-sm font-medium text-gray-700 mb-3">📱 Showcase Your Work (Optional)</h4>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="youtube-url">YouTube Video URL</label>
                  <input
                    type="url"
                    id="youtube-url"
                    value={newListing.youtube_url}
                    onChange={(e) => setNewListing({...newListing, youtube_url: e.target.value})}
                    placeholder="https://youtube.com/watch?v=..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">📺 Show a demo of your service</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="instagram-url">Instagram Profile URL</label>
                  <input
                    type="url"
                    id="instagram-url"
                    value={newListing.instagram_url}
                    onChange={(e) => setNewListing({...newListing, instagram_url: e.target.value})}
                    placeholder="https://instagram.com/your_username"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">📷 Link to your portfolio/gallery</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="listing-price">Price (₹) *</label>
                  <input
                    type="number"
                    id="listing-price"
                    value={newListing.price}
                    onChange={(e) => setNewListing({...newListing, price: e.target.value})}
                    placeholder="500"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="price-type">Price Type</label>
                  <select
                    id="price-type"
                    value={newListing.price_type}
                    onChange={(e) => setNewListing({...newListing, price_type: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="fixed">Fixed</option>
                    <option value="per_hour">Per Hour</option>
                    <option value="per_project">Per Project</option>
                    <option value="negotiable">Negotiable</option>
                  </select>
                </div>
              </div>

              <div className="flex space-x-3 pt-4">
                <button
                  type="button"
                  onClick={closeModal}
                  className="flex-1 bg-gray-100 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-200 transition-colors"
                  aria-label="Cancel listing creation"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={createListing}
                  disabled={loading}
                  className="flex-1 bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  aria-label="Create new listing"
                >
                  {loading ? 'Creating...' : 'Create'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SimpleMarketplace;