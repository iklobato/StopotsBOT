const contentModule = require('../content.js');

const {
    LETTER_XPATH,
    JOGAR_BUTTON_XPATH,
    AVALIAR_BUTTON_XPATH,
    CATEGORY_LABEL_XPATH,
    CATEGORY_INPUT_XPATH,
    getElementByXPath,
    getElementsByXPath,
    getCurrentLetter,
    getCategories,
    fillCategory,
    clickJogarButton,
    clickAvaliarButton,
    processRound,
    setEnabled,
} = contentModule;

describe('XPath Constants', () => {
  test('LETTER_XPATH is defined', () => {
    expect(LETTER_XPATH).toBeDefined();
    expect(typeof LETTER_XPATH).toBe('string');
  });

  test('JOGAR_BUTTON_XPATH is defined', () => {
    expect(JOGAR_BUTTON_XPATH).toBeDefined();
    expect(typeof JOGAR_BUTTON_XPATH).toBe('string');
  });

  test('AVALIAR_BUTTON_XPATH is defined', () => {
    expect(AVALIAR_BUTTON_XPATH).toBeDefined();
    expect(typeof AVALIAR_BUTTON_XPATH).toBe('string');
  });

  test('CATEGORY_LABEL_XPATH is defined', () => {
    expect(CATEGORY_LABEL_XPATH).toBeDefined();
    expect(typeof CATEGORY_LABEL_XPATH).toBe('string');
  });

  test('CATEGORY_INPUT_XPATH is defined', () => {
    expect(CATEGORY_INPUT_XPATH).toBeDefined();
    expect(typeof CATEGORY_INPUT_XPATH).toBe('string');
  });
});

describe('getElementByXPath', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div id="test-container">
        <p class="letter">A</p>
        <button id="jogar-btn">JOGAR</button>
        <input id="test-input" value="test" />
      </div>
    `;
  });

  test('returns element for valid xpath', () => {
    const el = getElementByXPath('//p[@class="letter"]');
    expect(el).toBeTruthy();
    expect(el.textContent).toBe('A');
  });

  test('returns null for invalid xpath', () => {
    const el = getElementByXPath('//div[@class="nonexistent"]');
    expect(el).toBeNull();
  });

  test('can search within parent element', () => {
    const container = document.getElementById('test-container');
    const el = getElementByXPath('//p[@class="letter"]', container);
    expect(el).toBeTruthy();
  });

  test('returns first matching element', () => {
    document.body.innerHTML = `
      <div><p class="letter">First</p></div>
      <div><p class="letter">Second</p></div>
    `;
    const el = getElementByXPath('//p[@class="letter"]');
    expect(el.textContent).toBe('First');
  });

  test('handles xpath with text()', () => {
    document.body.innerHTML = `<span>Hello World</span>`;
    const el = getElementByXPath('//span[text()="Hello World"]');
    expect(el).toBeTruthy();
    expect(el.textContent).toBe('Hello World');
  });

  test('handles xpath with contains()', () => {
    document.body.innerHTML = `<div class="category-item">Category</div>`;
    const el = getElementByXPath('//div[contains(@class, "category")]');
    expect(el).toBeTruthy();
  });
});

describe('getElementsByXPath', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div id="categories">
        <div class="category"><legend><p>animal</p></legend><input value="" /></div>
        <div class="category"><legend><p>fruta</p></legend><input value="" /></div>
        <div class="category"><legend><p>comida</p></legend><input value="" /></div>
      </div>
    `;
  });

  test('returns array of elements', () => {
    const elements = getElementsByXPath('//div[@class="category"]//p');
    expect(Array.isArray(elements)).toBe(true);
    expect(elements.length).toBe(3);
  });

  test('returns empty array for no matches', () => {
    const elements = getElementsByXPath('//div[@class="nonexistent"]');
    expect(elements).toEqual([]);
  });

  test('returns correct elements in order', () => {
    const elements = getElementsByXPath('//div[@class="category"]//p');
    expect(elements[0].textContent).toBe('animal');
    expect(elements[1].textContent).toBe('fruta');
    expect(elements[2].textContent).toBe('comida');
  });

  test('handles nested xpath', () => {
    document.body.innerHTML = `
      <ul>
        <li><span>Item 1</span></li>
        <li><span>Item 2</span></li>
      </ul>
    `;
    const elements = getElementsByXPath('//ul/li/span');
    expect(elements.length).toBe(2);
  });

  test('returns empty array for null xpath', () => {
    const elements = getElementsByXPath(null);
    expect(elements).toEqual([]);
  });
});

