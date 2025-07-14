import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

const MarketplaceInterface = ({ user, token, api }) => {
  const { t } = useTranslation();
  const [activeView, setActiveView] = useState('browse'); // browse, create, my-listings, verification, analytics
  const [listings, setListings] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [myListings, setMyListings] = useState([]);

  // Enhanced search filters
  const [filters, setFilters] = useState({
    state: '',
    city: '',
    pincode: '',
    minPrice: '',
    maxPrice: '',
    verificationLevel: '',
    onlyVerifiedSellers: false,
    sortBy: 'created_at'
  });

  // Verification state
  const [verificationStatus, setVerificationStatus] = useState({});
  const [showVerificationModal, setShowVerificationModal] = useState(false);
  const [phoneVerification, setPhoneVerification] = useState({
    phone: '',
    otp: '',
    step: 'phone' // phone, otp, complete
  });
  const [govIdVerification, setGovIdVerification] = useState({
    idType: '',
    idNumber: '',
    fullName: '',
    dateOfBirth: '',
    address: ''
  });

  // Analytics state
  const [analytics, setAnalytics] = useState({});
  const [marketplaceStats, setMarketplaceStats] = useState({});

  // Safety check-in state
  const [showSafetyModal, setShowSafetyModal] = useState(false);
  const [selectedListingForSafety, setSelectedListingForSafety] = useState(null);
  const [safetyCheckIn, setSafetyCheckIn] = useState({
    meetingLocation: '',
    meetingTime: '',
    contactPhone: '',
    emergencyContactName: '',
    emergencyContactPhone: ''
  });

  // New listing form state
  const [newListing, setNewListing] = useState({
    title: '',
    description: '',
    category: '',
    price: '',
    price_type: 'fixed',
    tags: '',
    contact_method: 'chat'
  });

  // Fetch data on component mount
  useEffect(() => {
    fetchCategories();
    fetchListings();
    fetchVerificationStatus();
    if (activeView === 'my-listings') {
      fetchMyListings();
    } else if (activeView === 'analytics') {
      fetchAnalytics();
      fetchMarketplaceStats();
    }
  }, [activeView]);

  // Fetch verification status
  const fetchVerificationStatus = async () => {
    try {
      const response = await axios.get(`${api}/verification/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setVerificationStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch verification status:', error);
    }
  };

  // Fetch analytics
  const fetchAnalytics = async () => {
    try {
      const response = await axios.get(`${api}/analytics/dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAnalytics(response.data);
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
    }
  };

  // Fetch marketplace stats
  const fetchMarketplaceStats = async () => {
    try {
      const response = await axios.get(`${api}/analytics/marketplace-stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMarketplaceStats(response.data);
    } catch (error) {
      console.error('Failed to fetch marketplace stats:', error);
    }
  };

  // Fetch marketplace categories
  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${api}/marketplace/categories`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCategories(response.data.categories);
    } catch (error) {
      console.error('Failed to fetch categories:', error);
    }
  };

  // Enhanced fetch listings with filters
  const fetchListings = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      
      if (selectedCategory) params.append('category', selectedCategory);
      if (searchQuery) params.append('query', searchQuery);
      if (filters.state) params.append('state', filters.state);
      if (filters.city) params.append('city', filters.city);
      if (filters.pincode) params.append('pincode', filters.pincode);
      if (filters.minPrice) params.append('min_price', filters.minPrice);
      if (filters.maxPrice) params.append('max_price', filters.maxPrice);
      if (filters.verificationLevel) params.append('verification_level', filters.verificationLevel);
      if (filters.onlyVerifiedSellers) params.append('only_verified_sellers', 'true');
      if (filters.sortBy) params.append('sort_by', filters.sortBy);
      
      const response = await axios.get(`${api}/marketplace/listings?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setListings(response.data.listings);
    } catch (error) {
      console.error('Failed to fetch listings:', error);
    } finally {
      setLoading(false);
    }
  };

  // Fetch user's listings
  const fetchMyListings = async () => {
    try {
      const response = await axios.get(`${api}/marketplace/my-listings`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMyListings(response.data.listings);
    } catch (error) {
      console.error('Failed to fetch my listings:', error);
    }
  };

  // Handle enhanced search
  const handleEnhancedSearch = () => {
    fetchListings();
  };

  // Phone verification functions
  const sendPhoneOTP = async () => {
    try {
      const response = await axios.post(`${api}/verification/phone/send-otp`, {
        phone_number: phoneVerification.phone
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.status === 'success') {
        setPhoneVerification({...phoneVerification, step: 'otp'});
        alert('OTP sent successfully! Check your phone.');
      }
    } catch (error) {
      console.error('Failed to send OTP:', error);
      alert('Failed to send OTP. Please try again.');
    }
  };

  const verifyPhoneOTP = async () => {
    try {
      const response = await axios.post(`${api}/verification/phone/verify-otp`, {
        otp: phoneVerification.otp
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.status === 'success') {
        setPhoneVerification({...phoneVerification, step: 'complete'});
        fetchVerificationStatus();
        alert('Phone verified successfully!');
      }
    } catch (error) {
      console.error('Failed to verify OTP:', error);
      alert('Invalid OTP. Please try again.');
    }
  };

  // Government ID verification
  const submitGovernmentID = async () => {
    try {
      const response = await axios.post(`${api}/verification/government-id`, govIdVerification, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.status === 'success') {
        fetchVerificationStatus();
        alert(response.data.message);
        setShowVerificationModal(false);
      }
    } catch (error) {
      console.error('Failed to submit government ID:', error);
      alert('Failed to submit government ID. Please check your details.');
    }
  };

  // Safety check-in functions
  const createSafetyCheckIn = async () => {
    try {
      const checkInData = {
        listing_id: selectedListingForSafety.listing_id,
        meeting_location: safetyCheckIn.meetingLocation,
        meeting_time: new Date(safetyCheckIn.meetingTime).toISOString(),
        contact_phone: safetyCheckIn.contactPhone,
        emergency_contact_name: safetyCheckIn.emergencyContactName,
        emergency_contact_phone: safetyCheckIn.emergencyContactPhone
      };

      const response = await axios.post(`${api}/safety/check-in`, checkInData, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.status === 'success') {
        alert('Safety check-in created successfully!');
        setShowSafetyModal(false);
        setSafetyCheckIn({
          meetingLocation: '',
          meetingTime: '',
          contactPhone: '',
          emergencyContactName: '',
          emergencyContactPhone: ''
        });
      }
    } catch (error) {
      console.error('Failed to create safety check-in:', error);
      alert('Failed to create safety check-in. Please try again.');
    }
  };

  // Create new listing
  const handleCreateListing = async () => {
    try {
      if (!newListing.title || !newListing.description || !newListing.category) {
        alert('Please fill in all required fields');
        return;
      }

      const listingData = {
        ...newListing,
        price: newListing.price ? parseFloat(newListing.price) : null,
        tags: newListing.tags ? newListing.tags.split(',').map(tag => tag.trim()) : []
      };

      await axios.post(`${api}/marketplace/listings`, listingData, {
        headers: { Authorization: `Bearer ${token}` }
      });

      alert('Listing created successfully!');
      setShowCreateModal(false);
      setNewListing({
        title: '',
        description: '',
        category: '',
        price: '',
        price_type: 'fixed',
        tags: '',
        contact_method: 'chat'
      });
      
      if (activeView === 'my-listings') {
        fetchMyListings();
      } else {
        fetchListings();
      }
    } catch (error) {
      console.error('Failed to create listing:', error);
      alert('Failed to create listing. Please try again.');
    }
  };

  // Contact seller
  const handleContactSeller = async (listing) => {
    try {
      const message = `Hi! I'm interested in your listing: ${listing.title}`;
      
      await axios.post(`${api}/marketplace/listings/${listing.listing_id}/message`, {
        recipient_id: listing.owner?.user_id || listing.user_id,
        message: message
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      alert('Message sent! Check your chats to continue the conversation.');
    } catch (error) {
      console.error('Failed to send message:', error);
      alert('Failed to send message. Please try again.');
    }
  };

  // Update listing availability
  const updateListingAvailability = async (listingId, status) => {
    try {
      await axios.put(`${api}/marketplace/listings/${listingId}/availability`, 
        { status }, 
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      alert(`Listing marked as ${status}`);
      fetchMyListings();
    } catch (error) {
      console.error('Failed to update listing:', error);
      alert('Failed to update listing. Please try again.');
    }
  };

  // Enhanced listing card with verification badges and safety features
  const renderListingCard = (listing, isOwnListing = false) => (
    <div key={listing.listing_id} className="bg-white rounded-lg shadow-md p-4 mb-4">
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-lg font-semibold text-gray-900">{listing.title}</h3>
        <div className="flex items-center space-x-2">
          {listing.category && (
            <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
              {categories.find(c => c.value === listing.category)?.label || listing.category}
            </span>
          )}
          <span className={`text-xs px-2 py-1 rounded ${
            listing.availability === 'available' ? 'bg-green-100 text-green-800' :
            listing.availability === 'pending' ? 'bg-yellow-100 text-yellow-800' :
            'bg-red-100 text-red-800'
          }`}>
            {listing.availability}
          </span>
        </div>
      </div>

      {/* Seller verification badges */}
      {listing.seller && (
        <div className="flex items-center space-x-2 mb-2">
          <span className="text-sm text-gray-600">By {listing.seller.display_name}</span>
          <div className="flex space-x-1">
            {listing.seller.email_verified && (
              <span className="bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded" title="Email Verified">
                📧
              </span>
            )}
            {listing.seller.phone_verified && (
              <span className="bg-green-100 text-green-700 text-xs px-2 py-1 rounded" title="Phone Verified">
                📱
              </span>
            )}
            {listing.seller.government_id_verified && (
              <span className="bg-purple-100 text-purple-700 text-xs px-2 py-1 rounded" title="Government ID Verified">
                🆔
              </span>
            )}
            <span className={`text-xs px-2 py-1 rounded ${
              listing.seller.verification_level === 'premium' ? 'bg-gold-100 text-gold-700' :
              listing.seller.verification_level === 'verified' ? 'bg-green-100 text-green-700' :
              'bg-gray-100 text-gray-600'
            }`}>
              {listing.seller.verification_level.toUpperCase()}
            </span>
          </div>
        </div>
      )}

      <p className="text-gray-600 text-sm mb-3 line-clamp-2">{listing.description}</p>

      {/* Location information */}
      {listing.location && (
        <div className="text-xs text-gray-500 mb-2">
          📍 {typeof listing.location === 'string' ? listing.location : 
             `${listing.location?.city || ''}${listing.location?.city && listing.location?.state ? ', ' : ''}${listing.location?.state || ''}${listing.location?.pincode ? ` - ${listing.location.pincode}` : ''}`}
        </div>
      )}

      <div className="flex justify-between items-center mb-3">
        <div>
          {listing.price && (
            <span className="text-lg font-bold text-green-600">
              ₹{listing.price}
              {listing.price_type === 'hourly' && '/hr'}
            </span>
          )}
          {listing.price_type === 'negotiable' && (
            <span className="text-sm text-gray-500 ml-2">Negotiable</span>
          )}
          {listing.price_type === 'free' && (
            <span className="text-lg font-bold text-blue-600">Free</span>
          )}
        </div>
      </div>

      {listing.tags && listing.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {listing.tags.map((tag, index) => (
            <span key={index} className="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded">
              #{tag}
            </span>
          ))}
        </div>
      )}

      <div className="flex justify-between items-center text-xs text-gray-500 mb-3">
        <span>Posted {new Date(listing.created_at).toLocaleDateString()}</span>
        <span>{listing.views || 0} views • {listing.messages_count || 0} messages</span>
      </div>

      {isOwnListing ? (
        <div className="flex space-x-2">
          <select
            value={listing.availability}
            onChange={(e) => updateListingAvailability(listing.listing_id, e.target.value)}
            className="text-xs border border-gray-300 rounded px-2 py-1"
          >
            <option value="available">Available</option>
            <option value="pending">Pending</option>
            <option value="sold">Sold</option>
          </select>
          <button className="text-xs bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600">
            Edit
          </button>
        </div>
      ) : (
        <div className="flex space-x-2">
          <button
            onClick={() => handleContactSeller(listing)}
            disabled={listing.availability === 'sold'}
            className="flex-1 bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed text-sm"
          >
            💬 Contact Seller
          </button>
          <button 
            onClick={() => {
              setSelectedListingForSafety(listing);
              setShowSafetyModal(true);
            }}
            className="bg-green-500 text-white py-2 px-4 rounded-lg hover:bg-green-600 text-sm"
          >
            🛡️ Safety Check-in
          </button>
          <button className="bg-gray-100 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-200 text-sm">
            📁 Save
          </button>
        </div>
      )}
    </div>
  );

  return (
    <div className="flex-1 flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <h2 className="text-xl font-bold text-gray-900 mb-4">🛒 Marketplace</h2>
        
        {/* Navigation tabs */}
        <div className="flex space-x-4 mb-4">
          <button
            onClick={() => setActiveView('browse')}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${
              activeView === 'browse'
                ? 'bg-blue-500 text-white'
                : 'text-gray-600 hover:text-blue-600'
            }`}
          >
            Browse
          </button>
          <button
            onClick={() => setActiveView('my-listings')}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${
              activeView === 'my-listings'
                ? 'bg-blue-500 text-white'
                : 'text-gray-600 hover:text-blue-600'
            }`}
          >
            My Listings
          </button>
          <button
            onClick={() => setActiveView('verification')}
            className={`px-4 py-2 rounded-lg text-sm font-medium relative ${
              activeView === 'verification'
                ? 'bg-green-500 text-white'
                : 'text-gray-600 hover:text-green-600'
            }`}
          >
            🛡️ Verification
            {!verificationStatus.government_id_verified && (
              <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-3 h-3"></span>
            )}
          </button>
          <button
            onClick={() => setActiveView('analytics')}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${
              activeView === 'analytics'
                ? 'bg-purple-500 text-white'
                : 'text-gray-600 hover:text-purple-600'
            }`}
          >
            📊 Analytics
          </button>
        </div>

        {/* Enhanced search and filters */}
        {activeView === 'browse' && (
          <div className="space-y-4">
            {/* Main search bar */}
            <div className="flex space-x-2">
              <input
                type="text"
                placeholder="Search listings..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleEnhancedSearch()}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
              
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Categories</option>
                {categories.map(category => (
                  <option key={category.value} value={category.value}>
                    {category.icon} {category.label}
                  </option>
                ))}
              </select>
              
              <button
                onClick={handleEnhancedSearch}
                className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600"
              >
                🔍
              </button>
            </div>

            {/* Enhanced filters for Indian market */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <input
                type="text"
                placeholder="State (e.g., Maharashtra)"
                value={filters.state}
                onChange={(e) => setFilters({...filters, state: e.target.value})}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
              />
              <input
                type="text"
                placeholder="City (e.g., Mumbai)"
                value={filters.city}
                onChange={(e) => setFilters({...filters, city: e.target.value})}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
              />
              <input
                type="text"
                placeholder="Pincode (6 digits)"
                value={filters.pincode}
                onChange={(e) => setFilters({...filters, pincode: e.target.value})}
                maxLength={6}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
              />
              <select
                value={filters.sortBy}
                onChange={(e) => setFilters({...filters, sortBy: e.target.value})}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
              >
                <option value="created_at">Latest First</option>
                <option value="price_low">Price: Low to High</option>
                <option value="price_high">Price: High to Low</option>
                <option value="relevance">Most Relevant</option>
              </select>
            </div>

            {/* Price and verification filters */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <input
                type="number"
                placeholder="Min Price (₹)"
                value={filters.minPrice}
                onChange={(e) => setFilters({...filters, minPrice: e.target.value})}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
              />
              <input
                type="number"
                placeholder="Max Price (₹)"
                value={filters.maxPrice}
                onChange={(e) => setFilters({...filters, maxPrice: e.target.value})}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
              />
              <select
                value={filters.verificationLevel}
                onChange={(e) => setFilters({...filters, verificationLevel: e.target.value})}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
              >
                <option value="">All Sellers</option>
                <option value="basic">Basic</option>
                <option value="verified">Verified</option>
                <option value="premium">Premium</option>
              </select>
              <label className="flex items-center space-x-2 px-3 py-2">
                <input
                  type="checkbox"
                  checked={filters.onlyVerifiedSellers}
                  onChange={(e) => setFilters({...filters, onlyVerifiedSellers: e.target.checked})}
                  className="rounded"
                />
                <span className="text-sm">Verified Only</span>
              </label>
              <button
                onClick={() => setFilters({
                  state: '', city: '', pincode: '', minPrice: '', maxPrice: '',
                  verificationLevel: '', onlyVerifiedSellers: false, sortBy: 'created_at'
                })}
                className="text-sm text-gray-600 hover:text-red-600"
              >
                Clear Filters
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 p-4 overflow-y-auto">
        {/* Create listing button */}
        <div className="mb-4">
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 text-sm font-medium"
          >
            ➕ Create Listing
          </button>
        </div>

        {/* Listings */}
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-2"></div>
            <p className="text-gray-600">Loading listings...</p>
          </div>
        ) : (
          <div>
            {activeView === 'browse' && (
              <>
                {listings.length === 0 ? (
                  <div className="text-center py-8">
                    <p className="text-gray-600">No listings found. Try adjusting your search.</p>
                  </div>
                ) : (
                  <div>
                    <h3 className="text-lg font-semibold mb-4">
                      {listings.length} listing{listings.length !== 1 ? 's' : ''} found
                    </h3>
                    {listings.map(listing => renderListingCard(listing))}
                  </div>
                )}
              </>
            )}

            {activeView === 'my-listings' && (
              <>
                {myListings.length === 0 ? (
                  <div className="text-center py-8">
                    <p className="text-gray-600">You haven't created any listings yet.</p>
                    <button
                      onClick={() => setShowCreateModal(true)}
                      className="mt-2 text-blue-500 hover:text-blue-700"
                    >
                      Create your first listing
                    </button>
                  </div>
                ) : (
                  <div>
                    <h3 className="text-lg font-semibold mb-4">Your Listings ({myListings.length})</h3>
                    {myListings.map(listing => renderListingCard(listing, true))}
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>

      {/* Create Listing Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold text-gray-900">Create New Listing</h3>
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
                  placeholder="What are you selling or offering?"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  maxLength={100}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category *</label>
                <select
                  value={newListing.category}
                  onChange={(e) => setNewListing({...newListing, category: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select a category</option>
                  {categories.map(category => (
                    <option key={category.value} value={category.value}>
                      {category.icon} {category.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description *</label>
                <textarea
                  value={newListing.description}
                  onChange={(e) => setNewListing({...newListing, description: e.target.value})}
                  placeholder="Describe your item or service in detail..."
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  maxLength={1000}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Price</label>
                  <input
                    type="number"
                    value={newListing.price}
                    onChange={(e) => setNewListing({...newListing, price: e.target.value})}
                    placeholder="0.00"
                    min="0"
                    step="0.01"
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
                    <option value="fixed">Fixed Price</option>
                    <option value="hourly">Per Hour</option>
                    <option value="negotiable">Negotiable</option>
                    <option value="free">Free</option>
                    <option value="barter">Barter/Trade</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tags</label>
                <input
                  type="text"
                  value={newListing.tags}
                  onChange={(e) => setNewListing({...newListing, tags: e.target.value})}
                  placeholder="electronics, smartphone, iPhone (comma separated)"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="flex space-x-3 pt-4">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 bg-gray-100 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateListing}
                  className="flex-1 bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600"
                >
                  Create Listing
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MarketplaceInterface;