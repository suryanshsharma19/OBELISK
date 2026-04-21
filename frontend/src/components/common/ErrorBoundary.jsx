/**
 * React error boundary — catches render errors and shows a
 * friendly fallback UI instead of a blank screen.
 */

import React from 'react';
import { AlertTriangle } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    // In production, send this to an error-tracking service
    console.error('[ErrorBoundary]', error, info.componentStack);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-[40vh] flex-col items-center justify-center gap-4 p-8 text-gray-400">
          <AlertTriangle size={48} className="text-red-400" />
          <h2 className="text-xl font-semibold text-white">Something went wrong</h2>
          <p className="max-w-md text-center text-sm">
            {this.state.error?.message || 'An unexpected error occurred.'}
          </p>
          <button
            onClick={this.handleRetry}
            className="rounded-lg bg-neon-600 px-4 py-2 text-sm font-medium text-white hover:bg-neon-700"
          >
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
