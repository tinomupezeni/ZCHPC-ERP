import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

// Separate from vite.config.ts (which uses Vite's own defineConfig and a
// loadEnv-dependent function form) so the dev/build pipeline is untouched.
// Test-only config: jsdom environment + the same '@' alias the app uses.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: false,
    // Radix's Select/Dialog primitives can hang under jsdom's incomplete
    // PointerEvent support rather than throwing - fail fast instead of
    // eating the default 5s x however many retries.
    testTimeout: 8000,
  },
});
