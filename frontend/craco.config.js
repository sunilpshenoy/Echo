const WebpackObfuscator = require('webpack-obfuscator');
const path = require('path');

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
    setupMiddlewares: (middlewares, devServer) => {
      // Set security headers
      devServer.app.use((req, res, next) => {
        res.setHeader('X-Content-Type-Options', 'nosniff');
        res.setHeader('X-Frame-Options', 'DENY');
        res.setHeader('X-XSS-Protection', '1; mode=block');
        res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
        res.setHeader('Content-Security-Policy', "default-src 'self' *; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline' *; img-src 'self' data: https: http:; font-src 'self' *; connect-src 'self' https: http: ws: wss: *; frame-ancestors 'none';");
        next();
      });
      
      return middlewares;
    },
  },
};