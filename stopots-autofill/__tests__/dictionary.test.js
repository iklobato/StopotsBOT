const DICTIONARY = require('../dictionary.js');

const { getAnswer, removeAccents, DICTIONARY: DICT_DATA } = DICTIONARY;

describe('removeAccents', () => {
  test('removes acute accent from a', () => {
    expect(removeAccents('á')).toBe('a');
  });

  test('removes grave accent from a', () => {
    expect(removeAccents('à')).toBe('a');
  });

  test('removes circumflex from a', () => {
    expect(removeAccents('â')).toBe('a');
  });

  test('removes tilde from a', () => {
    expect(removeAccents('ã')).toBe('a');
  });

  test('removes cedilla from c', () => {
    expect(removeAccents('ç')).toBe('c');
  });

  test('removes multiple accents from word', () => {
    expect(removeAccents('Elétro Eletrônico')).toBe('Eletro Eletronico');
  });

  test('handles empty string', () => {
    expect(removeAccents('')).toBe('');
  });

  test('handles string without accents', () => {
    expect(removeAccents('casa')).toBe('casa');
  });

  test('removes accent from e', () => {
    expect(removeAccents('café')).toBe('cafe');
  });

  test('removes accent from i', () => {
    expect(removeAccents('vídeo')).toBe('video');
  });

  test('removes accent from o', () => {
    expect(removeAccents('não')).toBe('nao');
  });

  test('removes accent from u', () => {
    expect(removeAccents('cúpula')).toBe('cupula');
  });

  test('handles all portuguese accents', () => {
    expect(removeAccents('áàâãéêíóôõúüç')).toBe('aaaaeeiooouuc');
  });

  test('handles uppercase with accents', () => {
    expect(removeAccents('ÁÉÍÓÚ')).toBe('AEIOU');
  });

  test('handles mixed case with accents', () => {
    expect(removeAccents('São Paulo')).toBe('Sao Paulo');
  });

  test('handles special characters without accents', () => {
    expect(removeAccents('!@#$%^&*()')).toBe('!@#$%^&*()');
  });

  test('handles numbers', () => {
    expect(removeAccents('abc123')).toBe('abc123');
  });

  test('handles unicode emoji', () => {
    expect(removeAccents('hello😀')).toBe('hello😀');
  });

  test('handles whitespace', () => {
    expect(removeAccents('  espaço  ')).toBe('  espaco  ');
  });

  test('handles empty input', () => {
    expect(removeAccents('')).toBe('');
  });
});

