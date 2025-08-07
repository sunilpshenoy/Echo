import React, { useState, useEffect, useCallback } from 'react';
import { offlineGameManager } from './OfflineGameManager';

const Game2048 = ({ gameState, onMove, currentUser, mode = 'online' }) => {
  const [grid, setGrid] = useState(Array(4).fill().map(() => Array(4).fill(0)));
  const [score, setScore] = useState(0);
  const [bestScore, setBestScore] = useState(0);
  const [gameOver, setGameOver] = useState(false);
  const [gameWon, setGameWon] = useState(false);
  const [isOffline, setIsOffline] = useState(mode === 'offline');
  const [offlineGameId, setOfflineGameId] = useState(null);

  useEffect(() => {
    if (isOffline && !offlineGameId) {
      initializeOfflineGame();
    } else if (gameState) {
      setGrid(gameState.grid || Array(4).fill().map(() => Array(4).fill(0)));
      setScore(gameState.score || 0);
      setBestScore(gameState.bestScore || 0);
      setGameOver(gameState.gameOver || false);
      setGameWon(gameState.gameWon || false);
    }
  }, [gameState, isOffline, offlineGameId]);

  const initializeOfflineGame = () => {
    const { gameId, gameState: newGameState } = offlineGameManager.createOfflineGame('2048', currentUser?.display_name || 'Player');
    setOfflineGameId(gameId);
    
    const storedBest = localStorage.getItem('pulse_2048_best') || 0;
    setBestScore(parseInt(storedBest));
    
    startNewGame();
  };

  const startNewGame = () => {
    const newGrid = Array(4).fill().map(() => Array(4).fill(0));
    addRandomTile(newGrid);
    addRandomTile(newGrid);
    
    setGrid(newGrid);
    setScore(0);
    setGameOver(false);
    setGameWon(false);

    if (isOffline && offlineGameId) {
      offlineGameManager.updateGameState(offlineGameId, {
        grid: newGrid,
        score: 0,
        bestScore,
        gameOver: false,
        gameWon: false
      });
    }
  };

  const addRandomTile = (grid) => {
    const emptyCells = [];
    for (let i = 0; i < 4; i++) {
      for (let j = 0; j < 4; j++) {
        if (grid[i][j] === 0) {
          emptyCells.push([i, j]);
        }
      }
    }

    if (emptyCells.length > 0) {
      const randomCell = emptyCells[Math.floor(Math.random() * emptyCells.length)];
      const [row, col] = randomCell;
      grid[row][col] = Math.random() < 0.9 ? 2 : 4;
    }
  };

  const moveLeft = (grid) => {
    const newGrid = grid.map(row => [...row]);
    let moved = false;
    let newScore = 0;

    for (let i = 0; i < 4; i++) {
      // Slide tiles left
      const row = newGrid[i].filter(val => val !== 0);
      
      // Merge adjacent equal tiles
      for (let j = 0; j < row.length - 1; j++) {
        if (row[j] === row[j + 1]) {
          row[j] *= 2;
          row[j + 1] = 0;
          newScore += row[j];
          j++; // Skip next tile as it was merged
        }
      }
      
      // Remove zeros again and pad with zeros
      const filteredRow = row.filter(val => val !== 0);
      while (filteredRow.length < 4) {
        filteredRow.push(0);
      }
      
      // Check if row changed
      for (let j = 0; j < 4; j++) {
        if (newGrid[i][j] !== filteredRow[j]) {
          moved = true;
        }
      }
      
      newGrid[i] = filteredRow;
    }

    return { grid: newGrid, moved, score: newScore };
  };

  const rotateGrid = (grid) => {
    const newGrid = Array(4).fill().map(() => Array(4).fill(0));
    for (let i = 0; i < 4; i++) {
      for (let j = 0; j < 4; j++) {
        newGrid[j][3 - i] = grid[i][j];
      }
    }
    return newGrid;
  };

  const move = (direction) => {
    if (gameOver || gameWon) return;

    let currentGrid = grid.map(row => [...row]);
    let result;

    // Rotate grid to make all moves equivalent to left move
    switch (direction) {
      case 'left':
        result = moveLeft(currentGrid);
        break;
      case 'right':
        currentGrid = rotateGrid(rotateGrid(currentGrid));
        result = moveLeft(currentGrid);
        result.grid = rotateGrid(rotateGrid(result.grid));
        break;
      case 'up':
        currentGrid = rotateGrid(rotateGrid(rotateGrid(currentGrid)));
        result = moveLeft(currentGrid);
        result.grid = rotateGrid(result.grid);
        break;
      case 'down':
        currentGrid = rotateGrid(currentGrid);
        result = moveLeft(currentGrid);
        result.grid = rotateGrid(rotateGrid(rotateGrid(result.grid)));
        break;
      default:
        return;
    }

    if (result.moved) {
      addRandomTile(result.grid);
      
      const newScore = score + result.score;
      const newBestScore = Math.max(bestScore, newScore);
      
      setGrid(result.grid);
      setScore(newScore);
      setBestScore(newBestScore);

      // Save best score to localStorage
      localStorage.setItem('pulse_2048_best', newBestScore.toString());

      // Check for 2048 tile (win condition)
      const hasWon = result.grid.some(row => row.some(cell => cell === 2048));
      if (hasWon && !gameWon) {
        setGameWon(true);
      }

      // Check for game over
      if (isGameOver(result.grid)) {
        setGameOver(true);
      }

      if (isOffline && offlineGameId) {
        offlineGameManager.updateGameState(offlineGameId, {
          grid: result.grid,
          score: newScore,
          bestScore: newBestScore,
          gameOver: isGameOver(result.grid),
          gameWon: hasWon
        });
      }
    }
  };

  const isGameOver = (grid) => {
    // Check for empty cells
    for (let i = 0; i < 4; i++) {
      for (let j = 0; j < 4; j++) {
        if (grid[i][j] === 0) return false;
      }
    }

    // Check for possible merges
    for (let i = 0; i < 4; i++) {
      for (let j = 0; j < 4; j++) {
        const current = grid[i][j];
        if (
          (i < 3 && grid[i + 1][j] === current) ||
          (j < 3 && grid[i][j + 1] === current)
        ) {
          return false;
        }
      }
    }

    return true;
  };

  const handleKeyPress = useCallback((event) => {
    switch (event.key) {
      case 'ArrowLeft':
        event.preventDefault();
        move('left');
        break;
      case 'ArrowRight':
        event.preventDefault();
        move('right');
        break;
      case 'ArrowUp':
        event.preventDefault();
        move('up');
        break;
      case 'ArrowDown':
        event.preventDefault();
        move('down');
        break;
    }
  }, [grid, gameOver, gameWon]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyPress);
    return () => {
      window.removeEventListener('keydown', handleKeyPress);
    };
  }, [handleKeyPress]);

  const getTileColor = (value) => {
    const colors = {
      0: 'bg-gray-200',
      2: 'bg-gray-100 text-gray-800',
      4: 'bg-gray-200 text-gray-800',
      8: 'bg-orange-200 text-white',
      16: 'bg-orange-300 text-white',
      32: 'bg-orange-400 text-white',
      64: 'bg-red-400 text-white',
      128: 'bg-yellow-300 text-white',
      256: 'bg-yellow-400 text-white',
      512: 'bg-yellow-500 text-white',
      1024: 'bg-yellow-600 text-white',
      2048: 'bg-yellow-700 text-white'
    };
    
    return colors[value] || 'bg-purple-600 text-white';
  };

  const toggleMode = () => {
    setIsOffline(!isOffline);
    if (!isOffline) {
      startNewGame();
    }
  };

  return (
    <div className="game-2048 max-w-md mx-auto">
      <div className="mb-4">
        <h3 className="text-2xl font-bold text-gray-800 mb-2">🔢 2048</h3>
        
        {/* Score Display */}
        <div className="flex justify-between items-center mb-4">
          <div className="flex space-x-4">
            <div className="bg-gray-200 rounded px-3 py-2">
              <div className="text-xs font-semibold text-gray-600">SCORE</div>
              <div className="text-lg font-bold">{score}</div>
            </div>
            <div className="bg-gray-200 rounded px-3 py-2">
              <div className="text-xs font-semibold text-gray-600">BEST</div>
              <div className="text-lg font-bold">{bestScore}</div>
            </div>
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
              onClick={startNewGame}
              className="bg-orange-500 text-white px-3 py-1 rounded hover:bg-orange-600 text-sm"
            >
              New Game
            </button>
          </div>
        </div>

        {/* Game Status Messages */}
        {gameWon && (
          <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded mb-4">
            🎉 You Win! You reached 2048!
            <button
              onClick={startNewGame}
              className="ml-2 underline hover:no-underline"
            >
              Play Again
            </button>
          </div>
        )}

        {gameOver && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            💀 Game Over! Final Score: {score}
            <button
              onClick={startNewGame}
              className="ml-2 underline hover:no-underline"
            >
              Try Again
            </button>
          </div>
        )}
      </div>

      {/* Game Grid */}
      <div className="bg-gray-400 rounded-lg p-2 mb-4">
        <div className="grid grid-cols-4 gap-2">
          {grid.map((row, i) =>
            row.map((cell, j) => (
              <div
                key={`${i}-${j}`}
                className={`w-16 h-16 rounded flex items-center justify-center font-bold text-lg ${getTileColor(cell)}`}
              >
                {cell !== 0 ? cell : ''}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Controls */}
      <div className="mb-4">
        <div className="grid grid-cols-3 gap-2 max-w-xs mx-auto">
          <div></div>
          <button
            onClick={() => move('up')}
            className="bg-gray-600 text-white p-3 rounded hover:bg-gray-700 transition-colors"
          >
            ↑
          </button>
          <div></div>
          <button
            onClick={() => move('left')}
            className="bg-gray-600 text-white p-3 rounded hover:bg-gray-700 transition-colors"
          >
            ←
          </button>
          <div></div>
          <button
            onClick={() => move('right')}
            className="bg-gray-600 text-white p-3 rounded hover:bg-gray-700 transition-colors"
          >
            →
          </button>
          <div></div>
          <button
            onClick={() => move('down')}
            className="bg-gray-600 text-white p-3 rounded hover:bg-gray-700 transition-colors"
          >
            ↓
          </button>
          <div></div>
        </div>
      </div>

      {/* Instructions */}
      <div className="text-xs text-gray-500 bg-blue-50 rounded-lg p-3">
        <strong>How to play:</strong> Use arrow keys or buttons to slide tiles. When two tiles with the same number touch, they merge into one! 
        Reach 2048 to win!
        {isOffline && <div className="mt-1"><strong>Offline Mode:</strong> Classic 2048 puzzle. No internet required!</div>}
      </div>
    </div>
  );
};

export default Game2048;