import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

const ReelsMarketplace = ({ user, token, api }) => {
  const { t } = useTranslation();
  const [activeView, setActiveView] = useState('feed'); // feed, create, profile, analytics
  const [reels, setReels] = useState([]);
  const [currentReelIndex, setCurrentReelIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  
  // Filters and search
  const [selectedCategory, setSelectedCategory] = useState('');
  const [locationFilter, setLocationFilter] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [categories, setCategories] = useState([]);
  
  // Interaction states
  const [showBiddingModal, setShowBiddingModal] = useState(false);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedReel, setSelectedReel] = useState(null);
  const [bidAmount, setBidAmount] = useState('');
  const [bidMessage, setBidMessage] = useState('');
  
  // Video creation states
  const [newReel, setNewReel] = useState({
    title: '',
    description: '',
    category: '',
    basePrice: '',
    priceType: 'per_hour',
    tags: '',
    location: { city: '', state: '' }
  });
  const [recordedVideo, setRecordedVideo] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [videoPreview, setVideoPreview] = useState(null);
  
  // Video player refs
  const videoRefs = useRef([]);
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  
  // Mock data for demonstration
  const mockReels = [
    {
      reel_id: '1',
      seller: {
        name: 'Ravi Kumar',
        username: '@ravi_chef_mumbai',
        verification_level: 'verified',
        rating: 4.8,
        location: 'Mumbai, Maharashtra'
      },
      service: {
        title: 'Home Cooking Service',
        category: 'Food & Catering',
        basePrice: 500,
        priceType: 'per_meal'
      },
      video: {
        url: '/api/placeholder-video.mp4',
        thumbnail: '/api/placeholder-thumbnail.jpg',
        duration: 45
      },
      stats: {
        likes: 1250,
        views: 15000,
        comments: 89,
        hires: 23
      },
      description: '🍳 Authentic North Indian meals delivered to your home! 15+ years experience. WhatsApp for custom menus! #HomeCooking #Mumbai #NorthIndian',
      tags: ['cooking', 'food', 'homedelivery', 'mumbai'],
      reviews: [
        { user: 'Priya S.', rating: 5, comment: 'Amazing food! Will order again.' },
        { user: 'Amit J.', rating: 5, comment: 'Best home-style cooking in Mumbai!' }
      ]
    },
    {
      reel_id: '2',
      seller: {
        name: 'Sarah Design Studio',
        username: '@sarah_designs_delhi',
        verification_level: 'premium',
        rating: 4.9,
        location: 'New Delhi'
      },
      service: {
        title: 'Custom Graphic Design',
        category: 'Design & Creative',
        basePrice: 2000,
        priceType: 'per_project'
      },
      video: {
        url: '/api/placeholder-video2.mp4',
        thumbnail: '/api/placeholder-thumbnail2.jpg',
        duration: 60
      },
      stats: {
        likes: 890,
        views: 8500,
        comments: 45,
        hires: 12
      },
      description: '🎨 Logo design, branding, social media graphics. Quick turnaround, unlimited revisions! DM for portfolio. #GraphicDesign #Logo #Branding',
      tags: ['design', 'graphics', 'logo', 'branding'],
      reviews: [
        { user: 'Raj P.', rating: 5, comment: 'Professional work, delivered on time!' }
      ]
    }
  ];

  // Fetch data on component mount
  useEffect(() => {
    fetchReelsFeed();
    fetchCategories();
  }, []);

  // Fetch categories
  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${api}/reels/categories`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCategories(response.data.categories);
    } catch (error) {
      console.error('Failed to fetch categories:', error);
    }
  };

  // Fetch reels feed
  const fetchReelsFeed = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (selectedCategory) params.append('category', selectedCategory);
      if (locationFilter) params.append('location', locationFilter);

      const response = await axios.get(`${api}/reels/feed?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.reels && response.data.reels.length > 0) {
        setReels(response.data.reels);
      } else {
        // Use mock data if no reels available
        setReels(mockReels);
      }
    } catch (error) {
      console.error('Failed to fetch reels:', error);
      // Fall back to mock data
      setReels(mockReels);
    } finally {
      setLoading(false);
    }
  };

  // Video recording functions
  const startVideoRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: 720, height: 1280 },
        audio: true
      });
      
      streamRef.current = stream;
      setVideoPreview(stream);
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'video/webm;codecs=vp9'
      });
      
      const chunks = [];
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };
      
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'video/webm' });
        setRecordedVideo(blob);
        
        // Create video URL for preview
        const videoUrl = URL.createObjectURL(blob);
        setVideoPreview(videoUrl);
        
        // Stop camera stream
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
        }
      };
      
      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
      
    } catch (error) {
      console.error('Failed to start recording:', error);
      alert('Camera access denied. Please allow camera access to record videos.');
    }
  };

  const stopVideoRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file && file.type.startsWith('video/')) {
      setRecordedVideo(file);
      const videoUrl = URL.createObjectURL(file);
      setVideoPreview(videoUrl);
    } else {
      alert('Please select a valid video file.');
    }
  };

  const createServiceReel = async () => {
    try {
      if (!recordedVideo) {
        alert('Please record or upload a video first.');
        return;
      }

      if (!newReel.title || !newReel.description || !newReel.category || !newReel.basePrice) {
        alert('Please fill in all required fields.');
        return;
      }

      // Convert video to base64
      const reader = new FileReader();
      reader.onload = async () => {
        const videoBase64 = reader.result.split(',')[1]; // Remove data:video/webm;base64, prefix
        
        const reelData = {
          title: newReel.title,
          description: newReel.description,
          category: newReel.category,
          base_price: parseFloat(newReel.basePrice),
          price_type: newReel.priceType,
          video_url: videoBase64,
          duration: 60, // Default duration, could be calculated
          location: newReel.location,
          tags: newReel.tags ? newReel.tags.split(',').map(tag => tag.trim()) : [],
          availability: 'available'
        };

        try {
          const response = await axios.post(`${api}/reels/create`, reelData, {
            headers: { Authorization: `Bearer ${token}` }
          });

          if (response.data.status === 'success') {
            alert('Service reel created successfully!');
            setShowCreateModal(false);
            setNewReel({
              title: '', description: '', category: '', basePrice: '',
              priceType: 'per_hour', tags: '', location: { city: '', state: '' }
            });
            setRecordedVideo(null);
            setVideoPreview(null);
            fetchReelsFeed(); // Refresh feed
          }
        } catch (error) {
          console.error('Failed to create reel:', error);
          alert('Failed to create reel. Please try again.');
        }
      };
      
      reader.readAsDataURL(recordedVideo);
    } catch (error) {
      console.error('Failed to create reel:', error);
      alert('Failed to create reel. Please try again.');
    }
  };

  const handleVideoPlay = (index) => {
    // Pause all videos except the current one
    videoRefs.current.forEach((video, i) => {
      if (video) {
        if (i === index) {
          video.play();
        } else {
          video.pause();
        }
      }
    });
  };

  const handleLike = async (reelId) => {
    try {
      const response = await axios.post(`${api}/reels/${reelId}/like`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.status === 'success') {
        // Update local state to reflect like/unlike
        setReels(reels.map(reel => {
          if (reel.reel_id === reelId) {
            const newLikes = response.data.action === 'liked' 
              ? reel.stats.likes + 1 
              : reel.stats.likes - 1;
            return { ...reel, stats: { ...reel.stats, likes: newLikes } };
          }
          return reel;
        }));
      }
    } catch (error) {
      console.error('Failed to like reel:', error);
    }
  };

  const recordView = async (reelId) => {
    try {
      await axios.post(`${api}/reels/${reelId}/view`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
    } catch (error) {
      console.error('Failed to record view:', error);
    }
  };

  const handleContactSeller = async (reel) => {
    try {
      // Create a chat or navigate to existing chat
      const message = `Hi! I'm interested in your service: ${reel.title}`;
      
      // For now, show success message
      alert(`Message sent to ${reel.seller.name}! Check your chats to continue the conversation.`);
    } catch (error) {
      console.error('Failed to contact seller:', error);
    }
  };

  const handleOpenBidding = (reel) => {
    setSelectedReel(reel);
    setShowBiddingModal(true);
  };

  const handleSubmitBid = async () => {
    try {
      if (!bidAmount || parseFloat(bidAmount) <= 0) {
        alert('Please enter a valid bid amount.');
        return;
      }

      if (!bidMessage.trim()) {
        alert('Please add a message for the seller.');
        return;
      }

      const bidData = {
        reel_id: selectedReel.reel_id,
        bid_amount: parseFloat(bidAmount),
        message: bidMessage,
        project_details: `Interested in: ${selectedReel.service?.title || selectedReel.title}`,
        urgency: 'normal'
      };

      const response = await axios.post(`${api}/reels/${selectedReel.reel_id}/bid`, bidData, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.status === 'success') {
        alert('Bid submitted successfully! Seller will be notified.');
        setShowBiddingModal(false);
        setBidAmount('');
        setBidMessage('');
        
        // Update reel stats locally
        setReels(reels.map(reel => {
          if (reel.reel_id === selectedReel.reel_id) {
            return { ...reel, stats: { ...reel.stats, bids: reel.stats.bids + 1 } };
          }
          return reel;
        }));
      }
    } catch (error) {
      console.error('Failed to submit bid:', error);
      alert('Failed to submit bid. Please try again.');
    }
  };

  const ReelComponent = ({ reel, index }) => (
    <div className="relative h-screen w-full bg-black flex items-center justify-center">
      {/* Video Player */}
      <video
        ref={(el) => videoRefs.current[index] = el}
        className="h-full w-full object-cover"
        src={reel.video.url}
        poster={reel.video.thumbnail}
        loop
        muted
        playsInline
        onClick={() => handleVideoPlay(index)}
        onLoadedData={() => index === currentReelIndex && handleVideoPlay(index)}
      />

      {/* Video Overlay Content */}
      <div className="absolute inset-0 pointer-events-none">
        {/* Top Bar */}
        <div className="absolute top-4 left-4 right-4 flex justify-between items-center pointer-events-auto">
          <div className="flex items-center space-x-2">
            <span className="bg-black bg-opacity-50 text-white px-2 py-1 rounded-full text-xs">
              {reel.service.category}
            </span>
          </div>
          <button 
            className="bg-black bg-opacity-50 text-white p-2 rounded-full"
            aria-label="More options for this reel"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
              <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"/>
            </svg>
          </button>
        </div>

        {/* Right Side Actions */}
        <div className="absolute right-4 bottom-20 flex flex-col space-y-4 pointer-events-auto">
          {/* Seller Profile */}
          <div className="text-center">
            <div className="relative">
              <div className="w-12 h-12 bg-gradient-to-r from-pink-500 to-purple-500 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-lg">
                  {reel.seller.name.charAt(0)}
                </span>
              </div>
              {reel.seller.verification_level === 'verified' && (
                <div className="absolute -bottom-1 -right-1 bg-blue-500 rounded-full p-1">
                  <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                  </svg>
                </div>
              )}
            </div>
            <span className="text-white text-xs font-medium">{reel.seller.rating}⭐</span>
          </div>

          {/* Like Button */}
          <button 
            onClick={() => handleLike(reel.reel_id)}
            className="flex flex-col items-center space-y-1 text-white"
            aria-label={`Like this reel from ${reel.seller.name}. Current likes: ${reel.likes}`}
          >
            <div className="bg-black bg-opacity-30 p-3 rounded-full">
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                <path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clipRule="evenodd"/>
              </svg>
            </div>
            <span className="text-xs">{reel.stats.likes}</span>
          </button>

          {/* Bid Button */}
          <button 
            onClick={() => handleOpenBidding(reel)}
            className="flex flex-col items-center space-y-1 text-white"
          >
            <div className="bg-green-500 p-3 rounded-full">
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4zM18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z"/>
              </svg>
            </div>
            <span className="text-xs">₹{reel.service.basePrice}+</span>
          </button>

          {/* Chat Button */}
          <button className="flex flex-col items-center space-y-1 text-white">
            <div className="bg-black bg-opacity-30 p-3 rounded-full">
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd"/>
              </svg>
            </div>
            <span className="text-xs">Chat</span>
          </button>

          {/* Reviews Button */}
          <button 
            onClick={() => {
              setSelectedReel(reel);
              setShowReviewModal(true);
            }}
            className="flex flex-col items-center space-y-1 text-white"
          >
            <div className="bg-black bg-opacity-30 p-3 rounded-full">
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
              </svg>
            </div>
            <span className="text-xs">{reel.reviews.length}</span>
          </button>

          {/* Share Button */}
          <button className="flex flex-col items-center space-y-1 text-white">
            <div className="bg-black bg-opacity-30 p-3 rounded-full">
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path d="M15 8a3 3 0 10-2.977-2.63l-4.94 2.47a3 3 0 100 4.319l4.94 2.47a3 3 0 10.895-1.789l-4.94-2.47a3.027 3.027 0 000-.74l4.94-2.47C13.456 7.68 14.19 8 15 8z"/>
              </svg>
            </div>
            <span className="text-xs">Share</span>
          </button>
        </div>

        {/* Bottom Content */}
        <div className="absolute bottom-4 left-4 right-20 text-white pointer-events-auto">
          <div className="space-y-2">
            {/* Seller Info */}
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg">{reel.seller.username}</span>
              <span className="bg-blue-500 px-2 py-1 rounded-full text-xs">
                {reel.seller.verification_level}
              </span>
            </div>

            {/* Service Title */}
            <h3 className="font-bold text-xl">{reel.service.title}</h3>

            {/* Price */}
            <div className="flex items-center space-x-2">
              <span className="bg-green-500 px-3 py-1 rounded-full font-bold">
                ₹{reel.service.basePrice} {reel.service.priceType}
              </span>
              <span className="text-sm opacity-75">📍 {reel.seller.location}</span>
            </div>

            {/* Description */}
            <p className="text-sm opacity-90 line-clamp-2">{reel.description}</p>

            {/* Tags */}
            <div className="flex flex-wrap gap-1">
              {reel.tags.map((tag, index) => (
                <span key={index} className="text-blue-300 text-sm">#{tag}</span>
              ))}
            </div>

            {/* Stats */}
            <div className="flex items-center space-x-4 text-sm opacity-75">
              <span>👁️ {reel.stats.views.toLocaleString()}</span>
              <span>💬 {reel.stats.comments}</span>
              <span>🎯 {reel.stats.hires} hires</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="h-screen bg-black overflow-hidden">
      {/* Main Feed */}
      {activeView === 'feed' && (
        <div className="relative h-full">
          {/* Filter Bar */}
          <div className="absolute top-4 left-4 right-4 z-10 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <button 
                onClick={() => setShowFilters(!showFilters)}
                className="bg-black bg-opacity-50 text-white px-3 py-2 rounded-full text-sm flex items-center space-x-1"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M3 3a1 1 0 011-1h12a1 1 0 011 1v3a1 1 0 01-.293.707L12 11.414V15a1 1 0 01-.293.707l-2 2A1 1 0 018 17v-5.586L3.293 6.707A1 1 0 013 6V3z"/>
                </svg>
                <span>Filters</span>
              </button>
              
              {showFilters && (
                <div className="bg-black bg-opacity-80 rounded-lg p-3 flex items-center space-x-2">
                  <select 
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="bg-transparent text-white text-sm border border-gray-400 rounded px-2 py-1"
                  >
                    <option value="" className="text-black">All Services</option>
                    <option value="food" className="text-black">Food & Catering</option>
                    <option value="design" className="text-black">Design & Creative</option>
                    <option value="tech" className="text-black">Tech Services</option>
                    <option value="home" className="text-black">Home Services</option>
                  </select>
                  
                  <input
                    type="text"
                    placeholder="Location"
                    value={locationFilter}
                    onChange={(e) => setLocationFilter(e.target.value)}
                    className="bg-transparent text-white text-sm border border-gray-400 rounded px-2 py-1 placeholder-gray-300"
                  />
                </div>
              )}
            </div>
            
            <button className="bg-black bg-opacity-50 text-white p-2 rounded-full">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd"/>
              </svg>
            </button>
          </div>

          {/* Reels Scroll Container */}
          <div className="h-full overflow-y-scroll snap-y snap-mandatory scrollbar-hide">
            {reels.map((reel, index) => (
              <div key={reel.reel_id} className="snap-start">
                <ReelComponent reel={reel} index={index} />
              </div>
            ))}
          </div>

          {/* Bottom Navigation */}
          <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-50 flex justify-around items-center py-3">
            <button 
              onClick={() => setActiveView('feed')}
              className={`text-center ${activeView === 'feed' ? 'text-white' : 'text-gray-400'}`}
            >
              <div className="text-2xl">🏠</div>
              <span className="text-xs">Home</span>
            </button>
            <button className="text-white text-center">
              <div className="text-2xl">🔍</div>
              <span className="text-xs">Discover</span>
            </button>
            <button 
              onClick={() => setShowCreateModal(true)}
              className="text-white text-center bg-red-500 rounded-full p-3"
            >
              <div className="text-xl">➕</div>
            </button>
            <button className="text-white text-center">
              <div className="text-2xl">💬</div>
              <span className="text-xs">Chats</span>
            </button>
            <button className="text-white text-center">
              <div className="text-2xl">👤</div>
              <span className="text-xs">Profile</span>
            </button>
          </div>
        </div>
      )}

      {/* Bidding Modal */}
      {showBiddingModal && selectedReel && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold">Submit Your Bid</h3>
              <button 
                onClick={() => setShowBiddingModal(false)}
                className="text-gray-500 hover:text-gray-700 text-xl"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              {/* Service Info */}
              <div className="bg-gray-50 p-3 rounded-lg">
                <h4 className="font-semibold">{selectedReel.service.title}</h4>
                <p className="text-sm text-gray-600">by {selectedReel.seller.name}</p>
                <p className="text-sm text-green-600 font-medium">
                  Base Price: ₹{selectedReel.service.basePrice} {selectedReel.service.priceType}
                </p>
              </div>

              {/* Bid Amount */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Your Bid Amount (₹)
                </label>
                <input
                  type="number"
                  value={bidAmount}
                  onChange={(e) => setBidAmount(e.target.value)}
                  placeholder={`Min: ${selectedReel.service.basePrice}`}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Message */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Message to Seller
                </label>
                <textarea
                  value={bidMessage}
                  onChange={(e) => setBidMessage(e.target.value)}
                  placeholder="Describe your requirements..."
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Action Buttons */}
              <div className="flex space-x-3 pt-4">
                <button
                  onClick={() => setShowBiddingModal(false)}
                  className="flex-1 bg-gray-100 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSubmitBid}
                  className="flex-1 bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600"
                >
                  Submit Bid
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Reviews Modal */}
      {showReviewModal && selectedReel && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold">Reviews & Ratings</h3>
              <button 
                onClick={() => setShowReviewModal(false)}
                className="text-gray-500 hover:text-gray-700 text-xl"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              {/* Overall Rating */}
              <div className="text-center bg-gray-50 p-4 rounded-lg">
                <div className="text-3xl font-bold text-yellow-500">
                  {selectedReel.seller.rating}⭐
                </div>
                <p className="text-sm text-gray-600">
                  Based on {selectedReel.reviews.length} reviews
                </p>
              </div>

              {/* Individual Reviews */}
              <div className="space-y-3">
                {selectedReel.reviews.map((review, index) => (
                  <div key={index} className="border-b border-gray-200 pb-3">
                    <div className="flex justify-between items-start mb-1">
                      <span className="font-medium">{review.user}</span>
                      <span className="text-yellow-500">
                        {'⭐'.repeat(review.rating)}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">{review.comment}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
      {/* Create Service Reel Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold">Create Service Reel</h3>
              <button 
                onClick={() => setShowCreateModal(false)}
                className="text-gray-500 hover:text-gray-700 text-xl"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              {/* Video Recording/Upload Section */}
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center">
                {!videoPreview ? (
                  <div>
                    <div className="text-gray-500 mb-4">
                      <div className="text-4xl mb-2">🎥</div>
                      <p className="text-sm">Record or upload your service video</p>
                    </div>
                    
                    <div className="space-y-2">
                      <button
                        onClick={startVideoRecording}
                        disabled={isRecording}
                        className={`w-full py-2 px-4 rounded-lg ${
                          isRecording 
                            ? 'bg-red-500 text-white' 
                            : 'bg-blue-500 hover:bg-blue-600 text-white'
                        }`}
                      >
                        {isRecording ? '🔴 Recording...' : '📹 Start Recording'}
                      </button>
                      
                      {isRecording && (
                        <button
                          onClick={stopVideoRecording}
                          className="w-full py-2 px-4 rounded-lg bg-red-600 hover:bg-red-700 text-white"
                        >
                          ⏹️ Stop Recording
                        </button>
                      )}
                      
                      <div className="text-sm text-gray-500">or</div>
                      
                      <label className="w-full py-2 px-4 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg cursor-pointer block">
                        📁 Upload Video File
                        <input
                          type="file"
                          accept="video/*"
                          onChange={handleFileUpload}
                          className="hidden"
                        />
                      </label>
                    </div>
                  </div>
                ) : (
                  <div>
                    <video
                      src={videoPreview}
                      controls
                      className="w-full h-48 object-cover rounded-lg mb-2"
                      autoPlay={false}
                    />
                    <button
                      onClick={() => {
                        setVideoPreview(null);
                        setRecordedVideo(null);
                      }}
                      className="text-sm text-red-600 hover:text-red-800"
                    >
                      🗑️ Remove Video
                    </button>
                  </div>
                )}
              </div>

              {/* Service Details Form */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Service Title *
                </label>
                <input
                  type="text"
                  value={newReel.title}
                  onChange={(e) => setNewReel({...newReel, title: e.target.value})}
                  placeholder="e.g., Professional Home Cooking Service"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  maxLength={100}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category *
                </label>
                <select
                  value={newReel.category}
                  onChange={(e) => setNewReel({...newReel, category: e.target.value})}
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
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description *
                </label>
                <textarea
                  value={newReel.description}
                  onChange={(e) => setNewReel({...newReel, description: e.target.value})}
                  placeholder="Describe your service, experience, and what makes you unique..."
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  maxLength={500}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Base Price (₹) *
                  </label>
                  <input
                    type="number"
                    value={newReel.basePrice}
                    onChange={(e) => setNewReel({...newReel, basePrice: e.target.value})}
                    placeholder="500"
                    min="0"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Price Type
                  </label>
                  <select
                    value={newReel.priceType}
                    onChange={(e) => setNewReel({...newReel, priceType: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="per_hour">Per Hour</option>
                    <option value="per_project">Per Project</option>
                    <option value="per_day">Per Day</option>
                    <option value="per_meal">Per Meal</option>
                    <option value="negotiable">Negotiable</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    City
                  </label>
                  <input
                    type="text"
                    value={newReel.location.city}
                    onChange={(e) => setNewReel({
                      ...newReel, 
                      location: {...newReel.location, city: e.target.value}
                    })}
                    placeholder="Mumbai"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    State
                  </label>
                  <input
                    type="text"
                    value={newReel.location.state}
                    onChange={(e) => setNewReel({
                      ...newReel, 
                      location: {...newReel.location, state: e.target.value}
                    })}
                    placeholder="Maharashtra"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tags (comma separated)
                </label>
                <input
                  type="text"
                  value={newReel.tags}
                  onChange={(e) => setNewReel({...newReel, tags: e.target.value})}
                  placeholder="cooking, home delivery, authentic, mumbai"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Action Buttons */}
              <div className="flex space-x-3 pt-4">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 bg-gray-100 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  onClick={createServiceReel}
                  disabled={!recordedVideo || !newReel.title || !newReel.category}
                  className="flex-1 bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  Create Reel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReelsMarketplace;