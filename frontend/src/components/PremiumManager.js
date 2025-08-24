import React, { createContext, useContext, useState, useEffect } from 'react';

// ==================== PREMIUM FEATURES CONTEXT ====================

const PremiumContext = createContext();

export const usePremium = () => {
  const context = useContext(PremiumContext);
  if (!context) {
    throw new Error('usePremium must be used within PremiumProvider');
  }
  return context;
};

// ==================== PREMIUM FEATURES CONFIGURATION ====================

const PREMIUM_FEATURES = {
  // Tier-based features
  free: {
    features: ['chats', 'basic_games', 'basic_marketplace'],
    limits: {
      contacts: 50,
      groups: 2,
      games_per_day: 10,
      marketplace_listings: 3
    }
  },
  premium: {
    features: [
      'chats', 'teams', 'groups', 'advanced_games', 'marketplace', 
      'channels', 'trust_system', 'advanced_themes', 'priority_support'
    ],
    limits: {
      contacts: 500,
      groups: 25,
      games_per_day: 100,
      marketplace_listings: 25
    }
  },
  pro: {
    features: [
      'chats', 'teams', 'groups', 'advanced_games', 'marketplace',
      'channels', 'trust_system', 'advanced_themes', 'priority_support',
      'analytics', 'custom_branding', 'api_access', 'webhooks'
    ],
    limits: {
      contacts: 2000,
      groups: 100,
      games_per_day: 500,
      marketplace_listings: 100
    }
  }
};

// ==================== PREMIUM PROVIDER ====================

export const PremiumProvider = ({ children, user }) => {
  const [userTier, setUserTier] = useState('free');
  const [features, setFeatures] = useState(PREMIUM_FEATURES.free.features);
  const [limits, setLimits] = useState(PREMIUM_FEATURES.free.limits);
  const [usage, setUsage] = useState({});

  // Update premium status based on user data
  useEffect(() => {
    const tier = user?.subscription_tier || user?.premium_tier || 'free';
    const tierConfig = PREMIUM_FEATURES[tier] || PREMIUM_FEATURES.free;
    
    setUserTier(tier);
    setFeatures(tierConfig.features);
    setLimits(tierConfig.limits);
    
    // Load usage from localStorage or API
    const savedUsage = localStorage.getItem(`pulse_usage_${user?.user_id}`);
    if (savedUsage) {
      setUsage(JSON.parse(savedUsage));
    }
  }, [user]);

  // Feature access checker
  const hasFeature = (featureName) => {
    return features.includes(featureName);
  };

  // Limit checker
  const checkLimit = (limitType, currentValue) => {
    const limit = limits[limitType];
    return currentValue < limit;
  };

  // Usage tracker
  const trackUsage = (type, increment = 1) => {
    setUsage(prev => {
      const newUsage = {
        ...prev,
        [type]: (prev[type] || 0) + increment
      };
      
      // Save to localStorage
      localStorage.setItem(`pulse_usage_${user?.user_id}`, JSON.stringify(newUsage));
      
      return newUsage;
    });
  };

  // Upgrade prompt
  const promptUpgrade = (featureName) => {
    return {
      title: `Upgrade to Premium`,
      message: `${featureName} is a premium feature. Upgrade your account to unlock advanced capabilities.`,
      benefits: getPremiumBenefits(featureName),
      cta: 'Upgrade Now'
    };
  };

  const value = {
    userTier,
    features,
    limits,
    usage,
    hasFeature,
    checkLimit,
    trackUsage,
    promptUpgrade,
    isPremium: userTier !== 'free',
    isPro: userTier === 'pro'
  };

  return (
    <PremiumContext.Provider value={value}>
      {children}
    </PremiumContext.Provider>
  );
};

// ==================== PREMIUM BENEFITS ====================

