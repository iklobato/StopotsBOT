# StopotsBot

## Overview
StopotsBot is an automated bot designed to play the game "Stopots" by automatically filling in the answers based on pre-defined categories and letters. This bot interacts with the Stopots website using Playwright, filling out form fields and retrieving scores from the game interface. The answers are generated based on a JSON dictionary of predefined letter-category answers.

## How It Works
The bot operates through the following steps:
1. **Launching a Browser:** Uses Playwright to control a Chromium-based browser and navigate to the Stopots game page.
2. **Automated Interaction:**
   - Fills in the username and joins the game.
   - Listens for the game's current letter and category, then fills in the answers based on predefined mappings in `dictionary.json`.
   - Automatically clicks necessary buttons to interact with the game (e.g., "OK", "Estou Pronto").
3. **Scoring and Updates:**
   - Periodically retrieves and logs the user scores by parsing the game interface.
4. **Dynamic Answer Generation:** For each letter and category, it retrieves the appropriate answer from the dictionary file and fills it in the game form fields.

## Usage
To run the bot, ensure you have Python installed, along with the required dependencies.

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/iklobato/StopotsBOT.git
   cd stopotsbot
    ```
2. Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3. Run the bot:
    ```bash
    python stopotsbot.py --headless --username <username>
    ```
    - `--headless`: Run the browser in headless mode (without a GUI).
    - `--username`: Your username to use in the game.

### Dictionary File Structure
The bot uses a JSON file (dictionary.json) to generate the answers. The file structure looks like this:
```json
{
    "A": {
        "Animais": ["Anta", "Antílope", "Avestruz"],
        "Cidades": ["Aracaju", "Aparecida", "Araguaína"]
    },
    "B": {
        "Animais": ["Baleia", "Borboleta", "Búfalo"],
        "Cidades": ["Barueri", "Belo Horizonte", "Blumenau"]
    }
}
```

### Logging and Output
The bot logs its actions, such as the letter being used, the category, and the generated answers. It also logs the score updates for all players in the game.
```bash
2024-09-04 23:11:46,630 - INFO - Current letter: I
2024-09-04 23:11:46,656 - INFO - [I 1] Nome Masculino: Ivo
2024-09-04 23:11:46,767 - INFO - +---------------+----------+
| user          |   points |
+===============+==========+
| ik/3          |      110 |
| xxxxxxx       |       50 |
| xxxxxxxxxxxxx |       40 |
| xxxxxx        |       20 |
| xxxx          |        0 |
| xxxxxxxxxx    |        0 |
| xxxxx         |        0 |
| xxxxxxxxxx    |        0 |
| xxxxxxxxx     |        0 |
| xxxx          |        0 |
+---------------+----------+
2024-09-04 23:11:46,800 - INFO - [I 2] Sabor De Pizza: Italiana
2024-09-04 23:11:46,917 - INFO - [I 3] Desenho Animado: Invasor Zim
2024-09-04 23:11:47,073 - INFO - [I 4] Verbo: Imitar
2024-09-04 23:11:47,192 - INFO - [I 5] Pais: Italia
2024-09-04 23:11:47,348 - INFO - [I 6] Time Esportivo: Irlanda
2024-09-04 23:11:47,468 - INFO - [I 7] Doce: I-Naosei
2024-09-04 23:11:47,586 - INFO - [I 8] Profissao: Instrumentista
2024-09-04 23:11:47,705 - INFO - [I 9] Remedio: Ibuprofeno
2024-09-04 23:11:47,825 - INFO - [I 10] Palavra Em Ingles: Investigation
2024-09-04 23:11:47,974 - INFO - [I 11] Pch: Intestino Grosso
2024-09-04 23:11:48,085 - INFO - [I 12] Meio De Transporte: Iate
```