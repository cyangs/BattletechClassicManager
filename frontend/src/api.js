// Base URL for the FastAPI backend.
//
// In Docker (production): nginx proxies /api/* to the backend container,
// so an empty string makes all fetch calls relative to the current origin.
//
// In local dev: set VITE_API_URL=http://localhost:8000 in frontend/.env.local
// to point directly at the uvicorn dev server.
export const API = import.meta.env.VITE_API_URL ?? '';
