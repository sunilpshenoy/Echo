// Military-grade security protection system
class SecurityShield {
  constructor() {
    this.debuggerDetectionInterval = null;
    this.integrityCheckInterval = null;
    this.mouseMovementTracker = [];
    this.keyboardTracker = [];
    this.initTime = Date.now();
    this.securityViolations = 0;
    this.maxViolations = 3;
    
    this.init();
  }

  init() {
    this.enableDebuggerProtection();
    this.enableIntegrityProtection();
    this.enableAntiTampering();
    this.enableBehaviorAnalysis();
    this.enableEnvironmentChecks();
    this.obfuscateConsole();
  }

  // Anti-debugging protection
  enableDebuggerProtection() {
    // Method 1: Infinite debugger loop
    const debuggerTrap = () => {
      try {
        const start = performance.now();
        debugger;
        const end = performance.now();
        
        // If debugger is open, this will take significantly longer
        if (end - start > 100) {
          this.triggerSecurityBreach('debugger_detected');
        }
      } catch (e) {
        // Debugger detection failed, possible tampering
        this.triggerSecurityBreach('anti_debug_tampered');
      }
    };

    // Method 2: Console size detection
    const consoleDetection = () => {
      const threshold = 160;
      if (window.outerHeight - window.innerHeight > threshold || 
          window.outerWidth - window.innerWidth > threshold) {
        this.triggerSecurityBreach('dev_tools_detected');
      }
    };

    // Method 3: toString override detection
    const functionDetection = () => {
      const func = () => {};
      const originalToString = func.toString;
      func.toString = () => 'function() { [native code] }';
      
      if (func.toString !== originalToString && func.toString() !== 'function() { [native code] }') {
        this.triggerSecurityBreach('function_override_detected');
      }
    };

    // Run multiple detection methods
    this.debuggerDetectionInterval = setInterval(() => {
      debuggerTrap();
      consoleDetection();
      functionDetection();
    }, 1000);
  }

  // Code integrity protection
  enableIntegrityProtection() {
    const originalScript = document.currentScript?.src;
    const scriptHashes = new Map();
    
    // Calculate checksums of critical scripts
    document.querySelectorAll('script[src]').forEach(script => {
      if (script.src) {
        fetch(script.src)
          .then(response => response.text())
          .then(content => {
            const hash = this.calculateHash(content);
            scriptHashes.set(script.src, hash);
          })
          .catch(() => {
            this.triggerSecurityBreach('script_integrity_check_failed');
          });
      }
    });

    // Periodic integrity checks
    this.integrityCheckInterval = setInterval(() => {
      // Check for script modifications
      document.querySelectorAll('script[src]').forEach(script => {
        if (script.src && scriptHashes.has(script.src)) {
          fetch(script.src)
            .then(response => response.text())
            .then(content => {
              const currentHash = this.calculateHash(content);
              const originalHash = scriptHashes.get(script.src);
              
              if (currentHash !== originalHash) {
                this.triggerSecurityBreach('script_modified');
              }
            })
            .catch(() => {
              this.triggerSecurityBreach('script_integrity_recheck_failed');
            });
        }
      });

      // Check for DOM manipulation
      this.checkDOMIntegrity();
    }, 5000);
  }

  // Anti-tampering measures
  enableAntiTampering() {
    // Protect against Object.defineProperty tampering
    const originalDefineProperty = Object.defineProperty;
    Object.defineProperty = function(...args) {
      if (args[0] === window || args[0] === document || args[0] === console) {
        this.triggerSecurityBreach('critical_object_tampered');
        return;
      }
      return originalDefineProperty.apply(this, args);
    }.bind(this);

    // Protect against Function.prototype.toString tampering
    const originalToString = Function.prototype.toString;
    Function.prototype.toString = function() {
      if (this === SecurityShield.prototype.triggerSecurityBreach) {
        this.triggerSecurityBreach('security_function_accessed');
        return 'function() { [native code] }';
      }
      return originalToString.apply(this, arguments);
    }.bind(this);

    // Protect critical methods
    const criticalMethods = [
      'eval', 'setTimeout', 'setInterval', 'fetch', 'XMLHttpRequest'
    ];
    
    criticalMethods.forEach(method => {
      const original = window[method];
      if (original) {
        window[method] = new Proxy(original, {
          apply: (target, thisArg, argumentsList) => {
            // Log and analyze suspicious usage
            this.analyzeMethodUsage(method, argumentsList);
            return Reflect.apply(target, thisArg, argumentsList);
          }
        });
      }
    });
  }

