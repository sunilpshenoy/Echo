import React, { useState, useEffect } from 'react';

// ==================== PERFORMANCE MONITORING ====================

export const PerformanceMonitor = ({ enabled = process.env.NODE_ENV === 'development' }) => {
  const [metrics, setMetrics] = useState({
    initialLoad: 0,
    componentLoads: {},
    bundleSizes: {},
    memoryUsage: 0
  });

  useEffect(() => {
    if (!enabled) return;

    // Track initial page load
    const navigationTiming = performance.getEntriesByType('navigation')[0];
    if (navigationTiming) {
      setMetrics(prev => ({
        ...prev,
        initialLoad: navigationTiming.loadEventEnd - navigationTiming.loadEventStart
      }));
    }

    // Monitor memory usage
    const updateMemoryUsage = () => {
      if (performance.memory) {
        setMetrics(prev => ({
          ...prev,
          memoryUsage: performance.memory.usedJSHeapSize / 1024 / 1024 // MB
        }));
      }
    };

    // Track resource loading
    const observer = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry) => {
        if (entry.entryType === 'resource' && entry.name.includes('chunk')) {
          setMetrics(prev => ({
            ...prev,
            bundleSizes: {
              ...prev.bundleSizes,
              [entry.name]: entry.transferSize
            }
          }));
        }
      });
    });

    observer.observe({ entryTypes: ['resource'] });
    
    const memoryInterval = setInterval(updateMemoryUsage, 5000);

    return () => {
      observer.disconnect();
      clearInterval(memoryInterval);
    };
  }, [enabled]);

  // Performance metrics display (development only)
  if (!enabled || process.env.NODE_ENV !== 'development') {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 bg-black/80 text-white text-xs p-3 rounded-lg font-mono z-50 max-w-xs">
      <div className="font-bold mb-2">🚀 Performance Metrics</div>
      
      <div className="space-y-1">
        <div>Initial Load: {metrics.initialLoad.toFixed(2)}ms</div>
        <div>Memory: {metrics.memoryUsage.toFixed(1)}MB</div>
        
        {Object.keys(metrics.componentLoads).length > 0 && (
          <div className="mt-2">
            <div className="font-semibold">Component Loads:</div>
            {Object.entries(metrics.componentLoads).map(([name, time]) => (
              <div key={name}>{name}: {time.toFixed(2)}ms</div>
            ))}
          </div>
        )}
        
        {Object.keys(metrics.bundleSizes).length > 0 && (
          <div className="mt-2">
            <div className="font-semibold">Bundle Sizes:</div>
            {Object.entries(metrics.bundleSizes).slice(0, 3).map(([name, size]) => (
              <div key={name}>
                {name.split('/').pop()}: {(size / 1024).toFixed(1)}KB
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Hook for component-level performance tracking
export const useComponentPerformance = (componentName) => {
  useEffect(() => {
    const startTime = performance.now();
    console.log(`🚀 ${componentName} starting load...`);
    
    return () => {
      const endTime = performance.now();
      const loadTime = endTime - startTime;
      console.log(`✅ ${componentName} loaded in ${loadTime.toFixed(2)}ms`);
      
      // Send to analytics in production
      if (process.env.NODE_ENV === 'production' && window.gtag) {
        window.gtag('event', 'component_load_time', {
          component_name: componentName,
          load_time: Math.round(loadTime),
          custom_map: { metric1: 'load_time' }
        });
      }
    };
  }, [componentName]);
};

// Bundle size analyzer
export const BundleAnalyzer = () => {
  const [analysis, setAnalysis] = useState(null);

  useEffect(() => {
    // Estimate current bundle size based on loaded resources
    const resources = performance.getEntriesByType('resource');
    const jsResources = resources.filter(r => r.name.endsWith('.js'));
    const cssResources = resources.filter(r => r.name.endsWith('.css'));
    
    const totalJSSize = jsResources.reduce((sum, r) => sum + (r.transferSize || 0), 0);
    const totalCSSSize = cssResources.reduce((sum, r) => sum + (r.transferSize || 0), 0);
    
    setAnalysis({
      totalJS: totalJSSize,
      totalCSS: totalCSSSize,
      jsFiles: jsResources.length,
      cssFiles: cssResources.length,
      recommendations: generateRecommendations(totalJSSize, jsResources.length)
    });
  }, []);

  const generateRecommendations = (totalSize, fileCount) => {
    const recommendations = [];
    
    if (totalSize > 1024 * 1024) { // > 1MB
      recommendations.push('🔴 Bundle size is large (>1MB). Consider code splitting.');
    } else if (totalSize > 512 * 1024) { // > 512KB
      recommendations.push('🟡 Bundle size is moderate. Monitor for growth.');
    } else {
      recommendations.push('🟢 Bundle size is optimal.');
    }
    
    if (fileCount > 10) {
      recommendations.push('📦 Many JS files loaded. Consider bundling optimization.');
    }
    
    return recommendations;
  };

  if (!analysis || process.env.NODE_ENV !== 'development') {
    return null;
  }

  return (
    <div className="fixed top-4 right-4 bg-blue-900/90 text-white text-xs p-3 rounded-lg font-mono z-50 max-w-sm">
      <div className="font-bold mb-2">📊 Bundle Analysis</div>
      
      <div className="space-y-1">
        <div>JS: {(analysis.totalJS / 1024).toFixed(1)}KB ({analysis.jsFiles} files)</div>
        <div>CSS: {(analysis.totalCSS / 1024).toFixed(1)}KB ({analysis.cssFiles} files)</div>
        <div>Total: {((analysis.totalJS + analysis.totalCSS) / 1024).toFixed(1)}KB</div>
        
        <div className="mt-2 pt-2 border-t border-blue-700">
          {analysis.recommendations.map((rec, index) => (
            <div key={index} className="text-xs">{rec}</div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Performance optimization suggestions
export const PerformanceOptimizer = () => {
  const [suggestions, setSuggestions] = useState([]);

  useEffect(() => {
    const checkOptimizations = () => {
      const suggestions = [];
      
      // Check if service worker is registered
      if (!('serviceWorker' in navigator)) {
        suggestions.push({
          type: 'info',
          title: 'Service Worker',
          message: 'Service worker not supported in this browser.'
        });
      }
      
      // Check memory usage
      if (performance.memory && performance.memory.usedJSHeapSize > 50 * 1024 * 1024) {
        suggestions.push({
          type: 'warning',
          title: 'Memory Usage',
          message: 'High memory usage detected. Consider lazy loading more components.'
        });
      }
      
      // Check number of loaded resources
      const resources = performance.getEntriesByType('resource');
      if (resources.length > 50) {
        suggestions.push({
          type: 'warning',
          title: 'Resource Count',
          message: `${resources.length} resources loaded. Consider resource optimization.`
        });
      }
      
      setSuggestions(suggestions);
    };

    checkOptimizations();
  }, []);

  if (suggestions.length === 0 || process.env.NODE_ENV !== 'development') {
    return null;
  }

  return (
    <div className="fixed bottom-4 left-4 bg-yellow-900/90 text-white text-xs p-3 rounded-lg font-mono z-50 max-w-sm">
      <div className="font-bold mb-2">💡 Optimization Suggestions</div>
      
      <div className="space-y-2">
        {suggestions.map((suggestion, index) => (
          <div key={index} className="p-2 bg-yellow-800/50 rounded">
            <div className="font-semibold">{suggestion.title}</div>
            <div className="text-xs">{suggestion.message}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PerformanceMonitor;