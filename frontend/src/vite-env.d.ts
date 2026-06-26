/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base origin of the backend API, e.g. http://localhost:8000.
   *  Unset in production builds, where relative /api/* paths are used. */
  readonly VITE_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
