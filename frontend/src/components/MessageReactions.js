import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';

const MessageReactions = ({ 
  messageId, 
  reactions = [], 
  onAddReaction, 
  onRemoveReaction,
  currentUserId 
}) => {
  const { t } = useTranslation();
  const [showTooltip, setShowTooltip] = useState(null);

  // Quick reaction buttons (common emojis)
  const quickReactions = ['👍', '❤️', '😂', '😮', '😢', '😡'];

  const handleQuickReaction = (emoji) => {
    const existingReaction = reactions.find(r => r.emoji === emoji && r.user_reacted);
    
    if (existingReaction) {
      onRemoveReaction(messageId, emoji);
    } else {
      onAddReaction(messageId, emoji);
    }
  };

  const getReactionTooltip = (reaction) => {
    if (!reaction.users || reaction.users.length === 0) return '';
    
    const names = reaction.users.map(user => user.display_name || user.username);
    
    if (names.length === 1) {
      return names[0];
    } else if (names.length === 2) {
      return `${names[0]} and ${names[1]}`;
    } else if (names.length <= 5) {
      return `${names.slice(0, -1).join(', ')} and ${names[names.length - 1]}`;
    } else {
      return `${names.slice(0, 3).join(', ')} and ${names.length - 3} others`;
    }
  };

  if (!reactions || reactions.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-wrap gap-1 mt-1 relative">
      {reactions.map((reaction, index) => (
        <div
          key={`${reaction.emoji}-${index}`}
          className="relative"
          onMouseEnter={() => setShowTooltip(reaction.emoji)}
          onMouseLeave={() => setShowTooltip(null)}
        >
          <button
            onClick={() => handleQuickReaction(reaction.emoji)}
            className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs border transition-all hover:scale-105 ${
              reaction.user_reacted
                ? 'bg-blue-100 border-blue-300 text-blue-800'
                : 'bg-gray-100 border-gray-300 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <span className="text-sm">{reaction.emoji}</span>
            {reaction.count > 1 && (
              <span className="font-medium">{reaction.count}</span>
            )}
          </button>

          {/* Tooltip */}
          {showTooltip === reaction.emoji && (
            <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 z-50">
              <div className="bg-gray-800 text-white text-xs rounded px-2 py-1 whitespace-nowrap">
                {getReactionTooltip(reaction)}
                <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-800"></div>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default MessageReactions;