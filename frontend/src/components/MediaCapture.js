import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

const MediaCapture = ({ onMediaCapture, onClose }) => {
  const { t } = useTranslation();
  const [mode, setMode] = useState('photo'); // 'photo' or 'video'
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [capturedMedia, setCapturedMedia] = useState(null);
  const [stream, setStream] = useState(null);
  const [facingMode, setFacingMode] = useState('user'); // 'user' or 'environment'
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const mediaRecorder = useRef(null);
  const recordedChunks = useRef([]);

  useEffect(() => {
    startCamera();
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, [facingMode]);

  useEffect(() => {
    if (isRecording) {
      const interval = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [isRecording]);

  const startCamera = async () => {
    try {
      const constraints = {
        video: {
          facingMode: facingMode,
          width: { ideal: 1280 },
          height: { ideal: 720 }
        },
        audio: mode === 'video'
      };

      const mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (error) {
      console.error('Error accessing camera:', error);
      alert(t('media.cameraError'));
    }
  };

  const takePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const canvas = canvasRef.current;
      const video = videoRef.current;
      const context = canvas.getContext('2d');

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      context.drawImage(video, 0, 0, canvas.width, canvas.height);
      
      canvas.toBlob((blob) => {
        const url = URL.createObjectURL(blob);
        setCapturedMedia({
          type: 'photo',
          blob: blob,
          url: url,
          timestamp: Date.now()
        });
      }, 'image/jpeg', 0.8);
    }
  };

  const startVideoRecording = () => {
    if (stream) {
      recordedChunks.current = [];
      mediaRecorder.current = new MediaRecorder(stream);
      
      mediaRecorder.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          recordedChunks.current.push(event.data);
        }
      };
      
      mediaRecorder.current.onstop = () => {
        const blob = new Blob(recordedChunks.current, { type: 'video/webm' });
        const url = URL.createObjectURL(blob);
        setCapturedMedia({
          type: 'video',
          blob: blob,
          url: url,
          duration: recordingTime,
          timestamp: Date.now()
        });
      };
      
      mediaRecorder.current.start();
      setIsRecording(true);
      setRecordingTime(0);
    }
  };

  const stopVideoRecording = () => {
    if (mediaRecorder.current && mediaRecorder.current.state === 'recording') {
      mediaRecorder.current.stop();
      setIsRecording(false);
    }
  };

  const switchCamera = () => {
    setFacingMode(prev => prev === 'user' ? 'environment' : 'user');
  };

  const switchMode = (newMode) => {
    setMode(newMode);
    setIsRecording(false);
    setRecordingTime(0);
    setCapturedMedia(null);
  };

  const sendMedia = () => {
    if (capturedMedia) {
      onMediaCapture(capturedMedia);
      setCapturedMedia(null);
      onClose();
    }
  };

  const retakeMedia = () => {
    if (capturedMedia) {
      URL.revokeObjectURL(capturedMedia.url);
      setCapturedMedia(null);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (capturedMedia) {
    return (
      <div className="fixed inset-0 bg-black z-50 flex flex-col">
        <div className="flex items-center justify-between p-4 bg-gray-900">
          <h2 className="text-white font-semibold">
            {capturedMedia.type === 'photo' ? t('media.photoPreview') : t('media.videoPreview')}
          </h2>
          <button
            onClick={onClose}
            className="text-white hover:text-gray-300"
          >
            ✕
          </button>
        </div>
        
        <div className="flex-1 flex items-center justify-center bg-black">
          {capturedMedia.type === 'photo' ? (
            <img
              src={capturedMedia.url}
              alt="Captured"
              className="max-w-full max-h-full object-contain"
            />
          ) : (
            <video
              src={capturedMedia.url}
              controls
              className="max-w-full max-h-full"
            />
          )}
        </div>
        
        <div className="p-4 bg-gray-900 flex justify-center space-x-4">
          <button
            onClick={retakeMedia}
            className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
          >
            {t('media.retake')}
          </button>
          <button
            onClick={sendMedia}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            {t('media.send')}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black z-50 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-gray-900">
        <div className="flex space-x-4">
          <button
            onClick={() => switchMode('photo')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              mode === 'photo' 
                ? 'bg-blue-500 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            {t('media.photo')}
          </button>
          <button
            onClick={() => switchMode('video')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              mode === 'video' 
                ? 'bg-blue-500 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            {t('media.video')}
          </button>
        </div>
        
        <div className="flex items-center space-x-4">
          {isRecording && (
            <div className="flex items-center space-x-2 text-red-400">
              <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
              <span className="font-mono">{formatTime(recordingTime)}</span>
            </div>
          )}
          
          <button
            onClick={switchCamera}
            className="p-2 bg-gray-700 text-white rounded-full hover:bg-gray-600 transition-colors"
            title={t('media.switchCamera')}
          >
            🔄
          </button>
          
          <button
            onClick={onClose}
            className="text-white hover:text-gray-300"
          >
            ✕
          </button>
        </div>
      </div>
      
      {/* Camera View */}
      <div className="flex-1 relative">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="w-full h-full object-cover"
        />
        
        <canvas
          ref={canvasRef}
          className="hidden"
        />
        
        {/* Camera overlay */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="w-64 h-64 border-2 border-white border-opacity-50 rounded-lg"></div>
        </div>
      </div>
      
      {/* Controls */}
      <div className="p-6 bg-gray-900 flex justify-center items-center space-x-8">
        <div className="w-16"></div> {/* Spacer */}
        
        <div className="relative">
          {mode === 'photo' ? (
            <button
              onClick={takePhoto}
              className="w-16 h-16 bg-white rounded-full border-4 border-gray-300 hover:border-gray-400 transition-colors shadow-lg"
            >
              <div className="w-full h-full rounded-full bg-white"></div>
            </button>
          ) : (
            <button
              onClick={isRecording ? stopVideoRecording : startVideoRecording}
              className={`w-16 h-16 rounded-full border-4 border-gray-300 transition-colors shadow-lg ${
                isRecording 
                  ? 'bg-red-500 hover:bg-red-600' 
                  : 'bg-red-500 hover:bg-red-600'
              }`}
            >
              {isRecording ? (
                <div className="w-6 h-6 bg-white rounded-sm mx-auto"></div>
              ) : (
                <div className="w-full h-full rounded-full bg-red-500"></div>
              )}
            </button>
          )}
        </div>
        
        <div className="w-16"></div> {/* Spacer */}
      </div>
    </div>
  );
};

export default MediaCapture;