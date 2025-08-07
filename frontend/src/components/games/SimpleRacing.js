import React, { useState, useEffect, useRef } from 'react';
import { offlineGameManager } from './OfflineGameManager';

const SimpleRacing = ({ gameState, onMove, currentUser, mode = 'online' }) => {
  const [raceState, setRaceState] = useState({
    cars: [],
    raceDistance: 100,
    raceStarted: false,
    raceFinished: false,
    winner: null,
    countdown: 0
  });
  const [isOffline, setIsOffline] = useState(mode === 'offline');
  const [offlineGameId, setOfflineGameId] = useState(null);
  const [gameLoop, setGameLoop] = useState(null);
  const canvasRef = useRef(null);

  const carEmojis = ['🏎️', '🚗', '🚙', '🏁', '🚕', '🚐'];
  const trackWidth = 600;
  const trackHeight = 300;
  const carHeight = 30;

  useEffect(() => {
    if (isOffline && !offlineGameId) {
      initializeOfflineRace();
    } else if (gameState) {
      setRaceState(gameState);
    }
  }, [gameState, isOffline, offlineGameId]);

  const initializeOfflineRace = () => {
    const { gameId, gameState: newGameState } = offlineGameManager.createOfflineGame('racing', currentUser?.display_name || 'Player');
    setOfflineGameId(gameId);
    
    const cars = [
      { id: 'player', name: currentUser?.display_name || 'You', position: 0, speed: 0, emoji: '🏎️', isPlayer: true },
      { id: 'ai1', name: 'Lightning', position: 0, speed: 0, emoji: '🚗', isAI: true },
      { id: 'ai2', name: 'Thunder', position: 0, speed: 0, emoji: '🚙', isAI: true },
      { id: 'ai3', name: 'Bolt', position: 0, speed: 0, emoji: '🚕', isAI: true }
    ];

    const initialState = {
      ...newGameState,
      cars,
      raceDistance: 100,
      raceStarted: false,
      raceFinished: false,
      winner: null,
      countdown: 0
    };

    setRaceState(initialState);
    offlineGameManager.updateGameState(gameId, initialState);
  };

  const startRace = () => {
    if (raceState.raceStarted) return;

    let count = 3;
    setRaceState(prev => ({ ...prev, countdown: count }));

    const countdownInterval = setInterval(() => {
      count--;
      if (count > 0) {
        setRaceState(prev => ({ ...prev, countdown: count }));
      } else {
        setRaceState(prev => ({ 
          ...prev, 
          countdown: 0, 
          raceStarted: true,
          cars: prev.cars.map(car => ({ ...car, speed: car.isPlayer ? 0 : Math.random() * 2 + 1 }))
        }));
        clearInterval(countdownInterval);
        startGameLoop();
      }
    }, 1000);
  };

  const startGameLoop = () => {
    const loop = setInterval(() => {
      setRaceState(prev => {
        if (prev.raceFinished) return prev;

        const updatedCars = prev.cars.map(car => {
          let newPosition = car.position;
          
          if (car.isAI) {
            // AI cars have varying speeds with some randomness
            const aiSpeed = Math.random() * 1.5 + 0.5;
            newPosition = Math.min(car.position + aiSpeed, 100);
          } else {
            // Player car moves based on player input (handled separately)
            newPosition = car.position;
          }

          return { ...car, position: newPosition };
        });

        // Check for winner
        const finishedCar = updatedCars.find(car => car.position >= 100);
        const winner = finishedCar ? finishedCar.id : null;
        const raceFinished = !!winner;

        const newState = {
          ...prev,
          cars: updatedCars,
          winner,
          raceFinished
        };

        if (isOffline && offlineGameId) {
          offlineGameManager.updateGameState(offlineGameId, newState);
        }

        if (raceFinished) {
          clearInterval(loop);
        }

        return newState;
      });
    }, 100);

    setGameLoop(loop);
  };

  const accelerate = () => {
    if (!raceState.raceStarted || raceState.raceFinished) return;

    setRaceState(prev => {
      const updatedCars = prev.cars.map(car => 
        car.isPlayer ? { 
          ...car, 
          position: Math.min(car.position + Math.random() * 3 + 1, 100) 
        } : car
      );

      return { ...prev, cars: updatedCars };
    });
  };

  const resetRace = () => {
    if (gameLoop) {
      clearInterval(gameLoop);
      setGameLoop(null);
    }

    if (isOffline) {
      initializeOfflineRace();
    } else {
      onMove({ type: 'reset' });
    }
  };

  const toggleMode = () => {
    setIsOffline(!isOffline);
    resetRace();
  };

  // Canvas rendering for track visualization
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, trackWidth, trackHeight);

    // Draw track
    ctx.fillStyle = '#333';
    ctx.fillRect(0, 0, trackWidth, trackHeight);

    // Draw lane dividers
    ctx.strokeStyle = '#fff';
    ctx.setLineDash([10, 5]);
    for (let i = 1; i < raceState.cars.length; i++) {
      const y = (trackHeight / raceState.cars.length) * i;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(trackWidth, y);
      ctx.stroke();
    }

    // Draw finish line
    ctx.setLineDash([]);
    ctx.strokeStyle = '#ff0';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(trackWidth - 20, 0);
    ctx.lineTo(trackWidth - 20, trackHeight);
    ctx.stroke();

    // Draw cars
    raceState.cars.forEach((car, index) => {
      const laneY = (trackHeight / raceState.cars.length) * index + carHeight / 2;
      const carX = (car.position / 100) * (trackWidth - 50);
      
      ctx.font = '24px Arial';
      ctx.fillText(car.emoji, carX, laneY + 8);
    });

    // Draw countdown
    if (raceState.countdown > 0) {
      ctx.font = 'bold 48px Arial';
      ctx.fillStyle = '#ff0';
      ctx.textAlign = 'center';
      ctx.fillText(raceState.countdown.toString(), trackWidth / 2, trackHeight / 2);
    }

    // Draw start message
    if (raceState.countdown === 0 && raceState.raceStarted) {
      ctx.font = 'bold 24px Arial';
      ctx.fillStyle = '#0f0';
      ctx.textAlign = 'center';
      ctx.fillText('GO!', trackWidth / 2, trackHeight / 2);
    }
  }, [raceState]);

  const getStatusMessage = () => {
    if (raceState.countdown > 0) return `Get Ready! ${raceState.countdown}`;
    if (!raceState.raceStarted) return "🏁 Click START RACE to begin!";
    if (raceState.raceFinished) {
      const winner = raceState.cars.find(car => car.id === raceState.winner);
      return winner?.isPlayer ? "🎉 You won!" : `🏁 ${winner?.name} wins!`;
    }
    return "🏎️ Click ACCELERATE rapidly to speed up!";
  };

  return (
    <div className="racing-game text-center">
      <div className="mb-6">
        <h3 className="text-xl font-bold text-gray-800 mb-2">🏁 Simple Racing</h3>
        <div className="text-lg text-gray-600">{getStatusMessage()}</div>
        
        {/* Mode Toggle */}
        <div className="mt-2 flex justify-center">
          <button
            onClick={toggleMode}
            className={`px-3 py-1 rounded-full text-sm transition-all ${
              isOffline 
                ? 'bg-green-100 text-green-700 hover:bg-green-200' 
                : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
            }`}
          >
            {isOffline ? '🤖 vs AI' : '🌐 Online Mode'}
          </button>
        </div>
      </div>

      {/* Race Track */}
      <div className="mb-6 bg-gray-800 rounded-lg p-4 flex justify-center">
        <canvas
          ref={canvasRef}
          width={trackWidth}
          height={trackHeight}
          className="border-2 border-gray-600 rounded"
        />
      </div>

      {/* Race Controls */}
      <div className="flex justify-center space-x-4 mb-6">
        {!raceState.raceStarted && raceState.countdown === 0 && (
          <button
            onClick={startRace}
            className="bg-green-500 text-white px-6 py-3 rounded-lg hover:bg-green-600 transition-colors text-lg font-bold"
          >
            🏁 START RACE
          </button>
        )}
        
        {raceState.raceStarted && !raceState.raceFinished && (
          <button
            onClick={accelerate}
            className="bg-blue-500 text-white px-8 py-4 rounded-lg hover:bg-blue-600 transition-colors text-xl font-bold active:bg-blue-700"
            onMouseDown={accelerate}
          >
            ⚡ ACCELERATE
          </button>
        )}

        <button
          onClick={resetRace}
          className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors"
        >
          🔄 New Race
        </button>
      </div>

      {/* Race Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {raceState.cars.map((car, index) => (
          <div 
            key={car.id} 
            className={`bg-white rounded-lg p-3 border-2 ${
              car.id === raceState.winner ? 'border-yellow-400 bg-yellow-50' : 'border-gray-300'
            }`}
          >
            <div className="text-2xl mb-1">{car.emoji}</div>
            <div className="font-semibold text-sm">{car.name}</div>
            <div className="text-xs text-gray-600">
              {Math.round(car.position)}% complete
            </div>
            {car.id === raceState.winner && (
              <div className="text-xs text-yellow-600 font-bold">🏆 WINNER!</div>
            )}
          </div>
        ))}
      </div>

      {/* Game Rules */}
      <div className="text-xs text-gray-500 bg-blue-50 rounded-lg p-3">
        <strong>How to play:</strong> Click "START RACE" to begin countdown. When race starts, rapidly click "ACCELERATE" to speed up your car. 
        First to reach the finish line wins!
        {isOffline && <div className="mt-1"><strong>Offline Mode:</strong> Race against AI opponents. No internet required!</div>}
      </div>
    </div>
  );
};

export default SimpleRacing;