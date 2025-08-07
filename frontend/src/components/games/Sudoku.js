import React, { useState, useEffect } from 'react';
import { offlineGameManager } from './OfflineGameManager';

const Sudoku = ({ gameState, onMove, currentUser, mode = 'online' }) => {
  const [grid, setGrid] = useState(Array(9).fill().map(() => Array(9).fill(0)));
  const [initialGrid, setInitialGrid] = useState(Array(9).fill().map(() => Array(9).fill(0)));
  const [selectedCell, setSelectedCell] = useState({ row: -1, col: -1 });
  const [errors, setErrors] = useState(new Set());
  const [gameWon, setGameWon] = useState(false);
  const [difficulty, setDifficulty] = useState('medium');
  const [hints, setHints] = useState(3);
  const [timer, setTimer] = useState(0);
  const [isOffline, setIsOffline] = useState(mode === 'offline');
  const [offlineGameId, setOfflineGameId] = useState(null);

  const difficulties = {
    easy: 35,
    medium: 45,
    hard: 55,
    expert: 64
  };

  useEffect(() => {
    if (isOffline && !offlineGameId) {
      initializeOfflineGame();
    } else if (gameState) {
      setGrid(gameState.grid || Array(9).fill().map(() => Array(9).fill(0)));
      setInitialGrid(gameState.initialGrid || Array(9).fill().map(() => Array(9).fill(0)));
      setTimer(gameState.timer || 0);
      setHints(gameState.hints || 3);
      setGameWon(gameState.gameWon || false);
    }
  }, [gameState, isOffline, offlineGameId]);

  // Timer effect
  useEffect(() => {
    let interval;
    if (!gameWon && !isOffline) {
      interval = setInterval(() => {
        setTimer(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [gameWon, isOffline]);

  const initializeOfflineGame = () => {
    const { gameId, gameState: newGameState } = offlineGameManager.createOfflineGame('sudoku', currentUser?.display_name || 'Player');
    setOfflineGameId(gameId);
    generatePuzzle(difficulty);
  };

  const generatePuzzle = (diff) => {
    // Create a complete valid Sudoku grid
    const completeGrid = generateCompleteGrid();
    
    // Remove numbers based on difficulty
    const puzzleGrid = JSON.parse(JSON.stringify(completeGrid));
    const cellsToRemove = difficulties[diff];
    
    const positions = [];
    for (let i = 0; i < 9; i++) {
      for (let j = 0; j < 9; j++) {
        positions.push([i, j]);
      }
    }
    
    // Randomly remove cells
    for (let i = 0; i < cellsToRemove; i++) {
      const randomIndex = Math.floor(Math.random() * positions.length);
      const [row, col] = positions.splice(randomIndex, 1)[0];
      puzzleGrid[row][col] = 0;
    }
    
    setGrid(JSON.parse(JSON.stringify(puzzleGrid)));
    setInitialGrid(JSON.parse(JSON.stringify(puzzleGrid)));
    setSelectedCell({ row: -1, col: -1 });
    setErrors(new Set());
    setGameWon(false);
    setTimer(0);
    setHints(3);

    if (isOffline && offlineGameId) {
      offlineGameManager.updateGameState(offlineGameId, {
        grid: puzzleGrid,
        initialGrid: puzzleGrid,
        timer: 0,
        hints: 3,
        gameWon: false,
        difficulty: diff
      });
    }
  };

  const generateCompleteGrid = () => {
    const grid = Array(9).fill().map(() => Array(9).fill(0));
    
    // Simple backtracking algorithm to fill the grid
    const fillGrid = (grid) => {
      for (let row = 0; row < 9; row++) {
        for (let col = 0; col < 9; col++) {
          if (grid[row][col] === 0) {
            const numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9];
            // Shuffle numbers for randomness
            for (let i = numbers.length - 1; i > 0; i--) {
              const j = Math.floor(Math.random() * (i + 1));
              [numbers[i], numbers[j]] = [numbers[j], numbers[i]];
            }
            
            for (const num of numbers) {
              if (isValid(grid, row, col, num)) {
                grid[row][col] = num;
                if (fillGrid(grid)) {
                  return true;
                }
                grid[row][col] = 0;
              }
            }
            return false;
          }
        }
      }
      return true;
    };

    fillGrid(grid);
    return grid;
  };

  const isValid = (grid, row, col, num) => {
    // Check row
    for (let j = 0; j < 9; j++) {
      if (grid[row][j] === num) return false;
    }

    // Check column
    for (let i = 0; i < 9; i++) {
      if (grid[i][col] === num) return false;
    }

    // Check 3x3 box
    const boxRow = Math.floor(row / 3) * 3;
    const boxCol = Math.floor(col / 3) * 3;
    for (let i = boxRow; i < boxRow + 3; i++) {
      for (let j = boxCol; j < boxCol + 3; j++) {
        if (grid[i][j] === num) return false;
      }
    }

    return true;
  };

  const handleCellClick = (row, col) => {
    if (initialGrid[row][col] !== 0 || gameWon) return;
    setSelectedCell({ row, col });
  };

  const handleNumberInput = (num) => {
    const { row, col } = selectedCell;
    if (row === -1 || col === -1 || initialGrid[row][col] !== 0) return;

    const newGrid = JSON.parse(JSON.stringify(grid));
    const newErrors = new Set(errors);

    if (num === 0) {
      // Clear cell
      newGrid[row][col] = 0;
      newErrors.delete(`${row}-${col}`);
    } else {
      newGrid[row][col] = num;
      
      if (isValid(newGrid, row, col, num)) {
        newErrors.delete(`${row}-${col}`);
      } else {
        newErrors.add(`${row}-${col}`);
      }
    }

    setGrid(newGrid);
    setErrors(newErrors);

    // Check for win
    if (isPuzzleSolved(newGrid)) {
      setGameWon(true);
    }

    if (isOffline && offlineGameId) {
      offlineGameManager.updateGameState(offlineGameId, {
        grid: newGrid,
        timer,
        gameWon: isPuzzleSolved(newGrid)
      });
    }
  };

  const isPuzzleSolved = (grid) => {
    // Check if all cells are filled and no errors
    for (let i = 0; i < 9; i++) {
      for (let j = 0; j < 9; j++) {
        if (grid[i][j] === 0) return false;
      }
    }

    // Validate entire grid
    for (let i = 0; i < 9; i++) {
      for (let j = 0; j < 9; j++) {
        const tempGrid = JSON.parse(JSON.stringify(grid));
        const num = tempGrid[i][j];
        tempGrid[i][j] = 0;
        if (!isValid(tempGrid, i, j, num)) return false;
      }
    }

    return true;
  };

  const useHint = () => {
    if (hints <= 0 || gameWon) return;

    const emptyCells = [];
    for (let i = 0; i < 9; i++) {
      for (let j = 0; j < 9; j++) {
        if (grid[i][j] === 0) {
          emptyCells.push([i, j]);
        }
      }
    }

    if (emptyCells.length === 0) return;

    const [row, col] = emptyCells[Math.floor(Math.random() * emptyCells.length)];
    
    // Find the correct number for this cell
    for (let num = 1; num <= 9; num++) {
      const tempGrid = JSON.parse(JSON.stringify(grid));
      tempGrid[row][col] = num;
      if (isValid(tempGrid, row, col, num)) {
        handleNumberInput(num);
        setSelectedCell({ row, col });
        setHints(hints - 1);
        break;
      }
    }
  };

  const newGame = (newDifficulty = difficulty) => {
    setDifficulty(newDifficulty);
    if (isOffline) {
      generatePuzzle(newDifficulty);
    } else {
      onMove({ type: 'new_game', difficulty: newDifficulty });
    }
  };

  const toggleMode = () => {
    setIsOffline(!isOffline);
    if (!isOffline) {
      generatePuzzle(difficulty);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const renderCell = (row, col) => {
    const value = grid[row][col];
    const isInitial = initialGrid[row][col] !== 0;
    const isSelected = selectedCell.row === row && selectedCell.col === col;
    const hasError = errors.has(`${row}-${col}`);
    const isInSameRowColBox = selectedCell.row !== -1 && (
      selectedCell.row === row || 
      selectedCell.col === col || 
      (Math.floor(selectedCell.row / 3) === Math.floor(row / 3) && 
       Math.floor(selectedCell.col / 3) === Math.floor(col / 3))
    );

    return (
      <div
        key={`${row}-${col}`}
        onClick={() => handleCellClick(row, col)}
        className={`w-10 h-10 border border-gray-400 flex items-center justify-center text-lg font-semibold cursor-pointer transition-all ${
          isInitial 
            ? 'bg-gray-200 text-gray-800 cursor-not-allowed' 
            : 'bg-white text-blue-600 hover:bg-blue-50'
        } ${isSelected ? 'bg-blue-200 ring-2 ring-blue-500' : ''} ${
          hasError ? 'bg-red-100 text-red-600' : ''
        } ${isInSameRowColBox && !isSelected ? 'bg-gray-50' : ''} ${
          (row + 1) % 3 === 0 ? 'border-b-2 border-b-black' : ''
        } ${(col + 1) % 3 === 0 ? 'border-r-2 border-r-black' : ''}`}
      >
        {value !== 0 ? value : ''}
      </div>
    );
  };

  return (
    <div className="sudoku-game">
      <div className="mb-4">
        <h3 className="text-xl font-bold text-gray-800 mb-2">🔢 Sudoku</h3>
        
        {/* Game Controls */}
        <div className="flex justify-between items-center mb-4">
          <div className="flex items-center space-x-4 text-sm">
            <span>Time: {formatTime(timer)}</span>
            <span>Hints: {hints}</span>
            <span className="capitalize">Difficulty: {difficulty}</span>
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
              {isOffline ? '🧩 Offline' : '🌐 Online'}
            </button>
            
            <button
              onClick={useHint}
              disabled={hints <= 0}
              className="bg-yellow-500 text-white px-3 py-1 rounded text-sm hover:bg-yellow-600 disabled:bg-gray-400"
            >
              💡 Hint
            </button>
          </div>
        </div>

        {gameWon && (
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
            🎉 Congratulations! You solved the puzzle in {formatTime(timer)}!
          </div>
        )}
      </div>

      {/* Sudoku Grid */}
      <div className="flex justify-center mb-6">
        <div className="grid grid-cols-9 gap-0 border-2 border-black bg-white">
          {Array(9).fill().map((_, row) => 
            Array(9).fill().map((_, col) => renderCell(row, col))
          )}
        </div>
      </div>

      {/* Number Input Buttons */}
      <div className="flex justify-center mb-6">
        <div className="grid grid-cols-5 gap-2">
          {[1, 2, 3, 4, 5, 6, 7, 8, 9].map(num => (
            <button
              key={num}
              onClick={() => handleNumberInput(num)}
              className="w-12 h-12 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors font-semibold"
            >
              {num}
            </button>
          ))}
          <button
            onClick={() => handleNumberInput(0)}
            className="w-12 h-12 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors font-semibold"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Difficulty Selection */}
      <div className="flex justify-center space-x-2 mb-4">
        {Object.keys(difficulties).map(diff => (
          <button
            key={diff}
            onClick={() => newGame(diff)}
            className={`px-3 py-1 rounded text-sm transition-all capitalize ${
              difficulty === diff 
                ? 'bg-purple-500 text-white' 
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {diff}
          </button>
        ))}
      </div>

      {/* Game Rules */}
      <div className="text-xs text-gray-500 bg-blue-50 rounded-lg p-3">
        <strong>How to play:</strong> Fill the 9x9 grid so that each row, column, and 3x3 box contains digits 1-9 exactly once. 
        Click a cell and use number buttons to fill it.
        {isOffline && <div className="mt-1"><strong>Offline Mode:</strong> Classic Sudoku puzzles. No internet required!</div>}
      </div>
    </div>
  );
};

export default Sudoku;