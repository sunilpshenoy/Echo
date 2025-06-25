import React, { useState, useEffect } from 'react';
import ChessGame from './games/ChessGame';
import TicTacToe from './games/TicTacToe';
import WordGuessGame from './games/WordGuessGame';

const GameCenter = ({ user, token, activeChat, onClose, onSendMessage }) => {
  const [selectedGame, setSelectedGame] = useState(null);
  const [gameInvites, setGameInvites] = useState([]);

  const games = [
    {
      id: 'chess',
      name: 'Chess',
      icon: '♛',
      description: 'Classic chess game with your chat partner',
      players: '2 players',
      difficulty: 'Strategic',
      color: 'from-amber-500 to-yellow-600'
    },
    {
      id: 'tictactoe',
      name: 'Tic-Tac-Toe',
      icon: '⚡',
      description: 'Quick and fun tic-tac-toe matches',
      players: '2 players',
      difficulty: 'Easy',
      color: 'from-blue-500 to-cyan-600'
    },
    {
      id: 'wordguess',
      name: 'Word Guess',
      icon: '🎯',
      description: 'Guess the mystery word before time runs out',
      players: '1-2 players',
      difficulty: 'Medium',
      color: 'from-green-500 to-emerald-600'
    },
    {
      id: 'quiz',
      name: 'Quiz Battle',
      icon: '🧠',
      description: 'Test your knowledge in various categories',
      players: '1-4 players',
      difficulty: 'Varied',
      color: 'from-purple-500 to-violet-600'
    },
    {
      id: 'memory',
      name: 'Memory Cards',
      icon: '🃏',
      description: 'Match pairs of cards to win',
      players: '1-2 players',
      difficulty: 'Medium',
      color: 'from-pink-500 to-rose-600'
    },
    {
      id: 'snake',
      name: 'Snake Race',
      icon: '🐍',
      description: 'Classic snake game with multiplayer twist',
      players: '1-2 players',
      difficulty: 'Medium',
      color: 'from-indigo-500 to-blue-600'
    }
  ];

  const sendGameInvite = (gameId) => {
    if (!activeChat) {
      alert('Select a chat to send game invite');
      return;
    }

    const invite = {
      type: 'game_invite',
      game: gameId,
      from: user.username,
      chat_id: activeChat.chat_id,
      timestamp: new Date().toISOString()
    };

    // Send as a special message
    onSendMessage(`🎮 Game Invite: ${games.find(g => g.id === gameId)?.name}\n\nClick to accept and start playing!`, 'game_invite', invite);
  };

  const startGame = (gameId) => {
    setSelectedGame(gameId);
  };

  const renderGameComponent = () => {
    const gameProps = {
      user,
      token,
      activeChat,
      onClose: () => setSelectedGame(null),
      onSendMessage
    };

    switch (selectedGame) {
      case 'chess':
        return <ChessGame {...gameProps} />;
      case 'tictactoe':
        return <TicTacToe {...gameProps} />;
      case 'wordguess':
        return <WordGuessGame {...gameProps} />;
      default:
        return null;
    }
  };

  if (selectedGame) {
    return renderGameComponent();
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-3xl font-bold text-gray-900">🎮 Game Center</h2>
            <p className="text-gray-600">Play games with your friends in real-time!</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 p-2 rounded-lg hover:bg-gray-100 transition-all"
          >
            ✕
          </button>
        </div>

        {/* Game Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {games.map(game => (
            <div
              key={game.id}
              className="bg-white border border-gray-200 rounded-xl overflow-hidden hover:shadow-lg transition-all duration-300 hover:scale-105"
            >
              <div className={`bg-gradient-to-br ${game.color} p-6 text-white`}>
                <div className="text-4xl mb-2">{game.icon}</div>
                <h3 className="text-xl font-bold">{game.name}</h3>
                <p className="text-sm opacity-90">{game.players}</p>
              </div>
              
              <div className="p-4">
                <p className="text-gray-600 text-sm mb-3">{game.description}</p>
                
                <div className="flex items-center justify-between mb-4">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    game.difficulty === 'Easy' ? 'bg-green-100 text-green-800' :
                    game.difficulty === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                    game.difficulty === 'Strategic' ? 'bg-red-100 text-red-800' :
                    'bg-purple-100 text-purple-800'
                  }`}>
                    {game.difficulty}
                  </span>
                </div>
                
                <div className="space-y-2">
                  <button
                    onClick={() => startGame(game.id)}
                    disabled={!['chess', 'tictactoe', 'wordguess'].includes(game.id)}
                    className={`w-full py-2 px-4 rounded-lg font-medium transition-colors ${
                      ['chess', 'tictactoe', 'wordguess'].includes(game.id)
                        ? `bg-gradient-to-r ${game.color} text-white hover:opacity-90`
                        : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    }`}
                  >
                    {['chess', 'tictactoe', 'wordguess'].includes(game.id) ? 'Play Now' : 'Coming Soon'}
                  </button>
                  
                  {activeChat && ['chess', 'tictactoe', 'wordguess'].includes(game.id) && (
                    <button
                      onClick={() => sendGameInvite(game.id)}
                      className="w-full py-2 px-4 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                    >
                      Invite Friend
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Game Statistics */}
        <div className="mt-8 p-4 bg-gray-50 rounded-lg">
          <h3 className="font-semibold text-gray-900 mb-3">🏆 Your Gaming Stats</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-blue-600">0</div>
              <div className="text-sm text-gray-600">Games Played</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">0</div>
              <div className="text-sm text-gray-600">Wins</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-600">0</div>
              <div className="text-sm text-gray-600">High Score</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-orange-600">0</div>
              <div className="text-sm text-gray-600">Streak</div>
            </div>
          </div>
        </div>

        {/* Quick Tips */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h3 className="font-semibold text-blue-900 mb-2">💡 Gaming Tips</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Invite friends to play multiplayer games for more fun!</li>
            <li>• Games are played in real-time using chat messages</li>
            <li>• Your game progress is automatically saved</li>
            <li>• Try different difficulty levels to improve your skills</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default GameCenter;