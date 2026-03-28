module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleFileExtensions: ['js', 'jsx'],
  testMatch: ['**/tests/**/*.test.js'],
  collectCoverageFrom: [
    '*.js',
    '!package.json',
    '!jest.config.js',
    '!jest.setup.js',
  ],
  coverageDirectory: 'coverage',
  verbose: true,
};
