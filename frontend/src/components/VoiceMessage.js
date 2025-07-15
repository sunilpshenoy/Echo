import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

const VoiceMessage = ({ isRecording, onStartRecording, onStopRecording, onSendVoiceMessage }) => {
  const { t } = useTranslation();
  const [audioData, setAudioData] = useState(null);
  const [duration, setDuration] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [waveformData, setWaveformData] = useState([]);
  const mediaRecorder = useRef(null);
  const audioChunks = useRef([]);
  const audioRef = useRef(null);
  const animationRef = useRef(null);

  useEffect(() => {
    if (isRecording) {
      const interval = setInterval(() => {
        setDuration(prev => prev + 1);
        // Simulate waveform data during recording
        setWaveformData(prev => [
          ...prev.slice(-30), // Keep last 30 data points
          Math.random() * 100
        ]);
      }, 100);
      
      return () => clearInterval(interval);
    }
  }, [isRecording]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder.current = new MediaRecorder(stream);
      audioChunks.current = [];
      
      mediaRecorder.current.ondataavailable = (event) => {
        audioChunks.current.push(event.data);
      };
      
      mediaRecorder.current.onstop = () => {
        const audioBlob = new Blob(audioChunks.current, { type: 'audio/wav' });
        const audioUrl = URL.createObjectURL(audioBlob);
        setAudioData({
          blob: audioBlob,
          url: audioUrl,
          duration: duration
        });
        
        // Stop all audio tracks
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.current.start();
      onStartRecording();
      setDuration(0);
      setWaveformData([]);
    } catch (error) {
      console.error('Error starting recording:', error);
      alert(t('voice.recordingError'));
    }
  };

  const stopRecording = () => {
    if (mediaRecorder.current && mediaRecorder.current.state === 'recording') {
      mediaRecorder.current.stop();
      onStopRecording();
    }
  };

  const playAudio = () => {
    if (audioRef.current) {
      audioRef.current.play();
      setIsPlaying(true);
      
      // Update current time during playback
      const updateTime = () => {
        if (audioRef.current) {
          setCurrentTime(audioRef.current.currentTime);
          if (!audioRef.current.ended) {
            animationRef.current = requestAnimationFrame(updateTime);
          } else {
            setIsPlaying(false);
            setCurrentTime(0);
          }
        }
      };
      
      animationRef.current = requestAnimationFrame(updateTime);
    }
  };

  const pauseAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    }
  };

  const sendVoiceMessage = () => {
    if (audioData) {
      onSendVoiceMessage(audioData);
      setAudioData(null);
      setDuration(0);
      setCurrentTime(0);
      setWaveformData([]);
    }
  };

  const cancelRecording = () => {
    if (audioData) {
      URL.revokeObjectURL(audioData.url);
      setAudioData(null);
      setDuration(0);
      setCurrentTime(0);
      setWaveformData([]);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const renderWaveform = () => {
    if (waveformData.length === 0) return null;
    
    return (
      <div className="flex items-center justify-center space-x-1 h-8">
        {waveformData.map((height, index) => (
          <div
            key={index}
            className="w-1 bg-blue-500 rounded-full transition-all duration-100"
            style={{
              height: `${Math.max(4, height / 3)}px`,
              opacity: isRecording ? 1 : 0.7
            }}
          />
        ))}
      </div>
    );
  };

  if (isRecording) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium text-red-700">
              {t('voice.recording')}
            </span>
          </div>
          <span className="text-sm text-red-600">
            {formatTime(duration)}
          </span>
        </div>
        
        {renderWaveform()}
        
        <div className="flex justify-center space-x-2 mt-4">
          <button
            onClick={stopRecording}
            className="flex items-center space-x-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
          >
            <span>⏹️</span>
            <span>{t('voice.stop')}</span>
          </button>
        </div>
      </div>
    );
  }

  if (audioData) {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-blue-700">
            {t('voice.recorded')}
          </span>
          <span className="text-sm text-blue-600">
            {formatTime(audioData.duration)}
          </span>
        </div>
        
        <div className="flex items-center space-x-2 mb-4">
          <button
            onClick={isPlaying ? pauseAudio : playAudio}
            className="p-2 bg-blue-500 text-white rounded-full hover:bg-blue-600 transition-colors"
          >
            {isPlaying ? '⏸️' : '▶️'}
          </button>
          
          <div className="flex-1 bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all duration-100"
              style={{
                width: `${(currentTime / audioData.duration) * 100}%`
              }}
            />
          </div>
        </div>
        
        <audio
          ref={audioRef}
          src={audioData.url}
          onEnded={() => {
            setIsPlaying(false);
            setCurrentTime(0);
          }}
        />
        
        <div className="flex justify-center space-x-2">
          <button
            onClick={cancelRecording}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
          >
            <span>❌</span>
            <span>{t('common.cancel')}</span>
          </button>
          <button
            onClick={sendVoiceMessage}
            className="flex items-center space-x-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
          >
            <span>🎤</span>
            <span>{t('voice.send')}</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <button
      onClick={startRecording}
      className="p-3 bg-blue-500 text-white rounded-full hover:bg-blue-600 transition-colors"
      title={t('voice.record')}
    >
      🎤
    </button>
  );
};

export default VoiceMessage;