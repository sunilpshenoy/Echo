// Offline Game Manager - Handles local game state and AI opponents
export class OfflineGameManager {
  constructor() {
    this.gameStates = new Map();
    this.aiDifficulty = 'medium'; // easy, medium, hard
  }

  // Create offline game session
  createOfflineGame(gameType, playerName = 'Player') {
    const gameId = `offline_${Date.now()}`;
    const gameState = this.initializeGameState(gameType, gameId, playerName);
    this.gameStates.set(gameId, gameState);
    this.saveToLocalStorage(gameId, gameState);
    return { gameId, gameState };
  }

  // Initialize game state based on game type
  initializeGameState(gameType, gameId, playerName) {
    const baseState = {
      gameId,
      gameType,
      mode: 'offline',
      playerName,
      createdAt: new Date().toISOString(),
      status: 'playing'
    };

    switch (gameType) {
      case 'tic-tac-toe':
        return {
          ...baseState,
          board: Array(9).fill(null),
          currentPlayer: 'X',
          players: { human: 'X', ai: 'O' },
          playerNames: { X: playerName, O: 'Computer' },
          winner: null,
          moves: 0
        };

      case 'word-guess':
        const words = [
          { word: 'JAVASCRIPT', hint: 'Programming language' },
          { word: 'COMPUTER', hint: 'Electronic device' },
          { word: 'INTERNET', hint: 'Global network' },
          { word: 'KEYBOARD', hint: 'Input device' },
          { word: 'PROGRAMMING', hint: 'Writing code' },
          { word: 'ALGORITHM', hint: 'Step-by-step procedure' },
          { word: 'DATABASE', hint: 'Data storage system' },
          { word: 'WEBSITE', hint: 'Online presence' },
          { word: 'SOFTWARE', hint: 'Computer programs' },
          { word: 'HARDWARE', hint: 'Physical components' }
        ];
        const selectedWord = words[Math.floor(Math.random() * words.length)];
        return {
          ...baseState,
          word: selectedWord.word,
          hint: selectedWord.hint,
          guessedLetters: [],
          wrongGuesses: 0,
          maxWrongGuesses: 6,
          gameWon: false,
          gameLost: false
        };

      case 'ludo':
        return {
          ...baseState,
          board: this.initializeLudoBoard(),
          currentPlayer: 0,
          players: [
            { id: 'human', name: playerName, color: 'red', isAI: false },
            { id: 'ai', name: 'Computer', color: 'blue', isAI: true }
          ],
          diceValue: null,
          winner: null,
          turnPhase: 'roll' // roll, move, end
        };

      case 'mafia':
        // Single player Mafia is challenging, so we'll make it a deduction puzzle
        return {
          ...baseState,
          players: this.generateMafiaPlayers(playerName),
          phase: 'investigation', // investigation, accusation, result
          clues: this.generateMafiaClues(),
          accusations: [],
          correctMafia: null,
          maxAccusations: 3
        };

      case 'racing':
        return {
          ...baseState,
          cars: [
            { id: 'player', name: playerName, position: 0, speed: 0, emoji: '🏎️', isPlayer: true },
            { id: 'ai1', name: 'Lightning', position: 0, speed: 0, emoji: '🚗', isAI: true },
            { id: 'ai2', name: 'Thunder', position: 0, speed: 0, emoji: '🚙', isAI: true },
            { id: 'ai3', name: 'Bolt', position: 0, speed: 0, emoji: '🚕', isAI: true }
          ],
          raceDistance: 100,
          raceStarted: false,
          raceFinished: false,
          winner: null,
          countdown: 0
        };

      case 'solitaire':
        return {
          ...baseState,
          tableau: this.initializeSolitaireTableau(),
          foundations: [[], [], [], []],
          waste: [],
          stock: this.createShuffledDeck(),
          moves: 0,
          score: 0,
          gameWon: false
        };

      case 'sudoku':
        const difficulty = 'medium';
        const puzzle = this.generateSudokuPuzzle(difficulty);
        return {
          ...baseState,
          grid: puzzle.puzzle,
          initialGrid: puzzle.puzzle,
          solution: puzzle.solution,
          difficulty,
          timer: 0,
          hints: 3,
          gameWon: false
        };

      case '2048':
        const initialGrid = Array(4).fill().map(() => Array(4).fill(0));
        this.addRandom2048Tile(initialGrid);
        this.addRandom2048Tile(initialGrid);
        return {
          ...baseState,
          grid: initialGrid,
          score: 0,
          bestScore: parseInt(localStorage.getItem('pulse_2048_best') || 0),
          gameOver: false,
          gameWon: false
        };

      case 'blackjack':
        return {
          ...baseState,
          playerHand: [],
          dealerHand: [],
          deck: this.createShuffledDeck(),
          gamePhase: 'betting',
          playerScore: 0,
          dealerScore: 0,
          gameResult: '',
          playerMoney: parseInt(localStorage.getItem('pulse_blackjack_money') || 1000),
          currentBet: 0,
          showDealerCard: false
        };

      case 'snake':
        return {
          ...baseState,
          snake: [{ x: 10, y: 10 }],
          food: { x: 15, y: 15 },
          direction: { x: 0, y: 1 },
          score: 0,
          highScore: parseInt(localStorage.getItem('pulse_snake_high') || 0),
          gameRunning: false,
          gameOver: false,
          speed: 150
        };

      default:
        return baseState;
    }
  }

