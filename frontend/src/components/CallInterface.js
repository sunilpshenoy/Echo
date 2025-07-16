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

  // Call duration timer
  useEffect(() => {
    if (call?.status === 'active') {
      const interval = setInterval(() => {
        setCallDuration(prev => prev + 1);
      }, 1000);
      
      return () => clearInterval(interval);
    }
  }, [call?.status]);

  // Call quality monitoring
  useEffect(() => {
    if (call?.status === 'active') {
      const interval = setInterval(() => {
        // Simulate call quality monitoring
        const signal = Math.random() > 0.7 ? 'excellent' : Math.random() > 0.4 ? 'good' : 'poor';
        const network = Math.random() > 0.8 ? 'stable' : Math.random() > 0.5 ? 'unstable' : 'poor';
        setCallQuality({ signal, network });
        
        // Simulate call stats
        setCallStats(prev => ({
          ...prev,
          bytesReceived: prev.bytesReceived + Math.floor(Math.random() * 1000),
          bytesSent: prev.bytesSent + Math.floor(Math.random() * 1000),
          packetsLost: prev.packetsLost + Math.floor(Math.random() * 3),
          roundTripTime: Math.floor(Math.random() * 100)
        }));
      }, 2000);
      
      return () => clearInterval(interval);
    }
  }, [call?.status]);

  // Format call duration
  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Get quality indicator color
  const getQualityColor = (quality) => {
    switch (quality) {
      case 'excellent': return 'text-green-400';
      case 'good': return 'text-yellow-400';
      case 'poor': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

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
            <div className="flex items-center space-x-2 text-sm text-gray-300">
              <span>
                {callType === 'video' ? 'Video Call' : 'Voice Call'}
              </span>
              <span>•</span>
              <span>{formatDuration(callDuration)}</span>
              {/* Call Quality Indicator */}
              <div className="flex items-center space-x-1">
                <span className={`w-2 h-2 rounded-full ${getQualityColor(callQuality.signal)}`} style={{backgroundColor: 'currentColor'}}></span>
                <span className={`text-xs ${getQualityColor(callQuality.signal)}`}>
                  {callQuality.signal}
                </span>
              </div>
            </div>
          </div>
        </div>
        <button
          onClick={onEndCall}
          className="bg-red-500 text-white p-2 rounded-full hover:bg-red-600"
          title="End Call"
          aria-label="End call"
        >
          <span aria-hidden="true">📞❌</span>
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
            <p className="text-gray-300 mb-4">
              {formatDuration(callDuration)}
            </p>
            
            {/* Enhanced Audio Visualizer */}
            <div className="flex items-center justify-center space-x-1 mb-4">
              {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((i) => (
                <div
                  key={i}
                  className={`w-1 bg-blue-500 rounded-full animate-pulse ${
                    i <= 3 ? 'h-4' : i <= 6 ? 'h-6' : i <= 8 ? 'h-8' : 'h-10'
                  }`}
                  style={{
                    animationDelay: `${i * 0.1}s`,
                    animationDuration: '1s'
                  }}
                />
              ))}
            </div>
            
            {/* Call Quality Stats */}
            <div className="text-xs text-gray-400 space-y-1">
              <div className="flex justify-center space-x-4">
                <span>Network: <span className={getQualityColor(callQuality.network)}>{callQuality.network}</span></span>
                <span>RTT: {callStats.roundTripTime}ms</span>
              </div>
              <div className="flex justify-center space-x-4">
                <span>Packets lost: {callStats.packetsLost}</span>
                <span>Data: {Math.round(callStats.bytesReceived / 1024)}KB</span>
              </div>
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