describe('getCurrentLetter', () => {
  beforeEach(() => {
    document.body.innerHTML = `<p class="letter"></p>`;
  });

  test('returns letter from DOM', () => {
    document.querySelector('.letter').textContent = ' A ';
    const letter = getCurrentLetter();
    expect(letter).toBe('A');
  });

  test('returns null for question mark', () => {
    document.querySelector('.letter').textContent = '?';
    const letter = getCurrentLetter();
    expect(letter).toBeNull();
  });

  test('returns null for empty text', () => {
    document.querySelector('.letter').textContent = '';
    const letter = getCurrentLetter();
    expect(letter).toBeNull();
  });

  test('returns null when element not found', () => {
    document.body.innerHTML = '';
    const letter = getCurrentLetter();
    expect(letter).toBeNull();
  });

  test('extracts first letter from mixed content', () => {
    document.querySelector('.letter').textContent = 'Tempo: A';
    const letter = getCurrentLetter();
    expect(letter).toBe('T');
  });

  test('handles lowercase letter', () => {
    document.querySelector('.letter').textContent = 'b';
    const letter = getCurrentLetter();
    expect(letter).toBe('B');
  });

  test('handles letter with numbers', () => {
    document.querySelector('.letter').textContent = 'A1';
    const letter = getCurrentLetter();
    expect(letter).toBe('A');
  });

  test('handles special characters around letter', () => {
    document.querySelector('.letter').textContent = '#@$A$#@';
    const letter = getCurrentLetter();
    expect(letter).toBe('A');
  });

  test('handles whitespace-only input', () => {
    document.querySelector('.letter').textContent = '   ';
    const letter = getCurrentLetter();
    expect(letter).toBeNull();
  });

  test('handles letter with spaces around', () => {
    document.querySelector('.letter').textContent = '  Z  ';
    const letter = getCurrentLetter();
    expect(letter).toBe('Z');
  });

  test('handles multiple letters - returns first', () => {
    document.querySelector('.letter').textContent = 'ABC';
    const letter = getCurrentLetter();
    expect(letter).toBe('A');
  });

  test('handles unicode characters', () => {
    document.querySelector('.letter').textContent = 'Ação';
    const letter = getCurrentLetter();
    expect(letter).toBe('A');
  });

  test('handles Portuguese word with letter', () => {
    document.querySelector('.letter').textContent = 'Letra: P';
    const letter = getCurrentLetter();
    expect(letter).toBe('L');
  });
});

