// Security-focused webpack-dev-server override
const { overrideDevServer } = require('customize-cra');

const addSecurityConfig = () => (config) => {
  // SECURITY: Force localhost-only access (CVE-2025-30359/30360 mitigation)
  config.host = '127.0.0.1';
  config.port = 3000;
  config.allowedHosts = ['localhost', '127.0.0.1'];
  
  // SECURITY: Enhanced headers middleware
  config.setupMiddlewares = (middlewares, devServer) => {
    devServer.app.use((req, res, next) => {
      // Block non-localhost origins
      const origin = req.headers.origin;
      if (origin && !origin.includes('localhost') && !origin.includes('127.0.0.1')) {
        return res.status(403).send('Access denied: Non-localhost origin blocked for security');
      }
      
      // Security headers
      res.setHeader('X-Content-Type-Options', 'nosniff');
      res.setHeader('X-Frame-Options', 'DENY');
      res.setHeader('X-XSS-Protection', '1; mode=block');
      res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
      res.setHeader('Content-Security-Policy', 
        "default-src 'self'; " +
        "script-src 'self' 'unsafe-eval' 'unsafe-inline' localhost:* 127.0.0.1:*; " +
        "style-src 'self' 'unsafe-inline'; " +
        "img-src 'self' data: https: http:; " +
        "font-src 'self'; " +
        "connect-src 'self' localhost:* 127.0.0.1:* ws://localhost:* ws://127.0.0.1:*; " +
        "frame-ancestors 'none';"
      );
      
      next();
    });
    
    return middlewares;
  };
  
  // SECURITY: WebSocket restrictions
  config.client = {
    ...config.client,
    webSocketURL: 'ws://127.0.0.1:3000/ws',
    overlay: { errors: true, warnings: false }
  };
  
  return config;
};

module.exports = {
  addSecurityConfig
};