import React, { useState, useEffect } from 'react';
import { offlineGameManager } from './OfflineGameManager';

const Solitaire = ({ gameState, onMove, currentUser, mode = 'online' }) => {
  const [deck, setDeck] = useState([]);
  const [tableau, setTableau] = useState([[], [], [], [], [], [], []]);
  const [foundations, setFoundations] = useState([[], [], [], []]);
  const [waste, setWaste] = useState([]);
  const [stock, setStock] = useState([]);
  const [selectedCard, setSelectedCard] = useState(null);
  const [gameWon, setGameWon] = useState(false);
  const [moves, setMoves] = useState(0);
  const [score, setScore] = useState(0);
  const [isOffline, setIsOffline] = useState(mode === 'offline');
  const [offlineGameId, setOfflineGameId] = useState(null);

  const suits = ['♠', '♥', '♦', '♣'];
  const suitColors = { '♠': 'black', '♣': 'black', '♥': 'red', '♦': 'red' };
  const ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'];
  const rankValues = { 'A': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13 };

  useEffect(() => {
    if (isOffline && !offlineGameId) {
      initializeOfflineGame();
    } else if (gameState) {
      setTableau(gameState.tableau || []);
      setFoundations(gameState.foundations || []);
      setWaste(gameState.waste || []);
      setStock(gameState.stock || []);
      setMoves(gameState.moves || 0);
      setScore(gameState.score || 0);
      setGameWon(gameState.gameWon || false);
    }
  }, [gameState, isOffline, offlineGameId]);

  const createDeck = () => {
    const newDeck = [];
    suits.forEach(suit => {
      ranks.forEach(rank => {
        newDeck.push({
          suit,
          rank,
          color: suitColors[suit],
          value: rankValues[rank],
          id: `${suit}${rank}`,
          faceUp: false
        });
      });
    });
    return shuffleDeck(newDeck);
  };

  const shuffleDeck = (deck) => {
    const shuffled = [...deck];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
  };

  const initializeOfflineGame = () => {
    const { gameId, gameState: newGameState } = offlineGameManager.createOfflineGame('solitaire', currentUser?.display_name || 'Player');
    setOfflineGameId(gameId);
    dealCards();
  };

  const dealCards = () => {
    const newDeck = createDeck();
    const newTableau = [[], [], [], [], [], [], []];
    const newStock = [];
    let deckIndex = 0;

    // Deal cards to tableau
    for (let col = 0; col < 7; col++) {
      for (let row = 0; row <= col; row++) {
        const card = { ...newDeck[deckIndex] };
        card.faceUp = row === col; // Only top card is face up
        newTableau[col].push(card);
        deckIndex++;
      }
    }

    // Remaining cards go to stock
    for (let i = deckIndex; i < newDeck.length; i++) {
      newStock.push({ ...newDeck[i], faceUp: false });
    }

    setTableau(newTableau);
    setFoundations([[], [], [], []]);
    setWaste([]);
    setStock(newStock);
    setMoves(0);
    setScore(0);
    setGameWon(false);
    setSelectedCard(null);

    if (isOffline && offlineGameId) {
      offlineGameManager.updateGameState(offlineGameId, {
        tableau: newTableau,
        foundations: [[], [], [], []],
        waste: [],
        stock: newStock,
        moves: 0,
        score: 0,
        gameWon: false
      });
    }
  };

  const drawFromStock = () => {
    if (stock.length === 0) {
      // Reset stock from waste
      const newStock = waste.map(card => ({ ...card, faceUp: false })).reverse();
      setStock(newStock);
      setWaste([]);
    } else {
      // Draw card to waste
      const newStock = [...stock];
      const drawnCard = newStock.pop();
      drawnCard.faceUp = true;
      const newWaste = [...waste, drawnCard];
      setStock(newStock);
      setWaste(newWaste);
    }
    incrementMoves();
  };

  const canPlaceOnFoundation = (card, foundationIndex) => {
    const foundation = foundations[foundationIndex];
    if (foundation.length === 0) {
      return card.value === 1; // Only Ace can start foundation
    }
    const topCard = foundation[foundation.length - 1];
    return card.suit === topCard.suit && card.value === topCard.value + 1;
  };

  const canPlaceOnTableau = (card, columnIndex) => {
    const column = tableau[columnIndex];
    if (column.length === 0) {
      return card.value === 13; // Only King can go on empty column
    }
    const topCard = column[column.length - 1];
    return card.color !== topCard.color && card.value === topCard.value - 1;
  };

  const moveCard = (fromLocation, toLocation) => {
    // Implementation for moving cards between different locations
    incrementMoves();
    updateScore(10);
    checkForWin();
  };

  const incrementMoves = () => {
    const newMoves = moves + 1;
    setMoves(newMoves);
  };

  const updateScore = (points) => {
    const newScore = score + points;
    setScore(newScore);
  };

  const checkForWin = () => {
    const allFoundationsFull = foundations.every(foundation => foundation.length === 13);
    if (allFoundationsFull) {
      setGameWon(true);
      updateScore(1000); // Bonus for winning
    }
  };

  const renderCard = (card, onClick = null, className = '') => {
    if (!card) {
      return (
        <div className={`w-16 h-24 border-2 border-dashed border-gray-300 rounded-lg bg-gray-100 ${className}`}>
        </div>
      );
    }

    return (
      <div
        onClick={onClick}
        className={`w-16 h-24 border border-gray-400 rounded-lg flex flex-col items-center justify-center text-xs font-bold cursor-pointer transition-all hover:shadow-md ${
          card.faceUp 
            ? `bg-white ${card.color === 'red' ? 'text-red-600' : 'text-black'}` 
            : 'bg-blue-900 text-white'
        } ${selectedCard?.id === card.id ? 'ring-2 ring-blue-500' : ''} ${className}`}
      >
        {card.faceUp ? (
          <>
            <div className="text-lg">{card.rank}</div>
            <div className="text-lg">{card.suit}</div>
          </>
        ) : (
          <div className="text-xs">🂠</div>
        )}
      </div>
    );
  };

  const newGame = () => {
    if (isOffline) {
      dealCards();
    } else {
      onMove({ type: 'new_game' });
    }
  };

  const toggleMode = () => {
    setIsOffline(!isOffline);
    if (!isOffline) {
      dealCards();
    }
  };

  return (
    <div className="solitaire-game">
      <div className="mb-4">
        <h3 className="text-xl font-bold text-gray-800 mb-2">♠️ Solitaire</h3>
        
        {/* Game Stats */}
        <div className="flex justify-between items-center mb-4">
          <div className="flex space-x-4 text-sm">
            <span>Moves: {moves}</span>
            <span>Score: {score}</span>
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
              onClick={newGame}
              className="bg-purple-500 text-white px-3 py-1 rounded text-sm hover:bg-purple-600"
            >
              New Game
            </button>
          </div>
        </div>

        {gameWon && (
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
            🎉 Congratulations! You won in {moves} moves with a score of {score}!
          </div>
        )}
      </div>

      {/* Game Board */}
      <div className="solitaire-board">
        {/* Top Row: Stock, Waste, and Foundations */}
        <div className="flex justify-between mb-6">
          <div className="flex space-x-2">
            {/* Stock */}
            <div onClick={drawFromStock} className="cursor-pointer">
              {stock.length > 0 ? renderCard(stock[stock.length - 1]) : renderCard(null)}
              <div className="text-xs text-center mt-1">Stock</div>
            </div>

            {/* Waste */}
            <div>
              {waste.length > 0 ? renderCard(waste[waste.length - 1]) : renderCard(null)}
              <div className="text-xs text-center mt-1">Waste</div>
            </div>
          </div>

          {/* Foundations */}
          <div className="flex space-x-2">
            {foundations.map((foundation, index) => (
              <div key={index}>
                {foundation.length > 0 
                  ? renderCard(foundation[foundation.length - 1]) 
                  : renderCard(null)}
                <div className="text-xs text-center mt-1">{suits[index]}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Tableau */}
        <div className="flex justify-center space-x-2">
          {tableau.map((column, colIndex) => (
            <div key={colIndex} className="flex flex-col space-y-1 min-h-32">
              {column.length === 0 ? (
                renderCard(null, null, 'mb-1')
              ) : (
                column.map((card, cardIndex) => (
                  <div
                    key={card.id}
                    className={cardIndex === column.length - 1 ? '' : '-mb-20'}
                  >
                    {renderCard(card, () => setSelectedCard(card))}
                  </div>
                ))
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Game Rules */}
      <div className="mt-6 text-xs text-gray-500 bg-blue-50 rounded-lg p-3">
        <strong>How to play:</strong> Move all cards to the four foundation piles, starting with Aces and building up in suit. 
        In the tableau, build down in alternating colors. Click stock to draw cards.
        {isOffline && <div className="mt-1"><strong>Offline Mode:</strong> Classic solitaire. No internet required!</div>}
      </div>
    </div>
  );
};

export default Solitaire;