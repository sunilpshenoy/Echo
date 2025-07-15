import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

const MediaGallery = ({ user, token, api, contactId, onClose }) => {
  const { t } = useTranslation();
  const [mediaItems, setMediaItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedMedia, setSelectedMedia] = useState(null);
  const [filter, setFilter] = useState('all'); // all, photos, videos, documents
  const [sortBy, setSortBy] = useState('date'); // date, name, size

  useEffect(() => {
    fetchMediaItems();
  }, [contactId]);

  const fetchMediaItems = async () => {
    try {
      const response = await axios.get(`${api}/chats/${contactId}/media`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMediaItems(response.data.media || []);
    } catch (error) {
      console.error('Failed to fetch media items:', error);
    } finally {
      setLoading(false);
    }
  };

  const getFileIcon = (fileType) => {
    if (fileType.startsWith('image/')) return '🖼️';
    if (fileType.startsWith('video/')) return '🎥';
    if (fileType.startsWith('audio/')) return '🎵';
    if (fileType.includes('pdf')) return '📄';
    if (fileType.includes('doc')) return '📝';
    if (fileType.includes('xls') || fileType.includes('sheet')) return '📊';
    if (fileType.includes('zip') || fileType.includes('rar')) return '📦';
    return '📁';
  };

  const getFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const filterMediaItems = (items) => {
    let filtered = items;
    
    // Apply filter
    if (filter === 'photos') {
      filtered = filtered.filter(item => item.file_type?.startsWith('image/'));
    } else if (filter === 'videos') {
      filtered = filtered.filter(item => item.file_type?.startsWith('video/'));
    } else if (filter === 'documents') {
      filtered = filtered.filter(item => 
        !item.file_type?.startsWith('image/') && 
        !item.file_type?.startsWith('video/') && 
        !item.file_type?.startsWith('audio/')
      );
    }
    
    // Apply sorting
    if (sortBy === 'date') {
      filtered.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    } else if (sortBy === 'name') {
      filtered.sort((a, b) => a.file_name.localeCompare(b.file_name));
    } else if (sortBy === 'size') {
      filtered.sort((a, b) => (b.file_size || 0) - (a.file_size || 0));
    }
    
    return filtered;
  };

  const downloadFile = async (mediaItem) => {
    try {
      const response = await axios.get(`${api}/files/${mediaItem.file_id}/download`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.download = mediaItem.file_name;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download file:', error);
      alert(t('media.downloadError'));
    }
  };

  const openMediaPreview = (mediaItem) => {
    setSelectedMedia(mediaItem);
  };

  const closeMediaPreview = () => {
    setSelectedMedia(null);
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-white z-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  const filteredItems = filterMediaItems(mediaItems);

  return (
    <div className="fixed inset-0 bg-white z-50 flex flex-col">
      {/* Header */}
      <div className="bg-gray-900 text-white p-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold">{t('media.gallery')}</h2>
        <button
          onClick={onClose}
          className="text-white hover:text-gray-300"
        >
          ✕
        </button>
      </div>
      
      {/* Filters and Sort */}
      <div className="bg-gray-100 p-4 flex items-center justify-between">
        <div className="flex space-x-2">
          {['all', 'photos', 'videos', 'documents'].map((filterType) => (
            <button
              key={filterType}
              onClick={() => setFilter(filterType)}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                filter === filterType
                  ? 'bg-blue-500 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-200'
              }`}
            >
              {t(`media.${filterType}`)}
            </button>
          ))}
        </div>
        
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="px-3 py-1 bg-white border border-gray-300 rounded-lg text-sm"
        >
          <option value="date">{t('media.sortByDate')}</option>
          <option value="name">{t('media.sortByName')}</option>
          <option value="size">{t('media.sortBySize')}</option>
        </select>
      </div>
      
      {/* Media Grid */}
      <div className="flex-1 overflow-y-auto p-4">
        {filteredItems.length === 0 ? (
          <div className="text-center py-16 text-gray-500">
            <div className="text-6xl mb-4">🗂️</div>
            <p>{t('media.noItems')}</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {filteredItems.map((item) => (
              <div
                key={item.file_id}
                className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => openMediaPreview(item)}
              >
                <div className="aspect-square bg-gray-100 flex items-center justify-center">
                  {item.file_type?.startsWith('image/') && item.file_data ? (
                    <img
                      src={`data:${item.file_type};base64,${item.file_data}`}
                      alt={item.file_name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="text-4xl">
                      {getFileIcon(item.file_type)}
                    </div>
                  )}
                </div>
                
                <div className="p-3">
                  <h3 className="font-medium text-sm text-gray-800 truncate">
                    {item.file_name}
                  </h3>
                  <p className="text-xs text-gray-500 mt-1">
                    {getFileSize(item.file_size)} • {new Date(item.timestamp).toLocaleDateString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Media Preview Modal */}
      {selectedMedia && (
        <div className="fixed inset-0 bg-black bg-opacity-90 z-60 flex items-center justify-center">
          <div className="max-w-4xl max-h-4xl w-full h-full flex flex-col">
            {/* Preview Header */}
            <div className="bg-gray-900 text-white p-4 flex items-center justify-between">
              <div>
                <h3 className="font-semibold">{selectedMedia.file_name}</h3>
                <p className="text-sm text-gray-300">
                  {getFileSize(selectedMedia.file_size)} • {new Date(selectedMedia.timestamp).toLocaleDateString()}
                </p>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => downloadFile(selectedMedia)}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                >
                  {t('media.download')}
                </button>
                <button
                  onClick={closeMediaPreview}
                  className="text-white hover:text-gray-300"
                >
                  ✕
                </button>
              </div>
            </div>
            
            {/* Preview Content */}
            <div className="flex-1 flex items-center justify-center p-4">
              {selectedMedia.file_type?.startsWith('image/') && selectedMedia.file_data ? (
                <img
                  src={`data:${selectedMedia.file_type};base64,${selectedMedia.file_data}`}
                  alt={selectedMedia.file_name}
                  className="max-w-full max-h-full object-contain"
                />
              ) : selectedMedia.file_type?.startsWith('video/') && selectedMedia.file_data ? (
                <video
                  src={`data:${selectedMedia.file_type};base64,${selectedMedia.file_data}`}
                  controls
                  className="max-w-full max-h-full"
                />
              ) : (
                <div className="text-center text-white">
                  <div className="text-8xl mb-4">
                    {getFileIcon(selectedMedia.file_type)}
                  </div>
                  <p className="text-xl">{selectedMedia.file_name}</p>
                  <p className="text-gray-300 mt-2">
                    {t('media.previewNotAvailable')}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MediaGallery;