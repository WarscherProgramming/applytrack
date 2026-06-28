/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base origin of the backend API, e.g. http://localhost:8000.
   *  On Vercel production, set this to the Render backend origin. */
  readonly VITE_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
