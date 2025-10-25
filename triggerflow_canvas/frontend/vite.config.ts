import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const TEST_INCLUDE = "../../tests/triggerflow_canvas/frontend/**/*.test.{ts,tsx}";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://backend:8000",
        changeOrigin: true,
        secure: false
      }
    }
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./src/tests/setup.ts",
    include: [TEST_INCLUDE]
  }
});
