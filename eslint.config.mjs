// @ts-check
// Repository-wide ESLint flat config. Workspaces run `eslint .` from their own
// directory and ESLint resolves this file by walking up the tree.
import eslint from '@eslint/js';
import angular from 'angular-eslint';
import { defineConfig, globalIgnores } from 'eslint/config';
import globals from 'globals';
import tseslint from 'typescript-eslint';

export default defineConfig(
  globalIgnores([
    '**/node_modules/',
    '**/dist/',
    '**/coverage/',
    '**/.angular/',
    '**/.venv/',
    // Generated from packages/contract/openapi.yaml. Correctness is enforced by
    // `npm run verify:contract` (regenerate + diff), not by manual lint review.
    '**/*.gen.ts',
  ]),

  // All TypeScript: strict, type-aware rules.
  {
    files: ['**/*.ts'],
    extends: [
      eslint.configs.recommended,
      tseslint.configs.strictTypeChecked,
      tseslint.configs.stylisticTypeChecked,
    ],
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },

  // Angular application code.
  {
    files: ['apps/frontend/**/*.ts'],
    extends: [angular.configs.tsRecommended],
    processor: angular.processInlineTemplates,
    rules: {
      '@angular-eslint/component-selector': [
        'error',
        { type: 'element', prefix: 'app', style: 'kebab-case' },
      ],
      '@angular-eslint/directive-selector': [
        'error',
        { type: 'attribute', prefix: 'app', style: 'camelCase' },
      ],
    },
  },

  // Angular templates (external and inline).
  {
    files: ['apps/frontend/**/*.html'],
    extends: [angular.configs.templateRecommended, angular.configs.templateAccessibility],
  },

  // Node tooling scripts and config files.
  {
    files: ['**/*.{js,mjs}'],
    extends: [eslint.configs.recommended],
    languageOptions: { globals: globals.node },
  },
);
