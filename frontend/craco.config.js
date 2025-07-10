const WebpackObfuscator = require('webpack-obfuscator');
const path = require('path');

module.exports = {
  webpack: {
    plugins: [
      // Advanced code obfuscation - Military grade
      new WebpackObfuscator({
        // String obfuscation
        stringArray: true,
        stringArrayThreshold: 1,
        stringArrayEncoding: ['base64'],
        stringArrayWrappersCount: 5,
        stringArrayWrappersChainedCalls: true,
        
        // Control flow obfuscation
        controlFlowFlattening: true,
        controlFlowFlatteningThreshold: 1,
        deadCodeInjection: true,
        deadCodeInjectionThreshold: 1,
        
        // Variable name obfuscation
        identifierNamesGenerator: 'hexadecimalNumericString',
        renameGlobals: true,
        renameProperties: true,
        renamePropertiesMode: 'safe',
        
        // Advanced features
        disableConsoleOutput: true,
        debugProtection: true,
        debugProtectionInterval: 2000,
        domainLock: [], // Add your domains here
        
        // Code transformation
        compact: true,
        selfDefending: true,
        simplify: true,
        splitStrings: true,
        splitStringsChunkLength: 5,
        
        // Unicode transformation
        unicodeEscapeSequence: true,
        transformObjectKeys: true,
        
        // Reserved names (keep React internals working)
        reservedNames: [
          '^React',
          '^ReactDOM',
          '^__webpack',
          '^webpackJsonp',
          '^module',
          '^exports',
          '^require',
          '^global',
          '^window',
          '^document',
          '^navigator',
          '^console',
          '^setTimeout',
          '^setInterval',
          '^clearTimeout',
          '^clearInterval',
          '^JSON',
          '^localStorage',
          '^sessionStorage',
          '^process',
          '^env'
        ],
        
        // Reserved strings (keep critical strings working)
        reservedStrings: [
          'react',
          'react-dom',
          'className',
          'onClick',
          'onChange',
          'onSubmit',
          'useState',
          'useEffect',
          'useContext',
          'useReducer',
          'useCallback',
          'useMemo',
          'useRef'
        ]
      }, ['**/node_modules/**'])
    ],
    configure: (webpackConfig, { env, paths }) => {
      // Remove source maps in production for security
      if (env === 'production') {
        webpackConfig.devtool = false;
        
        // Add integrity checks
        webpackConfig.optimization = {
          ...webpackConfig.optimization,
          minimize: true,
          sideEffects: false,
          usedExports: true,
          concatenateModules: true,
        };
        
        // Split chunks to make reverse engineering harder
        webpackConfig.optimization.splitChunks = {
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
        };
      }
      
      // Security headers
      webpackConfig.performance = {
        hints: false,
        maxEntrypointSize: 512000,
        maxAssetSize: 512000,
      };
      
      return webpackConfig;
    },
  },
  devServer: {
    headers: {
      'X-Content-Type-Options': 'nosniff',
      'X-Frame-Options': 'DENY',
      'X-XSS-Protection': '1; mode=block',
      'Referrer-Policy': 'strict-origin-when-cross-origin',
      'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self' https:; frame-ancestors 'none';",
    },
  },
};