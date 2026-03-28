(function() {
    'use strict';

    const LETTER_XPATH = '//p[contains(@class, "letter")]';
    const JOGAR_BUTTON_XPATH = '//button[contains(., "JOGAR")]';
    const AVALIAR_BUTTON_XPATH = '//button[contains(., "AVALIAR")] | //button[contains(., "ESTOU PRONTO")]';
    const CATEGORY_LABEL_XPATH = '//div[contains(@class, "category")]//legend//p';
    const CATEGORY_INPUT_XPATH = '//div[contains(@class, "category")]//input';
    const VALIDATION_POPUP_XPATH = '//div[contains(@class, "modal")]';

    let isEnabled = false;
    let lastLetter = null;
    let gameLoopInterval = null;

    function log(msg) {
        console.log(`[Stopots-AutoFill] ${msg}`);
    }

    function removeAccents(str) {
        return str.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    }

    function getElementByXPath(xpath, parent = document) {
        return document.evaluate(
            xpath,
            parent,
            null,
            XPathResult.FIRST_ORDERED_NODE_TYPE,
            null
        ).singleNodeValue;
    }

    function getElementsByXPath(xpath, parent = document) {
        const result = document.evaluate(
            xpath,
            parent,
            null,
            XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
            null
        );
        const elements = [];
        for (let i = 0; i < result.snapshotLength; i++) {
            elements.push(result.snapshotItem(i));
        }
        return elements;
    }

    function getCurrentLetter() {
        const letterEl = getElementByXPath(LETTER_XPATH);
        if (!letterEl) return null;
        const text = letterEl.textContent.trim().toUpperCase();
        if (text === '?' || text === '') return null;
        const match = text.match(/[A-Z]/);
        return match ? match[0] : null;
    }

    function getCategories() {
        const labelEls = getElementsByXPath(CATEGORY_LABEL_XPATH);
        const inputEls = getElementsByXPath(CATEGORY_INPUT_XPATH);
        
        const categories = [];
        const count = Math.min(labelEls.length, inputEls.length);
        
        for (let i = 0; i < count; i++) {
            const label = labelEls[i].textContent.trim();
            const input = inputEls[i];
            categories.push({ label, input, filled: input.value.trim().length > 0 });
        }
        
        return categories;
    }

    function fillCategory(input, letter, category) {
        const answer = getAnswer(letter.toLowerCase(), category);
        input.value = answer;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
        log(`Filled: ${answer} (${category})`);
    }

    function clickJogarButton() {
        const btn = getElementByXPath(JOGAR_BUTTON_XPATH);
        if (btn && !btn.disabled) {
            btn.click();
            log('Clicked JOGAR');
            return true;
        }
        return false;
    }

    function clickAvaliarButton() {
        const btn = getElementByXPath(AVALIAR_BUTTON_XPATH);
        if (btn && !btn.disabled) {
            btn.click();
            log('Clicked AVALIAR');
            return true;
        }
        return false;
    }

    function processRound() {
        if (!isEnabled) return;

        const currentLetter = getCurrentLetter();
        if (!currentLetter) return;

        if (currentLetter === lastLetter) return;

        log(`New round: ${currentLetter}`);
        lastLetter = currentLetter;

        const categories = getCategories();
        let filledCount = 0;

        categories.forEach(({ label, input, filled }) => {
            if (!filled) {
                fillCategory(input, currentLetter, label);
                filledCount++;
            }
        });

        log(`Filled ${filledCount} categories for letter ${currentLetter}`);
    }

    function gameLoop() {
        if (!isEnabled) return;

        clickJogarButton();
        
        processRound();
        
        clickAvaliarButton();
    }

    function startGameLoop() {
        if (gameLoopInterval) return;
        log('Starting game loop');
        gameLoopInterval = setInterval(gameLoop, 500);
    }

    function stopGameLoop() {
        if (gameLoopInterval) {
            clearInterval(gameLoopInterval);
            gameLoopInterval = null;
            log('Stopped game loop');
        }
    }

    function setEnabled(enabled) {
        isEnabled = enabled;
        if (isEnabled) {
            startGameLoop();
        } else {
            stopGameLoop();
        }
        chrome.storage.local.set({ enabled });
    }

    function init() {
        log('Initializing...');
        
        chrome.storage.local.get('enabled', (result) => {
            setEnabled(result.enabled === true);
        });

        chrome.storage.onChanged.addListener((changes, area) => {
            if (changes.enabled) {
                setEnabled(changes.enabled.newValue);
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
