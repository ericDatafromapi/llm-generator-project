import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import * as Sentry from '@sentry/react'
import App from './App.tsx'
import './index.css'
import { initSentry } from './lib/sentry'

// Initialize Sentry before rendering
initSentry()

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <Sentry.ErrorBoundary
          fallback={({ error }: { error: Error }) => (
            <div style={{ padding: '2rem', textAlign: 'center' }}>
              <h1>Something went wrong</h1>
              <p>We've been notified and are working on it.</p>
              {import.meta.env.DEV && (
                <pre style={{ textAlign: 'left', marginTop: '1rem' }}>
                  {error.toString()}
                </pre>
              )}
              <button
                onClick={() => window.location.reload()}
                style={{
                  marginTop: '1rem',
                  padding: '0.5rem 1rem',
                  cursor: 'pointer',
                }}
              >
                Reload page
              </button>
            </div>
          )}
          showDialog
        >
          <App />
        </Sentry.ErrorBoundary>
      </QueryClientProvider>
    </BrowserRouter>
  </React.StrictMode>,
)