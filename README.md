# StopotsBot

## Overview
StopotsBot is an automated bot designed to play the game "Stopots" by automatically filling in the answers based on pre-defined categories and letters. This bot interacts with the Stopots website using Playwright, filling out form fields and retrieving scores from the game interface. The answers are generated based on a JSON dictionary of predefined letter-category answers.

https://github.com/user-attachments/assets/7987a2d1-1daf-4620-86d8-2fc647aead91

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
2. 
3. Run the bot:
    ```bash
    docker compose up
    ```

### Logging and Output
The bot logs its actions, such as the letter being used, the category, and the generated answers. It also logs the score updates for all players in the game.
```bash
server-1  | 2024-09-17 23:52:47,700 - INFO - Current letter: ?
server-1  | 2024-09-17 23:52:53,222 - INFO - 
server-1  | +---------------+----------+
server-1  | | user          |   points |
server-1  | +===============+==========+
server-1  | | xxxxxxx       |        0 |
server-1  | | xxxxxxx       |        0 |
server-1  | | xxxxxxx       |        0 |
server-1  | | xxxxxxx       |        0 |
server-1  | | xxxxxxx       |        0 |
server-1  | | xxxxxxx       |        0 |
server-1  | | xxxxxxx       |        0 |
server-1  | | xxxxxxx       |        0 |
server-1  | | xxxxxxx       |        0 |
server-1  | | > you         |        0 |
server-1  | +---------------+----------+
server-1  | 2024-09-17 23:52:53,223 - INFO - Current letter: R
server-1  | 2024-09-17 23:52:53,243 - INFO - [R 1] Esporte: Rugbi
server-1  | 2024-09-17 23:52:53,662 - INFO - [R 2] Animal: Rinoceronte
server-1  | 2024-09-17 23:52:54,458 - INFO - [R 3] Musica: Rosanna
server-1  | 2024-09-17 23:52:54,961 - INFO - [R 4] Meio De Transporte: Rolima
server-1  | 2024-09-17 23:52:55,396 - INFO - [R 5] Fantasia: Robin
server-1  | 2024-09-17 23:52:55,779 - INFO - [R 6] Desenho Animado: Riquinho
server-1  | 2024-09-17 23:52:56,447 - INFO - [R 7] Filme: Robin Hood
server-1  | 2024-09-17 23:52:57,225 - INFO - [R 8] Brinquedo: Robo
server-1  | 2024-09-17 23:52:57,528 - INFO - [R 9] Palavra Em Espanhol: Roja
server-1  | 2024-09-17 23:52:57,842 - INFO - [R 10] Profissao: Radialista
server-1  | 2024-09-17 23:52:58,544 - INFO - [R 11] Sobremesa: Rabanada
server-1  | 2024-09-17 23:52:59,162 - INFO - [R 12] Idioma: Romeno
```
As the username is randomly generated, it will be marked with a `>` symbol in the score table.

### Dictionary File Structure
The bot uses a JSON file (dictionary.json) to generate the answers. The file structure looks like this:
```json
{
    "A": {
        "Animais": ["Anta", "Antílope", "Avestruz"],
        "Cidades": ["Aracaju", "Aparecida", "Araguaína"],
        ...
    },
    "B": {
        "Animais": ["Baleia", "Borboleta", "Búfalo"],
        "Cidades": ["Barueri", "Belo Horizonte", "Blumenau"],
        ...
    }
}
```