describe('getCategories', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div id="categories">
        <div class="category">
          <legend><p>Animal</p></legend>
          <input value="" />
        </div>
        <div class="category">
          <legend><p>Fruta</p></legend>
          <input value="banana" />
        </div>
        <div class="category">
          <legend><p>Comida</p></legend>
          <input value="" />
        </div>
      </div>
    `;
  });

  test('returns array of category objects', () => {
    const categories = getCategories();
    expect(Array.isArray(categories)).toBe(true);
    expect(categories.length).toBe(3);
  });

  test('each category has label, input, and filled properties', () => {
    const categories = getCategories();
    categories.forEach(cat => {
      expect(cat).toHaveProperty('label');
      expect(cat).toHaveProperty('input');
      expect(cat).toHaveProperty('filled');
    });
  });

  test('correctly identifies filled inputs', () => {
    const categories = getCategories();
    expect(categories[0].filled).toBe(false);
    expect(categories[1].filled).toBe(true);
    expect(categories[2].filled).toBe(false);
  });

  test('returns empty array when no categories exist', () => {
    document.body.innerHTML = '<div id="empty"></div>';
    const categories = getCategories();
    expect(categories).toEqual([]);
  });

  test('handles whitespace in input value', () => {
    document.body.innerHTML = `
      <div class="category">
        <legend><p>Test</p></legend>
        <input value="   " />
      </div>
    `;
    const categories = getCategories();
    expect(categories[0].filled).toBe(false);
  });

  test('handles empty label', () => {
    document.body.innerHTML = `
      <div class="category">
        <legend><p></p></legend>
        <input value="" />
      </div>
    `;
    const categories = getCategories();
    expect(categories[0].label).toBe('');
  });

  test('handles label with special characters', () => {
    document.body.innerHTML = `
      <div class="category">
        <legend><p>App ou Site</p></legend>
        <input value="" />
      </div>
    `;
    const categories = getCategories();
    expect(categories[0].label).toBe('App ou Site');
  });

  test('handles more labels than inputs', () => {
    document.body.innerHTML = `
      <div class="category">
        <legend><p>Label 1</p></legend>
        <input value="" />
      </div>
      <div class="category">
        <legend><p>Label 2</p></legend>
      </div>
    `;
    const categories = getCategories();
    expect(categories.length).toBe(1);
  });

  test('handles more inputs than labels', () => {
    document.body.innerHTML = `
      <div class="category">
        <legend><p>Label 1</p></legend>
        <input value="" />
        <input value="" />
      </div>
    `;
    const categories = getCategories();
    expect(categories.length).toBe(1);
  });
});

describe('fillCategory', () => {
  let mockInput;

  beforeEach(() => {
    document.body.innerHTML = '<input id="test-input" />';
    mockInput = document.getElementById('test-input');
    jest.spyOn(mockInput, 'dispatchEvent');
  });

  test('sets input value', () => {
    fillCategory(mockInput, 'a', 'animal');
    expect(mockInput.value).toBeTruthy();
  });

  test('dispatches input event', () => {
    fillCategory(mockInput, 'a', 'animal');
    expect(mockInput.dispatchEvent).toHaveBeenCalled();
  });

  test('dispatches change event', () => {
    fillCategory(mockInput, 'a', 'animal');
    const events = mockInput.dispatchEvent.mock.calls.map(call => call[0].type);
    expect(events).toContain('input');
    expect(events).toContain('change');
  });

  test('handles uppercase letter', () => {
    fillCategory(mockInput, 'A', 'animal');
    expect(mockInput.value).toBeTruthy();
  });

  test('handles special category name', () => {
    fillCategory(mockInput, 'a', 'app ou site');
    expect(mockInput.value).toBeTruthy();
  });

  test('trims whitespace from input before checking', () => {
    mockInput.value = '  ';
    fillCategory(mockInput, 'a', 'animal');
    expect(mockInput.value).toBeTruthy();
  });
});

describe('clickJogarButton', () => {
  beforeEach(() => {
    document.body.innerHTML = '<button id="jogar">JOGAR</button>';
    jest.spyOn(document.getElementById('jogar'), 'click');
  });

  test('clicks button when exists and not disabled', () => {
    const result = clickJogarButton();
    expect(result).toBe(true);
    expect(document.getElementById('jogar').click).toHaveBeenCalled();
  });

  test('returns false when button not found', () => {
    document.body.innerHTML = '';
    const result = clickJogarButton();
    expect(result).toBe(false);
  });

  test('returns false when button is disabled', () => {
    document.body.innerHTML = '<button id="jogar" disabled>JOGAR</button>';
    const result = clickJogarButton();
    expect(result).toBe(false);
  });

  test('handles button with different case', () => {
    document.body.innerHTML = '<button id="jogar">jogar</button>';
    const result = clickJogarButton();
    expect(result).toBe(false);
  });

  test('handles button inside fieldset', () => {
    document.body.innerHTML = `
      <fieldset disabled>
        <button id="jogar">JOGAR</button>
      </fieldset>
    `;
    const result = clickJogarButton();
    expect(result).toBe(true);
  });
});

describe('clickAvaliarButton', () => {
  beforeEach(() => {
    document.body.innerHTML = '<button id="avaliar">AVALIAR</button>';
    jest.spyOn(document.getElementById('avaliar'), 'click');
  });

  test('clicks button when exists and not disabled', () => {
    const result = clickAvaliarButton();
    expect(result).toBe(true);
    expect(document.getElementById('avaliar').click).toHaveBeenCalled();
  });

  test('returns false when button not found', () => {
    document.body.innerHTML = '';
    const result = clickAvaliarButton();
    expect(result).toBe(false);
  });

  test('handles ESTOU PRONTO button', () => {
    document.body.innerHTML = '<button id="avaliar">ESTOU PRONTO</button>';
    jest.spyOn(document.getElementById('avaliar'), 'click');
    const result = clickAvaliarButton();
    expect(result).toBe(true);
  });

  test('handles lowercase avaliar', () => {
    document.body.innerHTML = '<button id="avaliar">avaliar</button>';
    jest.spyOn(document.getElementById('avaliar'), 'click');
    const result = clickAvaliarButton();
    expect(result).toBe(false);
  });

  test('returns false for disabled avaliar button', () => {
    document.body.innerHTML = '<button id="avaliar" disabled>AVALIAR</button>';
    const result = clickAvaliarButton();
    expect(result).toBe(false);
  });
});

describe('processRound', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <p class="letter">A</p>
      <div id="categories">
        <div class="category">
          <legend><p>animal</p></legend>
          <input value="" />
        </div>
      </div>
    `;
    setEnabled(false);
    contentModule.lastLetter = null;
  });

  afterEach(() => {
    setEnabled(false);
    contentModule.lastLetter = null;
  });

  test('does nothing when disabled', () => {
    setEnabled(false);
    processRound();
    const input = document.querySelector('input');
    expect(input.value).toBe('');
  });

  test('skips when no letter', () => {
    document.querySelector('.letter').textContent = '';
    setEnabled(true);
    processRound();
    const input = document.querySelector('input');
    expect(input.value).toBe('');
  });

  test('skips when letter is question mark', () => {
    document.querySelector('.letter').textContent = '?';
    setEnabled(true);
    processRound();
    const input = document.querySelector('input');
    expect(input.value).toBe('');
  });

  test('skips duplicate letter', () => {
    contentModule.lastLetter = 'A';
    setEnabled(true);
    processRound();
    const input = document.querySelector('input');
    expect(input.value).toBe('');
  });

  test('fills categories for new letter', () => {
    setEnabled(true);
    processRound();
    const input = document.querySelector('input');
    expect(input.value).toBeTruthy();
  });

  test('updates lastLetter', () => {
    setEnabled(true);
    processRound();
    expect(contentModule.lastLetter).toBe('A');
  });

  test('skips when all categories filled', () => {
    document.body.innerHTML = `
      <p class="letter">B</p>
      <div class="category">
        <legend><p>animal</p></legend>
        <input value="already filled" />
      </div>
    `;
    setEnabled(true);
    contentModule.lastLetter = null;
    processRound();
    const input = document.querySelector('input');
    expect(input.value).toBe('already filled');
  });

  test('handles mixed filled/unfilled categories', () => {
    document.body.innerHTML = `
      <p class="letter">C</p>
      <div class="category">
        <legend><p>animal</p></legend>
        <input value="filled" />
      </div>
      <div class="category">
        <legend><p>fruta</p></legend>
        <input value="" />
      </div>
    `;
    setEnabled(true);
    contentModule.lastLetter = null;
    processRound();
    const inputs = document.querySelectorAll('input');
    expect(inputs[0].value).toBe('filled');
    expect(inputs[1].value).toBeTruthy();
  });

  test('handles empty categories array', () => {
    document.body.innerHTML = `
      <p class="letter">D</p>
      <div id="categories"></div>
    `;
    setEnabled(true);
    contentModule.lastLetter = null;
    expect(() => processRound()).not.toThrow();
  });

  test('handles letter change', () => {
    setEnabled(true);
    contentModule.lastLetter = 'A';
    document.querySelector('.letter').textContent = 'B';
    processRound();
    expect(contentModule.lastLetter).toBe('B');
  });
});

