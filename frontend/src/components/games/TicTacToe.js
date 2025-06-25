import React, { useState, useEffect } from 'react';

const TicTacToe = ({ user, token, activeChat, onClose, onSendMessage }) => {
  const [board, setBoard] = useState(Array(9).fill(null));
  const [currentPlayer, setCurrentPlayer] = useState('X');
  const [gameStatus, setGameStatus] = useState('active');
  const [playerSymbol, setPlayerSymbol] = useState('X');
  const [isPlayerTurn, setIsPlayerTurn] = useState(true);
  const [scores, setScores] = useState({ X: 0, O: 0, draws: 0 });

  const winningLines = [
    [0, 1, 2], [3, 4, 5], [6, 7, 8], // Rows
    [0, 3, 6], [1, 4, 7], [2, 5, 8], // Columns
    [0, 4, 8], [2, 4, 6] // Diagonals
  ];

  const checkWinner = (squares) => {
    for (let line of winningLines) {
      const [a, b, c] = line;
      if (squares[a] && squares[a] === squares[b] && squares[a] === squares[c]) {
        return squares[a];
      }
    }
    return null;
  };

  const checkDraw = (squares) => {
    return squares.every(square => square !== null);
  };

  const handleSquareClick = (index) => {
    if (!isPlayerTurn || board[index] || gameStatus !== 'active') return;

    const newBoard = [...board];
    newBoard[index] = currentPlayer;
    setBoard(newBoard);

    const winner = checkWinner(newBoard);
    const isDraw = checkDraw(newBoard);

    if (winner) {
      setGameStatus(`${winner}_wins`);
      setScores(prev => ({
        ...prev,
        [winner]: prev[winner] + 1
      }));
      onSendMessage(`⚡ Tic-Tac-Toe: ${winner} wins! 🎉`, 'tictactoe_win', {
        winner,
        board: newBoard,
        finalMove: index
      });
    } else if (isDraw) {
      setGameStatus('draw');
      setScores(prev => ({
        ...prev,
        draws: prev.draws + 1
      }));
      onSendMessage(`⚡ Tic-Tac-Toe: It's a draw! 🤝`, 'tictactoe_draw', {
        board: newBoard
      });
    } else {
      const nextPlayer = currentPlayer === 'X' ? 'O' : 'X';
      setCurrentPlayer(nextPlayer);
      setIsPlayerTurn(nextPlayer === playerSymbol);
      
      onSendMessage(`⚡ Tic-Tac-Toe: ${currentPlayer} played position ${index + 1}`, 'tictactoe_move', {
        move: index,
        player: currentPlayer,
        board: newBoard,
        nextPlayer: nextPlayer
      });
    }
  };

  const resetGame = () => {
    setBoard(Array(9).fill(null));
    setCurrentPlayer('X');
    setGameStatus('active');
    setIsPlayerTurn(playerSymbol === 'X');
    onSendMessage(`⚡ Tic-Tac-Toe: New game started! ${user.username} is ${playerSymbol}`, 'tictactoe_reset');
  };

  const switchSides = () => {
    const newSymbol = playerSymbol === 'X' ? 'O' : 'X';
    setPlayerSymbol(newSymbol);
    setIsPlayerTurn(newSymbol === currentPlayer);
  };

  const getSquareDisplay = (value, index) => {
    if (!value) return '';
    
    if (value === 'X') {
      return <span className="text-blue-600 text-4xl font-bold">✕</span>;
    } else {
      return <span className="text-red-600 text-4xl font-bold">◯</span>;
    }
  };

  const getStatusMessage = () => {
    if (gameStatus === 'X_wins') return '🎉 X Wins!';
    if (gameStatus === 'O_wins') return '🎉 O Wins!';
    if (gameStatus === 'draw') return '🤝 It\'s a Draw!';
    if (!isPlayerTurn) return `⏳ Waiting for opponent (${currentPlayer})'s turn`;
    return `Your turn (${currentPlayer})`;
  };

  const getStatusColor = () => {
    if (gameStatus.includes('wins')) return 'text-green-600';
    if (gameStatus === 'draw') return 'text-yellow-600';
    if (!isPlayerTurn) return 'text-orange-600';
    return 'text-blue-600';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">⚡ Tic-Tac-Toe</h2>
            <p className={`font-semibold ${getStatusColor()}`}>
              {getStatusMessage()}
            </p>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={resetGame}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              New Game
            </button>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 p-2"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Player Info */}
        <div className="flex items-center justify-between mb-6 p-4 bg-gray-50 rounded-lg">
          <div className="text-center">
            <div className="text-lg font-semibold text-gray-900">{user.username}</div>
            <div className={`text-2xl font-bold ${playerSymbol === 'X' ? 'text-blue-600' : 'text-red-600'}`}>
              {playerSymbol === 'X' ? '✕' : '◯'}
            </div>
          </div>
          <div className="text-center">
            <button
              onClick={switchSides}
              className="bg-purple-100 text-purple-700 px-3 py-2 rounded-lg hover:bg-purple-200 transition-colors text-sm"
            >
              Switch Sides
            </button>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-gray-900">Opponent</div>
            <div className={`text-2xl font-bold ${playerSymbol === 'X' ? 'text-red-600' : 'text-blue-600'}`}>
              {playerSymbol === 'X' ? '◯' : '✕'}
            </div>
          </div>
        </div>

        {/* Game Board */}
        <div className="flex justify-center mb-6">
          <div className="grid grid-cols-3 gap-2 bg-gray-800 p-4 rounded-xl">
            {board.map((square, index) => (
              <button
                key={index}
                onClick={() => handleSquareClick(index)}
                disabled={!isPlayerTurn || square || gameStatus !== 'active'}
                className={`w-20 h-20 bg-white rounded-lg border-2 border-gray-200 
                  flex items-center justify-center transition-all duration-200
                  ${(!isPlayerTurn || square || gameStatus !== 'active') 
                    ? 'cursor-not-allowed opacity-50' 
                    : 'hover:bg-gray-50 hover:border-blue-300 cursor-pointer'
                  }
                  ${square ? 'bg-gray-50' : ''}
                `}
              >
                {getSquareDisplay(square, index)}
              </button>
            ))}
          </div>
        </div>

        {/* Scores */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{scores.X}</div>
            <div className="text-sm text-blue-800">X Wins</div>
          </div>
          <div className="text-center p-3 bg-yellow-50 rounded-lg">
            <div className="text-2xl font-bold text-yellow-600">{scores.draws}</div>
            <div className="text-sm text-yellow-800">Draws</div>
          </div>
          <div className="text-center p-3 bg-red-50 rounded-lg">
            <div className="text-2xl font-bold text-red-600">{scores.O}</div>
            <div className="text-sm text-red-800">O Wins</div>
          </div>
        </div>

        {/* Game Rules */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-2">How to Play</h3>
          <ul className="text-sm text-gray-700 space-y-1">
            <li>• Get three in a row (horizontal, vertical, or diagonal) to win</li>
            <li>• Take turns with your opponent</li>
            <li>• Moves are shared in real-time through chat</li>
            <li>• Click "Switch Sides" to change your symbol</li>
          </ul>
        </div>

        {/* Quick Actions */}
        {gameStatus !== 'active' && (
          <div className="mt-4 flex space-x-3">
            <button
              onClick={resetGame}
              className="flex-1 bg-green-600 text-white py-3 px-4 rounded-lg hover:bg-green-700 transition-colors font-medium"
            >
              🎮 Play Again
            </button>
            <button
              onClick={switchSides}
              className="flex-1 bg-purple-600 text-white py-3 px-4 rounded-lg hover:bg-purple-700 transition-colors font-medium"
            >
              🔄 Switch Sides
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default TicTacToe;