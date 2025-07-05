import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Translation files
import en from './locales/en.json';
import hi from './locales/hi.json';
import bn from './locales/bn.json';
import te from './locales/te.json';
import mr from './locales/mr.json';
import ta from './locales/ta.json';
import gu from './locales/gu.json';
import ur from './locales/ur.json';
import kn from './locales/kn.json';
import ml from './locales/ml.json';
import pa from './locales/pa.json';

const resources = {
  en: { translation: en },
  hi: { translation: hi },
  bn: { translation: bn },
  te: { translation: te },
  mr: { translation: mr },
  ta: { translation: ta },
  gu: { translation: gu },
  ur: { translation: ur },
  kn: { translation: kn },
  ml: { translation: ml },
  pa: { translation: pa }
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    lng: localStorage.getItem('i18nextLng') || 'en', // Use stored language or default to English
    
    detection: {
      order: ['localStorage', 'navigator', 'htmlTag', 'cookie'],
      lookupLocalStorage: 'i18nextLng',
      lookupCookie: 'i18next',
      lookupFromPathIndex: 0,
      lookupFromSubdomainIndex: 0,
      caches: ['localStorage', 'cookie'],
      excludeCacheFor: ['cimode'],
      checkWhitelist: true
    },

    interpolation: {
      escapeValue: false
    },

    react: {
      useSuspense: false
    },

    // Force synchronous loading
    load: 'languageOnly',
    preload: ['en', 'hi'],
    
    // Debug mode
    debug: false
  });

// Set initial language on load
const savedLang = localStorage.getItem('i18nextLng');
if (savedLang && savedLang !== i18n.language) {
  i18n.changeLanguage(savedLang);
  document.documentElement.lang = savedLang;
  document.documentElement.dir = savedLang === 'ur' ? 'rtl' : 'ltr';
}

export default i18n;