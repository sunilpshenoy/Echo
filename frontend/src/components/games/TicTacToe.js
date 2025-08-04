import React, { useState, useEffect } from 'react';

const TicTacToeGame = ({ gameState, onMove, currentUser }) => {
  const [board, setBoard] = useState(Array(9).fill(null));
  const [currentPlayer, setCurrentPlayer] = useState('X');
  const [winner, setWinner] = useState(null);
  const [gameStatus, setGameStatus] = useState('waiting');

  useEffect(() => {
    if (gameState) {
      setBoard(gameState.board || Array(9).fill(null));
      setCurrentPlayer(gameState.currentPlayer || 'X');
      setWinner(gameState.winner || null);
      setGameStatus(gameState.status || 'playing');
    }
  }, [gameState]);

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
    return null;
  };

  const handleCellClick = (index) => {
    if (board[index] || winner || gameStatus !== 'playing') return;
    
    // Check if it's the current user's turn
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
      isDraw: !gameWinner && newBoard.every(cell => cell !== null)
    });
  };

  const resetGame = () => {
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
  };

  const renderCell = (index) => {
    const value = board[index];
    return (
      <button
        key={index}
        className={`w-20 h-20 border-2 border-gray-400 bg-white hover:bg-gray-50 text-3xl font-bold flex items-center justify-center transition-all duration-200 ${
          value === 'X' ? 'text-blue-600' : 'text-red-600'
        } ${!value && !winner && gameStatus === 'playing' ? 'hover:bg-blue-50 cursor-pointer' : 'cursor-not-allowed'}`}
        onClick={() => handleCellClick(index)}
        disabled={!!value || !!winner || gameStatus !== 'playing'}
      >
        {value}
      </button>
    );
  };

  const getStatusMessage = () => {
    if (winner) {
      const winnerName = gameState?.playerNames?.[winner] || `Player ${winner}`;
      return `🎉 ${winnerName} wins!`;
    }
    if (board.every(cell => cell !== null)) {
      return "🤝 It's a draw!";
    }
    if (gameStatus === 'waiting') {
      return "⏳ Waiting for players...";
    }
    const currentPlayerName = gameState?.playerNames?.[currentPlayer] || `Player ${currentPlayer}`;
    return `🎯 ${currentPlayerName}'s turn`;
  };

  return (
    <div className="tic-tac-toe-game text-center">
      <div className="mb-6">
        <h3 className="text-xl font-bold text-gray-800 mb-2">⭕ Tic-Tac-Toe</h3>
        <div className="text-lg text-gray-600">{getStatusMessage()}</div>
      </div>

      {/* Game Board */}
      <div className="grid grid-cols-3 gap-2 justify-center mx-auto w-fit mb-6">
        {Array(9).fill(null).map((_, index) => renderCell(index))}
      </div>

      {/* Game Controls */}
      <div className="flex justify-center space-x-4">
        <button
          onClick={resetGame}
          className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors"
        >
          🔄 New Game
        </button>
        
        {gameState?.spectators?.length > 0 && (
          <div className="text-sm text-gray-500">
            👥 {gameState.spectators.length} watching
          </div>
        )}
      </div>

      {/* Player Info */}
      {gameState?.players && (
        <div className="mt-6 bg-gray-50 rounded-lg p-4">
          <h4 className="font-semibold text-gray-700 mb-2">Players</h4>
          <div className="flex justify-center space-x-6">
            {Object.entries(gameState.players).map(([playerId, symbol]) => (
              <div key={playerId} className="text-center">
                <div className={`text-2xl font-bold ${symbol === 'X' ? 'text-blue-600' : 'text-red-600'}`}>
                  {symbol}
                </div>
                <div className="text-sm text-gray-600">
                  {gameState.playerNames?.[playerId] || 'Player'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Game Rules */}
      <div className="mt-4 text-xs text-gray-500 bg-blue-50 rounded-lg p-3">
        <strong>How to play:</strong> Get three of your symbols in a row (horizontally, vertically, or diagonally) to win!
      </div>
    </div>
  );
};

export default TicTacToeGame;