  // Make AI move based on game type
  makeAIMove(gameId, gameState) {
    switch (gameState.gameType) {
      case 'tic-tac-toe':
        return this.makeTicTacToeAIMove(gameState);
      case 'ludo':
        return this.makeLudoAIMove(gameState);
      default:
        return gameState;
    }
  }

  // Tic-Tac-Toe AI Logic
  makeTicTacToeAIMove(gameState) {
    if (gameState.currentPlayer !== 'O' || gameState.winner) {
      return gameState;
    }

    const bestMove = this.getBestTicTacToeMove(gameState.board);
    if (bestMove !== -1) {
      const newBoard = [...gameState.board];
      newBoard[bestMove] = 'O';
      
      const winner = this.checkTicTacToeWinner(newBoard);
      
      return {
        ...gameState,
        board: newBoard,
        currentPlayer: 'X',
        winner,
        moves: gameState.moves + 1,
        status: winner || gameState.moves >= 8 ? 'finished' : 'playing'
      };
    }
    
    return gameState;
  }

  // Tic-Tac-Toe AI strategy (minimax algorithm simplified)
  getBestTicTacToeMove(board) {
    // Try to win first
    for (let i = 0; i < 9; i++) {
      if (!board[i]) {
        const testBoard = [...board];
        testBoard[i] = 'O';
        if (this.checkTicTacToeWinner(testBoard) === 'O') {
          return i;
        }
      }
    }

    // Block player from winning
    for (let i = 0; i < 9; i++) {
      if (!board[i]) {
        const testBoard = [...board];
        testBoard[i] = 'X';
        if (this.checkTicTacToeWinner(testBoard) === 'X') {
          return i;
        }
      }
    }

    // Take center if available
    if (!board[4]) return 4;

    // Take corners
    const corners = [0, 2, 6, 8];
    const availableCorners = corners.filter(i => !board[i]);
    if (availableCorners.length > 0) {
      return availableCorners[Math.floor(Math.random() * availableCorners.length)];
    }

    // Take any available spot
    const available = board.map((cell, index) => cell === null ? index : null).filter(i => i !== null);
    return available.length > 0 ? available[Math.floor(Math.random() * available.length)] : -1;
  }

