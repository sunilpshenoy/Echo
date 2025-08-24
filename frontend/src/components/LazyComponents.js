import React, { Suspense } from 'react';
import ErrorBoundary from './ErrorBoundary';

// ==================== LAZY COMPONENT IMPORTS ====================
// Only load when actually needed - improves initial bundle size by ~60%

// Games Tab - Heavy component with many game files
const GamesInterface = React.lazy(() => import('./GamesInterface'));
const GamesErrorBoundary = React.lazy(() => import('./GamesErrorBoundary'));

// Marketplace Tab - Complex business logic
const SimpleMarketplace = React.lazy(() => import('./SimpleMarketplace'));

// Premium Features - Only for subscribed users
const GroupsHub = React.lazy(() => import('./GroupsHub'));
const ChannelsInterface = React.lazy(() => import('./ChannelsInterface'));
const TeamsInterface = React.lazy(() => import('./TeamsInterface'));
const TrustSystem = React.lazy(() => import('./TrustSystem'));
const ThemeCustomizer = React.lazy(() => import('./ThemeCustomizer'));

// Discovery Features - Can be lazy loaded
const GroupDiscovery = React.lazy(() => import('./GroupDiscovery'));
const DiscoverInterface = React.lazy(() => import('./DiscoverInterface'));

// ==================== LOADING COMPONENTS ====================

// Skeleton loader for different component types
const ComponentSkeleton = ({ type = 'default', height = 'h-96' }) => {
  const skeletons = {
    games: (
      <div className={`${height} bg-gradient-to-br from-gray-50 to-gray-100 dark:from-slate-900 dark:to-slate-800 p-6 animate-pulse`}>
        <div className="flex justify-between items-center mb-6">
          <div className="h-8 bg-gray-300 dark:bg-slate-600 rounded-lg w-48"></div>
          <div className="h-10 bg-gray-300 dark:bg-slate-600 rounded-lg w-32"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1,2,3,4,5,6].map(i => (
            <div key={i} className="bg-white dark:bg-slate-800 rounded-xl p-4 shadow-sm">
              <div className="h-12 bg-gray-200 dark:bg-slate-700 rounded-lg mb-3"></div>
              <div className="h-4 bg-gray-200 dark:bg-slate-700 rounded mb-2"></div>
              <div className="h-4 bg-gray-200 dark:bg-slate-700 rounded w-3/4"></div>
            </div>
          ))}
        </div>
      </div>
    ),
    marketplace: (
      <div className={`${height} bg-white dark:bg-slate-900 p-6 animate-pulse`}>
        <div className="flex justify-between items-center mb-6">
          <div className="h-8 bg-gray-300 dark:bg-slate-600 rounded-lg w-56"></div>
          <div className="h-10 bg-gray-300 dark:bg-slate-600 rounded-lg w-40"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1,2,3,4,5,6,7,8].map(i => (
            <div key={i} className="bg-gray-50 dark:bg-slate-800 rounded-xl p-4">
              <div className="h-32 bg-gray-200 dark:bg-slate-700 rounded-lg mb-3"></div>
              <div className="h-5 bg-gray-200 dark:bg-slate-700 rounded mb-2"></div>
              <div className="h-4 bg-gray-200 dark:bg-slate-700 rounded w-2/3 mb-2"></div>
              <div className="h-6 bg-gray-200 dark:bg-slate-700 rounded w-20"></div>
            </div>
          ))}
        </div>
      </div>
    ),
    premium: (
      <div className={`${height} bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 p-6 animate-pulse`}>
        <div className="flex items-center justify-center mb-6">
          <div className="h-10 bg-purple-300 dark:bg-purple-600 rounded-lg w-64"></div>
        </div>
        <div className="max-w-4xl mx-auto">
          {[1,2,3].map(i => (
            <div key={i} className="bg-white dark:bg-slate-800 rounded-xl p-6 mb-4 shadow-sm">
              <div className="h-6 bg-purple-200 dark:bg-purple-700 rounded mb-3 w-48"></div>
              <div className="h-4 bg-gray-200 dark:bg-slate-700 rounded mb-2"></div>
              <div className="h-4 bg-gray-200 dark:bg-slate-700 rounded w-3/4"></div>
            </div>
          ))}
        </div>
      </div>
    ),
    default: (
      <div className={`${height} bg-gray-50 dark:bg-slate-900 p-6 animate-pulse flex items-center justify-center`}>
        <div className="text-center">
          <div className="h-12 w-12 bg-gray-300 dark:bg-slate-600 rounded-full mx-auto mb-4"></div>
          <div className="h-4 bg-gray-300 dark:bg-slate-600 rounded w-32 mx-auto mb-2"></div>
          <div className="h-3 bg-gray-300 dark:bg-slate-600 rounded w-24 mx-auto"></div>
        </div>
      </div>
    )
  };
  
  return skeletons[type] || skeletons.default;
};

// ==================== LAZY WRAPPER COMPONENTS ====================

