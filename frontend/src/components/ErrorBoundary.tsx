import { Component, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-jazari-dark flex items-center justify-center">
          <div className="text-center space-y-4">
            <h1 className="text-jazari-gold text-2xl font-bold">Something went wrong</h1>
            <p className="text-jazari-text-dim text-sm">Jazari needs a moment. Please refresh.</p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-jazari-gold text-jazari-dark text-sm font-medium rounded-lg hover:bg-jazari-gold-light transition-colors"
            >
              Refresh
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
