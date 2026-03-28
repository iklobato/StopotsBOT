module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleFileExtensions: ['js', 'jsx'],
  testMatch: ['**/__tests__/**/*.test.js'],
  collectCoverageFrom: [
    '*.js',
    '!package.json',
    '!jest.config.js',
    '!jest.setup.js',
  ],
  coverageDirectory: 'coverage',
  verbose: true,
};
