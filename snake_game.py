import random
import time
import os
from anthropic import Anthropic
from openai import OpenAI
from abc import ABC, abstractmethod
from colorama import init, Fore, Back, Style
import csv
from datetime import datetime

# initialize colorama
init()

class SnakeGame:
    def __init__(self, width=20, height=20, model_name=None):
        self.width = width
        self.height = height
        self.snake = [(width//2, height//2)]
        self.food = self._place_food()
        self.direction = 'RIGHT'
        self.score = 0
        self.game_over = False
        self.model_name = model_name
        # 定义颜色方案
        self.colors = {
            'border': Fore.BLUE,
            'snake_head': Fore.GREEN,
            'snake_body': Fore.LIGHTGREEN_EX,
            'food': Fore.RED,
            'score': Fore.YELLOW
        }
    
    def _place_food(self):
        while True:
            food = (random.randint(0, self.width-1), random.randint(0, self.height-1))
            if food not in self.snake:
                return food
    
    def _clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def _draw(self):
        """draw game interface with color"""
        self._clear_screen()
        print(f"{self.colors['score']}Score: {self.score}{Style.RESET_ALL}")
        if self.model_name:
            print(f"Model: {self.model_name}")
        
        border = self.colors['border']
        print(f"{border}+" + "-" * self.width + "+{Style.RESET_ALL}")
        
        for y in range(self.height):
            print(f"{border}|{Style.RESET_ALL}", end="")
            for x in range(self.width):
                if (x, y) == self.snake[0]:
                    print(f"{self.colors['snake_head']}O{Style.RESET_ALL}", end="")
                elif (x, y) in self.snake[1:]:
                    print(f"{self.colors['snake_body']}o{Style.RESET_ALL}", end="")
                elif (x, y) == self.food:
                    print(f"{self.colors['food']}*{Style.RESET_ALL}", end="")
                else:
                    print(" ", end="")
            print(f"{border}|{Style.RESET_ALL}")
            
        print(f"{border}+" + "-" * self.width + f"+{Style.RESET_ALL}")
        if self.game_over:
            print(f"{Fore.RED}Game Over! Final Score: {self.score}{Style.RESET_ALL}")
    
    def step(self, direction):
        """执行一步移动"""
        if self.game_over:
            return
            
        # check if the move direction is valid (cannot move directly opposite to current direction)
        if (direction == 'UP' and self.direction == 'DOWN' or
            direction == 'DOWN' and self.direction == 'UP' or
            direction == 'LEFT' and self.direction == 'RIGHT' or
            direction == 'RIGHT' and self.direction == 'LEFT'):
            # 如果是无效的反向移动，保持原方向
            direction = self.direction
            
        self.direction = direction
        head = self.snake[0]
        
        # 根据方向移动蛇头
        if direction == 'UP':
            new_head = (head[0], head[1]-1)
        elif direction == 'DOWN':
            new_head = (head[0], head[1]+1)
        elif direction == 'LEFT':
            new_head = (head[0]-1, head[1])
        elif direction == 'RIGHT':
            new_head = (head[0]+1, head[1])
        
        # check if hit wall
        if (new_head[0] < 0 or new_head[0] >= self.width or
            new_head[1] < 0 or new_head[1] >= self.height):
            self.game_over = True
            return
        
        # check if hit self (not including tail, because tail will move)
        if new_head in self.snake[:-1]:
            self.game_over = True
            return
        
        # move snake
        self.snake.insert(0, new_head)
        
        # check if eat food
        if new_head == self.food:
            self.score += 1
            self.food = self._place_food()
        else:
            self.snake.pop()

class AIPlayer(ABC):
    """AI玩家基类"""
    @abstractmethod
    def get_move(self, game):
        pass
    
    def _format_board(self, game):
        """格式化游戏板状态"""
        board = [["" for _ in range(game.width)] for _ in range(game.height)]
        
        # 标记蛇的位置
        for i, (x, y) in enumerate(game.snake):
            board[y][x] = "H" if i == 0 else "B"  # H for head, B for body
        
        # 标记食物位置
        x, y = game.food
        board[y][x] = "F"
        
        return "\n".join(" ".join(cell if cell else "." for cell in row) for row in board)
    
    def _get_prompt(self, game):
        """Generate prompt for AI model"""
        # Calculate dangerous positions (near walls and snake body)
        danger_positions = set()
        # Wall positions
        wall_positions = set()
        
        # Top and bottom walls
        for x in range(game.width):
            wall_positions.add((x, -1))  # Top boundary wall
            wall_positions.add((x, game.height))  # Bottom boundary wall
            danger_positions.add((x, 0))  # Top wall danger zone
            danger_positions.add((x, game.height-1))  # Bottom wall danger zone
        
        # Left and right walls
        for y in range(game.height):
            wall_positions.add((-1, y))  # Left boundary wall
            wall_positions.add((game.width, y))  # Right boundary wall
            danger_positions.add((0, y))  # Left wall danger zone
            danger_positions.add((game.width-1, y))  # Right wall danger zone
        
        # Dangerous positions near snake body
        for segment in game.snake[1:]:
            x, y = segment
            for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                danger_pos = (x+dx, y+dy)
                if (0 <= danger_pos[0] < game.width and 
                    0 <= danger_pos[1] < game.height):
                    danger_positions.add(danger_pos)

        return f"""You are playing a snake game. Please choose the optimal move direction based on the current state.

Game Environment:
- Game Boundary: {game.width}x{game.height}
- Wall Positions: 
  * Top Wall: y = -1 (x: 0 to {game.width-1})
  * Bottom Wall: y = {game.height} (x: 0 to {game.width-1})
  * Left Wall: x = -1 (y: 0 to {game.height-1})
  * Right Wall: x = {game.width} (y: 0 to {game.height-1})
- Current Score: {game.score}
- Snake Length: {len(game.snake)}
- Available Space: {game.width * game.height - len(game.snake)} cells

Current State:
Game Board (H=snake head, B=snake body, F=food, .=empty):
{self._format_board(game)}

Key Position Information:
- Snake Head: {game.snake[0]}
- Snake Body: {game.snake[1:]}
- Food Position: {game.food}
- Current Direction: {game.direction}
- Wall Positions: {list(wall_positions)}
- Dangerous Positions: {list(danger_positions)}

Decision Priority (High to Low):
1. [Highest] Survival: Absolutely avoid walls and self-collision
2. [High] Mobility: Avoid dead ends and confined spaces
3. [Medium] Food Chase: Approach food when safe
4. [Low] Space Utilization: Maintain accessibility to game area

Advanced Strategy Tips:
1. When snake is long, prioritize keeping open space over direct food pursuit
2. Plan turning paths in advance when approaching walls
3. Avoid forming enclosed loops with snake body to prevent cutting off movement paths
4. When in dangerous areas, prioritize directions with more escape options

Basic Rules:
- Cannot move directly opposite to current direction {game.direction}
- Cannot hit walls (coordinates must be within 0 to {game.width-1} for x and 0 to {game.height-1} for y)
- Cannot collide with snake body
- Valid moves are: UP, DOWN, LEFT, RIGHT only

Strict Requirement: Respond with only one direction word (UP/DOWN/LEFT/RIGHT), no additional text or explanation."""

    def _is_valid_move(self, game, move):
        """check if the move is valid"""
        if move not in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
            return False
            
        head_x, head_y = game.snake[0]
        
        # 计算新的头部位置
        if move == 'UP':
            new_head = (head_x, head_y - 1)
        elif move == 'DOWN':
            new_head = (head_x, head_y + 1)
        elif move == 'LEFT':
            new_head = (head_x - 1, head_y)
        else:  # RIGHT
            new_head = (head_x + 1, head_y)
            
        # 检查是否撞墙
        if (new_head[0] < 0 or new_head[0] >= game.width or
            new_head[1] < 0 or new_head[1] >= game.height):
            return False
            
        # 检查是否撞到自己
        if new_head in game.snake[:-1]:
            return False
            
        return True
    
    def _get_backup_move(self, game):
        """get backup move"""
        for direction in ['UP', 'RIGHT', 'DOWN', 'LEFT']:
            if self._is_valid_move(game, direction):
                return direction
        return game.direction  # 如果没有有移动，保持当前方向
    
    def initialize_logger(self, model_name):
        """initialize logger"""
        self.logger = GameLogger(model_name)

class ClaudePlayer(AIPlayer):
    def __init__(self, api_key, model_name="claude-3-5-sonnet-20241022"):
        super().__init__()  # 调用父类的初始化方法
        self.client = Anthropic(api_key=api_key)
        self.model_name = model_name
        self.move_history = []
        self.initialize_logger(model_name)  
        
    def get_move(self, game):
        """get Claude's next move"""
        prompt = self._get_prompt(game)
        board_state = self._format_board(game)  
        
        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=4096,
                temperature=1.0,
                messages=[{"role": "user", "content": prompt}]
            )
            
            move = response.content[0].text.strip().upper()
            is_valid = self._is_valid_move(game, move)
            
            # 记录日志
            self.logger.log_move(game, move, board_state, is_valid)
            
            if not is_valid:
                raise ValueError(f"Invalid move: {move}")
                
            return move
            
        except Exception as e:
            # 记录错误日志
            self.logger.log_move(game, str(e), board_state, False)
            raise e
    
    def _format_move_history(self):
        """format move history"""
        return "\n".join([
            f"Step {h['step']}: {h['move']} "
            f"(Score: {h['score']}, "
            f"Length: {h['snake_length']}, "
            f"Head: {h['head_pos']}, "
            f"Food: {h['food_pos']})"
            for h in self.move_history[-5:]  # 只显示最近5步
        ])

class GPTPlayer(AIPlayer):
    def __init__(self, api_key, model_name="gpt-4"):
        super().__init__()  # 调用父类的初始化方法
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name
        self.move_history = []
        self.initialize_logger(model_name)  # 初始化日志记录器
    
    def get_move(self, game):
        """get GPT's next move"""
        prompt = self._get_prompt(game)
        board_state = self._format_board(game)  # 获取当前游戏板状态
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                temperature=1.0,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )
            
            move = response.choices[0].message.content.strip().upper()
            is_valid = self._is_valid_move(game, move)
            
            # record log
            self.logger.log_move(game, move, board_state, is_valid)
            
            if not is_valid:
                raise ValueError(f"Invalid move: {move}")
                
            return move
            
        except Exception as e:
            # record error log
            self.logger.log_move(game, str(e), board_state, False)
            raise e
    
    def _format_move_history(self):
        """格式化移动历史"""
        return "\n".join([
            f"Step {h['step']}: {h['move']} "
            f"(Score: {h['score']}, "
            f"Length: {h['snake_length']}, "
            f"Head: {h['head_pos']}, "
            f"Food: {h['food_pos']})"
            for h in self.move_history[-5:]  # 只显示最近5步
        ])