  // Check Tic-Tac-Toe winner
  checkTicTacToeWinner(board) {
    const lines = [
      [0, 1, 2], [3, 4, 5], [6, 7, 8], // rows
      [0, 3, 6], [1, 4, 7], [2, 5, 8], // columns
      [0, 4, 8], [2, 4, 6] // diagonals
    ];

    for (const [a, b, c] of lines) {
      if (board[a] && board[a] === board[b] && board[a] === board[c]) {
        return board[a];
      }
    }

    if (board.every(cell => cell !== null)) {
      return 'draw';
    }

    return null;
  }

  // Initialize Ludo board for offline play
  initializeLudoBoard() {
    return {
      track: Array(52).fill(null),
      homes: {
        red: Array(4).fill(null),
        blue: Array(4).fill(null)
      },
      pieces: {
        red: Array(4).fill().map((_, i) => ({ id: i, position: 'home', homeIndex: i })),
        blue: Array(4).fill().map((_, i) => ({ id: i, position: 'home', homeIndex: i }))
      }
    };
  }

  // Ludo AI logic (simplified)
  makeLudoAIMove(gameState) {
    if (!gameState.players[gameState.currentPlayer]?.isAI) {
      return gameState;
    }

    // AI automatically rolls dice and makes best move
    const diceValue = Math.floor(Math.random() * 6) + 1;
    // Simplified AI logic - just move the first available piece
    
    return {
      ...gameState,
      diceValue,
      currentPlayer: (gameState.currentPlayer + 1) % gameState.players.length
    };
  }

  // Generate Mafia game for single player (deduction puzzle)
  generateMafiaPlayers(playerName) {
    const names = ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank'];
    const roles = ['mafia', 'townsperson', 'townsperson', 'detective', 'townsperson', 'doctor'];
    
    return names.map((name, index) => ({
      id: index,
      name,
      role: roles[index],
      alive: true,
      suspicious: Math.random() > 0.5,
      clueGiven: false
    }));
  }

  // Generate clues for Mafia deduction puzzle
  generateMafiaClues() {
    return [
      "The mafia member was seen near the library last night",
      "Someone with a blue jacket seemed nervous during the meeting",
      "The guilty person avoided eye contact with the detective",
      "A witness heard suspicious whispering from the east side",
      "The mafia member has been acting differently this week"
    ];
  }

  // Update game state
  updateGameState(gameId, newState) {
    this.gameStates.set(gameId, newState);
    this.saveToLocalStorage(gameId, newState);
    return newState;
  }

  // Get game state
  getGameState(gameId) {
    let state = this.gameStates.get(gameId);
    if (!state) {
      state = this.loadFromLocalStorage(gameId);
      if (state) {
        this.gameStates.set(gameId, state);
      }
    }
    return state;
  }

  // Save to localStorage
  saveToLocalStorage(gameId, gameState) {
    try {
      localStorage.setItem(`pulse_game_${gameId}`, JSON.stringify(gameState));
    } catch (error) {
      console.warn('Failed to save game state to localStorage:', error);
    }
  }

  // Load from localStorage
  loadFromLocalStorage(gameId) {
    try {
      const saved = localStorage.getItem(`pulse_game_${gameId}`);
      return saved ? JSON.parse(saved) : null;
    } catch (error) {
      console.warn('Failed to load game state from localStorage:', error);
      return null;
    }
  }

  // Get all offline games
  getOfflineGames() {
    const games = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith('pulse_game_offline_')) {
        try {
          const gameState = JSON.parse(localStorage.getItem(key));
          games.push(gameState);
        } catch (error) {
          console.warn('Failed to parse saved game:', error);
        }
      }
    }
    return games.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
  }

  // Delete offline game
  deleteOfflineGame(gameId) {
    this.gameStates.delete(gameId);
    localStorage.removeItem(`pulse_game_${gameId}`);
  }

  // Check if online
  isOnline() {
    return navigator.onLine && window.WebSocket;
  }
}

// Create global instance
export const offlineGameManager = new OfflineGameManager();