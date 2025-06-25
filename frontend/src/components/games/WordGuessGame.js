import React, { useState, useEffect } from 'react';

const WordGuessGame = ({ user, token, activeChat, onClose, onSendMessage }) => {
  const [currentWord, setCurrentWord] = useState('');
  const [guessedLetters, setGuessedLetters] = useState([]);
  const [wrongGuesses, setWrongGuesses] = useState([]);
  const [gameStatus, setGameStatus] = useState('active');
  const [difficulty, setDifficulty] = useState('medium');
  const [category, setCategory] = useState('general');
  const [hint, setHint] = useState('');
  const [timeLeft, setTimeLeft] = useState(180); // 3 minutes
  const [score, setScore] = useState(0);
  const [streak, setStreak] = useState(0);

  const wordLists = {
    easy: {
      general: ['cat', 'dog', 'sun', 'car', 'book', 'tree', 'bird', 'fish', 'moon', 'star'],
      animals: ['cat', 'dog', 'bird', 'fish', 'bear', 'lion', 'duck', 'frog'],
      colors: ['red', 'blue', 'green', 'yellow', 'black', 'white', 'pink'],
      food: ['pizza', 'bread', 'apple', 'cake', 'milk', 'egg', 'rice']
    },
    medium: {
      general: ['computer', 'rainbow', 'elephant', 'guitar', 'mountain', 'butterfly', 'treasure', 'diamond'],
      animals: ['elephant', 'butterfly', 'penguin', 'dolphin', 'kangaroo', 'giraffe'],
      technology: ['computer', 'internet', 'software', 'keyboard', 'monitor', 'smartphone'],
      nature: ['rainbow', 'mountain', 'ocean', 'forest', 'desert', 'volcano']
    },
    hard: {
      general: ['extraordinary', 'fascinating', 'magnificent', 'revolutionary', 'spectacular', 'phenomenal'],
      science: ['photosynthesis', 'electromagnetic', 'quantum', 'chromosome', 'ecosystem'],
      geography: ['mediterranean', 'himalayas', 'antarctica', 'sahara', 'archipelago'],
      advanced: ['sophistication', 'entrepreneurship', 'metamorphosis', 'philosophical']
    }
  };

  const hints = {
    // Easy hints
    'cat': 'A furry pet that says meow',
    'dog': 'Man\'s best friend',
    'sun': 'The bright star in our sky',
    'car': 'A vehicle with four wheels',
    'book': 'You read this for knowledge or fun',
    
    // Medium hints
    'computer': 'Electronic device for processing data',
    'rainbow': 'Colorful arc in the sky after rain',
    'elephant': 'Largest land mammal with a trunk',
    'guitar': 'String instrument you strum',
    'mountain': 'Very tall natural elevation',
    
    // Hard hints
    'extraordinary': 'Beyond what is normal or usual',
    'fascinating': 'Extremely interesting or captivating',
    'photosynthesis': 'How plants make food from sunlight',
    'mediterranean': 'Sea between Europe and Africa'
  };

  const maxWrongGuesses = 6;

  useEffect(() => {
    startNewGame();
  }, [difficulty, category]);

  useEffect(() => {
    if (timeLeft > 0 && gameStatus === 'active') {
      const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000);
      return () => clearTimeout(timer);
    } else if (timeLeft === 0 && gameStatus === 'active') {
      endGame('timeout');
    }
  }, [timeLeft, gameStatus]);

  const startNewGame = () => {
    const words = wordLists[difficulty][category] || wordLists[difficulty].general;
    const randomWord = words[Math.floor(Math.random() * words.length)].toLowerCase();
    
    setCurrentWord(randomWord);
    setGuessedLetters([]);
    setWrongGuesses([]);
    setGameStatus('active');
    setHint(hints[randomWord] || `A ${difficulty} ${category} word`);
    setTimeLeft(difficulty === 'easy' ? 120 : difficulty === 'medium' ? 180 : 240);
  };

  const guessLetter = (letter) => {
    if (guessedLetters.includes(letter) || gameStatus !== 'active') return;

    const newGuessedLetters = [...guessedLetters, letter];
    setGuessedLetters(newGuessedLetters);

    if (currentWord.includes(letter)) {
      // Correct guess
      const wordLetters = [...new Set(currentWord.split(''))];
      const correctGuesses = newGuessedLetters.filter(l => currentWord.includes(l));
      
      if (wordLetters.every(l => correctGuesses.includes(l))) {
        // Word completed!
        endGame('win');
      } else {
        onSendMessage(`🎯 Word Guess: "${letter}" is in the word! 🎉`, 'wordguess_correct', {
          letter,
          word: getDisplayWord(newGuessedLetters)
        });
      }
    } else {
      // Wrong guess
      const newWrongGuesses = [...wrongGuesses, letter];
      setWrongGuesses(newWrongGuesses);
      
      if (newWrongGuesses.length >= maxWrongGuesses) {
        endGame('lose');
      } else {
        onSendMessage(`🎯 Word Guess: "${letter}" is not in the word. ${maxWrongGuesses - newWrongGuesses.length} guesses left.`, 'wordguess_wrong', {
          letter,
          wrongGuesses: newWrongGuesses,
          remaining: maxWrongGuesses - newWrongGuesses.length
        });
      }
    }
  };

  const endGame = (result) => {
    setGameStatus(result);
    
    if (result === 'win') {
      const points = (difficulty === 'easy' ? 10 : difficulty === 'medium' ? 20 : 30) + Math.floor(timeLeft / 10);
      setScore(score + points);
      setStreak(streak + 1);
      onSendMessage(`🎯 Word Guess: ${user.username} won! The word was "${currentWord.toUpperCase()}" 🎉 (+${points} points)`, 'wordguess_win', {
        word: currentWord,
        points,
        timeLeft
      });
    } else if (result === 'lose') {
      setStreak(0);
      onSendMessage(`🎯 Word Guess: Game over! The word was "${currentWord.toUpperCase()}" 😔`, 'wordguess_lose', {
        word: currentWord
      });
    } else if (result === 'timeout') {
      setStreak(0);
      onSendMessage(`🎯 Word Guess: Time's up! The word was "${currentWord.toUpperCase()}" ⏰`, 'wordguess_timeout', {
        word: currentWord
      });
    }
  };

  const getDisplayWord = (letters = guessedLetters) => {
    return currentWord
      .split('')
      .map(letter => letters.includes(letter) ? letter.toUpperCase() : '_')
      .join(' ');
  };

  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const alphabet = 'abcdefghijklmnopqrstuvwxyz'.split('');

  const getTimeColor = () => {
    if (timeLeft > 60) return 'text-green-600';
    if (timeLeft > 30) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getHangmanDisplay = () => {
    const stages = [
      '  +---+\n  |   |\n      |\n      |\n      |\n      |\n=========',
      '  +---+\n  |   |\n  |   |\n      |\n      |\n      |\n=========',
      '  +---+\n  |   |\n  |   |\n  O   |\n      |\n      |\n=========',
      '  +---+\n  |   |\n  |   |\n  O   |\n  |   |\n      |\n=========',
      '  +---+\n  |   |\n  |   |\n  O   |\n /|   |\n      |\n=========',
      '  +---+\n  |   |\n  |   |\n  O   |\n /|\\  |\n      |\n=========',
      '  +---+\n  |   |\n  |   |\n  O   |\n /|\\  |\n /    |\n=========',
      '  +---+\n  |   |\n  |   |\n  O   |\n /|\\  |\n / \\  |\n========='
    ];
    return stages[wrongGuesses.length] || stages[0];
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">🎯 Word Guess Game</h2>
            <p className="text-gray-600">
              Difficulty: <span className="font-semibold capitalize">{difficulty}</span> | 
              Category: <span className="font-semibold capitalize">{category}</span>
            </p>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={startNewGame}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              New Word
            </button>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 p-2"
            >
              ✕
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Game Area */}
          <div className="lg:col-span-2">
            {/* Word Display */}
            <div className="text-center mb-6">
              <div className="text-4xl font-mono font-bold text-gray-900 mb-4 tracking-wider">
                {getDisplayWord()}
              </div>
              <div className="text-gray-600 italic">
                Hint: {hint}
              </div>
            </div>

            {/* Alphabet Grid */}
            <div className="grid grid-cols-6 gap-2 mb-6">
              {alphabet.map(letter => {
                const isGuessed = guessedLetters.includes(letter);
                const isWrong = wrongGuesses.includes(letter);
                const isCorrect = isGuessed && currentWord.includes(letter);
                
                return (
                  <button
                    key={letter}
                    onClick={() => guessLetter(letter)}
                    disabled={isGuessed || gameStatus !== 'active'}
                    className={`p-3 rounded-lg font-bold text-lg transition-colors ${
                      isCorrect ? 'bg-green-500 text-white' :
                      isWrong ? 'bg-red-500 text-white' :
                      isGuessed ? 'bg-gray-300 text-gray-500 cursor-not-allowed' :
                      gameStatus !== 'active' ? 'bg-gray-200 text-gray-400 cursor-not-allowed' :
                      'bg-blue-100 text-blue-800 hover:bg-blue-200 cursor-pointer'
                    }`}
                  >
                    {letter.toUpperCase()}
                  </button>
                );
              })}
            </div>

            {/* Game Status */}
            {gameStatus !== 'active' && (
              <div className="text-center p-4 rounded-lg mb-4 bg-gray-50">
                {gameStatus === 'win' && (
                  <div className="text-green-600 font-bold text-xl">
                    🎉 Congratulations! You guessed it!
                  </div>
                )}
                {gameStatus === 'lose' && (
                  <div className="text-red-600 font-bold text-xl">
                    😔 Game Over! Better luck next time!
                  </div>
                )}
                {gameStatus === 'timeout' && (
                  <div className="text-orange-600 font-bold text-xl">
                    ⏰ Time's Up! The word was "{currentWord.toUpperCase()}"
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Info Panel */}
          <div className="space-y-4">
            {/* Timer */}
            <div className="bg-gray-50 rounded-lg p-4 text-center">
              <div className="text-sm text-gray-600 mb-1">Time Remaining</div>
              <div className={`text-2xl font-bold ${getTimeColor()}`}>
                {formatTime(timeLeft)}
              </div>
            </div>

            {/* Score */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-center mb-3">
                <div className="text-sm text-gray-600">Score</div>
                <div className="text-2xl font-bold text-purple-600">{score}</div>
              </div>
              <div className="text-center">
                <div className="text-sm text-gray-600">Streak</div>
                <div className="text-xl font-bold text-orange-600">{streak}</div>
              </div>
            </div>

            {/* Hangman Display */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-600 mb-2 text-center">
                Wrong Guesses: {wrongGuesses.length} / {maxWrongGuesses}
              </div>
              <pre className="text-xs font-mono text-center text-gray-700">
                {getHangmanDisplay()}
              </pre>
            </div>

            {/* Game Settings */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-3">Settings</h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm text-gray-600 mb-1">Difficulty</label>
                  <select
                    value={difficulty}
                    onChange={(e) => setDifficulty(e.target.value)}
                    className="w-full p-2 border rounded-lg text-sm"
                    disabled={gameStatus === 'active'}
                  >
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">Category</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full p-2 border rounded-lg text-sm"
                    disabled={gameStatus === 'active'}
                  >
                    <option value="general">General</option>
                    <option value="animals">Animals</option>
                    {difficulty !== 'easy' && <option value="technology">Technology</option>}
                    {difficulty !== 'easy' && <option value="nature">Nature</option>}
                    {difficulty === 'hard' && <option value="science">Science</option>}
                  </select>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WordGuessGame;