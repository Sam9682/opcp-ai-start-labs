import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'jsdom',
    include: ['skillhub/tests/**/*.test.js'],
    setupFiles: ['skillhub/tests/setup.js'],
  },
});
