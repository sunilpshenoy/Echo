import React, { useState, useEffect } from 'react';

const LudoGame = ({ gameState, onMove, currentUser }) => {
  const [board, setBoard] = useState(null);
  const [currentPlayer, setCurrentPlayer] = useState(0);
  const [diceValue, setDiceValue] = useState(null);
  const [gameStatus, setGameStatus] = useState('waiting');
  const [selectedPiece, setSelectedPiece] = useState(null);
  const [playerColors] = useState(['red', 'blue', 'green', 'yellow']);
  const [winner, setWinner] = useState(null);

  useEffect(() => {
    if (gameState) {
      setBoard(gameState.board || initializeBoard());
      setCurrentPlayer(gameState.currentPlayer || 0);
      setDiceValue(gameState.diceValue || null);
      setGameStatus(gameState.status || 'waiting');
      setWinner(gameState.winner || null);
    }
  }, [gameState]);

  const initializeBoard = () => {
    // Initialize Ludo board with 4 home areas and main track
    const board = {
      track: Array(52).fill(null), // Main circular track
      homes: {
        red: [null, null, null, null],
        blue: [null, null, null, null],
        green: [null, null, null, null],
        yellow: [null, null, null, null]
      },
      safe: {
        red: Array(6).fill(null), // Home straight
        blue: Array(6).fill(null),
        green: Array(6).fill(null),
        yellow: Array(6).fill(null)
      },
      pieces: {
        red: [{ id: 0, position: 'home', homeIndex: 0 }, { id: 1, position: 'home', homeIndex: 1 }, 
              { id: 2, position: 'home', homeIndex: 2 }, { id: 3, position: 'home', homeIndex: 3 }],
        blue: [{ id: 0, position: 'home', homeIndex: 0 }, { id: 1, position: 'home', homeIndex: 1 }, 
               { id: 2, position: 'home', homeIndex: 2 }, { id: 3, position: 'home', homeIndex: 3 }],
        green: [{ id: 0, position: 'home', homeIndex: 0 }, { id: 1, position: 'home', homeIndex: 1 }, 
                { id: 2, position: 'home', homeIndex: 2 }, { id: 3, position: 'home', homeIndex: 3 }],
        yellow: [{ id: 0, position: 'home', homeIndex: 0 }, { id: 1, position: 'home', homeIndex: 1 }, 
                 { id: 2, position: 'home', homeIndex: 2 }, { id: 3, position: 'home', homeIndex: 3 }]
      }
    };
    return board;
  };

  const rollDice = () => {
    if (gameStatus !== 'playing') return;
    
    const newDiceValue = Math.floor(Math.random() * 6) + 1;
    
    onMove({
      type: 'roll_dice',
      diceValue: newDiceValue,
      player: currentPlayer
    });
  };

  const movePiece = (color, pieceId) => {
    if (!diceValue || gameStatus !== 'playing') return;
    
    const piece = board?.pieces[color]?.find(p => p.id === pieceId);
    if (!piece) return;

    // Calculate new position based on current position and dice value
    let newPosition = piece.position;
    let newTrackIndex = piece.trackIndex;
    let newHomeIndex = piece.homeIndex;

    if (piece.position === 'home' && diceValue === 6) {
      // Move from home to start position
      newPosition = 'track';
      newTrackIndex = getStartPosition(color);
      newHomeIndex = null;
    } else if (piece.position === 'track') {
      // Move along the track
      newTrackIndex = (piece.trackIndex + diceValue) % 52;
      
      // Check if piece should enter home straight
      if (shouldEnterHomeStraight(color, newTrackIndex)) {
        newPosition = 'safe';
        newTrackIndex = null;
        newHomeIndex = 0;
      }
    } else if (piece.position === 'safe') {
      // Move in home straight
      newHomeIndex = piece.homeIndex + diceValue;
      if (newHomeIndex >= 6) {
        newPosition = 'finished';
        newHomeIndex = null;
      }
    }

    onMove({
      type: 'move_piece',
      color,
      pieceId,
      newPosition,
      newTrackIndex,
      newHomeIndex,
      diceValue
    });

    setSelectedPiece(null);
  };

  const getStartPosition = (color) => {
    const startPositions = { red: 0, blue: 13, green: 26, yellow: 39 };
    return startPositions[color];
  };

  const shouldEnterHomeStraight = (color, trackIndex) => {
    const homeStraightStarts = { red: 51, blue: 12, green: 25, yellow: 38 };
    return trackIndex === homeStraightStarts[color];
  };

  const getMovablePieces = (color) => {
    if (!board || !diceValue) return [];
    
    return board.pieces[color].filter(piece => {
      if (piece.position === 'finished') return false;
      if (piece.position === 'home') return diceValue === 6;
      if (piece.position === 'safe') return piece.homeIndex + diceValue <= 6;
      return true;
    });
  };

  const renderDice = () => {
    const diceFaces = ['⚀', '⚁', '⚂', '⚃', '⚄', '⚅'];
    
    return (
      <div className="text-center mb-6">
        <div className="text-6xl mb-2">
          {diceValue ? diceFaces[diceValue - 1] : '🎲'}
        </div>
        <button
          onClick={rollDice}
          disabled={gameStatus !== 'playing' || diceValue !== null}
          className={`px-6 py-3 rounded-lg font-semibold transition-all ${
            currentPlayer === getPlayerIndex() && gameStatus === 'playing' && !diceValue
              ? 'bg-blue-500 text-white hover:bg-blue-600'
              : 'bg-gray-300 text-gray-600 cursor-not-allowed'
          }`}
        >
          {diceValue ? 'Move a piece' : 'Roll Dice'}
        </button>
      </div>
    );
  };

  const getPlayerIndex = () => {
    // Get current user's player index
    return gameState?.playerOrder?.indexOf(currentUser.user_id) || 0;
  };

  const renderBoard = () => {
    if (!board) return null;

    return (
      <div className="ludo-board bg-white rounded-lg shadow-lg p-4 max-w-lg mx-auto">
        {/* Simplified board representation */}
        <div className="grid grid-cols-4 gap-2 mb-4">
          {playerColors.map((color, index) => (
            <div key={color} className={`home-area bg-${color}-100 border-2 border-${color}-300 rounded-lg p-3`}>
              <div className={`text-center font-bold text-${color}-700 mb-2`}>
                {color.toUpperCase()}
              </div>
              <div className="grid grid-cols-2 gap-1">
                {board.pieces[color].map((piece, pieceIndex) => {
                  const isMovable = getMovablePieces(color).includes(piece);
                  const isSelected = selectedPiece?.color === color && selectedPiece?.pieceId === piece.id;
                  
                  return (
                    <button
                      key={piece.id}
                      onClick={() => {
                        if (currentPlayer === getPlayerIndex() && isMovable) {
                          if (isSelected) {
                            movePiece(color, piece.id);
                          } else {
                            setSelectedPiece({ color, pieceId: piece.id });
                          }
                        }
                      }}
                      disabled={!isMovable || currentPlayer !== getPlayerIndex()}
                      className={`w-8 h-8 rounded-full border-2 transition-all ${
                        piece.position === 'finished' 
                          ? `bg-${color}-600 border-${color}-700 text-white`
                          : piece.position === 'home'
                          ? `bg-${color}-300 border-${color}-400`
                          : `bg-${color}-500 border-${color}-600`
                      } ${isSelected ? 'ring-2 ring-yellow-400' : ''} ${
                        isMovable ? 'cursor-pointer hover:scale-110' : 'cursor-not-allowed opacity-60'
                      }`}
                    >
                      {piece.position === 'finished' ? '🏁' : '●'}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Track representation */}
        <div className="track-area bg-gray-100 rounded-lg p-4">
          <div className="text-center text-sm text-gray-600 mb-2">Main Track</div>
          <div className="flex flex-wrap justify-center gap-1">
            {Array(52).fill(null).map((_, index) => {
              const piecesHere = [];
              Object.entries(board.pieces).forEach(([color, pieces]) => {
                pieces.forEach(piece => {
                  if (piece.position === 'track' && piece.trackIndex === index) {
                    piecesHere.push({ color, piece });
                  }
                });
              });

              return (
                <div
                  key={index}
                  className={`w-6 h-6 border border-gray-300 text-xs flex items-center justify-center ${
                    [0, 13, 26, 39].includes(index) ? 'bg-yellow-200' : 'bg-white'
                  }`}
                >
                  {piecesHere.length > 0 && (
                    <div className={`w-3 h-3 rounded-full bg-${piecesHere[0].color}-500`}></div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  const getStatusMessage = () => {
    if (gameStatus === 'waiting') return '⏳ Waiting for players...';
    if (winner) return `🎉 ${playerColors[winner]} wins!`;
    
    const currentPlayerColor = playerColors[currentPlayer];
    const isMyTurn = currentPlayer === getPlayerIndex();
    
    return `🎯 ${currentPlayerColor.toUpperCase()}'s turn ${isMyTurn ? '(You)' : ''}`;
  };

  return (
    <div className="ludo-game text-center">
      <div className="mb-6">
        <h3 className="text-xl font-bold text-gray-800 mb-2">🎲 Ludo</h3>
        <div className="text-lg text-gray-600">{getStatusMessage()}</div>
      </div>

      {/* Dice Section */}
      {renderDice()}

      {/* Game Board */}
      {renderBoard()}

      {/* Game Controls */}
      <div className="mt-6 flex justify-center space-x-4">
        <button
          onClick={() => onMove({ type: 'restart' })}
          className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors"
        >
          🔄 New Game
        </button>
        
        {gameState?.spectators?.length > 0 && (
          <div className="text-sm text-gray-500 flex items-center">
            👥 {gameState.spectators.length} watching
          </div>
        )}
      </div>

      {/* Player Info */}
      {gameState?.players && (
        <div className="mt-6 bg-gray-50 rounded-lg p-4">
          <h4 className="font-semibold text-gray-700 mb-2">Players</h4>
          <div className="grid grid-cols-2 gap-2">
            {gameState.players.map((player, index) => (
              <div key={player.id} className="flex items-center space-x-2">
                <div className={`w-4 h-4 rounded-full bg-${playerColors[index]}-500`}></div>
                <span className="text-sm">{player.name}</span>
                {currentPlayer === index && <span className="text-xs">👑</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Game Rules */}
      <div className="mt-4 text-xs text-gray-500 bg-blue-50 rounded-lg p-3">
        <strong>How to play:</strong> Roll a 6 to get pieces out of home. Get all 4 pieces to the finish line first to win!
      </div>
    </div>
  );
};

export default LudoGame;