import React, { useState, useEffect } from 'react';

const AdvancedCustomization = ({ onClose, currentSettings, onSettingsChange }) => {
  const [activeTab, setActiveTab] = useState('themes');
  const [settings, setSettings] = useState({
    theme: 'whatsapp',
    dynamicTheme: false,
    animations: 'smooth',
    soundPack: 'default',
    customBackground: '',
    particleEffects: false,
    glassmorphism: false,
    darkMode: false,
    accentColor: '#25D366',
    fontSize: 'medium',
    fontFamily: 'Inter',
    borderRadius: 'medium',
    spacing: 'normal',
    messageStyle: 'modern',
    ...currentSettings
  });

  const [previewMode, setPreviewMode] = useState(false);

  const themes = {
    whatsapp: {
      name: 'WhatsApp Classic',
      description: 'Clean and familiar WhatsApp-inspired design',
      preview: '💚',
      colors: {
        primary: '#25D366',
        secondary: '#128C7E',
        background: '#ffffff',
        surface: '#f0f0f0',
        text: '#1f2937'
      }
    },
    discord: {
      name: 'Discord Dark',
      description: 'Gaming-focused dark theme with vibrant accents',
      preview: '🎮',
      colors: {
        primary: '#5865F2',
        secondary: '#4752C4',
        background: '#36393f',
        surface: '#2f3136',
        text: '#ffffff'
      }
    },
    telegram: {
      name: 'Telegram Blue',
      description: 'Elegant blue design inspired by Telegram',
      preview: '💙',
      colors: {
        primary: '#0088cc',
        secondary: '#0077b3',
        background: '#ffffff',
        surface: '#f4f4f5',
        text: '#1f2937'
      }
    },
    sunset: {
      name: 'Sunset Gradient',
      description: 'Warm gradient theme with sunset colors',
      preview: '🌅',
      colors: {
        primary: '#ff6b6b',
        secondary: '#feca57',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        surface: 'rgba(255, 255, 255, 0.1)',
        text: '#ffffff'
      }
    },
    ocean: {
      name: 'Ocean Breeze',
      description: 'Cool and calming ocean-inspired theme',
      preview: '🌊',
      colors: {
        primary: '#0077be',
        secondary: '#00a8cc',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        surface: 'rgba(255, 255, 255, 0.15)',
        text: '#ffffff'
      }
    },
    nature: {
      name: 'Forest Green',
      description: 'Natural green theme for a calming experience',
      preview: '🌿',
      colors: {
        primary: '#2ecc71',
        secondary: '#27ae60',
        background: '#ffffff',
        surface: '#f8f9fa',
        text: '#2c3e50'
      }
    }
  };

  const animationOptions = [
    { value: 'none', label: 'No Animations', description: 'Disable all animations for faster performance' },
    { value: 'minimal', label: 'Minimal', description: 'Only essential animations' },
    { value: 'smooth', label: 'Smooth', description: 'Balanced animations for best experience' },
    { value: 'rich', label: 'Rich', description: 'Full animations with extra effects' },
    { value: 'extreme', label: 'Extreme', description: 'Maximum animations and effects' }
  ];

  const soundPacks = [
    { value: 'default', label: 'Default', description: 'Standard notification sounds' },
    { value: 'nature', label: 'Nature', description: 'Peaceful nature sounds' },
    { value: 'tech', label: 'Tech', description: 'Futuristic electronic sounds' },
    { value: 'retro', label: 'Retro', description: 'Classic arcade game sounds' },
    { value: 'minimal', label: 'Minimal', description: 'Subtle and quiet sounds' },
    { value: 'silent', label: 'Silent', description: 'No sounds at all' }
  ];

  const fontOptions = [
    { value: 'Inter', label: 'Inter (Modern)', preview: 'Aa' },
    { value: 'Roboto', label: 'Roboto (Android)', preview: 'Aa' },
    { value: 'San Francisco', label: 'SF Pro (iOS)', preview: 'Aa' },
    { value: 'Helvetica Neue', label: 'Helvetica Neue', preview: 'Aa' },
    { value: 'Arial', label: 'Arial (Classic)', preview: 'Aa' },
    { value: 'Georgia', label: 'Georgia (Serif)', preview: 'Aa' },
    { value: 'Courier New', label: 'Courier (Mono)', preview: 'Aa' },
    { value: 'Comic Sans MS', label: 'Comic Sans (Fun)', preview: 'Aa' }
  ];

  const messageStyles = [
    { value: 'modern', label: 'Modern Bubbles', description: 'Rounded message bubbles with shadows' },
    { value: 'classic', label: 'Classic', description: 'Traditional rectangular messages' },
    { value: 'minimal', label: 'Minimal', description: 'Clean lines without borders' },
    { value: 'retro', label: 'Retro', description: 'Vintage terminal-style messages' },
    { value: 'glass', label: 'Glass', description: 'Transparent glassmorphism effect' }
  ];

  useEffect(() => {
    if (previewMode) {
      applyPreviewStyles();
    }
  }, [settings, previewMode]);

  const applyPreviewStyles = () => {
    const root = document.documentElement;
    const theme = themes[settings.theme];
    
    if (theme) {
      root.style.setProperty('--primary-color', theme.colors.primary);
      root.style.setProperty('--secondary-color', theme.colors.secondary);
      root.style.setProperty('--bg-color', theme.colors.background);
      root.style.setProperty('--surface-color', theme.colors.surface);
      root.style.setProperty('--text-color', theme.colors.text);
    }
    
    root.style.setProperty('--font-family', settings.fontFamily);
    root.style.setProperty('--font-size', settings.fontSize);
    root.style.setProperty('--accent-color', settings.accentColor);
    
    // Apply animation class
    document.body.className = `animations-${settings.animations}`;
    
    // Apply glassmorphism
    if (settings.glassmorphism) {
      document.body.classList.add('glassmorphism');
    } else {
      document.body.classList.remove('glassmorphism');
    }
  };

  const handleSettingChange = (key, value) => {
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);
    
    if (previewMode) {
      onSettingsChange(newSettings);
    }
  };

  const applySettings = () => {
    onSettingsChange(settings);
    localStorage.setItem('chatapp-advanced-settings', JSON.stringify(settings));
    onClose();
  };

  const resetToDefaults = () => {
    const defaultSettings = {
      theme: 'whatsapp',
      dynamicTheme: false,
      animations: 'smooth',
      soundPack: 'default',
      customBackground: '',
      particleEffects: false,
      glassmorphism: false,
      darkMode: false,
      accentColor: '#25D366',
      fontSize: 'medium',
      fontFamily: 'Inter',
      borderRadius: 'medium',
      spacing: 'normal',
      messageStyle: 'modern'
    };
    setSettings(defaultSettings);
  };

  const exportSettings = () => {
    const dataStr = JSON.stringify(settings, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'chatapp-theme-settings.json';
    link.click();
  };

  const importSettings = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const importedSettings = JSON.parse(e.target.result);
          setSettings(importedSettings);
        } catch (error) {
          alert('Invalid settings file');
        }
      };
      reader.readAsText(file);
    }
  };

  const renderThemesTab = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Choose Your Theme</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(themes).map(([key, theme]) => (
            <div
              key={key}
              onClick={() => handleSettingChange('theme', key)}
              className={`p-4 border-2 rounded-lg cursor-pointer transition-all hover:shadow-md ${
                settings.theme === key ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
              }`}
            >
              <div className="text-center mb-3">
                <div className="text-3xl mb-2">{theme.preview}</div>
                <h4 className="font-semibold text-gray-900">{theme.name}</h4>
                <p className="text-sm text-gray-600">{theme.description}</p>
              </div>
              <div className="flex space-x-2 justify-center">
                <div
                  className="w-6 h-6 rounded-full border"
                  style={{ backgroundColor: theme.colors.primary }}
                />
                <div
                  className="w-6 h-6 rounded-full border"
                  style={{ backgroundColor: theme.colors.secondary }}
                />
                <div
                  className="w-6 h-6 rounded-full border"
                  style={{ backgroundColor: theme.colors.background === '#ffffff' ? '#f0f0f0' : theme.colors.background }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Theme Options</h3>
        <div className="space-y-4">
          <label className="flex items-center space-x-3">
            <input
              type="checkbox"
              checked={settings.dynamicTheme}
              onChange={(e) => handleSettingChange('dynamicTheme', e.target.checked)}
              className="rounded"
            />
            <div>
              <div className="font-medium">Dynamic Theme</div>
              <div className="text-sm text-gray-600">Theme changes based on time of day</div>
            </div>
          </label>

          <label className="flex items-center space-x-3">
            <input
              type="checkbox"
              checked={settings.darkMode}
              onChange={(e) => handleSettingChange('darkMode', e.target.checked)}
              className="rounded"
            />
            <div>
              <div className="font-medium">Dark Mode Override</div>
              <div className="text-sm text-gray-600">Force dark mode regardless of theme</div>
            </div>
          </label>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Custom Accent Color</label>
            <div className="flex items-center space-x-3">
              <input
                type="color"
                value={settings.accentColor}
                onChange={(e) => handleSettingChange('accentColor', e.target.value)}
                className="w-12 h-10 rounded border"
              />
              <input
                type="text"
                value={settings.accentColor}
                onChange={(e) => handleSettingChange('accentColor', e.target.value)}
                className="flex-1 p-2 border rounded-lg"
                placeholder="#25D366"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderAnimationsTab = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Animation Settings</h3>
        <div className="space-y-3">
          {animationOptions.map(option => (
            <label
              key={option.value}
              className={`block p-4 border-2 rounded-lg cursor-pointer transition-all ${
                settings.animations === option.value ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
              }`}
            >
              <input
                type="radio"
                name="animations"
                value={option.value}
                checked={settings.animations === option.value}
                onChange={(e) => handleSettingChange('animations', e.target.value)}
                className="sr-only"
              />
              <div className="font-medium text-gray-900">{option.label}</div>
              <div className="text-sm text-gray-600">{option.description}</div>
            </label>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Visual Effects</h3>
        <div className="space-y-4">
          <label className="flex items-center space-x-3">
            <input
              type="checkbox"
              checked={settings.particleEffects}
              onChange={(e) => handleSettingChange('particleEffects', e.target.checked)}
              className="rounded"
            />
            <div>
              <div className="font-medium">Particle Effects</div>
              <div className="text-sm text-gray-600">Animated particles in the background</div>
            </div>
          </label>

          <label className="flex items-center space-x-3">
            <input
              type="checkbox"
              checked={settings.glassmorphism}
              onChange={(e) => handleSettingChange('glassmorphism', e.target.checked)}
              className="rounded"
            />
            <div>
              <div className="font-medium">Glassmorphism Effect</div>
              <div className="text-sm text-gray-600">Translucent glass-like surfaces</div>
            </div>
          </label>
        </div>
      </div>
    </div>
  );

  const renderTypographyTab = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Font Family</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {fontOptions.map(font => (
            <div
              key={font.value}
              onClick={() => handleSettingChange('fontFamily', font.value)}
              className={`p-3 border-2 rounded-lg cursor-pointer text-center transition-all ${
                settings.fontFamily === font.value ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
              }`}
              style={{ fontFamily: font.value }}
            >
              <div className="text-2xl mb-1">{font.preview}</div>
              <div className="text-sm font-medium">{font.label}</div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Font Size</h3>
        <div className="flex space-x-3">
          {['small', 'medium', 'large', 'xl'].map(size => (
            <button
              key={size}
              onClick={() => handleSettingChange('fontSize', size)}
              className={`px-4 py-2 rounded-lg capitalize transition-all ${
                settings.fontSize === size
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {size}
            </button>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Message Style</h3>
        <div className="space-y-3">
          {messageStyles.map(style => (
            <label
              key={style.value}
              className={`block p-4 border-2 rounded-lg cursor-pointer transition-all ${
                settings.messageStyle === style.value ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
              }`}
            >
              <input
                type="radio"
                name="messageStyle"
                value={style.value}
                checked={settings.messageStyle === style.value}
                onChange={(e) => handleSettingChange('messageStyle', e.target.value)}
                className="sr-only"
              />
              <div className="font-medium text-gray-900">{style.label}</div>
              <div className="text-sm text-gray-600">{style.description}</div>
            </label>
          ))}
        </div>
      </div>
    </div>
  );

  const renderSoundsTab = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Sound Pack</h3>
        <div className="space-y-3">
          {soundPacks.map(pack => (
            <label
              key={pack.value}
              className={`block p-4 border-2 rounded-lg cursor-pointer transition-all ${
                settings.soundPack === pack.value ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
              }`}
            >
              <input
                type="radio"
                name="soundPack"
                value={pack.value}
                checked={settings.soundPack === pack.value}
                onChange={(e) => handleSettingChange('soundPack', e.target.value)}
                className="sr-only"
              />
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-gray-900">{pack.label}</div>
                  <div className="text-sm text-gray-600">{pack.description}</div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    // Play preview sound
                    console.log(`Playing preview for ${pack.value}`);
                  }}
                  className="px-3 py-1 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  Preview
                </button>
              </div>
            </label>
          ))}
        </div>
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-6xl max-h-[90vh] overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">🎨 Advanced Customization</h2>
            <p className="text-gray-600">Personalize every aspect of your experience</p>
          </div>
          <div className="flex items-center space-x-3">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={previewMode}
                onChange={(e) => setPreviewMode(e.target.checked)}
                className="rounded"
              />
              <span className="text-sm font-medium">Live Preview</span>
            </label>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 p-2"
            >
              ✕
            </button>
          </div>
        </div>

        <div className="flex">
          {/* Sidebar */}
          <div className="w-64 bg-gray-50 border-r">
            <nav className="p-4 space-y-2">
              {[
                { id: 'themes', label: 'Themes', icon: '🎨' },
                { id: 'animations', label: 'Animations', icon: '✨' },
                { id: 'typography', label: 'Typography', icon: '📝' },
                { id: 'sounds', label: 'Sounds', icon: '🔊' }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full text-left p-3 rounded-lg transition-colors ${
                    activeTab === tab.id
                      ? 'bg-blue-100 text-blue-900 font-medium'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  {tab.icon} {tab.label}
                </button>
              ))}
            </nav>
          </div>

          {/* Content */}
          <div className="flex-1 p-6 overflow-y-auto" style={{ maxHeight: 'calc(90vh - 140px)' }}>
            {activeTab === 'themes' && renderThemesTab()}
            {activeTab === 'animations' && renderAnimationsTab()}
            {activeTab === 'typography' && renderTypographyTab()}
            {activeTab === 'sounds' && renderSoundsTab()}
          </div>
        </div>

        {/* Footer */}
        <div className="border-t p-4 bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="flex space-x-3">
              <button
                onClick={resetToDefaults}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors"
              >
                Reset to Defaults
              </button>
              <label className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors cursor-pointer">
                Import Settings
                <input
                  type="file"
                  accept=".json"
                  onChange={importSettings}
                  className="hidden"
                />
              </label>
              <button
                onClick={exportSettings}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Export Settings
              </button>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={onClose}
                className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={applySettings}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Apply Changes
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdvancedCustomization;