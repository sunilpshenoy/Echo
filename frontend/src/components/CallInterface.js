import React, { useEffect, useRef, useState } from 'react';

const CallInterface = ({ 
  call,
  callType,
  localStream,
  remoteStream,
  onEndCall,
  onToggleMute,
  onToggleVideo,
  onToggleScreenShare,
  isMuted,
  isVideoOff,
  isScreenSharing,
  api,
  token
}) => {
  const localVideoRef = useRef(null);
  const remoteVideoRef = useRef(null);
  const [callDuration, setCallDuration] = useState(0);
  const [callQuality, setCallQuality] = useState({ signal: 'excellent', network: 'stable' });
  const [callStats, setCallStats] = useState({ 
    bytesReceived: 0, 
    bytesSent: 0, 
    packetsLost: 0,
    roundTripTime: 0
  });

  // Set up video streams when they change
  useEffect(() => {
    if (localStream && localVideoRef.current) {
      localVideoRef.current.srcObject = localStream;
    }
    
    if (remoteStream && remoteVideoRef.current) {
      remoteVideoRef.current.srcObject = remoteStream;
    }
  }, [localStream, remoteStream]);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-90 z-50 flex flex-col">
      {/* Call Header */}
      <div className="bg-gray-900 p-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
            <span className="text-white font-medium">
              {call?.other_user?.display_name?.[0]?.toUpperCase() || 'C'}
            </span>
          </div>
          <div>
            <h3 className="font-semibold text-white">
              {call?.other_user?.display_name || 'Contact'}
            </h3>
            <p className="text-sm text-gray-300">
              {callType === 'video' ? 'Video Call' : 'Voice Call'} • {call?.status || 'connecting...'}
            </p>
          </div>
        </div>
        <button
          onClick={onEndCall}
          className="bg-red-500 text-white p-2 rounded-full hover:bg-red-600"
          title="End Call"
        >
          📞❌
        </button>
      </div>
      
      {/* Video Area */}
      <div className="flex-1 flex items-center justify-center relative">
        {/* Remote Video (Full Screen) */}
        {callType === 'video' && remoteStream && (
          <video
            ref={remoteVideoRef}
            autoPlay
            playsInline
            className="absolute inset-0 w-full h-full object-cover"
          />
        )}
        
        {/* Local Video (Picture-in-Picture) */}
        {callType === 'video' && localStream && (
          <div className="absolute bottom-4 right-4 w-1/4 max-w-xs rounded-lg overflow-hidden border-2 border-white shadow-lg">
            <video
              ref={localVideoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover"
            />
          </div>
        )}
        
        {/* Voice Call UI */}
        {callType === 'voice' && (
          <div className="text-center">
            <div className="w-32 h-32 bg-blue-500 rounded-full mx-auto mb-4 flex items-center justify-center">
              <span className="text-white text-4xl">
                {call?.other_user?.display_name?.[0]?.toUpperCase() || 'C'}
              </span>
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">
              {call?.other_user?.display_name || 'Contact'}
            </h2>
            <p className="text-gray-300">
              {call?.duration ? `${Math.floor(call.duration / 60)}:${(call.duration % 60).toString().padStart(2, '0')}` : 'Connecting...'}
            </p>
            
            {/* Audio Visualizer */}
            <div className="flex items-center justify-center space-x-1 mt-4">
              <div className="w-1 h-4 bg-blue-500 animate-pulse"></div>
              <div className="w-1 h-6 bg-blue-500 animate-pulse" style={{animationDelay: '0.1s'}}></div>
              <div className="w-1 h-8 bg-blue-500 animate-pulse" style={{animationDelay: '0.2s'}}></div>
              <div className="w-1 h-10 bg-blue-500 animate-pulse" style={{animationDelay: '0.3s'}}></div>
              <div className="w-1 h-8 bg-blue-500 animate-pulse" style={{animationDelay: '0.4s'}}></div>
              <div className="w-1 h-6 bg-blue-500 animate-pulse" style={{animationDelay: '0.5s'}}></div>
              <div className="w-1 h-4 bg-blue-500 animate-pulse" style={{animationDelay: '0.6s'}}></div>
            </div>
          </div>
        )}
      </div>
      
      {/* Call Controls */}
      <div className="bg-gray-900 p-4 flex items-center justify-center space-x-4">
        <button
          onClick={onToggleMute}
          className={`p-3 rounded-full ${
            isMuted ? 'bg-red-500 text-white' : 'bg-gray-700 text-white'
          }`}
          title={isMuted ? 'Unmute' : 'Mute'}
        >
          {isMuted ? '🔇' : '🎤'}
        </button>
        
        {callType === 'video' && (
          <button
            onClick={onToggleVideo}
            className={`p-3 rounded-full ${
              isVideoOff ? 'bg-red-500 text-white' : 'bg-gray-700 text-white'
            }`}
            title={isVideoOff ? 'Turn Video On' : 'Turn Video Off'}
          >
            {isVideoOff ? '📵' : '📹'}
          </button>
        )}
        
        {callType === 'video' && (
          <button
            onClick={onToggleScreenShare}
            className={`p-3 rounded-full ${
              isScreenSharing ? 'bg-green-500 text-white' : 'bg-gray-700 text-white'
            }`}
            title={isScreenSharing ? 'Stop Sharing' : 'Share Screen'}
          >
            {isScreenSharing ? '📺✓' : '📺'}
          </button>
        )}
        
        <button
          onClick={onEndCall}
          className="p-3 bg-red-500 text-white rounded-full"
          title="End Call"
        >
          📞❌
        </button>
      </div>
    </div>
  );
};

export default CallInterface;
