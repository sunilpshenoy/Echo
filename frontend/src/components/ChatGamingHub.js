import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import TicTacToeGame from './games/TicTacToe';
import WordGuessGame from './games/WordGuessGame';
import LudoGame from './games/LudoGame';
import MafiaGame from './games/MafiaGame';

// Gaming Framework Component
const ChatGamingHub = ({ 
  user, 
  token, 
  api, 
  chatId, 
  socket, 
  onSendMessage,
  chatMembers = []
}) => {
  const { t } = useTranslation();
  const [activeGame, setActiveGame] = useState(null);
  const [gameState, setGameState] = useState(null);
  const [showGameMenu, setShowGameMenu] = useState(false);
  const [gameInvitations, setGameInvitations] = useState([]);
  const [availableGames] = useState([
    {
      id: 'tic-tac-toe',
      name: 'Tic-Tac-Toe',
      icon: '⭕',
      minPlayers: 2,
      maxPlayers: 2,
      description: 'Classic 3x3 grid game',
      difficulty: 'Easy',
      duration: '2-5 minutes'
    },
    {
      id: 'word-guess',
      name: 'Word Guessing',
      icon: '🔤',
      minPlayers: 2,
      maxPlayers: 8,
      description: 'Guess the word together',
      difficulty: 'Medium',
      duration: '5-10 minutes'
    },
    {
      id: 'ludo',
      name: 'Ludo',
      icon: '🎲',
      minPlayers: 2,
      maxPlayers: 4,
      description: 'Classic board race game',
      difficulty: 'Medium',
      duration: '15-30 minutes'
    },
    {
      id: 'mafia',
      name: 'Mafia',
      icon: '🕵️',
      minPlayers: 5,
      maxPlayers: 12,
      description: 'Social deduction game',
      difficulty: 'Hard',
      duration: '20-45 minutes'
    }
  ]);

  // Initialize gaming WebSocket listeners
  useEffect(() => {
    if (socket) {
      socket.on('game_invitation', handleGameInvitation);
      socket.on('game_started', handleGameStarted);
      socket.on('game_update', handleGameUpdate);
      socket.on('game_ended', handleGameEnded);
      
      return () => {
        socket.off('game_invitation', handleGameInvitation);
        socket.off('game_started', handleGameStarted);
        socket.off('game_update', handleGameUpdate);
        socket.off('game_ended', handleGameEnded);
      };
    }
  }, [socket]);

  const handleGameInvitation = (invitation) => {
    setGameInvitations(prev => [...prev, invitation]);
  };

  const handleGameStarted = (gameData) => {
    setActiveGame(gameData.gameType);
    setGameState(gameData.state);
    setShowGameMenu(false);
  };

  const handleGameUpdate = (update) => {
    setGameState(update.state);
  };

  const handleGameEnded = (result) => {
    // Send game result message to chat
    onSendMessage({
      type: 'game_result',
      content: `🎮 Game ended! ${result.message}`,
      gameResult: result
    });
    
    setActiveGame(null);
    setGameState(null);
  };

  const startGame = async (gameId) => {
    try {
      const response = await fetch(`${api}/games/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          gameType: gameId,
          chatId: chatId,
          players: [user.user_id]
        })
      });

      if (response.ok) {
        const gameData = await response.json();
        
        // Send game invitation message to chat
        onSendMessage({
          type: 'game_invitation',
          content: `🎮 ${user.display_name || user.username} started a ${availableGames.find(g => g.id === gameId)?.name} game! Click to join.`,
          gameInvitation: {
            gameId: gameData.gameId,
            gameType: gameId,
            creator: user.user_id,
            chatId: chatId
          }
        });
      }
    } catch (error) {
      console.error('Failed to start game:', error);
      alert('Failed to start game. Please try again.');
    }
  };

  const joinGame = async (gameId) => {
    try {
      const response = await fetch(`${api}/games/${gameId}/join`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          playerId: user.user_id
        })
      });

      if (response.ok) {
        // Game will start via WebSocket event
        console.log('Successfully joined game');
      }
    } catch (error) {
      console.error('Failed to join game:', error);
      alert('Failed to join game. Please try again.');
    }
  };

  const makeGameMove = async (move) => {
    try {
      const response = await fetch(`${api}/games/${gameState.gameId}/move`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          playerId: user.user_id,
          move: move
        })
      });

      if (response.ok) {
        // Game state will update via WebSocket
        console.log('Move made successfully');
      }
    } catch (error) {
      console.error('Failed to make game move:', error);
      alert('Invalid move. Please try again.');
    }
  };

  const renderActiveGame = () => {
    if (!activeGame || !gameState) return null;

    switch (activeGame) {
      case 'tic-tac-toe':
        return <TicTacToeGame gameState={gameState} onMove={makeGameMove} currentUser={user} />;
      case 'word-guess':
        return <WordGuessGame gameState={gameState} onMove={makeGameMove} currentUser={user} />;
      case 'ludo':
        return <LudoGame gameState={gameState} onMove={makeGameMove} currentUser={user} />;
      case 'mafia':
        return <MafiaGame gameState={gameState} onMove={makeGameMove} currentUser={user} />;
      default:
        return <div className="text-center p-4">🎮 Game not implemented yet</div>;
    }
  };

  return (
    <div className="gaming-hub">
      {/* Game Menu Toggle */}
      <button
        onClick={() => setShowGameMenu(!showGameMenu)}
        className="game-menu-toggle bg-purple-500 text-white p-2 rounded-lg hover:bg-purple-600 transition-colors"
        title="Gaming Hub"
      >
        🎮
      </button>

      {/* Game Selection Menu */}
      {showGameMenu && (
        <div className="game-menu absolute bottom-12 right-0 bg-white border border-gray-200 rounded-lg shadow-lg p-4 w-80 max-h-96 overflow-y-auto z-10">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-bold text-gray-900">🎮 Gaming Hub</h3>
            <button
              onClick={() => setShowGameMenu(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          <div className="space-y-3">
            {availableGames.map(game => {
              const canPlay = chatMembers.length >= game.minPlayers;
              
              return (
                <div
                  key={game.id}
                  className={`game-card border rounded-lg p-3 ${
                    canPlay 
                      ? 'border-purple-200 hover:border-purple-400 cursor-pointer hover:bg-purple-50' 
                      : 'border-gray-200 bg-gray-50 cursor-not-allowed opacity-60'
                  }`}
                  onClick={() => canPlay && startGame(game.id)}
                >
                  <div className="flex items-start space-x-3">
                    <div className="text-2xl">{game.icon}</div>
                    <div className="flex-1">
                      <div className="font-semibold text-gray-900">{game.name}</div>
                      <div className="text-sm text-gray-600">{game.description}</div>
                      <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                        <span>👥 {game.minPlayers}-{game.maxPlayers} players</span>
                        <span>⏱️ {game.duration}</span>
                        <span className={`px-2 py-1 rounded ${
                          game.difficulty === 'Easy' ? 'bg-green-100 text-green-700' :
                          game.difficulty === 'Medium' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-red-100 text-red-700'
                        }`}>
                          {game.difficulty}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  {!canPlay && (
                    <div className="text-xs text-red-500 mt-2">
                      Need at least {game.minPlayers} members to play
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
            <div className="text-sm text-blue-700">
              <strong>💡 Pro Tips:</strong>
              <ul className="mt-1 space-y-1 text-xs">
                <li>• Games are played directly in chat</li>
                <li>• All chat members can see the game</li>
                <li>• Use temporary chats for game sessions</li>
                <li>• Invite friends to reach minimum players</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Active Game Interface */}
      {activeGame && (
        <div className="active-game-container fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-gray-900 flex items-center">
                  {availableGames.find(g => g.id === activeGame)?.icon} {availableGames.find(g => g.id === activeGame)?.name}
                </h2>
                <button
                  onClick={() => {
                    setActiveGame(null);
                    setGameState(null);
                  }}
                  className="text-gray-500 hover:text-gray-700 text-xl"
                >
                  ✕
                </button>
              </div>
              
              {renderActiveGame()}
            </div>
          </div>
        </div>
      )}

      {/* Game Invitations */}
      {gameInvitations.length > 0 && (
        <div className="game-invitations absolute bottom-12 left-0 bg-green-50 border border-green-200 rounded-lg p-3 shadow-lg">
          <div className="text-sm font-medium text-green-800 mb-2">
            🎮 Game Invitations
          </div>
          {gameInvitations.map((invitation, index) => (
            <div key={index} className="flex items-center justify-between space-x-2 mb-2">
              <span className="text-sm text-green-700">
                {availableGames.find(g => g.id === invitation.gameType)?.name}
              </span>
              <div className="space-x-1">
                <button
                  onClick={() => joinGame(invitation.gameId)}
                  className="bg-green-500 text-white px-2 py-1 rounded text-xs hover:bg-green-600"
                >
                  Join
                </button>
                <button
                  onClick={() => setGameInvitations(prev => prev.filter((_, i) => i !== index))}
                  className="bg-gray-500 text-white px-2 py-1 rounded text-xs hover:bg-gray-600"
                >
                  Dismiss
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ChatGamingHub;