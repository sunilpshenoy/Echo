import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

const EmojiPicker = ({ onEmojiSelect, onClose, customEmojis = [] }) => {
  const { t } = useTranslation();
  const [activeCategory, setActiveCategory] = useState('smileys');
  const [searchQuery, setSearchQuery] = useState('');
  const [recentEmojis, setRecentEmojis] = useState([]);
  const pickerRef = useRef(null);

  // Emoji categories with commonly used emojis
  const emojiCategories = {
    recent: {
      name: t('emojis.recent'),
      icon: '🕐',
      emojis: recentEmojis
    },
    smileys: {
      name: t('emojis.smileysAndPeople'),
      icon: '😀',
      emojis: [
        '😀', '😃', '😄', '😁', '😆', '😅', '🤣', '😂', '🙂', '🙃', '😉', '😊', '😇',
        '🥰', '😍', '🤩', '😘', '😗', '☺️', '😚', '😙', '😋', '😛', '😜', '🤪',
        '😝', '🤑', '🤗', '🤔', '😐', '😑', '😶', '😏', '😒', '🙄', '😬', '🤥',
        '😔', '😪', '🤤', '😴', '😷', '🤒', '🤕', '🤢', '🤮', '🤧', '🥵', '🥶',
        '😵', '🤯', '🤠', '🥳', '😎', '🤓', '🧐', '😕', '😟', '🙁', '☹️', '😮',
        '😯', '😲', '😳', '🥺', '😦', '😧', '😨', '😰', '😥', '😢', '😭', '😱',
        '😖', '😣', '😞', '😓', '😩', '😫', '🥱', '😤', '😡', '😠', '🤬', '😈',
        '👿', '💀', '☠️', '💩', '🤡', '👹', '👺', '👻', '👽', '👾', '🤖'
      ]
    },
    animals: {
      name: t('emojis.animalsAndNature'),
      icon: '🐶',
      emojis: [
        '🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼', '🐨', '🐯', '🦁', '🐮',
        '🐷', '🐽', '🐸', '🐵', '🙈', '🙉', '🙊', '🐒', '🐔', '🐧', '🐦', '🐤',
        '🐣', '🐥', '🦆', '🦅', '🦉', '🦇', '🐺', '🐗', '🐴', '🦄', '🐝', '🐛',
        '🦋', '🐌', '🐞', '🐜', '🦟', '🦗', '🕷️', '🦂', '🐢', '🐍', '🦎', '🦖',
        '🦕', '🐙', '🦑', '🦐', '🦞', '🦀', '🐡', '🐠', '🐟', '🐬', '🐳', '🐋',
        '🦈', '🐊', '🐅', '🐆', '🦓', '🦍', '🦧', '🐘', '🦛', '🦏', '🐪', '🐫',
        '🦒', '🦘', '🐃', '🐂', '🐄', '🐎', '🐖', '🐏', '🐑', '🦙', '🐐', '🦌'
      ]
    },
    food: {
      name: t('emojis.foodAndDrink'),
      icon: '🍎',
      emojis: [
        '🍎', '🍐', '🍊', '🍋', '🍌', '🍉', '🍇', '🍓', '🍈', '🍒', '🍑', '🥭',
        '🍍', '🥥', '🥝', '🍅', '🍆', '🥑', '🥦', '🥬', '🥒', '🌶️', '🌽', '🥕',
        '🧄', '🧅', '🥔', '🍠', '🥐', '🥖', '🍞', '🥨', '🥯', '🧀', '🥚', '🍳',
        '🧈', '🥞', '🧇', '🥓', '🥩', '🍗', '🍖', '🌭', '🍔', '🍟', '🍕', '🥪',
        '🥙', '🧆', '🌮', '🌯', '🥗', '🍝', '🍜', '🍲', '🍛', '🍣', '🍱', '🥟',
        '🦪', '🍤', '🍙', '🍚', '🍘', '🍥', '🥠', '🥮', '🍢', '🍡', '🍧', '🍨',
        '🍦', '🥧', '🧁', '🍰', '🎂', '🍮', '🍭', '🍬', '🍫', '🍿', '🍩', '🍪'
      ]
    },
    activities: {
      name: t('emojis.activitiesAndSports'),
      icon: '⚽',
      emojis: [
        '⚽', '🏀', '🏈', '⚾', '🥎', '🎾', '🏐', '🏉', '🥏', '🎱', '🏓', '🏸',
        '🏒', '🏑', '🥍', '🏏', '⛳', '🏹', '🎣', '🤿', '🥊', '🥋', '🎽', '🛹',
        '🛼', '🛷', '⛸️', '🥌', '🎿', '⛷️', '🏂', '🏋️', '🤸', '⛹️', '🤺', '🤾',
        '🏌️', '🧘', '🏃', '🚶', '🧎', '🏇', '🧗', '🤹', '🎪', '🎨', '🎬', '🎤',
        '🎧', '🎼', '🎵', '🎶', '🥇', '🥈', '🥉', '🏆', '🏅', '🎖️', '🎗️', '🎫'
      ]
    },
    travel: {
      name: t('emojis.travelAndPlaces'),
      icon: '🚗',
      emojis: [
        '🚗', '🚕', '🚙', '🚌', '🚎', '🏎️', '🚓', '🚑', '🚒', '🚐', '🚚', '🚛',
        '🚜', '🏍️', '🛵', '🚲', '🛴', '🛹', '🚁', '✈️', '🛩️', '🛫', '🛬', '🚀',
        '🛰️', '🚉', '🚞', '🚝', '🚄', '🚅', '🚈', '🚂', '🚆', '🚇', '🚊', '🚟',
        '🚠', '🚡', '⛴️', '🚤', '🛥️', '🛳️', '⛵', '🚢', '⚓', '⛽', '🚧', '🚨',
        '🚥', '🚦', '🛑', '🏰', '🏯', '🏟️', '🎡', '🎢', '🎠', '⛲', '⛱️', '🏖️',
        '🏝️', '🏜️', '🌋', '⛰️', '🏔️', '🗻', '🏕️', '⛺', '🏠', '🏡', '🏘️', '🏚️'
      ]
    },
    objects: {
      name: t('emojis.objectsAndSymbols'),
      icon: '⌚',
      emojis: [
        '⌚', '📱', '📲', '💻', '⌨️', '🖥️', '🖨️', '🖱️', '📞', '☎️', '📠', '📺',
        '📻', '⏰', '⏳', '⌛', '📡', '🔋', '🔌', '💡', '🔦', '🕯️', '💸', '💵',
        '💴', '💶', '💷', '💰', '💳', '💎', '⚖️', '🔧', '🔨', '⚒️', '🛠️', '⛏️',
        '🔩', '⚙️', '🧱', '⛓️', '🔫', '💣', '🧨', '🔪', '🗡️', '⚔️', '🛡️', '🚬',
        '⚰️', '⚱️', '🏺', '🔮', '📿', '💈', '⚗️', '🔭', '🔬', '💊', '💉', '🧬',
        '🦠', '🧫', '🧪', '🌡️', '🧹', '🧺', '🧻', '🚽', '🚿', '🛁', '🧼', '🪥'
      ]
    },
    symbols: {
      name: t('emojis.symbols'),
      icon: '❤️',
      emojis: [
        '❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎', '💔', '❣️', '💕',
        '💞', '💓', '💗', '💖', '💘', '💝', '💟', '✨', '🌟', '💫', '⭐', '🌠',
        '☄️', '🔥', '💥', '💯', '💢', '♨️', '💨', '🕳️', '💤', '👍', '👎', '👌',
        '✌️', '🤞', '🤟', '🤘', '🤙', '👈', '👉', '👆', '🖕', '👇', '☝️', '👋',
        '🤚', '🖐️', '✋', '🖖', '👏', '🙌', '🤲', '🤝', '🙏', '✍️', '💅', '🤳'
      ]
    },
    custom: {
      name: t('emojis.custom'),
      icon: '⭐',
      emojis: customEmojis
    }
  };

  // Handle emoji search
  const filteredEmojis = searchQuery
    ? Object.entries(emojiCategories).reduce((acc, [categoryKey, category]) => {
        const filtered = category.emojis.filter(emoji => {
          if (typeof emoji === 'string') {
            return emoji.includes(searchQuery);
          } else {
            return emoji.name?.toLowerCase().includes(searchQuery.toLowerCase());
          }
        });
        if (filtered.length > 0) {
          acc[categoryKey] = { ...category, emojis: filtered };
        }
        return acc;
      }, {})
    : emojiCategories;

  // Load recent emojis from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('pulse_recent_emojis');
    if (saved) {
      setRecentEmojis(JSON.parse(saved));
    }
  }, []);

  // Handle emoji selection
  const handleEmojiSelect = (emoji) => {
    let emojiToAdd = emoji;
    
    // Handle custom emoji
    if (typeof emoji === 'object') {
      emojiToAdd = {
        type: 'custom',
        id: emoji.emoji_id,
        name: emoji.name,
        data: emoji.file_data
      };
    }

    // Add to recent emojis
    const newRecent = [emojiToAdd, ...recentEmojis.filter(e => {
      if (typeof e === 'object' && typeof emojiToAdd === 'object') {
        return e.id !== emojiToAdd.id;
      }
      return e !== emojiToAdd;
    })].slice(0, 24);
    
    setRecentEmojis(newRecent);
    localStorage.setItem('pulse_recent_emojis', JSON.stringify(newRecent));

    onEmojiSelect(emojiToAdd);
  };

  // Handle clicks outside to close
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (pickerRef.current && !pickerRef.current.contains(event.target)) {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  return (
    <div 
      ref={pickerRef}
      className="absolute bottom-12 left-0 bg-white rounded-2xl shadow-2xl border border-gray-200 w-80 h-96 z-50 flex flex-col"
    >
      {/* Header */}
      <div className="p-3 border-b border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-medium text-gray-900">{t('emojis.picker')}</h3>
          <button 
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-lg"
          >
            ✕
          </button>
        </div>
        
        {/* Search */}
        <input
          type="text"
          placeholder={t('emojis.search')}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {/* Category tabs */}
      <div className="flex overflow-x-auto border-b border-gray-200 px-1">
        {Object.entries(emojiCategories).map(([categoryKey, category]) => (
          <button
            key={categoryKey}
            onClick={() => setActiveCategory(categoryKey)}
            className={`flex-shrink-0 px-3 py-2 text-lg hover:bg-gray-100 rounded-lg ${
              activeCategory === categoryKey ? 'bg-blue-100 ring-1 ring-blue-500' : ''
            }`}
            title={category.name}
          >
            {category.icon}
          </button>
        ))}
      </div>

      {/* Emoji grid */}
      <div className="flex-1 overflow-y-auto p-2">
        {searchQuery ? (
          // Search results
          <div className="space-y-3">
            {Object.entries(filteredEmojis).map(([categoryKey, category]) => (
              <div key={categoryKey}>
                <h4 className="text-xs font-medium text-gray-500 mb-1">{category.name}</h4>
                <div className="grid grid-cols-8 gap-1">
                  {category.emojis.map((emoji, index) => (
                    <button
                      key={`${categoryKey}-${index}`}
                      onClick={() => handleEmojiSelect(emoji)}
                      className="w-8 h-8 flex items-center justify-center hover:bg-gray-100 rounded text-lg"
                      title={typeof emoji === 'object' ? emoji.name : emoji}
                    >
                      {typeof emoji === 'object' ? (
                        <img 
                          src={`data:${emoji.file_type};base64,${emoji.file_data}`}
                          alt={emoji.name}
                          className="w-6 h-6 object-contain"
                        />
                      ) : (
                        emoji
                      )}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          // Category view
          <div className="grid grid-cols-8 gap-1">
            {filteredEmojis[activeCategory]?.emojis.map((emoji, index) => (
              <button
                key={index}
                onClick={() => handleEmojiSelect(emoji)}
                className="w-8 h-8 flex items-center justify-center hover:bg-gray-100 rounded text-lg transition-colors"
                title={typeof emoji === 'object' ? emoji.name : emoji}
              >
                {typeof emoji === 'object' ? (
                  <img 
                    src={`data:${emoji.file_type};base64,${emoji.file_data}`}
                    alt={emoji.name}
                    className="w-6 h-6 object-contain"
                  />
                ) : (
                  emoji
                )}
              </button>
            ))}
          </div>
        )}

        {/* No results */}
        {searchQuery && Object.keys(filteredEmojis).length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-2">🔍</div>
            <p className="text-sm">{t('emojis.noResults')}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default EmojiPicker;