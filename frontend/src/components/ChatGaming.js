import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

const ChatGaming = ({ selectedChat, user, token, api, onSendMessage }) => {
  const { t } = useTranslation();
  const [activeGame, setActiveGame] = useState(null);
  const [gameState, setGameState] = useState(null);
  const [gameHistory, setGameHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // Available games
  const availableGames = [
    {
      id: 'word-chain',
      name: t('games.wordChain'),
      icon: '🔤',
      description: t('games.wordChainDesc'),
      minPlayers: 2,
      maxPlayers: 10
    },
    {
      id: 'quick-math',
      name: t('games.quickMath'),
      icon: '🔢',
      description: t('games.quickMathDesc'),
      minPlayers: 2,
      maxPlayers: 8
    },
    {
      id: 'emoji-story',
      name: t('games.emojiStory'),
      icon: '😀',
      description: t('games.emojiStoryDesc'),
      minPlayers: 2,
      maxPlayers: 6
    },
    {
      id: 'riddle-game',
      name: t('games.riddleGame'),
      icon: '🧩',
      description: t('games.riddleGameDesc'),
      minPlayers: 2,
      maxPlayers: 8
    }
  ];

  // Start a new game
  const startGame = async (gameId) => {
    setIsLoading(true);
    try {
      const response = await axios.post(
        `${api}/chats/${selectedChat.chat_id}/games/start`,
        { game_type: gameId },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setActiveGame(gameId);
      setGameState(response.data.game_state);
      
      // Send game start message
      onSendMessage({
        type: 'game_start',
        game_type: gameId,
        content: t('games.gameStarted', { game: availableGames.find(g => g.id === gameId)?.name })
      });
    } catch (error) {
      console.error('Failed to start game:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Join existing game
  const joinGame = async (gameId) => {
    try {
      const response = await axios.post(
        `${api}/chats/${selectedChat.chat_id}/games/${gameId}/join`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setActiveGame(gameId);
      setGameState(response.data.game_state);
    } catch (error) {
      console.error('Failed to join game:', error);
    }
  };

  // End game
  const endGame = async () => {
    try {
      await axios.post(
        `${api}/chats/${selectedChat.chat_id}/games/end`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setActiveGame(null);
      setGameState(null);
      
      onSendMessage({
        type: 'game_end',
        content: t('games.gameEnded')
      });
    } catch (error) {
      console.error('Failed to end game:', error);
    }
  };

  // Make game move
  const makeMove = async (moveData) => {
    try {
      const response = await axios.post(
        `${api}/chats/${selectedChat.chat_id}/games/move`,
        moveData,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setGameState(response.data.game_state);
      
      // Send move message
      onSendMessage({
        type: 'game_move',
        game_type: activeGame,
        move_data: moveData,
        content: formatMoveMessage(activeGame, moveData)
      });
    } catch (error) {
      console.error('Failed to make move:', error);
    }
  };

  // Format move message for display
  const formatMoveMessage = (gameType, moveData) => {
    switch (gameType) {
      case 'word-chain':
        return `🔤 ${moveData.word}`;
      case 'quick-math':
        return `🔢 ${moveData.answer}`;
      case 'emoji-story':
        return `😀 ${moveData.emojis}`;
      case 'riddle-game':
        return `🧩 ${moveData.answer}`;
      default:
        return JSON.stringify(moveData);
    }
  };

  // Word Chain Game Component
  const WordChainGame = () => {
    const [currentWord, setCurrentWord] = useState('');
    const [wordHistory, setWordHistory] = useState(gameState?.word_history || []);
    const [lastWord, setLastWord] = useState(gameState?.last_word || '');

    const submitWord = () => {
      if (!currentWord.trim()) return;
      
      const word = currentWord.toLowerCase().trim();
      
      // Check if word starts with last letter of previous word
      if (lastWord && !word.startsWith(lastWord.slice(-1))) {
        alert(t('games.wordChainError'));
        return;
      }
      
      // Check if word was already used
      if (wordHistory.includes(word)) {
        alert(t('games.wordAlreadyUsed'));
        return;
      }
      
      makeMove({ word, player: user.username });
      setCurrentWord('');
    };

    return (
      <div className="p-4 bg-blue-50 rounded-lg">
        <h3 className="font-medium text-blue-900 mb-2 flex items-center">
          <span className="mr-2">🔤</span>
          {t('games.wordChain')}
        </h3>
        
        {lastWord && (
          <p className="text-sm text-blue-700 mb-2">
            {t('games.lastWord')}: <strong>{lastWord}</strong>
          </p>
        )}
        
        <div className="flex space-x-2">
          <input
            type="text"
            value={currentWord}
            onChange={(e) => setCurrentWord(e.target.value)}
            placeholder={t('games.enterWord')}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            onKeyPress={(e) => e.key === 'Enter' && submitWord()}
            aria-label="Enter your word"
          />
          <button
            onClick={submitWord}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
            aria-label="Submit word"
          >
            {t('games.submit')}
          </button>
        </div>
        
        {wordHistory.length > 0 && (
          <div className="mt-3">
            <p className="text-sm text-gray-600 mb-1">{t('games.wordHistory')}:</p>
            <div className="text-sm text-gray-500">
              {wordHistory.slice(-5).join(' → ')}
            </div>
          </div>
        )}
      </div>
    );
  };

  // Quick Math Game Component
  const QuickMathGame = () => {
    const [answer, setAnswer] = useState('');
    const [question, setQuestion] = useState(gameState?.current_question || '');
    const [score, setScore] = useState(gameState?.scores || {});

    const submitAnswer = () => {
      if (!answer.trim()) return;
      
      const numAnswer = parseInt(answer);
      if (isNaN(numAnswer)) {
        alert(t('games.invalidNumber'));
        return;
      }
      
      makeMove({ answer: numAnswer, player: user.username });
      setAnswer('');
    };

    return (
      <div className="p-4 bg-green-50 rounded-lg">
        <h3 className="font-medium text-green-900 mb-2 flex items-center">
          <span className="mr-2">🔢</span>
          {t('games.quickMath')}
        </h3>
        
        {question && (
          <div className="mb-3">
            <p className="text-lg font-mono text-green-800 mb-2">{question}</p>
            <div className="flex space-x-2">
              <input
                type="number"
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder={t('games.enterAnswer')}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                onKeyPress={(e) => e.key === 'Enter' && submitAnswer()}
                aria-label="Enter your answer"
              />
              <button
                onClick={submitAnswer}
                className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
                aria-label="Submit answer"
              >
                {t('games.submit')}
              </button>
            </div>
          </div>
        )}
        
        {Object.keys(score).length > 0 && (
          <div className="mt-3">
            <p className="text-sm text-gray-600 mb-1">{t('games.scores')}:</p>
            <div className="text-sm text-gray-500">
              {Object.entries(score).map(([player, points]) => (
                <span key={player} className="mr-3">
                  {player}: {points}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  // Emoji Story Game Component
  const EmojiStoryGame = () => {
    const [selectedEmojis, setSelectedEmojis] = useState([]);
    const [story, setStory] = useState(gameState?.story || []);

    const commonEmojis = [
      '😀', '😃', '😄', '😁', '😅', '😂', '🤣', '😊', '😇', '🙂', '🙃', '😉',
      '😍', '🥰', '😘', '😗', '😙', '😚', '😋', '😛', '😜', '🤪', '😝', '🤑',
      '🤗', '🤔', '🤐', '🤨', '😐', '😑', '😶', '😏', '😒', '🙄', '😬', '🤥',
      '😔', '😪', '🤤', '😴', '😷', '🤒', '🤕', '🤢', '🤮', '🤧', '🥵', '🥶',
      '🥴', '😵', '🤯', '🤠', '🥳', '😎', '🤓', '🧐'
    ];

    const addEmoji = (emoji) => {
      if (selectedEmojis.length < 5) {
        setSelectedEmojis([...selectedEmojis, emoji]);
      }
    };

    const removeEmoji = (index) => {
      setSelectedEmojis(selectedEmojis.filter((_, i) => i !== index));
    };

    const submitStory = () => {
      if (selectedEmojis.length === 0) return;
      
      makeMove({ emojis: selectedEmojis, player: user.username });
      setSelectedEmojis([]);
    };

    return (
      <div className="p-4 bg-purple-50 rounded-lg">
        <h3 className="font-medium text-purple-900 mb-2 flex items-center">
          <span className="mr-2">😀</span>
          {t('games.emojiStory')}
        </h3>
        
        <div className="mb-3">
          <p className="text-sm text-purple-700 mb-2">{t('games.selectEmojis')}:</p>
          <div className="grid grid-cols-8 gap-1 max-h-32 overflow-y-auto">
            {commonEmojis.map((emoji, index) => (
              <button
                key={index}
                onClick={() => addEmoji(emoji)}
                className="p-2 hover:bg-purple-100 rounded text-lg"
                aria-label={`Add ${emoji} to story`}
              >
                {emoji}
              </button>
            ))}
          </div>
        </div>
        
        <div className="mb-3">
          <p className="text-sm text-purple-700 mb-2">{t('games.yourStory')}:</p>
          <div className="flex flex-wrap gap-1 min-h-[40px] p-2 bg-white rounded border">
            {selectedEmojis.map((emoji, index) => (
              <button
                key={index}
                onClick={() => removeEmoji(index)}
                className="text-2xl hover:bg-red-100 rounded p-1"
                aria-label={`Remove ${emoji} from story`}
              >
                {emoji}
              </button>
            ))}
          </div>
        </div>
        
        <button
          onClick={submitStory}
          disabled={selectedEmojis.length === 0}
          className="w-full px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:opacity-50"
          aria-label="Submit emoji story"
        >
          {t('games.submitStory')}
        </button>
        
        {story.length > 0 && (
          <div className="mt-3">
            <p className="text-sm text-gray-600 mb-1">{t('games.storyHistory')}:</p>
            <div className="text-lg">
              {story.map((segment, index) => (
                <span key={index} className="mr-2">
                  {segment.emojis.join('')}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  // Render active game
  const renderActiveGame = () => {
    switch (activeGame) {
      case 'word-chain':
        return <WordChainGame />;
      case 'quick-math':
        return <QuickMathGame />;
      case 'emoji-story':
        return <EmojiStoryGame />;
      default:
        return null;
    }
  };

  if (activeGame) {
    return (
      <div className="p-4 border-t border-gray-200">
        {renderActiveGame()}
        
        <div className="mt-4 flex justify-between items-center">
          <div className="text-sm text-gray-600">
            {t('games.currentTurn')}: {gameState?.current_player || 'Unknown'}
          </div>
          <button
            onClick={endGame}
            className="px-3 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600"
            aria-label="End current game"
          >
            {t('games.endGame')}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 border-t border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-medium text-gray-900 flex items-center">
          <span className="mr-2">🎮</span>
          {t('games.chatGames')}
        </h3>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {availableGames.map((game) => (
          <div
            key={game.id}
            className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
            onClick={() => startGame(game.id)}
            role="button"
            aria-label={`Start ${game.name} game`}
          >
            <div className="flex items-center space-x-3">
              <span className="text-2xl" aria-hidden="true">{game.icon}</span>
              <div>
                <h4 className="font-medium text-gray-900">{game.name}</h4>
                <p className="text-sm text-gray-600">{game.description}</p>
                <p className="text-xs text-gray-500 mt-1">
                  {game.minPlayers}-{game.maxPlayers} {t('games.players')}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {isLoading && (
        <div className="mt-4 text-center">
          <div className="inline-flex items-center">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500 mr-2"></div>
            <span className="text-sm text-gray-600">{t('games.starting')}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatGaming;