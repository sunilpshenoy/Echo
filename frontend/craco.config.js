const WebpackObfuscator = require('webpack-obfuscator');

// Check if we're in preview mode
const isPreviewMode = process.env.REACT_APP_BACKEND_URL && 
                     process.env.REACT_APP_BACKEND_URL.includes('emergentagent.com');

console.log('🔧 CRACO Config - Preview Mode:', isPreviewMode);
console.log('🔧 Backend URL:', process.env.REACT_APP_BACKEND_URL);

module.exports = {
  webpack: {
    plugins: [
      // Lighter obfuscation for development, full protection for production
      ...(process.env.NODE_ENV === 'production' ? [
        new WebpackObfuscator({
          // PRODUCTION: Military-grade protection
          stringArray: true,
          stringArrayThreshold: 1,
          stringArrayEncoding: ['base64'],
          stringArrayWrappersCount: 5,
          stringArrayWrappersChainedCalls: true,
          controlFlowFlattening: true,
          controlFlowFlatteningThreshold: 1,
          deadCodeInjection: true,
          deadCodeInjectionThreshold: 1,
          identifierNamesGenerator: 'hexadecimal',
          renameGlobals: true,
          renameProperties: true,
          renamePropertiesMode: 'safe',
          disableConsoleOutput: true,
          debugProtection: true,
          debugProtectionInterval: 2000,
          compact: true,
          selfDefending: true,
          simplify: true,
          splitStrings: true,
          splitStringsChunkLength: 5,
          unicodeEscapeSequence: true,
          transformObjectKeys: true,
          reservedNames: [
            '^React', '^ReactDOM', '^__webpack', '^webpackJsonp', '^module',
            '^exports', '^require', '^global', '^window', '^document',
            '^navigator', '^console', '^setTimeout', '^setInterval',
            '^clearTimeout', '^clearInterval', '^JSON', '^localStorage',
            '^sessionStorage', '^process', '^env'
          ],
          reservedStrings: [
            'react', 'react-dom', 'className', 'onClick', 'onChange',
            'onSubmit', 'useState', 'useEffect', 'useContext', 'useReducer',
            'useCallback', 'useMemo', 'useRef'
          ]
        }, ['**/node_modules/**'])
      ] : [
        // DEVELOPMENT: Basic protection (lighter on memory)
        new WebpackObfuscator({
          compact: false,
          controlFlowFlattening: false,
          deadCodeInjection: false,
          debugProtection: false,
          disableConsoleOutput: false,
          identifierNamesGenerator: 'mangled',
          renameGlobals: false,
          selfDefending: false,
          stringArray: true,
          stringArrayThreshold: 0.75,
          transformObjectKeys: false,
          unicodeEscapeSequence: false,
          reservedNames: [
            '^React', '^ReactDOM', '^__webpack', '^webpackJsonp', '^module',
            '^exports', '^require', '^global', '^window', '^document'
          ]
        }, ['**/node_modules/**'])
      ])
    ],
    configure: (webpackConfig, { env, paths }) => {
      // Memory management for development
      if (env === 'development') {
        webpackConfig.optimization = {
          ...webpackConfig.optimization,
          removeAvailableModules: false,
          removeEmptyChunks: false,
          splitChunks: false,
        };
        
        // Increase memory limit for Node.js
        process.env.NODE_OPTIONS = '--max-old-space-size=4096';
      }
      
      // Remove source maps in production for security
      if (env === 'production') {
        webpackConfig.devtool = false;
        
        webpackConfig.optimization = {
          ...webpackConfig.optimization,
          minimize: true,
          sideEffects: false,
          usedExports: true,
          concatenateModules: true,
          splitChunks: {
            chunks: 'all',
            maxSize: 200000,
            cacheGroups: {
              vendor: {
                test: /[\\/]node_modules[\\/]/,
                name: 'vendors',
                chunks: 'all',
                minChunks: 2,
              },
              common: {
                name: 'common',
                minChunks: 2,
                chunks: 'all',
                enforce: true,
              },
            },
          },
        };
      }
      
      return webpackConfig;
    },
  },
  devServer: {
    // Configure based on environment
    host: isPreviewMode ? '0.0.0.0' : '127.0.0.1',
    port: 3000,
    allowedHosts: isPreviewMode ? 'all' : ['localhost', '127.0.0.1'],
    
    // CORS and security headers
    headers: isPreviewMode ? {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': '*',
      'X-Content-Type-Options': 'nosniff',
      'X-Frame-Options': 'ALLOWALL',
    } : {
      'X-Content-Type-Options': 'nosniff',
      'X-Frame-Options': 'DENY',
    },
    
    // WebSocket configuration
    client: isPreviewMode ? {
      webSocketURL: 'auto',
      overlay: { errors: true, warnings: false }
    } : {
      webSocketURL: 'ws://127.0.0.1:3000/ws',
      overlay: { errors: true, warnings: false }
    },
    
    // History API fallback
    historyApiFallback: {
      disableDotRule: true,
    },
    
    // Hot reloading
    hot: true,
    liveReload: true,
    
    // Security middleware
    setupMiddlewares: (middlewares, devServer) => {
      if (!devServer.app) {
        throw new Error('webpack-dev-server is not defined');
      }
      
      devServer.app.use((req, res, next) => {
        const origin = req.headers.origin;
        const host = req.headers.host;
        
        console.log('🔍 Preview Request - Origin:', origin, 'Host:', host, 'Mode:', isPreviewMode ? 'Preview' : 'Dev');
        
        if (isPreviewMode) {
          // PREVIEW MODE: Allow trusted domains
          const trustedDomains = ['emergentagent.com', 'expo.dev', 'expo.io', 'localhost', '127.0.0.1'];
          const isTrusted = trustedDomains.some(domain => 
            (origin && origin.includes(domain)) || 
            (host && host.includes(domain)) ||
            !origin // Allow direct access
          );
          
          if (origin && !isTrusted && !origin.includes('chrome-extension://')) {
            console.warn('⚠️ Preview Mode - Blocked untrusted origin:', origin);
            return res.status(403).send(`Access denied: Untrusted origin "${origin}"`);
          }
          
          // Additional CORS headers for preview
          res.setHeader('Access-Control-Allow-Origin', '*');
          res.setHeader('Access-Control-Allow-Methods', '*');
          res.setHeader('Access-Control-Allow-Headers', '*');
        } else {
          // DEVELOPMENT MODE: Strict localhost-only
          if (origin && !origin.includes('localhost') && !origin.includes('127.0.0.1')) {
            console.warn('⚠️ Dev Mode - Blocked non-localhost origin:', origin);
            return res.status(403).send('Dev Mode: Non-localhost origin blocked');
          }
        }
        
        next();
      });
      
      return middlewares;
    },
  },
};