const getPremiumBenefits = (featureName) => {
  const benefits = {
    teams: [
      '🏢 Professional team collaboration',
      '📋 Advanced project management', 
      '🎯 Team analytics and insights',
      '🔒 Enhanced security controls'
    ],
    groups: [
      '👥 Create unlimited groups',
      '🎨 Custom group themes',
      '📊 Group analytics dashboard',
      '🔧 Advanced moderation tools'
    ],
    advanced_games: [
      '🎮 Premium game collection',
      '🏆 Tournament creation',
      '💎 Exclusive game modes',
      '📈 Detailed game statistics'
    ],
    channels: [
      '📺 Broadcast channels',
      '📢 Announcement system',
      '🎤 Voice channels',
      '📱 Channel customization'
    ],
    trust_system: [
      '🛡️ Advanced verification',
      '⭐ Trust score analytics',
      '🔍 Enhanced user validation',
      '🚫 Spam protection'
    ],
    advanced_themes: [
      '🎨 Custom color schemes',
      '🖼️ Personalized backgrounds',
      '✨ Animation effects',
      '📱 Multiple theme slots'
    ]
  };

  return benefits[featureName] || [
    '✨ Enhanced capabilities',
    '🚀 Priority support',
    '🔧 Advanced features',
    '📊 Detailed analytics'
  ];
};

// ==================== PREMIUM COMPONENTS ====================

// Premium feature gate component
export const PremiumGate = ({ 
  feature, 
  children, 
  fallback, 
  upgradePrompt = true,
  className = ""
}) => {
  const { hasFeature, promptUpgrade } = usePremium();

  if (hasFeature(feature)) {
    return <div className={className}>{children}</div>;
  }

  if (fallback) {
    return fallback;
  }

  if (upgradePrompt) {
    const prompt = promptUpgrade(feature);
    return (
      <div className={`premium-gate ${className}`}>
        <PremiumUpgradePrompt {...prompt} feature={feature} />
      </div>
    );
  }

  return null;
};

// Premium upgrade prompt component
export const PremiumUpgradePrompt = ({ title, message, benefits, cta, feature }) => {
  return (
    <div className="premium-upgrade-prompt bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-xl p-8 text-center max-w-md mx-auto">
      <div className="text-6xl mb-4">✨</div>
      
      <h3 className="text-2xl font-bold text-purple-600 dark:text-purple-400 mb-3">
        {title}
      </h3>
      
      <p className="text-gray-600 dark:text-gray-400 mb-6">
        {message}
      </p>
      
      <div className="mb-6">
        <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 uppercase tracking-wide">
          Premium Benefits
        </h4>
        <ul className="text-left space-y-2 text-sm">
          {benefits.map((benefit, index) => (
            <li key={index} className="flex items-center text-gray-600 dark:text-gray-400">
              <span className="mr-2">{benefit.split(' ')[0]}</span>
              <span>{benefit.split(' ').slice(1).join(' ')}</span>
            </li>
          ))}
        </ul>
      </div>
      
      <div className="space-y-3">
        <button className="w-full px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-600 hover:to-pink-600 transform hover:scale-105 transition-all font-semibold shadow-lg">
          {cta}
        </button>
        
        <button className="w-full px-4 py-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 text-sm transition-colors">
          Maybe later
        </button>
      </div>
    </div>
  );
};

// Usage limit indicator
export const UsageLimitIndicator = ({ type, label }) => {
  const { limits, usage } = usePremium();
  
  const limit = limits[type];
  const current = usage[type] || 0;
  const percentage = (current / limit) * 100;
  
  const getColor = () => {
    if (percentage < 50) return 'bg-green-500';
    if (percentage < 80) return 'bg-yellow-500'; 
    return 'bg-red-500';
  };

  return (
    <div className="usage-limit-indicator">
      <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
        <span>{label}</span>
        <span>{current} / {limit}</span>
      </div>
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
        <div 
          className={`h-1.5 rounded-full transition-all ${getColor()}`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
    </div>
  );
};

// ==================== HOOKS ====================

// Premium feature hook
export const usePremiumFeature = (feature) => {
  const { hasFeature, promptUpgrade } = usePremium();
  
  return {
    hasAccess: hasFeature(feature),
    prompt: () => promptUpgrade(feature)
  };
};

// Usage limit hook
export const useUsageLimit = (type) => {
  const { limits, usage, checkLimit, trackUsage } = usePremium();
  
  return {
    limit: limits[type],
    current: usage[type] || 0,
    canUse: checkLimit(type, usage[type] || 0),
    track: () => trackUsage(type),
    percentage: ((usage[type] || 0) / limits[type]) * 100
  };
};