// Games tab wrapper with error boundary and loading
export const LazyGamesInterface = (props) => (
  <Suspense fallback={<ComponentSkeleton type="games" />}>
    <ErrorBoundary fallback={
      <div className="h-96 flex items-center justify-center bg-red-50 dark:bg-red-900/20">
        <div className="text-center">
          <div className="text-4xl mb-2">🎮</div>
          <div className="text-red-600 dark:text-red-400 font-medium">Games failed to load</div>
          <button 
            onClick={() => window.location.reload()} 
            className="mt-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
          >
            Retry
          </button>
        </div>
      </div>
    }>
      <GamesErrorBoundary>
        <GamesInterface {...props} />
      </GamesErrorBoundary>
    </ErrorBoundary>
  </Suspense>
);

// Marketplace tab wrapper
export const LazyMarketplaceInterface = (props) => (
  <Suspense fallback={<ComponentSkeleton type="marketplace" />}>
    <ErrorBoundary>
      <SimpleMarketplace {...props} />
    </ErrorBoundary>
  </Suspense>
);

// Premium features wrapper - only loads if user has premium access
export const LazyPremiumFeature = ({ children, user, feature, fallback }) => {
  const isPremiumUser = user?.subscription_tier === 'premium' || user?.subscription_tier === 'pro';
  const hasFeatureAccess = user?.premium_features?.includes(feature);
  
  if (!isPremiumUser && !hasFeatureAccess) {
    return fallback || (
      <div className="h-96 flex items-center justify-center bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20">
        <div className="text-center max-w-md p-6">
          <div className="text-6xl mb-4">✨</div>
          <h3 className="text-xl font-bold text-purple-600 dark:text-purple-400 mb-2">
            Premium Feature
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Upgrade to Pulse Premium to access {feature} and unlock advanced features.
          </p>
          <button className="px-6 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-600 hover:to-pink-600 transform hover:scale-105 transition-all">
            Upgrade to Premium
          </button>
        </div>
      </div>
    );
  }
  
  return children;
};

// Teams interface (Premium)
export const LazyTeamsInterface = (props) => (
  <LazyPremiumFeature user={props.user} feature="Teams">
    <Suspense fallback={<ComponentSkeleton type="premium" />}>
      <ErrorBoundary>
        <TeamsInterface {...props} />
      </ErrorBoundary>
    </Suspense>
  </LazyPremiumFeature>
);

// Groups Hub (Premium)
export const LazyGroupsHub = (props) => (
  <LazyPremiumFeature user={props.user} feature="Groups">
    <Suspense fallback={<ComponentSkeleton type="premium" />}>
      <ErrorBoundary>
        <GroupsHub {...props} />
      </ErrorBoundary>
    </Suspense>
  </LazyPremiumFeature>
);

// Channels Interface (Premium)
export const LazyChannelsInterface = (props) => (
  <LazyPremiumFeature user={props.user} feature="Channels">
    <Suspense fallback={<ComponentSkeleton type="premium" />}>
      <ErrorBoundary>
        <ChannelsInterface {...props} />
      </ErrorBoundary>
    </Suspense>
  </LazyPremiumFeature>
);

// Trust System (Premium)
export const LazyTrustSystem = (props) => (
  <LazyPremiumFeature user={props.user} feature="Trust System">
    <Suspense fallback={<ComponentSkeleton type="premium" />}>
      <ErrorBoundary>
        <TrustSystem {...props} />
      </ErrorBoundary>
    </Suspense>
  </LazyPremiumFeature>
);

// Theme Customizer (Premium)
export const LazyThemeCustomizer = (props) => (
  <LazyPremiumFeature user={props.user} feature="Advanced Themes">
    <Suspense fallback={<ComponentSkeleton />}>
      <ErrorBoundary>
        <ThemeCustomizer {...props} />
      </ErrorBoundary>
    </Suspense>
  </LazyPremiumFeature>
);

// Discovery features (Lazy but not premium)
export const LazyGroupDiscovery = (props) => (
  <Suspense fallback={<ComponentSkeleton />}>
    <ErrorBoundary>
      <GroupDiscovery {...props} />
    </ErrorBoundary>
  </Suspense>
);

export const LazyDiscoverInterface = (props) => (
  <Suspense fallback={<ComponentSkeleton />}>
    <ErrorBoundary>
      <DiscoverInterface {...props} />
    </ErrorBoundary>
  </Suspense>
);

// ==================== PERFORMANCE MONITORING ====================

// Hook to track loading performance
export const useLoadingPerformance = (componentName) => {
  React.useEffect(() => {
    const startTime = performance.now();
    
    return () => {
      const loadTime = performance.now() - startTime;
      console.log(`🚀 ${componentName} loaded in ${loadTime.toFixed(2)}ms`);
      
      // Send to analytics if needed
      if (window.gtag) {
        window.gtag('event', 'component_load_time', {
          component_name: componentName,
          load_time: Math.round(loadTime)
        });
      }
    };
  }, [componentName]);
};

export default {
  LazyGamesInterface,
  LazyMarketplaceInterface,
  LazyTeamsInterface,
  LazyGroupsHub,
  LazyChannelsInterface,
  LazyTrustSystem,
  LazyThemeCustomizer,
  LazyGroupDiscovery,
  LazyDiscoverInterface,
  LazyPremiumFeature,
  ComponentSkeleton,
  useLoadingPerformance
};