import React from 'react';

// Tic-Tac-Toe Game Component
const TicTacToeGame = ({ gameState, onMove, currentUser }) => {
  const { board, currentPlayer, players, winner, gameStatus } = gameState;
  
  const isMyTurn = currentPlayer === currentUser.user_id;
  const mySymbol = players[currentUser.user_id]?.symbol || '?';
  const opponentId = Object.keys(players).find(id => id !== currentUser.user_id);
  const opponentName = players[opponentId]?.name || 'Opponent';
  const opponentSymbol = players[opponentId]?.symbol || '?';

  const handleCellClick = (row, col) => {
    if (!isMyTurn || board[row][col] !== '' || winner) return;
    
    onMove({
      type: 'place_symbol',
      row: row,
      col: col
    });
  };

  const renderCell = (row, col) => {
    const cellValue = board[row][col];
    const isEmpty = cellValue === '';
    
    return (
      <button
        key={`${row}-${col}`}
        onClick={() => handleCellClick(row, col)}
        className={`w-20 h-20 border-2 border-gray-400 flex items-center justify-center text-3xl font-bold transition-all ${
          isEmpty && isMyTurn && !winner 
            ? 'hover:bg-blue-100 cursor-pointer' 
            : 'cursor-not-allowed'
        } ${
          cellValue === 'X' ? 'text-blue-600' : 'text-red-600'
        }`}
        disabled={!isEmpty || !isMyTurn || winner}
      >
        {cellValue}
      </button>
    );
  };

  const getStatusMessage = () => {
    if (winner) {
      if (winner === 'draw') {
        return "🤝 It's a draw!";
      } else if (winner === currentUser.user_id) {
        return "🎉 You won!";
      } else {
        return `😔 ${opponentName} won!`;
      }
    } else if (isMyTurn) {
      return `🎯 Your turn (${mySymbol})`;
    } else {
      return `⏳ ${opponentName}'s turn (${opponentSymbol})`;
    }
  };

  return (
    <div className="tic-tac-toe-game">
      {/* Game Status */}
      <div className="game-status text-center mb-6">
        <div className="text-lg font-semibold text-gray-800 mb-2">
          {getStatusMessage()}
        </div>
        
        {/* Player Info */}
        <div className="flex justify-center space-x-6 text-sm">
          <div className={`flex items-center space-x-2 px-3 py-1 rounded ${
            currentPlayer === currentUser.user_id ? 'bg-blue-100 text-blue-700' : 'text-gray-600'
          }`}>
            <span className="font-semibold">{mySymbol}</span>
            <span>You</span>
            {currentPlayer === currentUser.user_id && <span className="animate-pulse">🎯</span>}
          </div>
          
          <div className={`flex items-center space-x-2 px-3 py-1 rounded ${
            currentPlayer === opponentId ? 'bg-red-100 text-red-700' : 'text-gray-600'
          }`}>
            <span className="font-semibold">{opponentSymbol}</span>
            <span>{opponentName}</span>
            {currentPlayer === opponentId && <span className="animate-pulse">🎯</span>}
          </div>
        </div>
      </div>

      {/* Game Board */}
      <div className="game-board flex flex-col items-center mb-6">
        <div className="grid grid-cols-3 gap-1 bg-gray-600 p-2 rounded-lg">
          {board.map((row, rowIndex) => 
            row.map((_, colIndex) => renderCell(rowIndex, colIndex))
          )}
        </div>
      </div>

      {/* Game Controls */}
      <div className="game-controls text-center">
        {winner && (
          <div className="space-y-3">
            <div className="text-lg">
              {winner === 'draw' ? '🤝' : winner === currentUser.user_id ? '🏆' : '💪'}
            </div>
            
            <div className="flex justify-center space-x-3">
              <button
                onClick={() => onMove({ type: 'play_again' })}
                className="bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 transition-colors"
              >
                🔄 Play Again
              </button>
              
              <button
                onClick={() => onMove({ type: 'end_game' })}
                className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors"
              >
                🚪 End Game
              </button>
            </div>
          </div>
        )}
        
        {!winner && (
          <div className="text-sm text-gray-600">
            💡 Click on an empty cell to place your {mySymbol}
          </div>
        )}
      </div>

      {/* Game Stats */}
      <div className="game-stats mt-6 p-4 bg-gray-50 rounded-lg">
        <div className="text-sm text-gray-600 text-center">
          <div className="flex justify-center space-x-6">
            <div>
              <span className="font-medium">Moves:</span> {gameState.moveCount || 0}
            </div>
            <div>
              <span className="font-medium">Duration:</span> {gameState.duration || '0:00'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TicTacToeGame;