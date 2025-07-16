import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

const ThemeCustomizer = ({ onClose, onApplyTheme, currentTheme = 'default' }) => {
  const { t } = useTranslation();
  const [selectedTheme, setSelectedTheme] = useState(currentTheme);

  // Predefined themes
  const predefinedThemes = {
    default: {
      name: 'Default',
      colors: {
        primary: '#3B82F6',
        secondary: '#6366F1',
        accent: '#8B5CF6',
        background: '#F9FAFB',
        surface: '#FFFFFF',
        text: '#111827',
        textSecondary: '#6B7280'
      },
      chatBubbles: {
        style: 'rounded',
        ownBubbleColor: '#3B82F6',
        otherBubbleColor: '#F3F4F6',
        textColor: '#FFFFFF',
        otherTextColor: '#111827'
      }
    },
    dark: {
      name: 'Dark Mode',
      colors: {
        primary: '#3B82F6',
        secondary: '#6366F1',
        accent: '#8B5CF6',
        background: '#111827',
        surface: '#1F2937',
        text: '#F9FAFB',
        textSecondary: '#D1D5DB'
      },
      chatBubbles: {
        style: 'rounded',
        ownBubbleColor: '#3B82F6',
        otherBubbleColor: '#374151',
        textColor: '#FFFFFF',
        otherTextColor: '#F9FAFB'
      }
    },
    purple: {
      name: 'Purple Dream',
      colors: {
        primary: '#8B5CF6',
        secondary: '#A855F7',
        accent: '#C084FC',
        background: '#FAF5FF',
        surface: '#FFFFFF',
        text: '#581C87',
        textSecondary: '#7C3AED'
      },
      chatBubbles: {
        style: 'rounded',
        ownBubbleColor: '#8B5CF6',
        otherBubbleColor: '#F3E8FF',
        textColor: '#FFFFFF',
        otherTextColor: '#581C87'
      }
    },
    ocean: {
      name: 'Ocean Breeze',
      colors: {
        primary: '#0891B2',
        secondary: '#0E7490',
        accent: '#06B6D4',
        background: '#F0F9FF',
        surface: '#FFFFFF',
        text: '#0C4A6E',
        textSecondary: '#0369A1'
      },
      chatBubbles: {
        style: 'rounded',
        ownBubbleColor: '#0891B2',
        otherBubbleColor: '#E0F2FE',
        textColor: '#FFFFFF',
        otherTextColor: '#0C4A6E'
      }
    }
  };

  const applyTheme = (themeId) => {
    const theme = predefinedThemes[themeId];
    if (theme) {
      onApplyTheme(theme);
      setSelectedTheme(themeId);
    }
  };

  const getThemePreview = (theme) => (
    <div className="w-full h-20 rounded-lg overflow-hidden border-2 border-gray-200">
      <div 
        className="h-full flex items-end p-2"
        style={{ backgroundColor: theme.colors.background }}
      >
        <div className="flex space-x-1">
          <div 
            className="w-8 h-4 rounded text-xs"
            style={{ backgroundColor: theme.chatBubbles.otherBubbleColor }}
            aria-hidden="true"
          ></div>
          <div 
            className="w-12 h-4 rounded text-xs"
            style={{ backgroundColor: theme.chatBubbles.ownBubbleColor }}
            aria-hidden="true"
          ></div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-labelledby="theme-customizer-title">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 id="theme-customizer-title" className="text-2xl font-bold text-gray-900 flex items-center space-x-2">
              <span aria-hidden="true">🎨</span>
              <span>{t('themes.title')}</span>
            </h2>
            <button 
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-xl"
              aria-label="Close theme customizer"
            >
              <span aria-hidden="true">✕</span>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-4">
                {t('themes.currentTheme')}: {predefinedThemes[selectedTheme]?.name || 'Custom'}
              </h3>
              
              {/* Predefined Themes */}
              <div className="grid grid-cols-2 gap-4" role="radiogroup" aria-labelledby="theme-selection-title">
                <h4 id="theme-selection-title" className="sr-only">Select a theme</h4>
                {Object.entries(predefinedThemes).map(([key, theme]) => (
                  <div key={key} className="text-center">
                    <button
                      onClick={() => applyTheme(key)}
                      className={`w-full mb-2 border-2 rounded-lg overflow-hidden transition-all ${
                        selectedTheme === key ? 'border-blue-500 shadow-lg' : 'border-gray-200 hover:border-gray-300'
                      }`}
                      role="radio"
                      aria-checked={selectedTheme === key}
                      aria-label={`Select ${theme.name} theme`}
                      aria-describedby={`theme-${key}-description`}
                    >
                      {getThemePreview(theme)}
                    </button>
                    <p id={`theme-${key}-description`} className="text-sm font-medium">{theme.name}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 flex justify-between">
          <button
            onClick={onClose}
            className="px-6 py-2 text-gray-600 hover:text-gray-800 transition-colors"
            aria-label="Cancel theme selection"
          >
            {t('common.cancel')}
          </button>
          <button
            onClick={() => {
              const theme = predefinedThemes[selectedTheme];
              if (theme) {
                onApplyTheme(theme);
                onClose();
              }
            }}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            aria-label={`Apply ${predefinedThemes[selectedTheme]?.name || 'selected'} theme`}
          >
            {t('themes.apply')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ThemeCustomizer;