  // Behavior analysis for bot detection
  enableBehaviorAnalysis() {
    // Track mouse movements
    document.addEventListener('mousemove', (e) => {
      this.mouseMovementTracker.push({
        x: e.clientX,
        y: e.clientY,
        timestamp: Date.now()
      });
      
      // Keep only last 100 movements
      if (this.mouseMovementTracker.length > 100) {
        this.mouseMovementTracker.shift();
      }
    });

    // Track keyboard patterns
    document.addEventListener('keydown', (e) => {
      this.keyboardTracker.push({
        key: e.key,
        timestamp: Date.now(),
        ctrlKey: e.ctrlKey,
        altKey: e.altKey,
        shiftKey: e.shiftKey
      });

      // Detect developer shortcuts
      if ((e.ctrlKey || e.metaKey) && (e.key === 'u' || e.key === 'U')) {
        this.triggerSecurityBreach('view_source_attempt');
      }
      if (e.key === 'F12') {
        this.triggerSecurityBreach('dev_tools_shortcut');
      }

      // Keep only last 50 keystrokes
      if (this.keyboardTracker.length > 50) {
        this.keyboardTracker.shift();
      }
    });

    // Analyze behavior patterns periodically
    setInterval(() => {
      this.analyzeBehaviorPatterns();
    }, 10000);
  }

  // Environment validation
  enableEnvironmentChecks() {
    // Check for headless browsers
    if (navigator.webdriver || 
        window.phantom || 
        window._phantom || 
        window.callPhantom) {
      this.triggerSecurityBreach('headless_browser_detected');
    }

    // Check for automation tools
    if (window.external && window.external.toString() === '[object External]') {
      this.triggerSecurityBreach('automation_tool_detected');
    }

    // Check for suspicious user agent
    const suspiciousUAs = ['headless', 'phantom', 'selenium', 'webdriver'];
    if (suspiciousUAs.some(ua => navigator.userAgent.toLowerCase().includes(ua))) {
      this.triggerSecurityBreach('suspicious_user_agent');
    }

    // Verify expected browser features
    if (typeof window.chrome === 'undefined' && 
        navigator.userAgent.includes('Chrome')) {
      this.triggerSecurityBreach('browser_spoofing_detected');
    }
  }

  // Console obfuscation
  obfuscateConsole() {
    const methods = ['log', 'error', 'warn', 'info', 'debug', 'trace'];
    methods.forEach(method => {
      const original = console[method];
      console[method] = function(...args) {
        // Only show messages in development
        if (process.env.NODE_ENV === 'development') {
          return original.apply(console, args);
        }
        // In production, show fake security message
        return original.apply(console, ['🛡️ Security system active. Unauthorized access monitored.']);
      };
    });
  }

