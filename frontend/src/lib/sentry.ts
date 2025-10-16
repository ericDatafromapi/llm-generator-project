/**
 * Sentry configuration for frontend error tracking and monitoring.
 * Integrates with React, React Router, and React Query.
 */
import * as Sentry from '@sentry/react';

/**
 * Initialize Sentry SDK for error tracking.
 * Call this function once at application startup.
 */
export function initSentry() {
  const sentryDsn = import.meta.env.VITE_SENTRY_DSN;
  const environment = import.meta.env.VITE_ENVIRONMENT || 'development';
  
  // Only initialize Sentry if DSN is provided
  if (!sentryDsn || sentryDsn === '') {
    console.log('Sentry disabled - No DSN configured');
    return;
  }
  
  Sentry.init({
    dsn: sentryDsn,
    environment,
    
    // Performance monitoring
    integrations: [
      new Sentry.BrowserTracing({
        // Set sampling rate for performance monitoring
        tracePropagationTargets: [
          'localhost',
          /^\//,  // Relative URLs
          /^https:\/\/yourapi\.yourdomain\.com/,  // Production API
        ],
      }),
    ],
    
    // Tracing - capture 10% of transactions in production
    tracesSampleRate: environment === 'production' ? 0.1 : 1.0,
    
    // Release tracking (optional)
    // release: 'llmready-frontend@1.0.0',
    
    // Additional options
    beforeSend(event: Sentry.Event, hint: Sentry.EventHint) {
      // Don't send events in development (unless explicitly enabled)
      if (environment === 'development' && !import.meta.env.VITE_SENTRY_DEBUG) {
        console.log('Sentry event (not sent in dev):', event);
        return null;
      }
      
      // Filter out specific errors if needed
      const error = hint.originalException;
      if (error instanceof Error) {
        // Skip network errors from failed API calls
        if (error.message.includes('Network Error')) {
          return null;
        }
        
        // Skip cancelled requests
        if (error.message.includes('cancelled') || error.message.includes('aborted')) {
          return null;
        }
      }
      
      return event;
    },
    
    // Don't send default PII (Personally Identifiable Information)
    sendDefaultPii: false,
    
    // Attach stack traces to messages
    attachStacktrace: true,
    
    // Normalize URLs to remove query parameters
    normalizeDepth: 10,
    
    // Ignore certain errors
    ignoreErrors: [
      // Browser extensions
      'top.GLOBALS',
      'chrome-extension://',
      'moz-extension://',
      // Network errors
      'Network request failed',
      'Failed to fetch',
      // Chunk loading errors (usually just old cached code)
      'Loading chunk',
      'ChunkLoadError',
    ],
  });
  
  console.log(`Sentry initialized - Environment: ${environment}`);
}

/**
 * Set user context for Sentry.
 * Call this after user authentication.
 */
export function setSentryUser(user: { id: string; email?: string; username?: string }) {
  Sentry.setUser({
    id: user.id,
    email: user.email,
    username: user.username,
  });
}

/**
 * Clear user context.
 * Call this on logout.
 */
export function clearSentryUser() {
  Sentry.setUser(null);
}

/**
 * Manually capture an exception.
 */
export function captureException(error: Error, context?: Record<string, any>) {
  Sentry.captureException(error, {
    extra: context,
  });
}

/**
 * Manually capture a message.
 */
export function captureMessage(message: string, level: Sentry.SeverityLevel = 'info') {
  Sentry.captureMessage(message, level);
}

/**
 * Add breadcrumb for debugging.
 */
export function addBreadcrumb(message: string, data?: Record<string, any>) {
  Sentry.addBreadcrumb({
    message,
    data,
    level: 'info',
  });
}