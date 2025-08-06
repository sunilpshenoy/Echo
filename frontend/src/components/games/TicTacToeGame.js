import React, { useState, useEffect } from 'react';
import { offlineGameManager } from './OfflineGameManager';

const TicTacToeGame = ({ gameState, onMove, currentUser, mode = 'online' }) => {
  const [board, setBoard] = useState(Array(9).fill(null));
  const [currentPlayer, setCurrentPlayer] = useState('X');
  const [winner, setWinner] = useState(null);
  const [gameStatus, setGameStatus] = useState('waiting');
  const [isOffline, setIsOffline] = useState(mode === 'offline');
  const [offlineGameId, setOfflineGameId] = useState(null);
  const [aiThinking, setAiThinking] = useState(false);

  useEffect(() => {
    if (isOffline && !offlineGameId) {
      // Create new offline game
      const { gameId, gameState: newGameState } = offlineGameManager.createOfflineGame('tic-tac-toe', currentUser?.display_name || 'Player');
      setOfflineGameId(gameId);
      setBoard(newGameState.board);
      setCurrentPlayer(newGameState.currentPlayer);
      setGameStatus('playing');
    } else if (gameState) {
      setBoard(gameState.board || Array(9).fill(null));
      setCurrentPlayer(gameState.currentPlayer || 'X');
      setWinner(gameState.winner || null);
      setGameStatus(gameState.status || 'playing');
    }
  }, [gameState, isOffline, offlineGameId, currentUser]);

  const checkWinner = (squares) => {
    const lines = [
      [0, 1, 2], [3, 4, 5], [6, 7, 8], // rows
      [0, 3, 6], [1, 4, 7], [2, 5, 8], // columns
      [0, 4, 8], [2, 4, 6] // diagonals
    ];

    for (let i = 0; i < lines.length; i++) {
      const [a, b, c] = lines[i];
      if (squares[a] && squares[a] === squares[b] && squares[a] === squares[c]) {
        return squares[a];
      }
    }
    
    if (squares.every(cell => cell !== null)) {
      return 'draw';
    }
    
    return null;
  };

  const handleCellClick = async (index) => {
    if (board[index] || winner || gameStatus !== 'playing') return;
    
    if (isOffline) {
      // Offline mode
      if (currentPlayer !== 'X') return; // Only human can make moves when it's their turn
      
      const newBoard = [...board];
      newBoard[index] = currentPlayer;
      
      const gameWinner = checkWinner(newBoard);
      const nextPlayer = currentPlayer === 'X' ? 'O' : 'X';
      
      setBoard(newBoard);
      setCurrentPlayer(nextPlayer);
      setWinner(gameWinner);
      
      // Update offline game state
      const updatedState = offlineGameManager.updateGameState(offlineGameId, {
        ...offlineGameManager.getGameState(offlineGameId),
        board: newBoard,
        currentPlayer: nextPlayer,
        winner: gameWinner,
        moves: (offlineGameManager.getGameState(offlineGameId)?.moves || 0) + 1,
        status: gameWinner ? 'finished' : 'playing'
      });
      
      // If game not finished and it's AI's turn, make AI move
      if (!gameWinner && nextPlayer === 'O') {
        setAiThinking(true);
        setTimeout(() => {
          const aiState = offlineGameManager.makeAIMove(offlineGameId, updatedState);
          setBoard(aiState.board);
          setCurrentPlayer(aiState.currentPlayer);
          setWinner(aiState.winner);
          setGameStatus(aiState.status);
          setAiThinking(false);
        }, 500 + Math.random() * 1000); // Random delay to simulate AI thinking
      }
    } else {
      // Online mode
      const userSymbol = gameState?.players?.[currentUser.user_id] || 'X';
      if (currentPlayer !== userSymbol) return;

      const newBoard = [...board];
      newBoard[index] = currentPlayer;
      
      const gameWinner = checkWinner(newBoard);
      const nextPlayer = currentPlayer === 'X' ? 'O' : 'X';
      
      // Send move to server
      onMove({
        type: 'cell_click',
        position: index,
        board: newBoard,
        currentPlayer: nextPlayer,
        winner: gameWinner,
        isDraw: gameWinner === 'draw'
      });
    }
  };

  const resetGame = () => {
    if (isOffline) {
      // Create new offline game
      const { gameId, gameState: newGameState } = offlineGameManager.createOfflineGame('tic-tac-toe', currentUser?.display_name || 'Player');
      setOfflineGameId(gameId);
      setBoard(newGameState.board);
      setCurrentPlayer(newGameState.currentPlayer);
      setWinner(null);
      setGameStatus('playing');
      setAiThinking(false);
    } else {
      // Online mode reset
      setBoard(Array(9).fill(null));
      setCurrentPlayer('X');
      setWinner(null);
      setGameStatus('playing');
      
      onMove({
        type: 'reset',
        board: Array(9).fill(null),
        currentPlayer: 'X',
        winner: null
      });
    }
  };

  const toggleMode = () => {
    setIsOffline(!isOffline);
    if (!isOffline) {
      // Switching to offline mode
      const { gameId, gameState: newGameState } = offlineGameManager.createOfflineGame('tic-tac-toe', currentUser?.display_name || 'Player');
      setOfflineGameId(gameId);
      setBoard(newGameState.board);
      setCurrentPlayer(newGameState.currentPlayer);
      setWinner(null);
      setGameStatus('playing');
    } else {
      // Switching to online mode
      resetGame();
    }
  };

  const renderCell = (index) => {
    const value = board[index];
    return (
      <button
        key={index}
        className={`w-20 h-20 border-2 border-gray-400 bg-white hover:bg-gray-50 text-3xl font-bold flex items-center justify-center transition-all duration-200 ${
          value === 'X' ? 'text-blue-600' : 'text-red-600'
        } ${!value && !winner && gameStatus === 'playing' && (!isOffline || currentPlayer === 'X') ? 'hover:bg-blue-50 cursor-pointer' : 'cursor-not-allowed'}`}
        onClick={() => handleCellClick(index)}
        disabled={!!value || !!winner || gameStatus !== 'playing' || (isOffline && currentPlayer === 'O') || aiThinking}
      >
        {value}
      </button>
    );
  };

  const getStatusMessage = () => {
    if (aiThinking) {
      return "🤖 AI is thinking...";
    }
    if (winner === 'draw') {
      return "🤝 It's a draw!";
    }
    if (winner === 'X') {
      return isOffline ? "🎉 You win!" : `🎉 ${gameState?.playerNames?.X || 'Player X'} wins!`;
    }
    if (winner === 'O') {
      return isOffline ? "🤖 Computer wins!" : `🎉 ${gameState?.playerNames?.O || 'Player O'} wins!`;
    }
    if (gameStatus === 'waiting') {
      return "⏳ Waiting for players...";
    }
    
    if (isOffline) {
      return currentPlayer === 'X' ? "🎯 Your turn" : "🤖 Computer's turn";
    } else {
      const currentPlayerName = gameState?.playerNames?.[currentPlayer] || `Player ${currentPlayer}`;
      return `🎯 ${currentPlayerName}'s turn`;
    }
  };

  return (
    <div className="tic-tac-toe-game text-center">
      <div className="mb-6">
        <h3 className="text-xl font-bold text-gray-800 mb-2">⭕ Tic-Tac-Toe</h3>
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
            {isOffline ? '🤖 vs Computer' : '🌐 Online Mode'}
          </button>
        </div>
      </div>

      {/* Game Board */}
      <div className={`grid grid-cols-3 gap-2 justify-center mx-auto w-fit mb-6 ${aiThinking ? 'opacity-50' : ''}`}>
        {Array(9).fill(null).map((_, index) => renderCell(index))}
      </div>

      {/* Game Controls */}
      <div className="flex justify-center space-x-4">
        <button
          onClick={resetGame}
          className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors"
          disabled={aiThinking}
        >
          🔄 New Game
        </button>
        
        {!isOffline && gameState?.spectators?.length > 0 && (
          <div className="text-sm text-gray-500">
            👥 {gameState.spectators.length} watching
          </div>
        )}
      </div>

      {/* Player Info */}
      <div className="mt-6 bg-gray-50 rounded-lg p-4">
        <h4 className="font-semibold text-gray-700 mb-2">Players</h4>
        <div className="flex justify-center space-x-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">X</div>
            <div className="text-sm text-gray-600">
              {isOffline ? (currentUser?.display_name || 'You') : (gameState?.playerNames?.X || 'Player X')}
            </div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">O</div>
            <div className="text-sm text-gray-600">
              {isOffline ? 'Computer' : (gameState?.playerNames?.O || 'Player O')}
            </div>
          </div>
        </div>
      </div>

      {/* Game Rules */}
      <div className="mt-4 text-xs text-gray-500 bg-blue-50 rounded-lg p-3">
        <strong>How to play:</strong> Get three of your symbols in a row (horizontally, vertically, or diagonally) to win!
        {isOffline && <div className="mt-1"><strong>Offline Mode:</strong> Play against the computer AI. No internet required!</div>}
      </div>
    </div>
  );
};

export default TicTacToeGame;