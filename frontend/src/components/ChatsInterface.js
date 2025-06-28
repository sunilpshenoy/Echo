import React from 'react';

const ChatsInterface = () => {
  return (
    <div>
      <div>
        {/* Your existing content */}
        {someCondition && (
          <div>
          </div>
        )}
      </div>

      {/* My PIN & QR Code Modal */}
      {showMyPin && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold text-gray-900">My Connection PIN</h2>
              <button
                onClick={() => setShowMyPin(false)}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ✕
              </button>
            </div>
            
            <div className="text-center">
              <div className="bg-gray-100 p-6 rounded-2xl mb-6">
                <div className="text-3xl font-mono font-bold text-blue-600 tracking-widest mb-4">
                  {user?.connection_pin || 'PIN-' + (user?.user_id?.slice(-6) || '123456')}
                </div>
                <div className="bg-white p-4 rounded-lg mb-4">
                  {/* QR Code would go here */}
                  <div className="w-32 h-32 mx-auto bg-gray-200 rounded-lg flex items-center justify-center">
                    <span className="text-gray-500">QR Code</span>
                  </div>
                </div>
                <p className="text-sm text-gray-600">
                  Share this PIN or QR code for others to connect with you
                </p>
              </div>
              
              <div className="flex space-x-3">
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(user?.connection_pin || 'PIN-' + (user?.user_id?.slice(-6) || '123456'));
                    alert('PIN copied to clipboard! 📋');
                  }}
                  className="flex-1 bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600"
                >
                  📋 Copy PIN
                </button>
                <button
                  onClick={() => {
                    if (navigator.share) {
                      navigator.share({
                        title: 'Connect with me!',
                        text: `My connection PIN: ${user?.connection_pin || 'PIN-' + (user?.user_id?.slice(-6) || '123456')}`,
                      });
                    }
                  }}
                  className="flex-1 bg-green-500 text-white py-2 px-4 rounded-lg hover:bg-green-600"
                >
                  📤 Share
                </button>
              </div>
              
              <p className="text-xs text-gray-500 mt-4">
                💡 Your PIN is unique and private. Only share with people you want to connect with.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Add Contact Modal */}
      {showAddContact && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold text-gray-900">Add Contact</h2>
              <button
                onClick={() => setShowAddContact(false)}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Enter Contact's PIN
                </label>
                <input
                  type="text"
                  value={contactPin}
                  onChange={(e) => setContactPin(e.target.value)}
                  placeholder="PIN-123456"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-center tracking-widest"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Enter the PIN they shared with you
                </p>
              </div>
              
              <div className="flex space-x-3">
                <button
                  onClick={() => setShowAddContact(false)}
                  className="flex-1 bg-gray-200 text-gray-800 py-2 px-4 rounded-lg hover:bg-gray-300"
                >
                  Cancel
                </button>
                <button
                  onClick={sendConnectionRequest}
                  disabled={!contactPin.trim()}
                  className="flex-1 bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  Send Request
                </button>
              </div>
              
              <div className="text-center pt-4 border-t border-gray-200">
                <p className="text-sm text-gray-600 mb-2">Or scan QR code</p>
                <button className="bg-green-500 text-white py-2 px-4 rounded-lg hover:bg-green-600">
                  📷 Scan QR Code
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatsInterface;
