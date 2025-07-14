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

    try {
      setLoading(true);
      
      // Try real API first
      await axios.post(`${api}/marketplace/listings`, {
        title: newListing.title,
        description: newListing.description,
        category: newListing.category,
        price: parseFloat(newListing.price),
        price_type: newListing.price_type,
        tags: []
      }, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 5000
      });

      alert('Listing created successfully!');
      setShowCreateModal(false);
      setNewListing({ title: '', description: '', category: 'food', price: '', price_type: 'fixed' });
      loadListings();
    } catch (error) {
      console.error('Create listing error:', error);
      
      // Add to mock data as fallback
      const mockListing = {
        id: Date.now().toString(),
        ...newListing,
        price: parseFloat(newListing.price),
        seller: user.username || 'You',
        location: 'Your Location',
        rating: 4.5,
        verified: false
      };
      
      setListings(prev => [mockListing, ...prev]);
      alert('Listing created (demo mode)!');
      setShowCreateModal(false);
      setNewListing({ title: '', description: '', category: 'food', price: '', price_type: 'fixed' });
    }
    setLoading(false);
  };

  const contactSeller = (listing) => {
    alert(`📱 Contact ${listing.seller}\n\nThis will open a chat to discuss: ${listing.title}\n\n(Demo: In the full version, this opens an encrypted chat)`);
  };

  return (
    <div className="flex-1 bg-gray-50 p-4">
      {/* Header */}
      <div className="bg-white rounded-lg p-4 mb-4 shadow-sm">
        <h2 className="text-xl font-bold text-gray-900 mb-4">🛒 Marketplace</h2>
        
        {/* Simple Navigation */}
        <div className="flex space-x-3 mb-4">
          <button
            onClick={() => setActiveView('browse')}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${
              activeView === 'browse' ? 'bg-blue-500 text-white' : 'text-gray-600 hover:text-blue-600'
            }`}
          >
            Browse
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-green-500 text-white rounded-lg text-sm font-medium hover:bg-green-600"
          >
            ➕ Create Listing
          </button>
        </div>

        {/* Simple Category Filter */}
        <div className="flex space-x-2">
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Categories</option>
            {categories.map(cat => (
              <option key={cat.value} value={cat.value}>
                {cat.icon} {cat.label}
              </option>
            ))}
          </select>
          <button
            onClick={loadListings}
            className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600"
          >
            🔍 Search
          </button>
        </div>
      </div>

      {/* Content */}
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
                    📍 {listing.location}
                  </div>
                </div>

                <div className="flex justify-between items-center">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-600">By {listing.seller}</span>
                    <span className="text-sm text-yellow-600">⭐ {listing.rating}</span>
                  </div>
                  
                  <button
                    onClick={() => contactSeller(listing)}
                    className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 text-sm"
                  >
                    💬 Contact
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Simple Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold">Create Listing</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-gray-500 hover:text-gray-700 text-xl"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Title *</label>
                <input
                  type="text"
                  value={newListing.title}
                  onChange={(e) => setNewListing({...newListing, title: e.target.value})}
                  placeholder="Service title"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category *</label>
                <select
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
                <label className="block text-sm font-medium text-gray-700 mb-1">Description *</label>
                <textarea
                  value={newListing.description}
                  onChange={(e) => setNewListing({...newListing, description: e.target.value})}
                  placeholder="Describe your service..."
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Price (₹) *</label>
                  <input
                    type="number"
                    value={newListing.price}
                    onChange={(e) => setNewListing({...newListing, price: e.target.value})}
                    placeholder="500"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Price Type</label>
                  <select
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
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 bg-gray-100 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  onClick={createListing}
                  disabled={loading}
                  className="flex-1 bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 disabled:opacity-50"
                >
                  {loading ? '...' : 'Create'}
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