  // Utility methods
  calculateHash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return hash.toString(36);
  }

  checkDOMIntegrity() {
    // Check for suspicious script injections
    const scripts = document.querySelectorAll('script:not([src])');
    scripts.forEach(script => {
      if (script.textContent.includes('eval') || 
          script.textContent.includes('Function') ||
          script.textContent.includes('debugger')) {
        this.triggerSecurityBreach('malicious_script_injection');
      }
    });
  }

  analyzeMethodUsage(method, args) {
    // Detect suspicious eval usage
    if (method === 'eval' && args.length > 0) {
      this.triggerSecurityBreach('eval_usage_detected');
    }

    // Detect code injection attempts
    if (method === 'setTimeout' || method === 'setInterval') {
      if (typeof args[0] === 'string') {
        this.triggerSecurityBreach('string_execution_attempt');
      }
    }
  }

  analyzeBehaviorPatterns() {
    const now = Date.now();
    const timeWindow = 10000; // 10 seconds

    // Analyze mouse movements
    const recentMouse = this.mouseMovementTracker.filter(
      movement => now - movement.timestamp < timeWindow
    );

    // Detect bot-like behavior (too perfect movements)
    if (recentMouse.length > 50) {
      const movements = recentMouse.map(m => ({ x: m.x, y: m.y }));
      if (this.isMovementTooRobotic(movements)) {
        this.triggerSecurityBreach('robotic_behavior_detected');
      }
    }

    // Check for absence of human interaction
    if (now - this.initTime > 30000 && 
        this.mouseMovementTracker.length === 0 && 
        this.keyboardTracker.length === 0) {
      this.triggerSecurityBreach('no_human_interaction');
    }
  }

  isMovementTooRobotic(movements) {
    if (movements.length < 10) return false;

    // Check for perfectly straight lines or repeated patterns
    let straightLines = 0;
    for (let i = 2; i < movements.length; i++) {
      const dx1 = movements[i-1].x - movements[i-2].x;
      const dy1 = movements[i-1].y - movements[i-2].y;
      const dx2 = movements[i].x - movements[i-1].x;
      const dy2 = movements[i].y - movements[i-1].y;

      // Check if movement is in perfectly straight line
      if (dx1 === dx2 && dy1 === dy2 && (dx1 !== 0 || dy1 !== 0)) {
        straightLines++;
      }
    }

    // Too many straight line movements indicate bot behavior
    return straightLines > movements.length * 0.7;
  }

  triggerSecurityBreach(type) {
    this.securityViolations++;
    
    // Log security violation (in real app, send to security endpoint)
    console.warn(`🚨 Security breach detected: ${type}`);

    // Escalating security responses
    if (this.securityViolations >= this.maxViolations) {
      this.executeCountermeasures();
    } else {
      // Warning actions
      this.showSecurityWarning(type);
    }
  }

  showSecurityWarning(type) {
    // Create subtle warning overlay
    const warning = document.createElement('div');
    warning.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: #ff4444;
      color: white;
      padding: 10px;
      border-radius: 5px;
      z-index: 10000;
      font-family: monospace;
      font-size: 12px;
      max-width: 300px;
    `;
    warning.textContent = `Security Alert: ${type}`;
    document.body.appendChild(warning);

    setTimeout(() => {
      if (warning.parentNode) {
        warning.parentNode.removeChild(warning);
      }
    }, 5000);
  }

  executeCountermeasures() {
    // Level 1: Clear sensitive data
    try {
      localStorage.clear();
      sessionStorage.clear();
    } catch (e) {}

    // Level 2: Redirect to security page
    setTimeout(() => {
      window.location.href = 'about:blank';
    }, 1000);

    // Level 3: Disable page functionality
    document.body.style.display = 'none';
    document.body.innerHTML = `
      <div style="
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: #000;
        color: #ff0000;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: monospace;
        font-size: 24px;
        z-index: 999999;
      ">
        🛡️ SECURITY BREACH DETECTED<br>
        ACCESS TERMINATED
      </div>
    `;

    // Level 4: Crash the tab
    setTimeout(() => {
      while (true) {
        // Infinite loop to consume resources
        console.log('Security breach - terminating session');
      }
    }, 2000);
  }

  // Clean shutdown
  destroy() {
    if (this.debuggerDetectionInterval) {
      clearInterval(this.debuggerDetectionInterval);
    }
    if (this.integrityCheckInterval) {
      clearInterval(this.integrityCheckInterval);
    }
  }
}

// Auto-initialize security shield
const securityShield = new SecurityShield();

// Export for use in other components
export default SecurityShield;