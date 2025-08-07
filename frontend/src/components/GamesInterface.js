import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../contexts/ThemeContext';
import io from 'socket.io-client';
import { offlineGameManager } from './games/OfflineGameManager';
import { gameCategoryColors, difficultyColors } from '../styles/designSystem';
import Button from './ui/Button';
import Card from './ui/Card';
import Badge from './ui/Badge';
import Input from './ui/Input';
import Modal from './ui/Modal';
import './GamesInterface.css';
import TicTacToeGame from './games/TicTacToeGame';
import WordGuessGame from './games/WordGuessGame';
import LudoGame from './games/LudoGame';
import MafiaGame from './games/MafiaGame';
import SimpleRacing from './games/SimpleRacing';
import Solitaire from './games/Solitaire';
import Sudoku from './games/Sudoku';
import Game2048 from './games/Game2048';
import Blackjack from './games/Blackjack';
import Snake from './games/Snake';

const GamesInterface = ({ user, token, api }) => {
  const { t } = useTranslation();
  const { theme, toggleTheme, isDark } = useTheme();
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
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [difficultyFilter, setDifficultyFilter] = useState('all');
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [offlineGames, setOfflineGames] = useState([]);
  const [gameMode, setGameMode] = useState('auto'); // auto, online, offline
  const [currentOfflineGame, setCurrentOfflineGame] = useState(null);
  const [viewMode, setViewMode] = useState('grid'); // grid, list
  const socketRef = useRef(null);

  const availableGames = [
    {
      id: 'tic-tac-toe',
      name: 'Tic-Tac-Toe',
      icon: '⭕',
      minPlayers: 1,
      maxPlayers: 2,
      description: 'Classic 3x3 grid game',
      difficulty: 'Easy',
      duration: '2-5 minutes',
      category: 'Strategy',
      offlineSupported: true
    },
    {
      id: 'word-guess',
      name: 'Word Guessing',
      icon: '🔤',
      minPlayers: 1,
      maxPlayers: 8,
      description: 'Guess the word with hints',
      difficulty: 'Medium',
      duration: '5-10 minutes',
      category: 'Word',
      offlineSupported: true
    },
    {
      id: 'racing',
      name: 'Simple Racing',
      icon: '🏁',
      minPlayers: 1,
      maxPlayers: 4,
      description: 'Fast-paced car racing',
      difficulty: 'Easy',
      duration: '3-7 minutes',
      category: 'Action',
      offlineSupported: true
    },
    {
      id: 'solitaire',
      name: 'Solitaire',
      icon: '♠️',
      minPlayers: 1,
      maxPlayers: 1,
      description: 'Classic card game',
      difficulty: 'Medium',
      duration: '10-20 minutes',
      category: 'Cards',
      offlineSupported: true
    },
    {
      id: 'blackjack',
      name: 'Blackjack',
      icon: '🃏',
      minPlayers: 1,
      maxPlayers: 6,
      description: 'Beat the dealer at 21',
      difficulty: 'Medium',
      duration: '5-15 minutes',
      category: 'Cards',
      offlineSupported: true
    },
    {
      id: 'sudoku',
      name: 'Sudoku',
      icon: '🔢',
      minPlayers: 1,
      maxPlayers: 1,
      description: 'Number puzzle challenge',
      difficulty: 'Hard',
      duration: '10-30 minutes',
      category: 'Puzzle',
      offlineSupported: true
    },
    {
      id: '2048',
      name: '2048',
      icon: '🔲',
      minPlayers: 1,
      maxPlayers: 1,
      description: 'Slide and merge tiles',
      difficulty: 'Medium',
      duration: '5-20 minutes',
      category: 'Puzzle',
      offlineSupported: true
    },
    {
      id: 'snake',
      name: 'Snake',
      icon: '🐍',
      minPlayers: 1,
      maxPlayers: 1,
      description: 'Classic arcade game',
      difficulty: 'Easy',
      duration: '2-10 minutes',
      category: 'Arcade',
      offlineSupported: true
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
      category: 'Board',
      offlineSupported: true
    },
    {
      id: 'mafia',
      name: 'Mafia',
      icon: '🕵️',
      minPlayers: 5,
      maxPlayers: 12,
      description: 'Social deduction puzzle',
      difficulty: 'Hard',
      duration: '20-45 minutes',
      category: 'Social',
      offlineSupported: true
    }
  ];

  // Monitor online/offline status
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      setError('');
    };
    
    const handleOffline = () => {
      setIsOnline(false);
      setError('You are offline. Only offline games are available.');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Load offline games
  useEffect(() => {
    const loadOfflineGames = () => {
      const games = offlineGameManager.getOfflineGames();
      setOfflineGames(games);
    };

    loadOfflineGames();
    // Refresh offline games every 5 seconds
    const interval = setInterval(loadOfflineGames, 5000);
    return () => clearInterval(interval);
  }, []);

  // Initialize WebSocket connection only when online
  useEffect(() => {
    const initSocket = () => {
      if (!isOnline || gameMode === 'offline') return;
      
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
        setError('Failed to connect to game server. Switching to offline mode.');
        setGameMode('offline');
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

    if (token && isOnline && gameMode !== 'offline') {
      const socketConnection = initSocket();
      
      // Fetch initial game rooms
      fetchGameRooms();

      return () => {
        if (socketConnection) {
          socketConnection.disconnect();
        }
      };
    }
  }, [token, isOnline, gameMode]);

  const fetchGameRooms = async () => {
    if (!isOnline || gameMode === 'offline') return;
    
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
        setError('Failed to fetch game rooms. Using offline mode.');
        setGameMode('offline');
      }
    } catch (error) {
      console.error('Failed to fetch game rooms:', error);
      setError('Failed to connect to game server. Using offline mode.');
      setGameMode('offline');
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
    alert(`🎮 Game ended! ${result.message}`);
  };

  const handleGameInvitation = (invitation) => {
    setGameInvitations(prev => [...prev, invitation]);
  };

  const handleRoomJoined = (roomData) => {
    setCurrentRoom(roomData.roomId);
  };

  const handlePlayerJoined = (data) => {
    fetchGameRooms();
  };

  const handlePlayerLeft = (data) => {
    fetchGameRooms();
  };

  // Start offline game
  const startOfflineGame = (gameType) => {
    try {
      const { gameId, gameState: newGameState } = offlineGameManager.createOfflineGame(
        gameType, 
        user?.display_name || user?.username || 'Player'
      );
      
      setActiveGame(gameType);
      setGameState(newGameState);
      setCurrentOfflineGame(gameId);
      setGameMode('offline');
    } catch (error) {
      console.error('Failed to start offline game:', error);
      setError('Failed to start offline game');
    }
  };

  // Continue offline game
  const continueOfflineGame = (gameId) => {
    try {
      const savedGame = offlineGameManager.getGameState(gameId);
      if (savedGame) {
        setActiveGame(savedGame.gameType);
        setGameState(savedGame);
        setCurrentOfflineGame(gameId);
        setGameMode('offline');
      }
    } catch (error) {
      console.error('Failed to continue offline game:', error);
      setError('Failed to continue offline game');
    }
  };

  // Create online room
  const createGameRoom = async () => {
    if (!newRoomName.trim()) {
      setError('Please enter a room name');
      return;
    }

    if (!isOnline || gameMode === 'offline') {
      // Start offline game instead
      startOfflineGame(selectedGameType);
      setShowCreateRoom(false);
      setNewRoomName('');
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
        joinGameRoom(room.roomId);
      } else {
        setError('Failed to create game room. Starting offline game instead.');
        startOfflineGame(selectedGameType);
        setShowCreateRoom(false);
        setNewRoomName('');
      }
    } catch (error) {
      console.error('Failed to create game room:', error);
      setError('Network error. Starting offline game instead.');
      startOfflineGame(selectedGameType);
      setShowCreateRoom(false);
      setNewRoomName('');
    } finally {
      setIsLoading(false);
    }
  };

  const joinGameRoom = async (roomId) => {
    if (!isOnline) return;
    
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

  const leaveGame = () => {
    if (currentRoom && socket) {
      socket.emit('leave_game_room', { roomId: currentRoom });
      setCurrentRoom(null);
    }
    
    if (currentOfflineGame) {
      setCurrentOfflineGame(null);
    }
    
    setActiveGame(null);
    setGameState(null);
    setGameMode('auto');
  };

  const startGame = async () => {
    if (!currentRoom || !isOnline) return;

    try {
      const response = await fetch(`${api}/games/rooms/${currentRoom}/start`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
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
    if (currentOfflineGame) {
      // Offline game move
      const currentState = offlineGameManager.getGameState(currentOfflineGame);
      // Update the state and trigger re-render
      const newState = { ...currentState, ...move };
      offlineGameManager.updateGameState(currentOfflineGame, newState);
      setGameState(newState);
    } else if (socket && currentRoom) {
      // Online game move
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
      currentUser: user,
      mode: currentOfflineGame ? 'offline' : 'online'
    };

    switch (activeGame) {
      case 'tic-tac-toe':
        return <TicTacToeGame {...gameProps} />;
      case 'word-guess':
        return <WordGuessGame {...gameProps} />;
      case 'racing':
        return <SimpleRacing {...gameProps} />;
      case 'solitaire':
        return <Solitaire {...gameProps} />;
      case 'blackjack':
        return <Blackjack {...gameProps} />;
      case 'sudoku':
        return <Sudoku {...gameProps} />;
      case '2048':
        return <Game2048 {...gameProps} />;
      case 'snake':
        return <Snake {...gameProps} />;
      case 'ludo':
        return <LudoGame {...gameProps} />;
      case 'mafia':
        return <MafiaGame {...gameProps} />;
      default:
        return <div className="text-center p-4">🎮 Game not implemented yet</div>;
    }
  };

  const deleteOfflineGame = (gameId) => {
    offlineGameManager.deleteOfflineGame(gameId);
    setOfflineGames(offlineGameManager.getOfflineGames());
  };

  const filteredRooms = gameRooms.filter(room => 
    room.name.toLowerCase().includes(searchFilter.toLowerCase()) ||
    room.gameType.toLowerCase().includes(searchFilter.toLowerCase())
  );

  const filteredGames = availableGames.filter(game => {
    const matchesSearch = game.name.toLowerCase().includes(searchFilter.toLowerCase()) ||
                         game.category.toLowerCase().includes(searchFilter.toLowerCase()) ||
                         game.description.toLowerCase().includes(searchFilter.toLowerCase());
    
    const matchesCategory = categoryFilter === 'all' || game.category === categoryFilter;
    
    const matchesDifficulty = difficultyFilter === 'all' || game.difficulty === difficultyFilter;
    
    return matchesSearch && matchesCategory && matchesDifficulty;
  });

  const filteredOfflineGames = offlineGames.filter(game =>
    game.playerName.toLowerCase().includes(searchFilter.toLowerCase()) ||
    game.gameType.toLowerCase().includes(searchFilter.toLowerCase())
  );

  const gameCategories = ['all', ...new Set(availableGames.map(game => game.category))];
  const gameDifficulties = ['all', ...new Set(availableGames.map(game => game.difficulty))];

  // Helper functions for icons
  const getCategoryIcon = (category) => {
    const icons = {
      Strategy: '🧠',
      Word: '📝',
      Action: '⚡',
      Cards: '🃏',
      Puzzle: '🧩',
      Board: '🎲',
      Social: '👥',
      Arcade: '🎮'
    };
    return icons[category] || '🎯';
  };

  const getDifficultyIcon = (difficulty) => {
    const icons = {
      Easy: '🟢',
      Medium: '🟡',
      Hard: '🔴'
    };
    return icons[difficulty] || '⚪';
  };

  if (activeGame) {
    return (
      <div className="games-active-session h-full flex flex-col bg-gray-50 dark:bg-slate-900">
        <div className="flex-shrink-0 bg-white dark:bg-slate-800 border-b border-gray-200 dark:border-slate-700 p-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 flex items-center">
              🎮 {availableGames.find(g => g.id === activeGame)?.name}
              {currentOfflineGame && (
                <Badge variant="success" size="sm" className="ml-2">
                  📱 Offline
                </Badge>
              )}
            </h2>
            <Button
              variant="danger"
              size="md"
              onClick={leaveGame}
            >
              Leave Game
            </Button>
          </div>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4">
          {renderActiveGame()}
        </div>
      </div>
    );
  }

  return (
    <div className="games-interface h-full flex flex-col bg-gradient-to-br from-gray-50 to-gray-100 dark:from-slate-900 dark:to-slate-800">
      {/* Header */}
      <div className="flex-shrink-0 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm border-b border-gray-200 dark:border-slate-700 p-6">
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-3">
              <div className="text-3xl">🎮</div>
              <div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  Games Hub
                </h2>
                <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
                  <span>Discover & Play Games</span>
                  {!isOnline && (
                    <Badge variant="warning" size="sm">
                      📶 Offline
                    </Badge>
                  )}
                </div>
              </div>
            </div>
            
            {/* Theme Toggle */}
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleTheme}
              icon={isDark ? '☀️' : '🌙'}
              className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              {isDark ? 'Light' : 'Dark'}
            </Button>
          </div>
          
          <div className="flex items-center space-x-3">
            {/* View Mode Toggle */}
            <div className="flex bg-gray-100 dark:bg-slate-700 rounded-xl p-1 shadow-inner">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2.5 rounded-lg transition-all duration-200 ${
                  viewMode === 'grid'
                    ? 'bg-white dark:bg-slate-600 text-gray-900 dark:text-gray-100 shadow-sm transform scale-105'
                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-white/50 dark:hover:bg-slate-600/50'
                }`}
              >
                <span className="text-lg">⊞</span>
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2.5 rounded-lg transition-all duration-200 ${
                  viewMode === 'list'
                    ? 'bg-white dark:bg-slate-600 text-gray-900 dark:text-gray-100 shadow-sm transform scale-105'
                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-white/50 dark:hover:bg-slate-600/50'
                }`}
              >
                <span className="text-lg">☰</span>
              </button>
            </div>

            {/* Mode Toggle */}
            {isOnline && (
              <select
                value={gameMode}
                onChange={(e) => setGameMode(e.target.value)}
                className="px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-xl text-sm bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100 shadow-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
              >
                <option value="auto">🔄 Auto Mode</option>
                <option value="online">🌐 Online Only</option>
                <option value="offline">📱 Offline Only</option>
              </select>
            )}
            
            <Button
              variant="primary"
              size="md"
              onClick={() => setShowCreateRoom(true)}
              icon="➕"
              className="shadow-lg hover:shadow-xl"
            >
              {(!isOnline || gameMode === 'offline') ? '🎮 Start Game' : '🚀 Create Room'}
            </Button>
          </div>
        </div>

        {/* Enhanced Search and Filters */}
        <div className="space-y-4">
          {/* Search */}
          <div className="relative max-w-md">
            <Input
              type="text"
              placeholder="Search games or rooms..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              icon="🔍"
              className="pr-12"
              fullWidth
            />
            {searchFilter && (
              <button
                onClick={() => setSearchFilter('')}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
              >
                ✕
              </button>
            )}
          </div>

          {/* Enhanced Filters */}
          <div className="flex flex-wrap gap-4">
            {/* Category Filter */}
            <div className="flex items-center space-x-3">
              <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">Category:</span>
              <div className="flex flex-wrap gap-2">
                {gameCategories.map(category => (
                  <button
                    key={category}
                    onClick={() => setCategoryFilter(category)}
                    className={`filter-button px-4 py-2 rounded-full text-xs font-medium transition-all duration-200 transform hover:scale-105 ${
                      categoryFilter === category
                        ? 'bg-primary-500 text-white shadow-md active'
                        : 'bg-gray-200 dark:bg-slate-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-slate-600 shadow-sm'
                    }`}
                  >
                    {category === 'all' ? '🎯 All' : `${getCategoryIcon(category)} ${category}`}
                  </button>
                ))}
              </div>
            </div>

            {/* Difficulty Filter */}
            <div className="flex items-center space-x-3">
              <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">Difficulty:</span>
              <div className="flex flex-wrap gap-2">
                {gameDifficulties.map(difficulty => (
                  <button
                    key={difficulty}
                    onClick={() => setDifficultyFilter(difficulty)}
                    className={`filter-button px-4 py-2 rounded-full text-xs font-medium transition-all duration-200 transform hover:scale-105 ${
                      difficultyFilter === difficulty
                        ? 'bg-primary-500 text-white shadow-md active'
                        : 'bg-gray-200 dark:bg-slate-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-slate-600 shadow-sm'
                    }`}
                  >
                    {difficulty === 'all' ? '🎯 All' : `${getDifficultyIcon(difficulty)} ${difficulty}`}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="flex-shrink-0 bg-gradient-to-r from-red-50 to-pink-50 dark:from-red-900/20 dark:to-pink-900/20 border-l-4 border-red-500 p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="text-red-500 text-xl">⚠️</div>
              <div className="text-red-700 dark:text-red-300 font-medium">{error}</div>
            </div>
            <button
              onClick={() => setError('')}
              className="text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-200 ml-4 text-xl transition-colors"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 custom-scrollbar">
        <div className="max-w-7xl mx-auto space-y-8">
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

        {/* Offline Games (Saved Games) */}
        {(gameMode === 'offline' || !isOnline || offlineGames.length > 0) && (
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
              📱 Offline Games ({filteredOfflineGames.length})
            </h3>
            
            {filteredOfflineGames.length === 0 ? (
              <div className="text-center py-8 bg-white rounded-lg border-2 border-dashed border-gray-300">
                <div className="text-4xl mb-2">🎯</div>
                <div className="text-gray-600">No offline games found</div>
                <div className="text-sm text-gray-500 mt-1">Start a new offline game to play without internet!</div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredOfflineGames.map(game => {
                  const gameInfo = availableGames.find(g => g.id === game.gameType);
                  const isFinished = game.status === 'finished' || game.winner || game.gameWon || game.gameLost;
                  
                  return (
                    <div
                      key={game.gameId}
                      className="offline-game-card bg-white border rounded-lg p-4 hover:border-purple-500 hover:shadow-md transition-all cursor-pointer"
                      onClick={() => continueOfflineGame(game.gameId)}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <div className="font-semibold text-gray-900 flex items-center">
                            <span className="text-lg mr-2">{gameInfo?.icon}</span>
                            {gameInfo?.name}
                          </div>
                          <div className="text-sm text-gray-600 mt-1">
                            Player: {game.playerName}
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <div className={`px-2 py-1 rounded text-xs font-medium ${
                            isFinished ? 'bg-gray-100 text-gray-700' : 'bg-green-100 text-green-700'
                          }`}>
                            {isFinished ? 'Finished' : 'In Progress'}
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              deleteOfflineGame(game.gameId);
                            }}
                            className="text-red-500 hover:text-red-700 text-xs"
                          >
                            🗑️
                          </button>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <span>📱 Offline</span>
                        <span>{new Date(game.createdAt).toLocaleDateString()}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Active Game Rooms (Online Only) */}
        {isOnline && gameMode !== 'offline' && (
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
                <div className="text-sm text-gray-500 mt-1">Create a room to start playing online!</div>
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
        )}

        {/* Available Games */}
        <div>
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-6 space-y-2 sm:space-y-0">
            <div className="flex items-center space-x-3">
              <h3 className="text-xl font-bold text-gray-800 dark:text-gray-200 flex items-center">
                🎲 Available Games 
                <Badge variant="primary" size="sm" className="ml-3">
                  {filteredGames.length}
                </Badge>
              </h3>
            </div>
            
            <div className="flex items-center space-x-4 text-sm">
              <div className="text-gray-500 dark:text-gray-400">
                {categoryFilter !== 'all' && (
                  <span className="inline-flex items-center px-2 py-1 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 text-xs mr-2">
                    {getCategoryIcon(categoryFilter)} {categoryFilter}
                  </span>
                )}
                {difficultyFilter !== 'all' && (
                  <span className="inline-flex items-center px-2 py-1 rounded-full bg-secondary-100 dark:bg-secondary-900/30 text-secondary-700 dark:text-secondary-300 text-xs mr-2">
                    {getDifficultyIcon(difficultyFilter)} {difficultyFilter}
                  </span>
                )}
                <span className="text-gray-600 dark:text-gray-300">
                  {filteredGames.length} games available
                </span>
              </div>
            </div>
          </div>
          
          {filteredGames.length === 0 ? (
            <Card padding="xl" className="text-center bg-gradient-to-br from-gray-50 to-gray-100 dark:from-slate-800 dark:to-slate-700 border-2 border-dashed border-gray-300 dark:border-slate-600">
              <div className="py-12">
                <div className="text-6xl mb-4 opacity-50">🔍</div>
                <h4 className="text-lg font-semibold text-gray-600 dark:text-gray-300 mb-2">No games found</h4>
                <p className="text-gray-500 dark:text-gray-400 mb-6">
                  Try adjusting your search criteria or explore different categories
                </p>
                <div className="flex flex-wrap justify-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSearchFilter('');
                      setCategoryFilter('all');
                      setDifficultyFilter('all');
                    }}
                    className="animate-bounce-in"
                  >
                    🎯 Clear All Filters
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
                  >
                    {viewMode === 'grid' ? '☰ Switch to List' : '⊞ Switch to Grid'}
                  </Button>
                </div>
              </div>
            </Card>
          ) : (
            <div className={`${
              viewMode === 'grid' 
                ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:games-grid-2xl gap-4 sm:gap-6' 
                : 'space-y-3'
            }`}>
              {filteredGames.map(game => {
                const categoryStyle = gameCategoryColors[game.category] || gameCategoryColors.Strategy;
                const difficultyStyle = difficultyColors[game.difficulty] || difficultyColors.Easy;
                
                return (
                  <Card
                    key={game.id}
                    hover={true}
                    className={`cursor-pointer game-card-hover transform-gpu category-${game.category.toLowerCase()} ${
                      viewMode === 'list' ? 'p-4' : ''
                    } bg-gradient-to-br from-white to-gray-50 dark:from-slate-800 dark:to-slate-700 border-0 shadow-soft hover:shadow-soft-lg`}
                    onClick={() => {
                      setSelectedGameType(game.id);
                      setShowCreateRoom(true);
                    }}
                  >
                    {viewMode === 'grid' ? (
                      <div className="p-5">
                        {/* Game Icon and Status */}
                        <div className="flex items-start justify-between mb-4">
                          <div className="text-5xl drop-shadow-sm">{game.icon}</div>
                          <div className="flex flex-col items-end space-y-2">
                            {game.offlineSupported && (
                              <Badge variant="success" size="sm" className="shadow-sm">
                                📱 Offline
                              </Badge>
                            )}
                            <Badge 
                              className={`${difficultyStyle.bg} ${difficultyStyle.text} shadow-sm`}
                              size="sm"
                            >
                              {getDifficultyIcon(game.difficulty)} {game.difficulty}
                            </Badge>
                          </div>
                        </div>
                        
                        {/* Game Info */}
                        <div className="space-y-3">
                          <div>
                            <h4 className="font-bold text-lg text-gray-900 dark:text-gray-100 mb-1">
                              {game.name}
                            </h4>
                            <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                              {game.description}
                            </p>
                          </div>
                          
                          {/* Game Stats */}
                          <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-slate-700/50 rounded-lg px-3 py-2">
                            <div className="flex items-center space-x-1">
                              <span>👥</span>
                              <span>{game.minPlayers}-{game.maxPlayers}</span>
                            </div>
                            <div className="flex items-center space-x-1">
                              <span>⏱️</span>
                              <span>{game.duration}</span>
                            </div>
                          </div>
                          
                          {/* Category Badge */}
                          <div className="pt-1">
                            <Badge 
                              className={`${categoryStyle.bg} ${categoryStyle.text} shadow-sm`}
                              size="sm"
                            >
                              {getCategoryIcon(game.category)} {game.category}
                            </Badge>
                          </div>
                        </div>
                      </div>
                    ) : (
                      /* Enhanced List View */
                      <div className="flex items-center space-x-4 p-1">
                        <div className="text-4xl flex-shrink-0">{game.icon}</div>
                        <div className="flex-1 min-w-0">
                          <div className="flex flex-col sm:flex-row sm:items-center sm:space-x-3 mb-2">
                            <h4 className="font-semibold text-gray-900 dark:text-gray-100 text-lg">
                              {game.name}
                            </h4>
                            <div className="flex items-center space-x-2 mt-1 sm:mt-0">
                              {game.offlineSupported && (
                                <Badge variant="success" size="sm">📱</Badge>
                              )}
                              <Badge 
                                className={`${difficultyStyle.bg} ${difficultyStyle.text}`}
                                size="sm"
                              >
                                {getDifficultyIcon(game.difficulty)} {game.difficulty}
                              </Badge>
                            </div>
                          </div>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2 line-clamp-1">
                            {game.description}
                          </p>
                          <div className="flex items-center justify-between">
                            <Badge 
                              className={`${categoryStyle.bg} ${categoryStyle.text}`}
                              size="sm"
                            >
                              {getCategoryIcon(game.category)} {game.category}
                            </Badge>
                            <div className="text-xs text-gray-500 dark:text-gray-400 flex items-center space-x-4">
                              <span>👥 {game.minPlayers}-{game.maxPlayers}</span>
                              <span>⏱️ {game.duration}</span>
                            </div>
                          </div>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedGameType(game.id);
                            setShowCreateRoom(true);
                          }}
                        >
                          Play
                        </Button>
                      </div>
                    )}
                  </Card>
                );
              })}
            </div>
          )}
        </div>
        </div>
      </div>

      {/* Create Room/Start Game Modal */}
      {showCreateRoom && (
        <Modal
          isOpen={showCreateRoom}
          onClose={() => setShowCreateRoom(false)}
          size="lg"
          title={`🎮 ${(!isOnline || gameMode === 'offline') ? 'Start Offline Game' : 'Create Game Room'}`}
        >
          <div className="space-y-6">
            {(isOnline && gameMode !== 'offline') && (
              <Input
                label="Room Name"
                placeholder="Enter room name..."
                value={newRoomName}
                onChange={(e) => setNewRoomName(e.target.value)}
                error={!newRoomName.trim() && error}
                errorText="Please enter a room name"
                fullWidth
                icon="🏠"
              />
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Choose Game Type
              </label>
              <div className="grid grid-cols-1 gap-3 max-h-80 overflow-y-auto">
                {availableGames.map(game => {
                  const categoryStyle = gameCategoryColors[game.category] || gameCategoryColors.Strategy;
                  const difficultyStyle = difficultyColors[game.difficulty] || difficultyColors.Easy;
                  
                  return (
                    <div
                      key={game.id}
                      onClick={() => setSelectedGameType(game.id)}
                      className={`
                        p-4 rounded-xl border-2 transition-all duration-200 cursor-pointer
                        hover:shadow-md transform hover:-translate-y-0.5
                        ${selectedGameType === game.id
                          ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 shadow-glow'
                          : 'border-gray-200 dark:border-slate-600 hover:border-primary-300 dark:hover:border-primary-600'
                        }
                        bg-white dark:bg-slate-700/50
                      `}
                    >
                      <div className="flex items-center space-x-4">
                        <div className="text-3xl">{game.icon}</div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2 mb-1">
                            <h4 className="font-semibold text-gray-900 dark:text-gray-100">
                              {game.name}
                            </h4>
                            {game.offlineSupported && (
                              <Badge variant="success" size="sm">📱</Badge>
                            )}
                            {selectedGameType === game.id && (
                              <Badge variant="primary" size="sm">✓ Selected</Badge>
                            )}
                          </div>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                            {game.description}
                          </p>
                          <div className="flex items-center space-x-2">
                            <Badge 
                              className={`${categoryStyle.bg} ${categoryStyle.text}`}
                              size="sm"
                            >
                              {game.category}
                            </Badge>
                            <Badge 
                              className={`${difficultyStyle.bg} ${difficultyStyle.text}`}
                              size="sm"
                            >
                              {game.difficulty}
                            </Badge>
                            <div className="text-xs text-gray-500 dark:text-gray-400">
                              👥 {game.minPlayers}-{game.maxPlayers} • ⏱️ {game.duration}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {(!isOnline || gameMode === 'offline') && (
              <div className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border border-green-200 dark:border-green-800 rounded-xl p-4">
                <div className="flex items-center space-x-3">
                  <div className="text-2xl">📱</div>
                  <div>
                    <div className="text-sm font-medium text-green-800 dark:text-green-200">
                      Offline Mode Active
                    </div>
                    <div className="text-xs text-green-700 dark:text-green-300">
                      This game will be played offline against AI opponents. No internet connection required!
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="flex space-x-3 mt-8">
            <Button
              variant="secondary"
              size="md"
              fullWidth
              onClick={() => setShowCreateRoom(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="md"
              fullWidth
              loading={isLoading}
              disabled={!selectedGameType || (isOnline && gameMode !== 'offline' && !newRoomName.trim())}
              onClick={createGameRoom}
            >
              {(!isOnline || gameMode === 'offline') ? '🎮 Start Game' : '🚀 Create Room'}
            </Button>
          </div>
        </Modal>
      )}
    </div>
  );
};

export default GamesInterface;