import React, { useState, useEffect } from 'react';

const WordGuessGame = ({ gameState, onMove, currentUser }) => {
  const [currentWord, setCurrentWord] = useState('');
  const [guessedLetters, setGuessedLetters] = useState([]);
  const [wrongGuesses, setWrongGuesses] = useState(0);
  const [gameStatus, setGameStatus] = useState('waiting');
  const [inputLetter, setInputLetter] = useState('');
  const [hint, setHint] = useState('');

  const maxWrongGuesses = 6;

  useEffect(() => {
    if (gameState) {
      setCurrentWord(gameState.word || '');
      setGuessedLetters(gameState.guessedLetters || []);
      setWrongGuesses(gameState.wrongGuesses || 0);
      setGameStatus(gameState.status || 'waiting');
      setHint(gameState.hint || '');
    }
  }, [gameState]);

  const handleLetterGuess = (letter) => {
    if (!letter || guessedLetters.includes(letter.toLowerCase()) || gameStatus !== 'playing') {
      return;
    }

    const lowerLetter = letter.toLowerCase();
    const newGuessedLetters = [...guessedLetters, lowerLetter];
    const isCorrect = currentWord.toLowerCase().includes(lowerLetter);
    const newWrongGuesses = isCorrect ? wrongGuesses : wrongGuesses + 1;

    // Check if word is completed
    const wordCompleted = currentWord
      .toLowerCase()
      .split('')
      .every(letter => newGuessedLetters.includes(letter) || letter === ' ');

    const gameOver = newWrongGuesses >= maxWrongGuesses;
    const won = wordCompleted && !gameOver;

    onMove({
      type: 'letter_guess',
      letter: lowerLetter,
      guessedLetters: newGuessedLetters,
      wrongGuesses: newWrongGuesses,
      gameOver: gameOver,
      won: won,
      isCorrect: isCorrect
    });

    setInputLetter('');
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    handleLetterGuess(inputLetter);
  };

  const startNewGame = () => {
    onMove({
      type: 'new_game'
    });
  };

  const renderWord = () => {
    return currentWord
      .split('')
      .map((letter, index) => {
        const isGuessed = guessedLetters.includes(letter.toLowerCase());
        const showLetter = isGuessed || letter === ' ';
        
        return (
          <span
            key={index}
            className={`inline-block mx-1 text-2xl font-bold border-b-2 border-gray-400 pb-1 min-w-[2rem] text-center ${
              letter === ' ' ? 'border-transparent' : ''
            }`}
          >
            {showLetter ? letter.toUpperCase() : '_'}
          </span>
        );
      });
  };

  const renderHangman = () => {
    const stages = [
      '', // 0 wrong
      '  +---+\n      |\n      |\n      |\n      |\n      |\n=========', // 1 wrong
      '  +---+\n  |   |\n      |\n      |\n      |\n      |\n=========', // 2 wrong
      '  +---+\n  |   |\n  O   |\n      |\n      |\n      |\n=========', // 3 wrong
      '  +---+\n  |   |\n  O   |\n  |   |\n      |\n      |\n=========', // 4 wrong
      '  +---+\n  |   |\n  O   |\n /|   |\n      |\n      |\n=========', // 5 wrong
      '  +---+\n  |   |\n  O   |\n /|\\  |\n      |\n      |\n=========', // 6 wrong
      '  +---+\n  |   |\n  O   |\n /|\\  |\n /    |\n      |\n=========', // 7 wrong (game over)
    ];

    return (
      <pre className="text-sm font-mono text-gray-700 bg-gray-50 p-4 rounded-lg">
        {stages[Math.min(wrongGuesses, stages.length - 1)]}
      </pre>
    );
  };

  const getStatusMessage = () => {
    if (gameStatus === 'waiting') return '⏳ Waiting for game to start...';
    if (gameStatus === 'won') return '🎉 Congratulations! You guessed the word!';
    if (gameStatus === 'lost') return '💀 Game Over! The word was: ' + currentWord.toUpperCase();
    
    const remainingGuesses = maxWrongGuesses - wrongGuesses;
    return `🎯 ${remainingGuesses} wrong guesses remaining`;
  };

  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');

  return (
    <div className="word-guess-game text-center max-w-2xl mx-auto">
      <div className="mb-6">
        <h3 className="text-xl font-bold text-gray-800 mb-2">🔤 Word Guessing Game</h3>
        <div className="text-lg text-gray-600">{getStatusMessage()}</div>
      </div>

      {/* Hangman Drawing */}
      <div className="mb-6">
        {renderHangman()}
      </div>

      {/* Current Word */}
      <div className="mb-6 bg-white rounded-lg p-4 shadow-sm">
        <div className="text-3xl tracking-wider">
          {renderWord()}
        </div>
        {hint && (
          <div className="mt-4 text-sm text-gray-600 bg-yellow-50 rounded-lg p-3">
            💡 <strong>Hint:</strong> {hint}
          </div>
        )}
      </div>

      {/* Letter Input */}
      {gameStatus === 'playing' && (
        <div className="mb-6">
          <form onSubmit={handleSubmit} className="flex justify-center space-x-2 mb-4">
            <input
              type="text"
              value={inputLetter}
              onChange={(e) => setInputLetter(e.target.value.slice(0, 1))}
              placeholder="Enter a letter"
              className="w-16 h-12 text-center text-xl font-bold border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
              maxLength="1"
              pattern="[A-Za-z]"
            />
            <button
              type="submit"
              disabled={!inputLetter || guessedLetters.includes(inputLetter.toLowerCase())}
              className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              Guess
            </button>
          </form>

          {/* Alphabet Grid */}
          <div className="grid grid-cols-6 gap-2 max-w-md mx-auto mb-4">
            {alphabet.map(letter => {
              const isGuessed = guessedLetters.includes(letter.toLowerCase());
              const isCorrect = isGuessed && currentWord.toLowerCase().includes(letter.toLowerCase());
              
              return (
                <button
                  key={letter}
                  onClick={() => handleLetterGuess(letter)}
                  disabled={isGuessed}
                  className={`w-10 h-10 border-2 rounded-lg font-bold text-sm transition-all ${
                    isGuessed
                      ? isCorrect
                        ? 'bg-green-500 text-white border-green-500'
                        : 'bg-red-500 text-white border-red-500'
                      : 'bg-white border-gray-300 hover:border-blue-500 hover:bg-blue-50 cursor-pointer'
                  } ${isGuessed ? 'cursor-not-allowed' : ''}`}
                >
                  {letter}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Guessed Letters */}
      {guessedLetters.length > 0 && (
        <div className="mb-6 bg-gray-50 rounded-lg p-4">
          <h4 className="font-semibold text-gray-700 mb-2">Guessed Letters</h4>
          <div className="flex flex-wrap justify-center gap-2">
            {guessedLetters.map(letter => {
              const isCorrect = currentWord.toLowerCase().includes(letter);
              return (
                <span
                  key={letter}
                  className={`px-2 py-1 rounded text-sm font-bold ${
                    isCorrect ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                  }`}
                >
                  {letter.toUpperCase()}
                </span>
              );
            })}
          </div>
        </div>
      )}

      {/* Game Controls */}
      <div className="flex justify-center space-x-4 mb-4">
        <button
          onClick={startNewGame}
          className="bg-purple-500 text-white px-4 py-2 rounded-lg hover:bg-purple-600 transition-colors"
        >
          🔄 New Game
        </button>
        
        {gameState?.spectators?.length > 0 && (
          <div className="text-sm text-gray-500 flex items-center">
            👥 {gameState.spectators.length} watching
          </div>
        )}
      </div>

      {/* Game Stats */}
      {gameState?.players && (
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-semibold text-gray-700 mb-2">Game Stats</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-gray-600">Wrong Guesses</div>
              <div className="text-lg font-bold text-red-600">{wrongGuesses}/{maxWrongGuesses}</div>
            </div>
            <div>
              <div className="text-gray-600">Letters Guessed</div>
              <div className="text-lg font-bold text-blue-600">{guessedLetters.length}</div>
            </div>
          </div>
        </div>
      )}

      {/* Game Rules */}
      <div className="mt-4 text-xs text-gray-500 bg-blue-50 rounded-lg p-3">
        <strong>How to play:</strong> Guess letters to reveal the hidden word. You have {maxWrongGuesses} wrong guesses before the game ends!
      </div>
    </div>
  );
};

export default WordGuessGame;