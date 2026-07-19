import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';

interface Props {
  children?: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div className="flex flex-col items-center justify-center w-full h-screen p-8 text-white bg-red-900/50 backdrop-blur-md">
          <h2 className="mb-4 text-2xl font-bold text-red-200">Something went wrong</h2>
          <div className="p-4 overflow-auto text-sm bg-black rounded-lg text-red-100/80 max-w-2xl max-h-64 whitespace-pre-wrap">
            {this.state.error?.message}
          </div>
          <button 
            className="px-6 py-2 mt-6 text-white bg-red-600 rounded-full hover:bg-red-500"
            onClick={() => this.setState({ hasError: false, error: undefined })}
          >
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
