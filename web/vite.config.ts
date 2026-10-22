import { defineConfig } from 'vitest/config';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte()],
  base: process.env.BASE_PATH || '/ml_ops_vacancy/',
  test: { include: ['src/**/*.test.ts'] },
});