describe('getAnswer', () => {
  test('returns answer for valid letter and category', () => {
    const answer = getAnswer('a', 'animal');
    expect(answer).toBeDefined();
    expect(typeof answer).toBe('string');
    expect(answer.length).toBeGreaterThan(0);
  });

  test('returns answer for capital letter', () => {
    const answer = getAnswer('A', 'animal');
    expect(answer).toBeDefined();
    expect(typeof answer).toBe('string');
  });

  test('handles accented category name', () => {
    const answer = getAnswer('a', 'Elétro Eletrônico');
    expect(answer).toBeDefined();
  });

  test('returns fallback for invalid letter', () => {
    const answer = getAnswer('zz', 'animal');
    expect(answer).toBe('zz-NaoSei');
  });

  test('returns fallback for invalid category', () => {
    const answer = getAnswer('a', 'invalid-category-xyz');
    expect(answer).toBe('a-NaoSei');
  });

  test('returns fallback for empty category', () => {
    const answer = getAnswer('a', '');
    expect(answer).toBe('a-NaoSei');
  });

  test('handles lowercase category', () => {
    const answer = getAnswer('a', 'ANIMAL');
    expect(answer).toBeDefined();
  });

  test('handles mixed case letter', () => {
    const answer = getAnswer('Ab', 'animal');
    expect(answer).toBeDefined();
  });

  test('returns valid answer for comida category', () => {
    const answer = getAnswer('a', 'comida');
    expect(answer).toBeDefined();
    const validAnswers = DICT_DATA.a.comida;
    expect(validAnswers).toContain(answer);
  });

  test('returns valid answer for fruta category', () => {
    const answer = getAnswer('b', 'fruta');
    expect(answer).toBeDefined();
    const validAnswers = DICT_DATA.b.fruta;
    expect(validAnswers).toContain(answer);
  });

  test('handles categoria with special characters', () => {
    const answer = getAnswer('a', 'app ou site');
    expect(answer).toBeDefined();
  });

  test('handles space-only category as invalid', () => {
    const answer = getAnswer('a', '   ');
    expect(answer).toBe('a-NaoSei');
  });

  test('multiple calls return random answers from pool', () => {
    const answers = new Set();
    for (let i = 0; i < 20; i++) {
      answers.add(getAnswer('a', 'animal'));
    }
    expect(answers.size).toBeGreaterThan(1);
  });

  test('handles letter a to z', () => {
    const letters = 'abcdefghijklmnopqrstuvwxyz'.split('');
    letters.forEach(letter => {
      const answer = getAnswer(letter, 'animal');
      expect(answer).toBeDefined();
    });
  });

  test('handles empty array category returns fallback', () => {
    const answer = getAnswer('k', 'metodologia');
    expect(answer).toBe('k-NaoSei');
  });

  test('handles category with underscore', () => {
    const answer = getAnswer('a', 'comida_saudavel');
    expect(answer).toBeDefined();
  });

  test('handles category with multiple spaces', () => {
    const answer = getAnswer('a', 'comida    saudavel');
    expect(answer).toBeDefined();
  });

  test('handles null letter', () => {
    const answer = getAnswer(null, 'animal');
    expect(answer).toBeDefined();
  });

  test('handles undefined letter', () => {
    const answer = getAnswer(undefined, 'animal');
    expect(answer).toBeDefined();
  });

  test('handles null category', () => {
    const answer = getAnswer('a', null);
    expect(answer).toBe('a-NaoSei');
  });

  test('handles undefined category', () => {
    const answer = getAnswer('a', undefined);
    expect(answer).toBe('a-NaoSei');
  });

  test('handles numeric letter', () => {
    const answer = getAnswer(123, 'animal');
    expect(answer).toBeDefined();
  });

  test('handles different categories for same letter', () => {
    const categories = ['animal', 'fruta', 'comida', 'cor', 'filme'];
    categories.forEach(cat => {
      const answer = getAnswer('a', cat);
      expect(answer).toBeDefined();
    });
  });

  test('handles special Portuguese categories', () => {
    const answer = getAnswer('a', 'eletro eletronico');
    expect(answer).toBeDefined();
  });

  test('handles category case insensitivity', () => {
    const answer1 = getAnswer('a', 'ANIMAL');
    const answer2 = getAnswer('a', 'animal');
    const answer3 = getAnswer('a', 'AnImAl');
    expect(answer1).toBeDefined();
    expect(answer2).toBeDefined();
    expect(answer3).toBeDefined();
  });
});

describe('DICTIONARY data integrity', () => {
  test('contains all letters a-z', () => {
    const letters = 'abcdefghijklmnopqrstuvwxyz'.split('');
    letters.forEach(letter => {
      expect(DICT_DATA[letter]).toBeDefined();
    });
  });

  test('each letter has animal category', () => {
    const letters = 'abcdefghijklmnopqrstuvwxyz'.split('');
    letters.forEach(letter => {
      if (DICT_DATA[letter]) {
        expect(DICT_DATA[letter].animal).toBeDefined();
      }
    });
  });

  test('animal categories have answers for most letters', () => {
    let lettersWithAnimals = 0;
    'abcdefghijklmnopqrstuvwxyz'.split('').forEach(letter => {
      if (DICT_DATA[letter] && DICT_DATA[letter].animal && DICT_DATA[letter].animal.length > 0) {
        lettersWithAnimals++;
      }
    });
    expect(lettersWithAnimals).toBeGreaterThan(10);
  });

  test('common categories exist for multiple letters', () => {
    const commonCategories = ['animal', 'fruta', 'comida', 'cor', 'filme'];
    commonCategories.forEach(cat => {
      const counts = {};
      'abcdefghijklmnopqrstuvwxyz'.split('').forEach(letter => {
        if (DICT_DATA[letter] && DICT_DATA[letter][cat]) {
          counts[cat] = (counts[cat] || 0) + 1;
        }
      });
      expect(counts[cat]).toBeGreaterThan(10);
    });
  });
});
