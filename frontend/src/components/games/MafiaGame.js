import React, { useState, useEffect } from 'react';

const MafiaGame = ({ gameState, onMove, currentUser }) => {
  const [gamePhase, setGamePhase] = useState('lobby'); // lobby, day, night, voting, ended
  const [players, setPlayers] = useState([]);
  const [myRole, setMyRole] = useState(null);
  const [votingTarget, setVotingTarget] = useState(null);
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [gameLog, setGameLog] = useState([]);
  const [winner, setWinner] = useState(null);

  useEffect(() => {
    if (gameState) {
      setGamePhase(gameState.phase || 'lobby');
      setPlayers(gameState.players || []);
      setMyRole(gameState.roles?.[currentUser.user_id] || null);
      setTimeRemaining(gameState.timeRemaining || 0);
      setGameLog(gameState.log || []);
      setWinner(gameState.winner || null);
    }
  }, [gameState, currentUser.user_id]);

  // Timer effect
  useEffect(() => {
    if (timeRemaining > 0) {
      const timer = setTimeout(() => {
        setTimeRemaining(prev => prev - 1);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [timeRemaining]);

  const getRoleInfo = (role) => {
    const roleData = {
      mafia: { name: 'Mafia', icon: '🔫', color: 'red', description: 'Eliminate townspeople at night' },
      detective: { name: 'Detective', icon: '🕵️', color: 'blue', description: 'Investigate players to find mafia' },
      doctor: { name: 'Doctor', icon: '👨‍⚕️', color: 'green', description: 'Protect players from elimination' },
      townsperson: { name: 'Townsperson', icon: '👤', color: 'gray', description: 'Find and vote out the mafia' }
    };
    return roleData[role] || roleData.townsperson;
  };

  const vote = (targetId) => {
    if (gamePhase !== 'voting' && gamePhase !== 'day') return;
    
    setVotingTarget(targetId);
    onMove({
      type: 'vote',
      targetId,
      voterId: currentUser.user_id,
      phase: gamePhase
    });
  };

  const useNightAction = (targetId, action) => {
    if (gamePhase !== 'night') return;
    
    onMove({
      type: 'night_action',
      action,
      targetId,
      playerId: currentUser.user_id,
      role: myRole
    });
  };

  const startGame = () => {
    if (players.length < 5) {
      alert('Need at least 5 players to start Mafia');
      return;
    }
    
    onMove({
      type: 'start_game',
      players: players.map(p => p.id)
    });
  };

  const renderLobby = () => (
    <div className="lobby text-center">
      <h4 className="text-lg font-semibold mb-4">🕵️ Game Lobby</h4>
      <div className="mb-4">
        <div className="text-sm text-gray-600 mb-2">Players ({players.length}/12)</div>
        <div className="grid grid-cols-2 gap-2 max-w-md mx-auto">
          {players.map(player => (
            <div key={player.id} className="bg-gray-100 rounded-lg p-2 text-sm">
              {player.name}
            </div>
          ))}
        </div>
      </div>
      
      {players.length >= 5 && (
        <button
          onClick={startGame}
          className="bg-red-500 text-white px-6 py-3 rounded-lg hover:bg-red-600 transition-colors"
        >
          Start Game
        </button>
      )}
      
      {players.length < 5 && (
        <div className="text-sm text-gray-500">
          Need {5 - players.length} more players to start
        </div>
      )}
    </div>
  );

  const renderRole = () => {
    if (!myRole) return null;
    
    const roleInfo = getRoleInfo(myRole);
    
    return (
      <div className={`role-card bg-${roleInfo.color}-50 border border-${roleInfo.color}-200 rounded-lg p-4 mb-4`}>
        <div className="text-center">
          <div className="text-3xl mb-2">{roleInfo.icon}</div>
          <div className={`font-bold text-${roleInfo.color}-700`}>{roleInfo.name}</div>
          <div className="text-sm text-gray-600 mt-1">{roleInfo.description}</div>
        </div>
      </div>
    );
  };

  const renderPlayers = () => (
    <div className="players-grid grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
      {players.filter(p => p.alive).map(player => {
        const isMe = player.id === currentUser.user_id;
        const canVote = (gamePhase === 'voting' || gamePhase === 'day') && !isMe;
        const canTarget = gamePhase === 'night' && !isMe && 
                         (myRole === 'mafia' || myRole === 'detective' || myRole === 'doctor');
        
        return (
          <div
            key={player.id}
            className={`player-card border-2 rounded-lg p-3 transition-all ${
              isMe ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-white'
            } ${(canVote || canTarget) ? 'cursor-pointer hover:border-purple-500' : ''}`}
            onClick={() => {
              if (canVote) vote(player.id);
              else if (canTarget && myRole === 'mafia') useNightAction(player.id, 'eliminate');
              else if (canTarget && myRole === 'detective') useNightAction(player.id, 'investigate');
              else if (canTarget && myRole === 'doctor') useNightAction(player.id, 'protect');
            }}
          >
            <div className="text-center">
              <div className="text-2xl mb-1">👤</div>
              <div className="font-semibold text-sm">{player.name}</div>
              {isMe && <div className="text-xs text-blue-600">You</div>}
              {player.votes > 0 && (
                <div className="text-xs text-red-600 mt-1">
                  {player.votes} vote{player.votes > 1 ? 's' : ''}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );

  const renderPhaseInfo = () => {
    const phaseInfo = {
      day: { 
        title: '☀️ Day Phase', 
        description: 'Discuss and vote to eliminate a player',
        color: 'yellow' 
      },
      night: { 
        title: '🌙 Night Phase', 
        description: 'Special roles take action',
        color: 'blue' 
      },
      voting: { 
        title: '🗳️ Voting Phase', 
        description: 'Cast your vote to eliminate someone',
        color: 'purple' 
      }
    };
    
    const info = phaseInfo[gamePhase] || { title: 'Game Phase', description: '', color: 'gray' };
    
    return (
      <div className={`phase-info bg-${info.color}-50 border border-${info.color}-200 rounded-lg p-4 mb-4`}>
        <div className="text-center">
          <h4 className="font-bold text-lg">{info.title}</h4>
          <div className="text-sm text-gray-600">{info.description}</div>
          {timeRemaining > 0 && (
            <div className="text-lg font-mono mt-2">
              ⏰ {Math.floor(timeRemaining / 60)}:{(timeRemaining % 60).toString().padStart(2, '0')}
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderNightActions = () => {
    if (gamePhase !== 'night' || !myRole) return null;
    
    const actions = {
      mafia: { text: 'Choose someone to eliminate', color: 'red' },
      detective: { text: 'Choose someone to investigate', color: 'blue' },
      doctor: { text: 'Choose someone to protect', color: 'green' }
    };
    
    const action = actions[myRole];
    if (!action) return null;
    
    return (
      <div className={`night-actions bg-${action.color}-50 border border-${action.color}-200 rounded-lg p-4 mb-4`}>
        <div className="text-center text-sm">
          <div className={`font-semibold text-${action.color}-700`}>{action.text}</div>
          <div className="text-xs text-gray-600 mt-1">Click on a player above</div>
        </div>
      </div>
    );
  };

  const renderGameLog = () => (
    <div className="game-log bg-gray-50 rounded-lg p-4 max-h-32 overflow-y-auto">
      <h4 className="font-semibold text-gray-700 mb-2">📜 Game Log</h4>
      <div className="space-y-1 text-sm">
        {gameLog.slice(-5).map((entry, index) => (
          <div key={index} className="text-gray-600">
            {entry}
          </div>
        ))}
      </div>
    </div>
  );

  const renderGameEnd = () => {
    if (!winner) return null;
    
    return (
      <div className="game-end text-center bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg p-6">
        <div className="text-4xl mb-2">🎉</div>
        <h3 className="text-xl font-bold text-gray-800 mb-2">
          {winner} Wins!
        </h3>
        <button
          onClick={() => onMove({ type: 'new_game' })}
          className="bg-purple-500 text-white px-6 py-3 rounded-lg hover:bg-purple-600 transition-colors"
        >
          Play Again
        </button>
      </div>
    );
  };

  return (
    <div className="mafia-game max-w-2xl mx-auto">
      <div className="mb-6">
        <h3 className="text-xl font-bold text-gray-800 mb-2">🕵️ Mafia Game</h3>
      </div>

      {gamePhase === 'lobby' && renderLobby()}
      
      {gamePhase !== 'lobby' && gamePhase !== 'ended' && (
        <>
          {renderRole()}
          {renderPhaseInfo()}
          {renderPlayers()}
          {renderNightActions()}
        </>
      )}
      
      {gamePhase === 'ended' && renderGameEnd()}
      
      {gameLog.length > 0 && renderGameLog()}

      {/* Game Rules */}
      <div className="mt-4 text-xs text-gray-500 bg-blue-50 rounded-lg p-3">
        <strong>How to play:</strong> Mafia eliminates townspeople at night. Town votes out suspected mafia during day. 
        Detective investigates, Doctor protects. Town wins by eliminating all mafia. Mafia wins by equaling town numbers.
      </div>
    </div>
  );
};

export default MafiaGame;