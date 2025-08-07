import React, { useState, useEffect, useCallback } from 'react';
import { offlineGameManager } from './OfflineGameManager';

const Snake = ({ gameState, onMove, currentUser, mode = 'online' }) => {
  const [snake, setSnake] = useState([{ x: 10, y: 10 }]);
  const [food, setFood] = useState({ x: 15, y: 15 });
  const [direction, setDirection] = useState({ x: 0, y: 1 });
  const [gameRunning, setGameRunning] = useState(false);
  const [gameOver, setGameOver] = useState(false);
  const [score, setScore] = useState(0);
  const [highScore, setHighScore] = useState(0);
  const [speed, setSpeed] = useState(150);
  const [isOffline, setIsOffline] = useState(mode === 'offline');
  const [offlineGameId, setOfflineGameId] = useState(null);

  const BOARD_SIZE = 20;

  useEffect(() => {
    if (isOffline && !offlineGameId) {
      initializeOfflineGame();
    } else if (gameState) {
      setSnake(gameState.snake || [{ x: 10, y: 10 }]);
      setFood(gameState.food || { x: 15, y: 15 });
      setDirection(gameState.direction || { x: 0, y: 1 });
      setScore(gameState.score || 0);
      setHighScore(gameState.highScore || 0);
      setGameRunning(gameState.gameRunning || false);
      setGameOver(gameState.gameOver || false);
    }
  }, [gameState, isOffline, offlineGameId]);

  const initializeOfflineGame = () => {
    const { gameId, gameState: newGameState } = offlineGameManager.createOfflineGame('snake', currentUser?.display_name || 'Player');
    setOfflineGameId(gameId);
    
    const savedHighScore = localStorage.getItem('pulse_snake_high') || 0;
    setHighScore(parseInt(savedHighScore));
    
    resetGame();
  };

  const resetGame = () => {
    const newSnake = [{ x: 10, y: 10 }];
    const newFood = generateFood(newSnake);
    
    setSnake(newSnake);
    setFood(newFood);
    setDirection({ x: 0, y: 1 });
    setGameRunning(false);
    setGameOver(false);
    setScore(0);
    setSpeed(150);

    if (isOffline && offlineGameId) {
      offlineGameManager.updateGameState(offlineGameId, {
        snake: newSnake,
        food: newFood,
        direction: { x: 0, y: 1 },
        score: 0,
        highScore,
        gameRunning: false,
        gameOver: false
      });
    }
  };

  const generateFood = (currentSnake) => {
    let newFood;
    do {
      newFood = {
        x: Math.floor(Math.random() * BOARD_SIZE),
        y: Math.floor(Math.random() * BOARD_SIZE)
      };
    } while (currentSnake.some(segment => segment.x === newFood.x && segment.y === newFood.y));
    
    return newFood;
  };

  const moveSnake = useCallback(() => {
    if (!gameRunning || gameOver) return;

    setSnake(prevSnake => {
      const newSnake = [...prevSnake];
      const head = { ...newSnake[0] };
      
      head.x += direction.x;
      head.y += direction.y;
      
      // Check wall collision
      if (head.x < 0 || head.x >= BOARD_SIZE || head.y < 0 || head.y >= BOARD_SIZE) {
        setGameOver(true);
        setGameRunning(false);
        
        // Update high score
        const newHighScore = Math.max(score, highScore);
        setHighScore(newHighScore);
        localStorage.setItem('pulse_snake_high', newHighScore.toString());
        
        return prevSnake;
      }
      
      // Check self collision
      if (newSnake.some(segment => segment.x === head.x && segment.y === head.y)) {
        setGameOver(true);
        setGameRunning(false);
        
        // Update high score
        const newHighScore = Math.max(score, highScore);
        setHighScore(newHighScore);
        localStorage.setItem('pulse_snake_high', newHighScore.toString());
        
        return prevSnake;
      }
      
      newSnake.unshift(head);
      
      // Check food collision
      if (head.x === food.x && head.y === food.y) {
        const newScore = score + 10;
        setScore(newScore);
        setFood(generateFood(newSnake));
        
        // Increase speed slightly
        setSpeed(prev => Math.max(80, prev - 2));
      } else {
        newSnake.pop();
      }
      
      return newSnake;
    });
  }, [direction, food, gameRunning, gameOver, score, highScore]);

  // Game loop
  useEffect(() => {
    if (gameRunning) {
      const gameInterval = setInterval(moveSnake, speed);
      return () => clearInterval(gameInterval);
    }
  }, [moveSnake, speed, gameRunning]);

  const handleKeyPress = useCallback((e) => {
    if (!gameRunning) return;

    switch (e.key) {
      case 'ArrowUp':
        e.preventDefault();
        setDirection(prev => prev.y !== 1 ? { x: 0, y: -1 } : prev);
        break;
      case 'ArrowDown':
        e.preventDefault();
        setDirection(prev => prev.y !== -1 ? { x: 0, y: 1 } : prev);
        break;
      case 'ArrowLeft':
        e.preventDefault();
        setDirection(prev => prev.x !== 1 ? { x: -1, y: 0 } : prev);
        break;
      case 'ArrowRight':
        e.preventDefault();
        setDirection(prev => prev.x !== -1 ? { x: 1, y: 0 } : prev);
        break;
      case ' ':
        e.preventDefault();
        setGameRunning(false);
        break;
    }
  }, [gameRunning]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [handleKeyPress]);

  const startGame = () => {
    if (gameOver) {
      resetGame();
    }
    setGameRunning(true);
  };

  const pauseGame = () => {
    setGameRunning(!gameRunning);
  };

  const changeDirection = (newDirection) => {
    if (!gameRunning) return;
    
    const opposites = {
      up: 'down',
      down: 'up',
      left: 'right',
      right: 'left'
    };
    
    const currentDir = direction.x === 0 ? (direction.y === -1 ? 'up' : 'down') : (direction.x === -1 ? 'left' : 'right');
    
    if (opposites[currentDir] === newDirection) return;
    
    const directions = {
      up: { x: 0, y: -1 },
      down: { x: 0, y: 1 },
      left: { x: -1, y: 0 },
      right: { x: 1, y: 0 }
    };
    
    setDirection(directions[newDirection]);
  };

  const toggleMode = () => {
    setIsOffline(!isOffline);
    if (!isOffline) {
      resetGame();
    }
  };

  const renderBoard = () => {
    const board = [];
    
    for (let y = 0; y < BOARD_SIZE; y++) {
      for (let x = 0; x < BOARD_SIZE; x++) {
        let cellType = 'empty';
        
        // Check if it's the snake head
        if (snake[0] && snake[0].x === x && snake[0].y === y) {
          cellType = 'head';
        }
        // Check if it's snake body
        else if (snake.slice(1).some(segment => segment.x === x && segment.y === y)) {
          cellType = 'body';
        }
        // Check if it's food
        else if (food.x === x && food.y === y) {
          cellType = 'food';
        }
        
        const cellStyle = {
          empty: 'bg-gray-100',
          head: 'bg-green-600',
          body: 'bg-green-400',
          food: 'bg-red-500'
        };
        
        board.push(
          <div
            key={`${x}-${y}`}
            className={`w-4 h-4 ${cellStyle[cellType]} border border-gray-200`}
          />
        );
      }
    }
    
    return board;
  };

  return (
    <div className="snake-game max-w-2xl mx-auto">
      <div className="mb-4">
        <h3 className="text-xl font-bold text-gray-800 mb-2">🐍 Snake Game</h3>
        
        {/* Game Info */}
        <div className="flex justify-between items-center mb-4">
          <div className="flex space-x-4 text-sm">
            <span className="font-semibold">Score: {score}</span>
            <span>High Score: {highScore}</span>
            <span>Length: {snake.length}</span>
          </div>
          
          <div className="flex space-x-2">
            <button
              onClick={toggleMode}
              className={`px-3 py-1 rounded-full text-sm transition-all ${
                isOffline 
                  ? 'bg-green-100 text-green-700 hover:bg-green-200' 
                  : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
              }`}
            >
              {isOffline ? '🎮 Offline' : '🌐 Online'}
            </button>
            
            <button
              onClick={resetGame}
              className="bg-gray-500 text-white px-3 py-1 rounded text-sm hover:bg-gray-600"
            >
              Reset
            </button>
          </div>
        </div>

        {/* Game Status */}
        {gameOver && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            💀 Game Over! Final Score: {score}
            {score === highScore && score > 0 && <span className="ml-2">🏆 New High Score!</span>}
          </div>
        )}

        {!gameRunning && !gameOver && (
          <div className="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded mb-4">
            🎮 Ready to play! Click Start or use arrow keys to begin.
          </div>
        )}
      </div>

      {/* Game Board */}
      <div className="flex justify-center mb-6">
        <div 
          className="grid gap-0 border-2 border-gray-400 bg-white"
          style={{ gridTemplateColumns: `repeat(${BOARD_SIZE}, 1fr)` }}
        >
          {renderBoard()}
        </div>
      </div>

      {/* Game Controls */}
      <div className="text-center mb-6">
        {!gameRunning ? (
          <button
            onClick={startGame}
            className="bg-green-500 text-white px-6 py-3 rounded-lg hover:bg-green-600 transition-colors text-lg font-semibold"
          >
            {gameOver ? '🔄 Play Again' : '▶️ Start Game'}
          </button>
        ) : (
          <button
            onClick={pauseGame}
            className="bg-yellow-500 text-white px-6 py-3 rounded-lg hover:bg-yellow-600 transition-colors text-lg font-semibold"
          >
            ⏸️ Pause
          </button>
        )}
      </div>

      {/* Touch Controls */}
      <div className="grid grid-cols-3 gap-2 max-w-xs mx-auto mb-6">
        <div></div>
        <button
          onClick={() => changeDirection('up')}
          className="bg-gray-600 text-white p-3 rounded hover:bg-gray-700 transition-colors"
        >
          ↑
        </button>
        <div></div>
        <button
          onClick={() => changeDirection('left')}
          className="bg-gray-600 text-white p-3 rounded hover:bg-gray-700 transition-colors"
        >
          ←
        </button>
        <div></div>
        <button
          onClick={() => changeDirection('right')}
          className="bg-gray-600 text-white p-3 rounded hover:bg-gray-700 transition-colors"
        >
          →
        </button>
        <div></div>
        <button
          onClick={() => changeDirection('down')}
          className="bg-gray-600 text-white p-3 rounded hover:bg-gray-700 transition-colors"
        >
          ↓
        </button>
        <div></div>
      </div>

      {/* Game Rules */}
      <div className="text-xs text-gray-500 bg-blue-50 rounded-lg p-3">
        <strong>How to play:</strong> Use arrow keys or buttons to control the snake. Eat food (red squares) to grow longer and earn points. 
        Don't hit the walls or yourself! Press Space to pause.
        {isOffline && <div className="mt-1"><strong>Offline Mode:</strong> Classic snake game. No internet required!</div>}
      </div>
    </div>
  );
};

export default Snake;