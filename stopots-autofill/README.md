# Stopots Auto-Fill Chrome Extension

Chrome extension that automatically fills answers in the Stopots game.

## Features

- Automatic letter detection
- Fills all game categories with answers from built-in dictionary
- Toggle on/off via popup
- Handles accented Portuguese words
- Random answer selection from available options

## Installation

### From Source

1. Clone the repository or navigate to the extension folder:
   ```bash
   cd stopots-autofill
   ```

2. Install dependencies (for testing):
   ```bash
   npm install
   ```

3. Run tests (optional):
   ```bash
   npm test
   ```

### Load in Chrome

1. Open Chrome and navigate to `chrome://extensions/`

2. Enable **Developer mode** (toggle in top-right corner)

3. Click **Load unpacked**

4. Select the `stopots-autofill` folder

5. The extension icon should appear in your toolbar

## Usage

1. Navigate to [Stopots](https://stopots.com/pt/)

2. Join a game room

3. Click the extension icon in the toolbar

4. Toggle the switch to **ON**

5. The extension will automatically:
   - Click "JOGAR" when a new round starts
   - Fill all empty categories with answers
   - Click "AVALIAR" after filling

6. Toggle to **OFF** to stop automatic filling

## Testing

Run the unit tests:

```bash
npm test
```

Run tests with coverage:

```bash
npm run test:coverage
```

Run tests in watch mode:

```bash
npm run test:watch
```

## Project Structure

```
stopots-autofill/
├── manifest.json           # Extension configuration
├── dictionary.js          # Built-in answer dictionary
├── content.js            # Main automation logic
├── popup.html            # Toggle popup UI
├── popup.js              # Toggle logic
├── popup.css             # Popup styling
├── package.json          # Dependencies
├── jest.config.js        # Jest configuration
├── jest.setup.js         # Test mocks
└── __tests__/           # Unit tests
    ├── dictionary.test.js
    └── content.test.js
```

## Development

### Running Tests

```bash
npm test
```

### Test Coverage

The test suite covers:
- Dictionary lookup (accent removal, answer retrieval)
- XPath queries
- DOM operations
- Button clicking
- Game loop state management
- Edge cases and error handling

## License

MIT
