import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import io from 'socket.io-client';
import TicTacToeGame from './games/TicTacToeGame';
import WordGuessGame from './games/WordGuessGame';
import LudoGame from './games/LudoGame';
import MafiaGame from './games/MafiaGame';

const GamesInterface = ({ user, token, api }) => {
  const { t } = useTranslation();
  const [activeGame, setActiveGame] = useState(null);
  const [gameState, setGameState] = useState(null);
  const [gameRooms, setGameRooms] = useState([]);
  const [currentRoom, setCurrentRoom] = useState(null);
  const [showCreateRoom, setShowCreateRoom] = useState(false);
  const [newRoomName, setNewRoomName] = useState('');
  const [selectedGameType, setSelectedGameType] = useState('tic-tac-toe');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [socket, setSocket] = useState(null);
  const [gameInvitations, setGameInvitations] = useState([]);
  const [searchFilter, setSearchFilter] = useState('');
  const socketRef = useRef(null);

  const availableGames = [
    {
      id: 'tic-tac-toe',
      name: 'Tic-Tac-Toe',
      icon: '⭕',
      minPlayers: 2,
      maxPlayers: 2,
      description: 'Classic 3x3 grid game',
      difficulty: 'Easy',
      duration: '2-5 minutes',
      category: 'Strategy'
    },
    {
      id: 'word-guess',
      name: 'Word Guessing',
      icon: '🔤',
      minPlayers: 2,
      maxPlayers: 8,
      description: 'Guess the word together',
      difficulty: 'Medium',
      duration: '5-10 minutes',
      category: 'Word'
    },
    {
      id: 'ludo',
      name: 'Ludo',
      icon: '🎲',
      minPlayers: 2,
      maxPlayers: 4,
      description: 'Classic board race game',
      difficulty: 'Medium',
      duration: '15-30 minutes',
      category: 'Board'
    },
    {
      id: 'mafia',
      name: 'Mafia',
      icon: '🕵️',
      minPlayers: 5,
      maxPlayers: 12,
      description: 'Social deduction game',
      difficulty: 'Hard',
      duration: '20-45 minutes',
      category: 'Social'
    }
  ];

  // Initialize WebSocket connection
  useEffect(() => {
    const initSocket = () => {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const newSocket = io(backendUrl, {
        auth: {
          token: token
        },
        transports: ['websocket']
      });

      newSocket.on('connect', () => {
        console.log('🎮 Games WebSocket connected');
        setError('');
      });

      newSocket.on('disconnect', () => {
        console.log('🎮 Games WebSocket disconnected');
      });

      newSocket.on('connect_error', (error) => {
        console.error('🎮 Games WebSocket connection error:', error);
        setError('Failed to connect to game server');
      });

      // Game-specific events
      newSocket.on('game_rooms_updated', handleGameRoomsUpdate);
      newSocket.on('game_started', handleGameStarted);
      newSocket.on('game_state_update', handleGameStateUpdate);
      newSocket.on('game_ended', handleGameEnded);
      newSocket.on('game_invitation', handleGameInvitation);
      newSocket.on('room_joined', handleRoomJoined);
      newSocket.on('player_joined', handlePlayerJoined);
      newSocket.on('player_left', handlePlayerLeft);

      setSocket(newSocket);
      socketRef.current = newSocket;

      return newSocket;
    };

    if (token) {
      const socketConnection = initSocket();
      
      // Fetch initial game rooms
      fetchGameRooms();

      return () => {
        if (socketConnection) {
          socketConnection.disconnect();
        }
      };
    }
  }, [token]);

  const fetchGameRooms = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${api}/games/rooms`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const rooms = await response.json();
        setGameRooms(rooms);
      } else {
        setError('Failed to fetch game rooms');
      }
    } catch (error) {
      console.error('Failed to fetch game rooms:', error);
      setError('Failed to connect to game server');
    } finally {
      setIsLoading(false);
    }
  };

  // Socket event handlers
  const handleGameRoomsUpdate = (rooms) => {
    setGameRooms(rooms);
  };

  const handleGameStarted = (gameData) => {
    setActiveGame(gameData.gameType);
    setGameState(gameData.state);
    setCurrentRoom(gameData.roomId);
  };

  const handleGameStateUpdate = (update) => {
    setGameState(update);
  };

  const handleGameEnded = (result) => {
    setActiveGame(null);
    setGameState(null);
    // Show result notification
    alert(`🎮 Game ended! ${result.message}`);
  };

  const handleGameInvitation = (invitation) => {
    setGameInvitations(prev => [...prev, invitation]);
  };

  const handleRoomJoined = (roomData) => {
    setCurrentRoom(roomData.roomId);
  };

  const handlePlayerJoined = (data) => {
    // Update room data when player joins
    fetchGameRooms();
  };

  const handlePlayerLeft = (data) => {
    // Update room data when player leaves
    fetchGameRooms();
  };

  const createGameRoom = async () => {
    if (!newRoomName.trim()) {
      setError('Please enter a room name');
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`${api}/games/rooms/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: newRoomName,
          gameType: selectedGameType,
          maxPlayers: availableGames.find(g => g.id === selectedGameType)?.maxPlayers || 4,
          isPrivate: false
        })
      });

      if (response.ok) {
        const room = await response.json();
        setShowCreateRoom(false);
        setNewRoomName('');
        setCurrentRoom(room.roomId);
        // Join the room automatically
        joinGameRoom(room.roomId);
      } else {
        setError('Failed to create game room');
      }
    } catch (error) {
      console.error('Failed to create game room:', error);
      setError('Failed to create game room');
    } finally {
      setIsLoading(false);
    }
  };

  const joinGameRoom = async (roomId) => {
    setIsLoading(true);
    try {
      const response = await fetch(`${api}/games/rooms/${roomId}/join`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const roomData = await response.json();
        setCurrentRoom(roomId);
        
        // Emit socket event to join room
        if (socket) {
          socket.emit('join_game_room', { roomId });
        }
      } else {
        setError('Failed to join game room');
      }
    } catch (error) {
      console.error('Failed to join game room:', error);
      setError('Failed to join game room');
    } finally {
      setIsLoading(false);
    }
  };

  const leaveGameRoom = () => {
    if (currentRoom && socket) {
      socket.emit('leave_game_room', { roomId: currentRoom });
      setCurrentRoom(null);
      setActiveGame(null);
      setGameState(null);
    }
  };

  const startGame = async () => {
    if (!currentRoom) return;

    try {
      const response = await fetch(`${api}/games/rooms/${currentRoom}/start`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        // Game will start via WebSocket event
        console.log('Game starting...');
      } else {
        setError('Failed to start game');
      }
    } catch (error) {
      console.error('Failed to start game:', error);
      setError('Failed to start game');
    }
  };

  const makeGameMove = (move) => {
    if (socket && currentRoom) {
      socket.emit('game_move', {
        roomId: currentRoom,
        move,
        playerId: user.user_id
      });
    }
  };

  const renderActiveGame = () => {
    if (!activeGame || !gameState) return null;

    const gameProps = {
      gameState,
      onMove: makeGameMove,
      currentUser: user
    };

    switch (activeGame) {
      case 'tic-tac-toe':
        return <TicTacToeGame {...gameProps} />;
      case 'word-guess':
        return <WordGuessGame {...gameProps} />;
      case 'ludo':
        return <LudoGame {...gameProps} />;
      case 'mafia':
        return <MafiaGame {...gameProps} />;
      default:
        return <div className="text-center p-4">🎮 Game not implemented yet</div>;
    }
  };

  const filteredRooms = gameRooms.filter(room => 
    room.name.toLowerCase().includes(searchFilter.toLowerCase()) ||
    room.gameType.toLowerCase().includes(searchFilter.toLowerCase())
  );

  const filteredGames = availableGames.filter(game =>
    game.name.toLowerCase().includes(searchFilter.toLowerCase()) ||
    game.category.toLowerCase().includes(searchFilter.toLowerCase())
  );

  if (activeGame) {
    return (
      <div className="games-active-session h-full flex flex-col">
        <div className="flex-shrink-0 bg-white border-b p-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold text-gray-900 flex items-center">
              🎮 {availableGames.find(g => g.id === activeGame)?.name}
            </h2>
            <button
              onClick={leaveGameRoom}
              className="bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 transition-colors"
            >
              Leave Game
            </button>
          </div>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4">
          {renderActiveGame()}
        </div>
      </div>
    );
  }

  return (
    <div className="games-interface h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="flex-shrink-0 bg-white border-b p-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-gray-900 flex items-center">
            🎮 Games Hub
          </h2>
          <button
            onClick={() => setShowCreateRoom(true)}
            className="bg-purple-500 text-white px-4 py-2 rounded-lg hover:bg-purple-600 transition-colors flex items-center space-x-2"
          >
            <span>➕</span>
            <span>Create Room</span>
          </button>
        </div>

        {/* Search */}
        <div className="relative">
          <input
            type="text"
            placeholder="Search games or rooms..."
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
          <div className="absolute left-3 top-2.5 text-gray-400">🔍</div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="flex-shrink-0 bg-red-50 border-l-4 border-red-500 p-4">
          <div className="text-red-700">{error}</div>
          <button
            onClick={() => setError('')}
            className="text-red-500 hover:text-red-700 ml-2"
          >
            ✕
          </button>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {/* Game Invitations */}
        {gameInvitations.length > 0 && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
            <h3 className="font-semibold text-green-800 mb-3">🎮 Game Invitations</h3>
            <div className="space-y-2">
              {gameInvitations.map((invitation, index) => (
                <div key={index} className="flex items-center justify-between bg-white rounded-lg p-3">
                  <div>
                    <div className="font-medium">{invitation.gameName}</div>
                    <div className="text-sm text-gray-600">From: {invitation.senderName}</div>
                  </div>
                  <div className="space-x-2">
                    <button
                      onClick={() => joinGameRoom(invitation.roomId)}
                      className="bg-green-500 text-white px-3 py-1 rounded hover:bg-green-600"
                    >
                      Accept
                    </button>
                    <button
                      onClick={() => setGameInvitations(prev => prev.filter((_, i) => i !== index))}
                      className="bg-gray-500 text-white px-3 py-1 rounded hover:bg-gray-600"
                    >
                      Decline
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Active Game Rooms */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
            🏠 Active Game Rooms ({filteredRooms.length})
          </h3>
          
          {isLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500 mx-auto"></div>
              <div className="text-gray-600 mt-2">Loading...</div>
            </div>
          ) : filteredRooms.length === 0 ? (
            <div className="text-center py-8 bg-white rounded-lg border-2 border-dashed border-gray-300">
              <div className="text-4xl mb-2">🎯</div>
              <div className="text-gray-600">No game rooms found</div>
              <div className="text-sm text-gray-500 mt-1">Create a room to start playing!</div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredRooms.map(room => {
                const gameInfo = availableGames.find(g => g.id === room.gameType);
                const isFull = room.currentPlayers >= room.maxPlayers;
                
                return (
                  <div
                    key={room.roomId}
                    className={`room-card bg-white border rounded-lg p-4 transition-all ${
                      isFull ? 'border-gray-300 opacity-60' : 'border-gray-300 hover:border-purple-500 hover:shadow-md cursor-pointer'
                    }`}
                    onClick={() => !isFull && joinGameRoom(room.roomId)}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <div className="font-semibold text-gray-900">{room.name}</div>
                        <div className="text-sm text-gray-600 flex items-center mt-1">
                          <span className="text-lg mr-1">{gameInfo?.icon}</span>
                          {gameInfo?.name}
                        </div>
                      </div>
                      <div className={`px-2 py-1 rounded text-xs font-medium ${
                        room.status === 'waiting' ? 'bg-yellow-100 text-yellow-700' :
                        room.status === 'playing' ? 'bg-green-100 text-green-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {room.status}
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <div className="flex items-center space-x-4">
                        <span>👥 {room.currentPlayers}/{room.maxPlayers}</span>
                        <span>⏱️ {gameInfo?.duration}</span>
                        <span className={`px-2 py-1 rounded text-xs ${
                          gameInfo?.difficulty === 'Easy' ? 'bg-green-100 text-green-700' :
                          gameInfo?.difficulty === 'Medium' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-red-100 text-red-700'
                        }`}>
                          {gameInfo?.difficulty}
                        </span>
                      </div>
                    </div>
                    
                    {isFull && (
                      <div className="text-xs text-red-500 mt-2">Room is full</div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Available Games */}
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
            🎲 Available Games
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredGames.map(game => (
              <div
                key={game.id}
                className="game-card bg-white border border-gray-300 rounded-lg p-4 hover:border-purple-500 hover:shadow-md transition-all cursor-pointer"
                onClick={() => {
                  setSelectedGameType(game.id);
                  setShowCreateRoom(true);
                }}
              >
                <div className="flex items-start space-x-3">
                  <div className="text-3xl">{game.icon}</div>
                  <div className="flex-1">
                    <div className="font-semibold text-gray-900">{game.name}</div>
                    <div className="text-sm text-gray-600 mb-2">{game.description}</div>
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <span>👥 {game.minPlayers}-{game.maxPlayers} players</span>
                      <span>⏱️ {game.duration}</span>
                      <span className={`px-2 py-1 rounded ${
                        game.difficulty === 'Easy' ? 'bg-green-100 text-green-700' :
                        game.difficulty === 'Medium' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {game.difficulty}
                      </span>
                      <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded">
                        {game.category}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Create Room Modal */}
      {showCreateRoom && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-bold text-gray-900">🎮 Create Game Room</h3>
                <button
                  onClick={() => setShowCreateRoom(false)}
                  className="text-gray-500 hover:text-gray-700 text-xl"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Room Name
                  </label>
                  <input
                    type="text"
                    value={newRoomName}
                    onChange={(e) => setNewRoomName(e.target.value)}
                    placeholder="Enter room name..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Game Type
                  </label>
                  <select
                    value={selectedGameType}
                    onChange={(e) => setSelectedGameType(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  >
                    {availableGames.map(game => (
                      <option key={game.id} value={game.id}>
                        {game.icon} {game.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-sm text-gray-600">
                    {availableGames.find(g => g.id === selectedGameType)?.description}
                  </div>
                </div>
              </div>

              <div className="flex space-x-3 mt-6">
                <button
                  onClick={() => setShowCreateRoom(false)}
                  className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={createGameRoom}
                  disabled={isLoading || !newRoomName.trim()}
                  className="flex-1 px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:bg-gray-400 transition-colors"
                >
                  {isLoading ? 'Creating...' : 'Create Room'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GamesInterface;