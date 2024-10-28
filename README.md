# llm-snake-game

A Python implementation of the classic Snake game played by AI models (Claude, GPT, and DeepSeek). The AI models control the snake's movement through API calls, making decisions based on the current game state.

## Features

- **Multiple AI Players**: Supports three AI models:
  - Claude (Anthropic)
  - GPT (OpenAI)
  - DeepSeek
- **Colorful Interface**: Visual game board with colored elements for snake, food, and borders
- **Detailed Logging**: CSV logs for each game session with comprehensive move data
- **Smart Decision Making**: AI models receive detailed game state information including:
  - Current board state
  - Snake position
  - Food location
  - Dangerous positions
  - Wall locations

## Game Rules

- The snake moves in four directions: UP, DOWN, LEFT, RIGHT
- Cannot move directly opposite to the current direction
- Game ends if the snake:
  - Hits the wall
  - Collides with itself
- Score increases when the snake eats food
- Snake grows longer with each food eaten

## Requirements
```python 
pip install anthropic openai colorama
```

## Configuration

Before running the game, set up your API keys:
- Claude API key
- GPT API key
- DeepSeek API key

## Usage

Run the game:

```python
python snake_game.py
```

Select an AI model when prompted:
1. Claude
2. GPT
3. DeepSeek

## Game Display

- `O`: Snake head (Green)
- `o`: Snake body (Light Green)
- `*`: Food (Red)
- `+` and `|`: Border (Blue)
- Score display (Yellow)

## Logging

Game logs are stored in the `logs` directory with the format:
`snake_game_[model_name]_[timestamp].csv`

Log data includes:
- Timestamp
- Model name
- Step number
- Score
- Snake length
- Snake head position
- Food position
- Current direction
- Chosen move
- Board state
- Move validity
- Game over status

## AI Decision Making

The AI models receive detailed information about:
1. Game environment (boundaries, score, available space)
2. Current state (board visualization, positions)
3. Decision priorities (survival, mobility, food chase)
4. Strategy tips
5. Basic rules

## Code Structure

- `SnakeGame`: Main game logic and display
- `AIPlayer`: Abstract base class for AI players
- `ClaudePlayer`: Claude model implementation
- `GPTPlayer`: GPT model implementation
- `DeepSeekPlayer`: DeepSeek model implementation
- `GameLogger`: Logging functionality

## Contributing

Feel free to submit issues and try to play with many other models. 
