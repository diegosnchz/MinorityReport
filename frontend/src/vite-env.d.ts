/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_PRECOG_ENABLED: string
  readonly VITE_PRECOG_CONFIDENCE_THRESHOLD: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
