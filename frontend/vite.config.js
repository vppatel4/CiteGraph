import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// During local `npm run dev`, proxy API calls to the Go gateway so the browser
// can just call /api/... In production the nginx container does the same thing.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://localhost:8080", changeOrigin: true },
      "/healthz": { target: "http://localhost:8080", changeOrigin: true },
    },
  },
});
