import React from 'react';
import Button from './ui/Button';
import Card from './ui/Card';

class GamesErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null,
      retryCount: 0
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('🎮 Games Error Boundary caught an error:', error, errorInfo);
    
    this.setState({
      error: error,
      errorInfo: errorInfo
    });

    // Log games-specific error
    this.logGamesError(error, errorInfo);
  }

  logGamesError(error, errorInfo) {
    const errorReport = {
      type: 'games-error',
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      retryCount: this.state.retryCount,
      gameContext: {
        url: window.location.href,
        userAgent: navigator.userAgent,
        viewport: `${window.innerWidth}x${window.innerHeight}`
      }
    };
    
    // Store in localStorage for debugging
    const existingErrors = JSON.parse(localStorage.getItem('pulse-games-errors') || '[]');
    existingErrors.push(errorReport);
    localStorage.setItem('pulse-games-errors', JSON.stringify(existingErrors.slice(-5)));
  }

  handleRetry = () => {
    console.log('🔄 Retrying Games component...');
    this.setState(prevState => ({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: prevState.retryCount + 1
    }));
  };

  handleResetGames = () => {
    console.log('🎮 Resetting Games data...');
    // Clear any corrupted games data
    const keysToRemove = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && (key.startsWith('pulse_game_') || key.includes('games'))) {
        keysToRemove.push(key);
      }
    }
    keysToRemove.forEach(key => localStorage.removeItem(key));
    
    this.handleRetry();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="games-interface h-full flex flex-col bg-gradient-to-br from-gray-50 to-gray-100 dark:from-slate-900 dark:to-slate-800 p-6">
          <div className="flex-1 flex items-center justify-center">
            <Card className="max-w-lg w-full text-center" padding="xl">
              <div className="text-6xl mb-4">🎮💥</div>
              
              <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                Games Hub Error
              </h2>
              
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                The Games Hub encountered an unexpected error. Don't worry, your progress is safe!
              </p>

              <div className="space-y-3">
                <Button
                  variant="primary"
                  size="md"
                  fullWidth
                  onClick={this.handleRetry}
                  icon="🔄"
                >
                  Try Again
                </Button>

                {this.state.retryCount > 0 && (
                  <Button
                    variant="secondary"
                    size="md"
                    fullWidth
                    onClick={this.handleResetGames}
                    icon="🎯"
                  >
                    Reset Games Data
                  </Button>
                )}

                <Button
                  variant="outline"
                  size="md"
                  fullWidth
                  onClick={() => window.location.reload()}
                  icon="🔃"
                >
                  Refresh Page
                </Button>
              </div>

              {/* Error details for debugging */}
              <details className="mt-6 text-left">
                <summary className="cursor-pointer text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300">
                  Technical Details {this.state.retryCount > 0 && `(Retry ${this.state.retryCount})`}
                </summary>
                
                <div className="mt-3 text-xs bg-gray-100 dark:bg-slate-800 p-3 rounded-lg">
                  <div className="mb-2">
                    <strong className="text-red-600 dark:text-red-400">Error:</strong>
                    <br />
                    <code className="text-gray-800 dark:text-gray-200">
                      {this.state.error && this.state.error.toString()}
                    </code>
                  </div>
                  
                  {process.env.NODE_ENV === 'development' && (
                    <div>
                      <strong className="text-blue-600 dark:text-blue-400">Component Stack:</strong>
                      <pre className="whitespace-pre-wrap text-xs mt-1 text-gray-700 dark:text-gray-300 max-h-32 overflow-y-auto">
                        {this.state.errorInfo && this.state.errorInfo.componentStack}
                      </pre>
                    </div>
                  )}
                </div>
              </details>
            </Card>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default GamesErrorBoundary;