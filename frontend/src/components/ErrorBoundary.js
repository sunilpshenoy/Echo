import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log error details
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    this.setState({
      error: error,
      errorInfo: errorInfo
    });

    // Log to external service if needed
    this.logErrorToService(error, errorInfo);
  }

  logErrorToService(error, errorInfo) {
    // In a real app, you'd send this to an error reporting service
    const errorReport = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      userAgent: navigator.userAgent
    };
    
    // Store in localStorage for debugging
    const existingErrors = JSON.parse(localStorage.getItem('pulse-errors') || '[]');
    existingErrors.push(errorReport);
    // Keep only last 10 errors
    localStorage.setItem('pulse-errors', JSON.stringify(existingErrors.slice(-10)));
  }

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
  };

  handleReportError = () => {
    const { error, errorInfo } = this.state;
    const mailto = `mailto:support@pulse-app.com?subject=Error Report&body=${encodeURIComponent(
      `Error: ${error.message}\n\nStack: ${error.stack}\n\nComponent Stack: ${errorInfo.componentStack}\n\nURL: ${window.location.href}\n\nUser Agent: ${navigator.userAgent}`
    )}`;
    window.open(mailto);
  };

  render() {
    if (this.state.hasError) {
      // Custom error UI
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
          <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6 text-center">
            <div className="text-6xl mb-4">😔</div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">
              Oops! Something went wrong
            </h2>
            <p className="text-gray-600 mb-6">
              We're sorry for the inconvenience. The app encountered an unexpected error.
            </p>
            
            <div className="space-y-3">
              <button
                onClick={this.handleRetry}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
              >
                🔄 Try Again
              </button>
              
              <button
                onClick={() => window.location.reload()}
                className="w-full bg-gray-100 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-200 transition-colors"
              >
                🔃 Refresh Page
              </button>
              
              <button
                onClick={this.handleReportError}
                className="w-full bg-red-100 text-red-700 py-2 px-4 rounded-lg hover:bg-red-200 transition-colors"
              >
                📧 Report Error
              </button>
            </div>

            {/* Debug info for development */}
            {process.env.NODE_ENV === 'development' && (
              <details className="mt-6 text-left">
                <summary className="cursor-pointer text-sm text-gray-500">
                  Debug Information (Dev Mode)
                </summary>
                <div className="mt-2 text-xs text-gray-600 bg-gray-100 p-2 rounded">
                  <strong>Error:</strong> {this.state.error && this.state.error.toString()}
                  <br />
                  <strong>Component Stack:</strong>
                  <pre className="whitespace-pre-wrap text-xs mt-1">
                    {this.state.errorInfo && this.state.errorInfo.componentStack}
                  </pre>
                </div>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;