describe('setEnabled', () => {
  beforeEach(() => {
    setEnabled(false);
    contentModule.lastLetter = null;
    if (contentModule.gameLoopInterval) {
      clearInterval(contentModule.gameLoopInterval);
    }
  });

  afterEach(() => {
    setEnabled(false);
    if (contentModule.gameLoopInterval) {
      clearInterval(contentModule.gameLoopInterval);
    }
  });

  test('sets isEnabled to true', () => {
    setEnabled(true);
    expect(contentModule.isEnabled).toBe(true);
  });

  test('sets isEnabled to false', () => {
    setEnabled(true);
    setEnabled(false);
    expect(contentModule.isEnabled).toBe(false);
  });

  test('saves to chrome storage', () => {
    setEnabled(true);
    expect(chrome.storage.local.set).toHaveBeenCalledWith({ enabled: true });
  });

  test('starts game loop when enabled', () => {
    setEnabled(true);
    expect(contentModule.gameLoopInterval).toBeTruthy();
  });

  test('stops game loop when disabled', () => {
    setEnabled(true);
    setEnabled(false);
    expect(contentModule.gameLoopInterval).toBeNull();
  });

  test('does not start multiple intervals when called twice', () => {
    setEnabled(true);
    const firstInterval = contentModule.gameLoopInterval;
    setEnabled(true);
    const secondInterval = contentModule.gameLoopInterval;
    expect(firstInterval).toBe(secondInterval);
  });

  test('saves false to chrome storage when disabled', () => {
    setEnabled(true);
    setEnabled(false);
    expect(chrome.storage.local.set).toHaveBeenCalledWith({ enabled: false });
  });
});

