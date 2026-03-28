global.chrome = {
  storage: {
    local: {
      get: jest.fn((keys, callback) => {
        if (typeof keys === 'string') {
          callback({ [keys]: global.__chromeStorage?.[keys] });
        } else if (Array.isArray(keys)) {
          const result = {};
          keys.forEach(key => {
            result[key] = global.__chromeStorage?.[key];
          });
          callback(result);
        } else if (typeof keys === 'object' && keys !== null) {
          const result = {};
          Object.keys(keys).forEach(key => {
            result[key] = global.__chromeStorage?.[key] ?? keys[key];
          });
          callback(result);
        } else {
          callback(global.__chromeStorage || {});
        }
      }),
      set: jest.fn((items, callback) => {
        if (!global.__chromeStorage) {
          global.__chromeStorage = {};
        }
        Object.assign(global.__chromeStorage, items);
        if (callback) callback();
      }),
      onChanged: {
        addListener: jest.fn(),
        removeListener: jest.fn(),
      },
    },
  },
  tabs: {
    query: jest.fn(),
    sendMessage: jest.fn(),
  },
};

global.__chromeStorage = { enabled: false };
global.__TEST_MODE__ = true;

beforeEach(() => {
  jest.clearAllMocks();
  global.__chromeStorage = { enabled: false };
  chrome.storage.local.get.mockImplementation((keys, callback) => {
    if (typeof keys === 'string') {
      callback({ [keys]: global.__chromeStorage?.[keys] });
    } else if (Array.isArray(keys)) {
      const result = {};
      keys.forEach(key => {
        result[key] = global.__chromeStorage?.[key];
      });
      callback(result);
    } else if (typeof keys === 'object' && keys !== null) {
      const result = {};
      Object.keys(keys).forEach(key => {
        result[key] = global.__chromeStorage?.[key] ?? keys[key];
      });
      callback(result);
    } else {
      callback(global.__chromeStorage || {});
    }
  });
  chrome.storage.local.set.mockImplementation((items, callback) => {
    if (!global.__chromeStorage) {
      global.__chromeStorage = {};
    }
    Object.assign(global.__chromeStorage, items);
    if (callback) callback();
  });
});
