import js from '@eslint/js';

export default [
  js.configs.recommended,
  {
    ignores: ['node_modules/**', 'coverage/**', '*.test.js'],
  },
  {
    files: ['**/*.js'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'script',
      globals: {
        browser: 'readonly',
        chrome: 'readonly',
        console: 'readonly',
        setInterval: 'readonly',
        clearInterval: 'readonly',
        document: 'readonly',
        XPathResult: 'readonly',
        Event: 'readonly',
        window: 'readonly',
        module: 'readonly',
        require: 'readonly',
        exports: 'readonly',
      },
    },
    rules: {
      indent: 'off',
      'linebreak-style': 'off',
      quotes: 'off',
      semi: 'off',
      'no-unused-vars': 'off',
      'no-console': 'off',
      'no-undef': 'off',
    },
  },
];