describe('gameLoop', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <p class="letter">X</p>
      <button id="jogar">JOGAR</button>
      <button id="avaliar">AVALIAR</button>
      <div class="category">
        <legend><p>animal</p></legend>
        <input value="" />
      </div>
    `;
    jest.useFakeTimers();
    setEnabled(false);
    contentModule.lastLetter = null;
    if (contentModule.gameLoopInterval) {
      clearInterval(contentModule.gameLoopInterval);
    }
  });

  afterEach(() => {
    jest.useRealTimers();
    setEnabled(false);
    if (contentModule.gameLoopInterval) {
      clearInterval(contentModule.gameLoopInterval);
    }
  });

  test('does not run when disabled', () => {
    setEnabled(false);
    jest.advanceTimersByTime(5000);
    const input = document.querySelector('input');
    expect(input.value).toBe('');
  });

  test('runs at interval when enabled', () => {
    setEnabled(true);
    jest.advanceTimersByTime(500);
    const input = document.querySelector('input');
    expect(input.value).toBeTruthy();
  });

  test('processes multiple rounds over time', () => {
    setEnabled(true);
    jest.advanceTimersByTime(1500);
    const input = document.querySelector('input');
    expect(input.value).toBeTruthy();
  });
});

describe('integration: full game flow', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <p class="letter">B</p>
      <button id="jogar">JOGAR</button>
      <button id="avaliar">AVALIAR</button>
      <div id="categories">
        <div class="category">
          <legend><p>animal</p></legend>
          <input value="" />
        </div>
        <div class="category">
          <legend><p>fruta</p></legend>
          <input value="" />
        </div>
        <div class="category">
          <legend><p>comida</p></legend>
          <input value="arroz" />
        </div>
      </div>
    `;
    jest.useFakeTimers();
    setEnabled(false);
    contentModule.lastLetter = null;
    if (contentModule.gameLoopInterval) {
      clearInterval(contentModule.gameLoopInterval);
    }
  });

  afterEach(() => {
    jest.useRealTimers();
    setEnabled(false);
    if (contentModule.gameLoopInterval) {
      clearInterval(contentModule.gameLoopInterval);
    }
  });

  test('fills all unfilled categories when round starts', () => {
    setEnabled(true);
    processRound();
    const inputs = document.querySelectorAll('input');
    expect(inputs[0].value).toBeTruthy();
    expect(inputs[1].value).toBeTruthy();
    expect(inputs[2].value).toBe('arroz');
  });

  test('game loop runs and processes round', () => {
    setEnabled(true);
    jest.advanceTimersByTime(1000);
    const inputs = document.querySelectorAll('input');
    expect(inputs[0].value).toBeTruthy();
  });

  test('handles rapid enable/disable toggling', () => {
    setEnabled(true);
    jest.advanceTimersByTime(600);
    setEnabled(false);
    jest.advanceTimersByTime(100);
    setEnabled(true);
    jest.advanceTimersByTime(600);
    const input = document.querySelector('input');
    expect(input.value).toBeTruthy();
  });

  test('preserves filled answers across rounds', () => {
    setEnabled(true);
    processRound();
    const input = document.querySelectorAll('input')[2];
    expect(input.value).toBe('arroz');
  });
});
