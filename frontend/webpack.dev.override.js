// Security-focused webpack-dev-server override with Expo preview support
const { overrideDevServer } = require('customize-cra');

const addSecurityConfig = () => (config) => {
  // Get the backend URL to determine if we're in preview mode
  const backendUrl = process.env.REACT_APP_BACKEND_URL;
  const isPreviewMode = backendUrl && backendUrl.includes('emergentagent.com');
  
  if (isPreviewMode) {
    // PREVIEW MODE: Allow Expo preview access while maintaining security
    config.host = '0.0.0.0';
    config.port = 3000;
    config.allowedHosts = 'all'; // Allow Expo preview hosts
    config.disableHostCheck = true; // Required for Expo preview
  } else {
    // DEVELOPMENT MODE: Localhost-only access (CVE-2025-30359/30360 mitigation)
    config.host = '127.0.0.1';
    config.port = 3000;
    config.allowedHosts = ['localhost', '127.0.0.1'];
  }
  
  // SECURITY: Enhanced headers middleware
  config.setupMiddlewares = (middlewares, devServer) => {
    devServer.app.use((req, res, next) => {
      // Enhanced origin validation
      const origin = req.headers.origin;
      const host = req.headers.host;
      
      if (isPreviewMode) {
        // PREVIEW MODE: Allow Expo and trusted domains
        if (origin && !origin.includes('localhost') && 
            !origin.includes('127.0.0.1') && 
            !origin.includes('emergentagent.com') &&
            !origin.includes('expo.dev') &&
            !origin.includes('expo.io')) {
          console.warn('Blocked untrusted origin in preview mode:', origin);
          return res.status(403).send('Access denied: Untrusted origin blocked for security');
        }
      } else {
        // DEVELOPMENT MODE: Strict localhost-only
        if (origin && !origin.includes('localhost') && !origin.includes('127.0.0.1')) {
          return res.status(403).send('Access denied: Non-localhost origin blocked for security');
        }
      }
      
      // Security headers (always applied)
      res.setHeader('X-Content-Type-Options', 'nosniff');
      res.setHeader('X-Frame-Options', isPreviewMode ? 'ALLOWALL' : 'DENY'); // Allow framing in preview
      res.setHeader('X-XSS-Protection', '1; mode=block');
      res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
      
      // Adaptive CSP based on mode
      if (isPreviewMode) {
        res.setHeader('Content-Security-Policy', 
          "default-src 'self' https:; " +
          "script-src 'self' 'unsafe-eval' 'unsafe-inline' https: localhost:* *.emergentagent.com; " +
          "style-src 'self' 'unsafe-inline' https:; " +
          "img-src 'self' data: https: http:; " +
          "font-src 'self' https:; " +
          "connect-src 'self' https: http: ws: wss: localhost:* *.emergentagent.com; " +
          "frame-ancestors https://expo.dev https://expo.io https://*.emergentagent.com;"
        );
      } else {
        res.setHeader('Content-Security-Policy', 
          "default-src 'self'; " +
          "script-src 'self' 'unsafe-eval' 'unsafe-inline' localhost:* 127.0.0.1:*; " +
          "style-src 'self' 'unsafe-inline'; " +
          "img-src 'self' data: https: http:; " +
          "font-src 'self'; " +
          "connect-src 'self' localhost:* 127.0.0.1:* ws://localhost:* ws://127.0.0.1:*; " +
          "frame-ancestors 'none';"
        );
      }
      
      next();
    });
    
    return middlewares;
  };
  
  // SECURITY: Adaptive WebSocket restrictions
  if (isPreviewMode) {
    config.client = {
      ...config.client,
      overlay: { errors: true, warnings: false }
      // Let webpack determine WebSocket URL automatically in preview mode
    };
  } else {
    config.client = {
      ...config.client,
      webSocketURL: 'ws://127.0.0.1:3000/ws',
      overlay: { errors: true, warnings: false }
    };
  }
  
  return config;
};

module.exports = {
  addSecurityConfig
};