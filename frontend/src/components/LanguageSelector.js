import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';

const LanguageSelector = ({ className = "" }) => {
  const { i18n, t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);

  const languages = [
    { code: 'en', name: t('languages.english'), flag: '🇺🇸', dir: 'ltr' },
    { code: 'hi', name: t('languages.hindi'), flag: '🇮🇳', dir: 'ltr' },
    { code: 'bn', name: t('languages.bengali'), flag: '🇧🇩', dir: 'ltr' },
    { code: 'te', name: t('languages.telugu'), flag: '🇮🇳', dir: 'ltr' },
    { code: 'mr', name: t('languages.marathi'), flag: '🇮🇳', dir: 'ltr' },
    { code: 'ta', name: t('languages.tamil'), flag: '🇮🇳', dir: 'ltr' },
    { code: 'gu', name: t('languages.gujarati'), flag: '🇮🇳', dir: 'ltr' },
    { code: 'ur', name: t('languages.urdu'), flag: '🇵🇰', dir: 'rtl' },
    { code: 'kn', name: t('languages.kannada'), flag: '🇮🇳', dir: 'ltr' },
    { code: 'ml', name: t('languages.malayalam'), flag: '🇮🇳', dir: 'ltr' },
    { code: 'pa', name: t('languages.punjabi'), flag: '🇮🇳', dir: 'ltr' }
  ];

  const currentLanguage = languages.find(lang => lang.code === i18n.language) || languages[0];

  const handleLanguageChange = (langCode, direction) => {
    // Change language
    i18n.changeLanguage(langCode);
    
    // Set text direction for RTL languages
    document.documentElement.dir = direction;
    document.documentElement.lang = langCode;
    
    // Store in localStorage with explicit key
    localStorage.setItem('i18nextLng', langCode);
    
    // Also store as backup
    localStorage.setItem('pulse-language', langCode);
    
    // Close dropdown immediately
    setIsOpen(false);
    
    // Force immediate re-render of the entire app
    setTimeout(() => {
      // Trigger a custom event to force app re-render
      window.dispatchEvent(new CustomEvent('languageChanged', { detail: langCode }));
      
      // Force page reload as final fallback to ensure all components update
      window.location.reload();
    }, 200);
  };

  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 px-3 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all shadow-sm"
        title={t('languages.changeLanguage')}
      >
        <span className="text-lg">{currentLanguage.flag}</span>
        <span className="text-sm font-medium text-gray-700">{currentLanguage.name}</span>
        <svg 
          className={`w-4 h-4 text-gray-500 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setIsOpen(false)}
          />
          
          {/* Dropdown */}
          <div className="absolute top-full left-0 mt-1 w-64 bg-white border border-gray-200 rounded-lg shadow-lg z-20 max-h-80 overflow-y-auto">
            <div className="p-2">
              <div className="text-xs font-semibold text-gray-500 px-3 py-2 uppercase tracking-wider">
                {t('languages.changeLanguage')}
              </div>
              {languages.map((language) => (
                <button
                  key={language.code}
                  onClick={() => handleLanguageChange(language.code, language.dir)}
                  className={`w-full flex items-center space-x-3 px-3 py-2 text-left hover:bg-purple-50 rounded-md transition-colors ${
                    currentLanguage.code === language.code 
                      ? 'bg-purple-100 text-purple-700 font-medium' 
                      : 'text-gray-700'
                  }`}
                >
                  <span className="text-lg">{language.flag}</span>
                  <span className="text-sm">{language.name}</span>
                  {currentLanguage.code === language.code && (
                    <span className="ml-auto text-purple-600">
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default LanguageSelector;