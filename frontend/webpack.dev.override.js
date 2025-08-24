// Security-focused webpack-dev-server override with Expo preview support
const addSecurityConfig = () => (config) => {
  // Get the backend URL to determine if we're in preview mode
  const backendUrl = process.env.REACT_APP_BACKEND_URL;
  const isPreviewMode = backendUrl && backendUrl.includes('emergentagent.com');
  
  console.log('🔧 Webpack Dev Server Config:', { 
    backendUrl, 
    isPreviewMode,
    nodeEnv: process.env.NODE_ENV 
  });
  
  if (isPreviewMode) {
    // PREVIEW MODE: Allow Expo preview access while maintaining security
    console.log('🌐 Configuring for PREVIEW MODE');
    config.host = '0.0.0.0';
    config.port = 3000;
    config.allowedHosts = 'all'; // Allow all hosts for Expo preview
    config.client = {
      webSocketURL: 'auto', // Let webpack determine the correct WebSocket URL
      overlay: { errors: true, warnings: false }
    };
    // Enhanced CORS headers for preview
    config.headers = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': '*',
    };
    // History API fallback configuration
    config.historyApiFallback = {
      disableDotRule: true,
    };
  } else {
    // DEVELOPMENT MODE: Localhost-only access (CVE-2025-30359/30360 mitigation)
    console.log('🏠 Configuring for DEVELOPMENT MODE');
    config.host = '127.0.0.1';
    config.port = 3000;
    config.allowedHosts = ['localhost', '127.0.0.1'];
    config.client = {
      webSocketURL: 'ws://127.0.0.1:3000/ws',
      overlay: { errors: true, warnings: false }
    };
  }
  
  // SECURITY: Enhanced headers middleware with adaptive origin validation
  config.setupMiddlewares = (middlewares, devServer) => {
    if (!devServer.app) {
      throw new Error('webpack-dev-server is not defined');
    }
    
    devServer.app.use((req, res, next) => {
      const origin = req.headers.origin;
      const host = req.headers.host;
      const userAgent = req.headers['user-agent'] || '';
      
      console.log('🔍 Request Details:', { origin, host, userAgent: userAgent.substring(0, 50) });
      
      if (isPreviewMode) {
        // PREVIEW MODE: Allow trusted domains and Expo
        const trustedDomains = ['emergentagent.com', 'expo.dev', 'expo.io', 'localhost', '127.0.0.1'];
        const isTrusted = trustedDomains.some(domain => 
          (origin && origin.includes(domain)) || 
          (host && host.includes(domain))
        );
        
        if (origin && !isTrusted && !origin.includes('chrome-extension://')) {
          console.warn('⚠️ Blocked untrusted origin in preview mode:', origin);
          return res.status(403).send(`Access denied: Untrusted origin "${origin}" blocked for security`);
        }
      } else {
        // DEVELOPMENT MODE: Strict localhost-only
        if (origin && !origin.includes('localhost') && !origin.includes('127.0.0.1')) {
          console.warn('⚠️ Blocked non-localhost origin in dev mode:', origin);
          return res.status(403).send('Access denied: Non-localhost origin blocked for security');
        }
      }
      
      // Security headers (always applied)
      res.setHeader('X-Content-Type-Options', 'nosniff');
      res.setHeader('X-Frame-Options', isPreviewMode ? 'ALLOWALL' : 'DENY');
      res.setHeader('X-XSS-Protection', '1; mode=block');
      res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
      
      // Adaptive CORS headers
      if (isPreviewMode) {
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
        res.setHeader('Access-Control-Allow-Headers', '*');
      }
      
      // Adaptive CSP based on mode
      if (isPreviewMode) {
        res.setHeader('Content-Security-Policy', 
          "default-src 'self' https: data:; " +
          "script-src 'self' 'unsafe-eval' 'unsafe-inline' https: *.emergentagent.com; " +
          "style-src 'self' 'unsafe-inline' https:; " +
          "img-src 'self' data: https: http:; " +
          "font-src 'self' https: data:; " +
          "connect-src 'self' https: http: ws: wss: *.emergentagent.com; " +
          "frame-ancestors https://expo.dev https://expo.io https://*.emergentagent.com 'self';"
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
  
  return config;
};

module.exports = {
  addSecurityConfig
};