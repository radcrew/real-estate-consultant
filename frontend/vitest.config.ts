import { defineConfig } from "vitest/config";

export default defineConfig({
  // Resolve the `@utils/*`, `@lib/*`, ... aliases from tsconfig.json natively.
  resolve: {
    tsconfigPaths: true,
  },
  test: {
    // Pure-logic suites default to node; component suites opt into jsdom per-file
    // via a `// @vitest-environment jsdom` docblock.
    environment: "node",
    globals: true,
    include: ["**/*.{test,spec}.{ts,tsx}"],
    exclude: ["node_modules", ".next", "dist"],
    coverage: {
      provider: "v8",
      reporter: ["text", "html"],
      include: [
        "lib/**/*.ts",
        "services/**/*.ts",
        "utils/**/*.{ts,tsx}",
        "config/**/*.ts",
        "components/**/*.tsx",
      ],
      exclude: ["**/*.d.ts", "**/*.{test,spec}.{ts,tsx}", "**/index.ts"],
    },
  },
});