class DeepSeekPlayer(AIPlayer):
    def __init__(self, api_key, model_name="deepseek-chat"):
        super().__init__()  # 调用父类的初始化方法
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        self.model_name = model_name
        self.move_history = []
        self.initialize_logger(model_name)  # 初始化日志记录器
    
    def get_move(self, game):
        """get DeepSeek's next move"""
        prompt = self._get_prompt(game)
        board_state = self._format_board(game)  # 获取当前游戏板状态
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                temperature=1.0,
                max_tokens=4096,
                messages=[
                    # {"role": "system", "content": "You are playing a snake game. Respond only with UP, DOWN, LEFT, or RIGHT."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            move = response.choices[0].message.content.strip().upper()
            is_valid = self._is_valid_move(game, move)
            
            # record log
            self.logger.log_move(game, move, board_state, is_valid)
            
            if not is_valid:
                raise ValueError(f"Invalid move: {move}")
                
            return move
            
        except Exception as e:
            # record error log
            self.logger.log_move(game, str(e), board_state, False)
            raise e
    
    def _format_move_history(self):
        """格化移动历史"""
        return "\n".join([
            f"步骤 {h['step']}: {h['move']} "
            f"(分数: {h['score']}, "
            f"长度: {h['snake_length']}, "
            f"蛇头: {h['head_pos']}, "
            f"食物: {h['food_pos']})"
            for h in self.move_history[-5:]  
        ])

class GameLogger:
    def __init__(self, model_name):
        self.model_name = model_name
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = f"logs/snake_game_{model_name}_{self.timestamp}.csv"
        self.ensure_log_directory()
        self.initialize_csv()
        
    def ensure_log_directory(self):
        """Ensure log directory exists"""
        os.makedirs("logs", exist_ok=True)
        
    def initialize_csv(self):
        """Initialize CSV file with headers"""
        headers = [
            'timestamp',
            'model_name',
            'step',
            'score',
            'snake_length',
            'snake_head_pos',
            'food_pos',
            'current_direction',
            'chosen_move',
            'board_state',
            'is_valid_move',
            'game_over'
        ]
        with open(self.log_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
    def log_move(self, game, move, board_state, is_valid_move=True):
        """Record information for each move"""
        log_data = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            self.model_name,
            len(game.snake) - 1,  # step (score)
            game.score,
            len(game.snake),
            str(game.snake[0]),
            str(game.food),
            game.direction,
            move,
            board_state,
            is_valid_move,
            game.game_over
        ]
        with open(self.log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(log_data)

def main():
    claude_api_key = "<Your_ANTHROPIC_API_KEY>"
    gpt_api_key = "<Your_OPENAI_API_KEY>"
    deepseek_api_key = "<Your_DeepSeek_API_KEY>"  # 
    
    # 选择使用哪个模型
    print(f"{Fore.YELLOW}Select AI Model:{Style.RESET_ALL}")
    print("1: Claude")
    print("2: GPT")
    print("3: DeepSeek")
    model_type = input("Enter your choice (1, 2 or 3): ")
    
    if model_type == "1":
        model_name = "claude-3-5-sonnet-20241022"
        player = ClaudePlayer(claude_api_key, model_name)
    elif model_type == "2":
        model_name = "gpt-4o"
        player = GPTPlayer(gpt_api_key, model_name)
    else:
        model_name = "deepseek-chat"
        player = DeepSeekPlayer(deepseek_api_key, model_name)
    
    game = SnakeGame(model_name=model_name)
    
    try:
        while not game.game_over:
            game._draw()
            move = player.get_move(game)
            game.step(move)
            
            print(f"\n{Fore.CYAN}Game Status:{Style.RESET_ALL}")
            print(f"Snake Head: {game.snake[0]}")
            print(f"Food Position: {game.food}")
            print(f"Current Direction: {game.direction}")
            print(f"Chosen Move: {move}")
            
            time.sleep(0.5)
            
    except Exception as e:
        print(f"\n{Fore.RED}Game Terminated Abnormally:{Style.RESET_ALL}")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print(f"Final Score: {game.score}")

if __name__ == "__main__":
    main()
