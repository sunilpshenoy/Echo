import React, { useState, useEffect } from 'react';

const ChessGame = ({ user, token, activeChat, onClose, onSendMessage }) => {
  const [board, setBoard] = useState(initializeBoard());
  const [currentPlayer, setCurrentPlayer] = useState('white');
  const [selectedSquare, setSelectedSquare] = useState(null);
  const [gameStatus, setGameStatus] = useState('active');
  const [moveHistory, setMoveHistory] = useState([]);
  const [isPlayerTurn, setIsPlayerTurn] = useState(true);

  function initializeBoard() {
    const initialBoard = [
      ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
      ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
      [null, null, null, null, null, null, null, null],
      [null, null, null, null, null, null, null, null],
      [null, null, null, null, null, null, null, null],
      [null, null, null, null, null, null, null, null],
      ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
      ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
    ];
    return initialBoard;
  }

  const pieceSymbols = {
    'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
  };

  const isValidMove = (fromRow, fromCol, toRow, toCol) => {
    const piece = board[fromRow][fromCol];
    if (!piece) return false;

    const isWhitePiece = piece === piece.toUpperCase();
    const isCurrentPlayerPiece = (currentPlayer === 'white') === isWhitePiece;
    
    if (!isCurrentPlayerPiece) return false;

    // Basic bounds checking
    if (toRow < 0 || toRow > 7 || toCol < 0 || toCol > 7) return false;

    // Can't capture own piece
    const targetPiece = board[toRow][toCol];
    if (targetPiece) {
      const isTargetWhite = targetPiece === targetPiece.toUpperCase();
      if (isWhitePiece === isTargetWhite) return false;
    }

    // Piece-specific movement logic
    const pieceLower = piece.toLowerCase();
    switch (pieceLower) {
      case 'p': // Pawn
        return isValidPawnMove(fromRow, fromCol, toRow, toCol, isWhitePiece);
      case 'r': // Rook
        return isValidRookMove(fromRow, fromCol, toRow, toCol);
      case 'n': // Knight
        return isValidKnightMove(fromRow, fromCol, toRow, toCol);
      case 'b': // Bishop
        return isValidBishopMove(fromRow, fromCol, toRow, toCol);
      case 'q': // Queen
        return isValidQueenMove(fromRow, fromCol, toRow, toCol);
      case 'k': // King
        return isValidKingMove(fromRow, fromCol, toRow, toCol);
      default:
        return false;
    }
  };

  const isValidPawnMove = (fromRow, fromCol, toRow, toCol, isWhite) => {
    const direction = isWhite ? -1 : 1;
    const rowDiff = toRow - fromRow;
    const colDiff = Math.abs(toCol - fromCol);

    // Forward move
    if (colDiff === 0 && !board[toRow][toCol]) {
      if (rowDiff === direction) return true;
      if ((isWhite ? fromRow === 6 : fromRow === 1) && rowDiff === 2 * direction) return true;
    }

    // Diagonal capture
    if (colDiff === 1 && rowDiff === direction && board[toRow][toCol]) {
      return true;
    }

    return false;
  };

  const isValidRookMove = (fromRow, fromCol, toRow, toCol) => {
    if (fromRow !== toRow && fromCol !== toCol) return false;
    return isPathClear(fromRow, fromCol, toRow, toCol);
  };

  const isValidBishopMove = (fromRow, fromCol, toRow, toCol) => {
    if (Math.abs(fromRow - toRow) !== Math.abs(fromCol - toCol)) return false;
    return isPathClear(fromRow, fromCol, toRow, toCol);
  };

  const isValidQueenMove = (fromRow, fromCol, toRow, toCol) => {
    return isValidRookMove(fromRow, fromCol, toRow, toCol) || 
           isValidBishopMove(fromRow, fromCol, toRow, toCol);
  };

  const isValidKnightMove = (fromRow, fromCol, toRow, toCol) => {
    const rowDiff = Math.abs(fromRow - toRow);
    const colDiff = Math.abs(fromCol - toCol);
    return (rowDiff === 2 && colDiff === 1) || (rowDiff === 1 && colDiff === 2);
  };

  const isValidKingMove = (fromRow, fromCol, toRow, toCol) => {
    const rowDiff = Math.abs(fromRow - toRow);
    const colDiff = Math.abs(fromCol - toCol);
    return rowDiff <= 1 && colDiff <= 1;
  };

  const isPathClear = (fromRow, fromCol, toRow, toCol) => {
    const rowDirection = toRow > fromRow ? 1 : toRow < fromRow ? -1 : 0;
    const colDirection = toCol > fromCol ? 1 : toCol < fromCol ? -1 : 0;

    let currentRow = fromRow + rowDirection;
    let currentCol = fromCol + colDirection;

    while (currentRow !== toRow || currentCol !== toCol) {
      if (board[currentRow][currentCol] !== null) return false;
      currentRow += rowDirection;
      currentCol += colDirection;
    }

    return true;
  };

  const handleSquareClick = (row, col) => {
    if (!isPlayerTurn) return;

    if (selectedSquare) {
      const [fromRow, fromCol] = selectedSquare;
      
      if (fromRow === row && fromCol === col) {
        // Deselect
        setSelectedSquare(null);
        return;
      }

      if (isValidMove(fromRow, fromCol, row, col)) {
        // Make move
        const newBoard = board.map(r => [...r]);
        const piece = newBoard[fromRow][fromCol];
        const capturedPiece = newBoard[row][col];
        
        newBoard[row][col] = piece;
        newBoard[fromRow][fromCol] = null;

        setBoard(newBoard);
        setSelectedSquare(null);
        setCurrentPlayer(currentPlayer === 'white' ? 'black' : 'white');
        setIsPlayerTurn(false);

        // Send move to chat
        const moveNotation = `${String.fromCharCode(97 + fromCol)}${8 - fromRow}-${String.fromCharCode(97 + col)}${8 - row}`;
        const moveMessage = `♛ Chess Move: ${moveNotation}${capturedPiece ? ` (captured ${pieceSymbols[capturedPiece]})` : ''}`;
        
        onSendMessage(moveMessage, 'chess_move', {
          from: [fromRow, fromCol],
          to: [row, col],
          piece: piece,
          captured: capturedPiece,
          board: newBoard
        });

        // Add to move history
        setMoveHistory(prev => [...prev, {
          move: moveNotation,
          piece: piece,
          captured: capturedPiece,
          player: currentPlayer
        }]);

        // Check for game end conditions
        checkGameEnd(newBoard);
      }
    } else {
      // Select piece
      const piece = board[row][col];
      if (piece) {
        const isWhitePiece = piece === piece.toUpperCase();
        const isCurrentPlayerPiece = (currentPlayer === 'white') === isWhitePiece;
        
        if (isCurrentPlayerPiece) {
          setSelectedSquare([row, col]);
        }
      }
    }
  };

  const checkGameEnd = (currentBoard) => {
    // Simple check - in a real implementation, you'd check for checkmate, stalemate, etc.
    const whiteKing = findKing(currentBoard, true);
    const blackKing = findKing(currentBoard, false);
    
    if (!whiteKing) {
      setGameStatus('black_wins');
    } else if (!blackKing) {
      setGameStatus('white_wins');
    }
  };

  const findKing = (currentBoard, isWhite) => {
    const kingSymbol = isWhite ? 'K' : 'k';
    for (let row = 0; row < 8; row++) {
      for (let col = 0; col < 8; col++) {
        if (currentBoard[row][col] === kingSymbol) {
          return [row, col];
        }
      }
    }
    return null;
  };

  const resetGame = () => {
    setBoard(initializeBoard());
    setCurrentPlayer('white');
    setSelectedSquare(null);
    setGameStatus('active');
    setMoveHistory([]);
    setIsPlayerTurn(true);
  };

  const surrenderGame = () => {
    setGameStatus(currentPlayer === 'white' ? 'black_wins' : 'white_wins');
    onSendMessage(`♛ ${user.username} surrendered the chess game`, 'chess_surrender');
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-5xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">♛ Chess Game</h2>
            <p className="text-gray-600">
              Current turn: <span className="font-semibold capitalize">{currentPlayer}</span>
              {!isPlayerTurn && <span className="text-orange-500 ml-2">(Waiting for opponent)</span>}
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
              onClick={surrenderGame}
              className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
            >
              Surrender
            </button>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 p-2"
            >
              ✕
            </button>
          </div>
        </div>

        <div className="flex flex-col lg:flex-row gap-6">
          {/* Chess Board */}
          <div className="flex-1">
            <div className="inline-block border-4 border-amber-800 rounded-lg overflow-hidden">
              {board.map((row, rowIndex) => (
                <div key={rowIndex} className="flex">
                  {row.map((piece, colIndex) => {
                    const isLight = (rowIndex + colIndex) % 2 === 0;
                    const isSelected = selectedSquare && 
                      selectedSquare[0] === rowIndex && selectedSquare[1] === colIndex;
                    
                    return (
                      <div
                        key={`${rowIndex}-${colIndex}`}
                        className={`w-12 h-12 flex items-center justify-center cursor-pointer text-2xl border border-amber-700 ${
                          isLight ? 'bg-amber-100' : 'bg-amber-600'
                        } ${isSelected ? 'bg-yellow-300 border-yellow-500 border-2' : ''} 
                        hover:bg-opacity-80 transition-colors`}
                        onClick={() => handleSquareClick(rowIndex, colIndex)}
                      >
                        {piece && pieceSymbols[piece]}
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>

          {/* Game Info Panel */}
          <div className="lg:w-80">
            {/* Game Status */}
            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <h3 className="font-semibold text-gray-900 mb-2">Game Status</h3>
              {gameStatus === 'active' ? (
                <div className="text-green-600 font-medium">Game in progress</div>
              ) : gameStatus === 'white_wins' ? (
                <div className="text-blue-600 font-medium">White wins!</div>
              ) : gameStatus === 'black_wins' ? (
                <div className="text-red-600 font-medium">Black wins!</div>
              ) : (
                <div className="text-gray-600 font-medium">Game ended</div>
              )}
            </div>

            {/* Move History */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-2">Move History</h3>
              <div className="max-h-60 overflow-y-auto space-y-1">
                {moveHistory.length === 0 ? (
                  <p className="text-gray-500 text-sm">No moves yet</p>
                ) : (
                  moveHistory.map((move, index) => (
                    <div key={index} className="text-sm flex items-center justify-between">
                      <span className="font-mono">{move.move}</span>
                      <span className="text-gray-500">
                        {move.captured && `captured ${pieceSymbols[move.captured]}`}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Game Instructions */}
            <div className="bg-blue-50 rounded-lg p-4 mt-4">
              <h3 className="font-semibold text-blue-900 mb-2">How to Play</h3>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Click a piece to select it</li>
                <li>• Click a valid square to move</li>
                <li>• Moves are shared with your opponent</li>
                <li>• Standard chess rules apply</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChessGame;