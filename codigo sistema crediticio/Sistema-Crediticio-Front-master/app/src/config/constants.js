/**
 * Environment-based configuration.
 * Vite exposes only variables prefixed with VITE_ to the client.
 * Switch environments with: npm run dev -- --mode qa
 */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
export const APP_NAME = import.meta.env.VITE_APP_NAME || 'Colsubsidio NBO Engine'
export const APP_ENV = import.meta.env.VITE_APP_ENV || 'development'

export const POLLING_INTERVAL = 5000 // ms

export const ROUTES = {
  UPLOAD: '/',
  LOOKUP: '/lookup',
  HEALTH: '/health',
}

export const NAV_ITEMS = [
  { path: ROUTES.UPLOAD, label: 'Carga Masiva', icon: 'Upload' },
  { path: ROUTES.LOOKUP, label: 'Búsqueda', icon: 'Search' },
  { path: ROUTES.HEALTH, label: 'Salud', icon: 'Activity' },
]
