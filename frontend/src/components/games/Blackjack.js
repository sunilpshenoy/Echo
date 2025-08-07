import React, { useState, useEffect } from 'react';
import { offlineGameManager } from './OfflineGameManager';

const Blackjack = ({ gameState, onMove, currentUser, mode = 'online' }) => {
  const [playerHand, setPlayerHand] = useState([]);
  const [dealerHand, setDealerHand] = useState([]);
  const [deck, setDeck] = useState([]);
  const [gamePhase, setGamePhase] = useState('betting'); // betting, dealing, playing, dealer, finished
  const [playerScore, setPlayerScore] = useState(0);
  const [dealerScore, setDealerScore] = useState(0);
  const [gameResult, setGameResult] = useState('');
  const [playerMoney, setPlayerMoney] = useState(1000);
  const [currentBet, setCurrentBet] = useState(0);
  const [showDealerCard, setShowDealerCard] = useState(false);
  const [isOffline, setIsOffline] = useState(mode === 'offline');
  const [offlineGameId, setOfflineGameId] = useState(null);

  const suits = ['♠', '♥', '♦', '♣'];
  const suitColors = { '♠': 'black', '♣': 'black', '♥': 'red', '♦': 'red' };
  const ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'];

  useEffect(() => {
    if (isOffline && !offlineGameId) {
      initializeOfflineGame();
    } else if (gameState) {
      setPlayerHand(gameState.playerHand || []);
      setDealerHand(gameState.dealerHand || []);
      setPlayerScore(gameState.playerScore || 0);
      setDealerScore(gameState.dealerScore || 0);
      setGamePhase(gameState.gamePhase || 'betting');
      setGameResult(gameState.gameResult || '');
      setPlayerMoney(gameState.playerMoney || 1000);
      setCurrentBet(gameState.currentBet || 0);
      setShowDealerCard(gameState.showDealerCard || false);
    }
  }, [gameState, isOffline, offlineGameId]);

  const initializeOfflineGame = () => {
    const { gameId, gameState: newGameState } = offlineGameManager.createOfflineGame('blackjack', currentUser?.display_name || 'Player');
    setOfflineGameId(gameId);
    
    const savedMoney = localStorage.getItem('pulse_blackjack_money');
    const initialMoney = savedMoney ? parseInt(savedMoney) : 1000;
    setPlayerMoney(initialMoney);
    
    resetGame();
  };

  const createDeck = () => {
    const newDeck = [];
    suits.forEach(suit => {
      ranks.forEach(rank => {
        let value = parseInt(rank);
        if (rank === 'A') value = 11;
        else if (['J', 'Q', 'K'].includes(rank)) value = 10;
        
        newDeck.push({
          suit,
          rank,
          value,
          color: suitColors[suit],
          id: `${suit}${rank}`
        });
      });
    });
    
    // Shuffle deck
    for (let i = newDeck.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [newDeck[i], newDeck[j]] = [newDeck[j], newDeck[i]];
    }
    
    return newDeck;
  };

  const calculateScore = (hand) => {
    let score = 0;
    let aces = 0;
    
    hand.forEach(card => {
      if (card.rank === 'A') {
        aces++;
        score += 11;
      } else {
        score += card.value;
      }
    });
    
    // Adjust for Aces
    while (score > 21 && aces > 0) {
      score -= 10;
      aces--;
    }
    
    return score;
  };

  const resetGame = () => {
    const newDeck = createDeck();
    setDeck(newDeck);
    setPlayerHand([]);
    setDealerHand([]);
    setPlayerScore(0);
    setDealerScore(0);
    setGamePhase('betting');
    setGameResult('');
    setCurrentBet(0);
    setShowDealerCard(false);
  };

  const placeBet = (amount) => {
    if (amount > playerMoney || amount <= 0) return;
    
    setCurrentBet(amount);
    setGamePhase('dealing');
    dealInitialCards();
  };

  const dealInitialCards = () => {
    const newDeck = [...deck];
    const newPlayerHand = [newDeck.pop(), newDeck.pop()];
    const newDealerHand = [newDeck.pop(), newDeck.pop()];
    
    setDeck(newDeck);
    setPlayerHand(newPlayerHand);
    setDealerHand(newDealerHand);
    setPlayerScore(calculateScore(newPlayerHand));
    setDealerScore(calculateScore([newDealerHand[0]])); // Only show first dealer card
    setGamePhase('playing');
    
    // Check for natural blackjack
    const playerBlackjack = calculateScore(newPlayerHand) === 21;
    const dealerBlackjack = calculateScore(newDealerHand) === 21;
    
    if (playerBlackjack || dealerBlackjack) {
      setShowDealerCard(true);
      setDealerScore(calculateScore(newDealerHand));
      finishGame(newPlayerHand, newDealerHand);
    }
  };

  const hit = () => {
    if (gamePhase !== 'playing') return;
    
    const newDeck = [...deck];
    const newPlayerHand = [...playerHand, newDeck.pop()];
    const newScore = calculateScore(newPlayerHand);
    
    setDeck(newDeck);
    setPlayerHand(newPlayerHand);
    setPlayerScore(newScore);
    
    if (newScore > 21) {
      setShowDealerCard(true);
      setDealerScore(calculateScore(dealerHand));
      finishGame(newPlayerHand, dealerHand);
    }
  };

  const stand = () => {
    if (gamePhase !== 'playing') return;
    
    setGamePhase('dealer');
    setShowDealerCard(true);
    dealerPlay();
  };

  const dealerPlay = () => {
    let currentDealerHand = [...dealerHand];
    let currentDeck = [...deck];
    let dealerCurrentScore = calculateScore(currentDealerHand);
    
    while (dealerCurrentScore < 17) {
      currentDealerHand.push(currentDeck.pop());
      dealerCurrentScore = calculateScore(currentDealerHand);
    }
    
    setDealerHand(currentDealerHand);
    setDealerScore(dealerCurrentScore);
    setDeck(currentDeck);
    
    setTimeout(() => {
      finishGame(playerHand, currentDealerHand);
    }, 1000);
  };

  const finishGame = (finalPlayerHand, finalDealerHand) => {
    const finalPlayerScore = calculateScore(finalPlayerHand);
    const finalDealerScore = calculateScore(finalDealerHand);
    
    let result = '';
    let payout = 0;
    
    if (finalPlayerScore > 21) {
      result = 'Player Busts - Dealer Wins!';
      payout = -currentBet;
    } else if (finalDealerScore > 21) {
      result = 'Dealer Busts - Player Wins!';
      payout = currentBet;
    } else if (finalPlayerScore === 21 && finalPlayerHand.length === 2) {
      if (finalDealerScore === 21 && finalDealerHand.length === 2) {
        result = 'Both Blackjack - Push!';
        payout = 0;
      } else {
        result = 'Blackjack! Player Wins!';
        payout = Math.floor(currentBet * 1.5);
      }
    } else if (finalDealerScore === 21 && finalDealerHand.length === 2) {
      result = 'Dealer Blackjack!';
      payout = -currentBet;
    } else if (finalPlayerScore > finalDealerScore) {
      result = 'Player Wins!';
      payout = currentBet;
    } else if (finalDealerScore > finalPlayerScore) {
      result = 'Dealer Wins!';
      payout = -currentBet;
    } else {
      result = 'Push!';
      payout = 0;
    }
    
    const newMoney = playerMoney + payout;
    setPlayerMoney(newMoney);
    setGameResult(result);
    setGamePhase('finished');
    
    // Save money to localStorage
    localStorage.setItem('pulse_blackjack_money', newMoney.toString());
    
    if (isOffline && offlineGameId) {
      offlineGameManager.updateGameState(offlineGameId, {
        playerHand: finalPlayerHand,
        dealerHand: finalDealerHand,
        playerScore: finalPlayerScore,
        dealerScore: finalDealerScore,
        gamePhase: 'finished',
        gameResult: result,
        playerMoney: newMoney,
        showDealerCard: true
      });
    }
  };

  const renderCard = (card, hidden = false) => {
    if (hidden) {
      return (
        <div className="w-16 h-24 bg-blue-900 border border-gray-400 rounded-lg flex items-center justify-center">
          <div className="text-white text-xs">🂠</div>
        </div>
      );
    }
    
    return (
      <div className={`w-16 h-24 bg-white border border-gray-400 rounded-lg flex flex-col items-center justify-center text-xs font-bold ${
        card.color === 'red' ? 'text-red-600' : 'text-black'
      }`}>
        <div className="text-lg">{card.rank}</div>
        <div className="text-lg">{card.suit}</div>
      </div>
    );
  };

  const toggleMode = () => {
    setIsOffline(!isOffline);
    if (!isOffline) {
      resetGame();
    }
  };

  const resetMoney = () => {
    setPlayerMoney(1000);
    localStorage.setItem('pulse_blackjack_money', '1000');
    resetGame();
  };

  return (
    <div className="blackjack-game max-w-4xl mx-auto">
      <div className="mb-4">
        <h3 className="text-xl font-bold text-gray-800 mb-2">♠️ Blackjack</h3>
        
        {/* Game Info */}
        <div className="flex justify-between items-center mb-4">
          <div className="flex space-x-4 text-sm">
            <span className="font-semibold">Money: ${playerMoney}</span>
            {currentBet > 0 && <span>Bet: ${currentBet}</span>}
          </div>
          
          <div className="flex space-x-2">
            <button
              onClick={toggleMode}
              className={`px-3 py-1 rounded-full text-sm transition-all ${
                isOffline 
                  ? 'bg-green-100 text-green-700 hover:bg-green-200' 
                  : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
              }`}
            >
              {isOffline ? '🃏 Offline' : '🌐 Online'}
            </button>
            
            <button
              onClick={resetMoney}
              className="bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600"
            >
              Reset Money
            </button>
            
            <button
              onClick={resetGame}
              className="bg-gray-500 text-white px-3 py-1 rounded text-sm hover:bg-gray-600"
            >
              New Game
            </button>
          </div>
        </div>

        {/* Game Result */}
        {gameResult && (
          <div className={`px-4 py-3 rounded mb-4 ${
            gameResult.includes('Player Wins') || gameResult.includes('Blackjack') 
              ? 'bg-green-100 text-green-700' 
              : gameResult.includes('Push') 
              ? 'bg-yellow-100 text-yellow-700'
              : 'bg-red-100 text-red-700'
          }`}>
            {gameResult}
          </div>
        )}
      </div>

      {/* Dealer Section */}
      <div className="mb-8 text-center">
        <h4 className="text-lg font-semibold mb-2">
          Dealer {showDealerCard ? `(${dealerScore})` : ''}
        </h4>
        <div className="flex justify-center space-x-2 mb-2">
          {dealerHand.map((card, index) => (
            <div key={card.id}>
              {renderCard(card, !showDealerCard && index === 1)}
            </div>
          ))}
        </div>
      </div>

      {/* Player Section */}
      <div className="mb-8 text-center">
        <h4 className="text-lg font-semibold mb-2">
          You ({playerScore})
          {playerScore === 21 && playerHand.length === 2 && <span className="text-yellow-600 ml-2">Blackjack!</span>}
          {playerScore > 21 && <span className="text-red-600 ml-2">Bust!</span>}
        </h4>
        <div className="flex justify-center space-x-2 mb-4">
          {playerHand.map(card => (
            <div key={card.id}>
              {renderCard(card)}
            </div>
          ))}
        </div>
      </div>

      {/* Game Controls */}
      <div className="text-center">
        {/* Betting Phase */}
        {gamePhase === 'betting' && (
          <div>
            <h4 className="text-lg font-semibold mb-4">Place Your Bet</h4>
            <div className="flex justify-center space-x-2 flex-wrap">
              {[10, 25, 50, 100, 250, 500].filter(amount => amount <= playerMoney).map(amount => (
                <button
                  key={amount}
                  onClick={() => placeBet(amount)}
                  className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors m-1"
                >
                  ${amount}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Playing Phase */}
        {gamePhase === 'playing' && (
          <div className="flex justify-center space-x-4">
            <button
              onClick={hit}
              className="bg-green-500 text-white px-6 py-3 rounded-lg hover:bg-green-600 transition-colors text-lg font-semibold"
            >
              Hit
            </button>
            <button
              onClick={stand}
              className="bg-red-500 text-white px-6 py-3 rounded-lg hover:bg-red-600 transition-colors text-lg font-semibold"
            >
              Stand
            </button>
          </div>
        )}

        {/* Dealer Playing */}
        {gamePhase === 'dealer' && (
          <div className="text-lg font-semibold text-blue-600">
            Dealer is playing...
          </div>
        )}

        {/* Game Finished */}
        {gamePhase === 'finished' && (
          <button
            onClick={resetGame}
            className="bg-purple-500 text-white px-6 py-3 rounded-lg hover:bg-purple-600 transition-colors text-lg font-semibold"
          >
            New Hand
          </button>
        )}
      </div>

      {/* Game Rules */}
      <div className="mt-8 text-xs text-gray-500 bg-blue-50 rounded-lg p-3">
        <strong>How to play:</strong> Get as close to 21 as possible without going over. Face cards = 10, Aces = 11 or 1. 
        Beat the dealer to win! Blackjack (21 with 2 cards) pays 3:2.
        {isOffline && <div className="mt-1"><strong>Offline Mode:</strong> Classic casino blackjack. No internet required!</div>}
      </div>
    </div>
  );
};

export default Blackjack;