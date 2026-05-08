import pygame
import json
import os
import sys
import random
import time

# Initialize Pygame
pygame.init()

# Load configuration
with open('assets/config.json', 'r') as f:
    CONFIG = json.load(f)

# Colors
COLORS = {
    'BLACK': (0, 0, 0),
    'WHITE': (255, 255, 255),
    'RED': (255, 0, 0),
    'GREEN': (0, 255, 0),
    'BLUE': (0, 0, 255),
    'CYAN': (0, 255, 255),
    'MAGENTA': (255, 0, 255),
    'YELLOW': (255, 255, 0),
    'ORANGE': (255, 165, 0)
}

# Tetromino shapes
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[1, 1, 1], [0, 1, 0]],  # T
    [[1, 1, 1], [1, 0, 0]],  # L
    [[1, 1, 1], [0, 0, 1]],  # J
    [[1, 1, 0], [0, 1, 1]],  # S
    [[0, 1, 1], [1, 1, 0]]   # Z
]

class AudioManager:
    def __init__(self):
        pygame.mixer.init()

        # self.sounds = {
        #     'rotate': pygame.mixer.Sound('assets/rotate.wav'),
        #     'clear': pygame.mixer.Sound('assets/clear.wav'),
        #     'drop': pygame.mixer.Sound('assets/drop.wav'),
        #     'gameover': pygame.mixer.Sound('assets/gameover.wav')
        # }
        self.sounds = {}
    def play_sound(self, sound_name):
        if sound_name in self.sounds:
            self.sounds[sound_name].play()

class Leaderboard:
    def __init__(self):
        self.scores = []
        self.load_scores()
        
    def load_scores(self):
        try:
            with open('assets/leaderboard.json', 'r') as f:
                self.scores = json.load(f)
        except:
            self.scores = []
            
    def save_scores(self):
        with open('assets/leaderboard.json', 'w') as f:
            json.dump(self.scores, f)
            
    def add_score(self, name, score):
        self.scores.append({'name': name, 'score': score})
        self.scores.sort(key=lambda x: x['score'], reverse=True)
        self.scores = self.scores[:10]  # Keep only top 10
        self.save_scores()

class Menu:
    def __init__(self, screen, grid_x, grid_y, grid_width, grid_height, block_size):
        self.screen = screen
        self.font = pygame.font.Font(None, 48)
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.block_size = block_size
        
    def draw_main_menu(self):
        self.screen.fill(COLORS['BLACK'])
        title = self.font.render('TETRIS', True, COLORS['WHITE'])
        start = self.font.render('Press ENTER to Start', True, COLORS['WHITE'])
        quit_msg = self.font.render('Press Q to Quit', True, COLORS['WHITE'])
        
        self.screen.blit(title, (CONFIG['window']['width']//2 - title.get_width()//2, 100))
        self.screen.blit(start, (CONFIG['window']['width']//2 - start.get_width()//2, 300))
        self.screen.blit(quit_msg, (CONFIG['window']['width']//2 - quit_msg.get_width()//2, 400))
        
        # Draw empty grid frame on menu
        border_thickness = 2
        pygame.draw.line(self.screen, COLORS['WHITE'],
                        (self.grid_x, self.grid_y),
                        (self.grid_x, self.grid_y + self.grid_height * self.block_size),
                        border_thickness)
        pygame.draw.line(self.screen, COLORS['WHITE'],
                        (self.grid_x + self.grid_width * self.block_size, self.grid_y),
                        (self.grid_x + self.grid_width * self.block_size, self.grid_y + self.grid_height * self.block_size),
                        border_thickness)
        pygame.draw.line(self.screen, COLORS['WHITE'],
                        (self.grid_x, self.grid_y + self.grid_height * self.block_size),
                        (self.grid_x + self.grid_width * self.block_size, self.grid_y + self.grid_height * self.block_size),
                        border_thickness)
        
    def draw_game_over(self, score):
        self.screen.fill(COLORS['BLACK'])
        game_over = self.font.render('GAME OVER', True, COLORS['RED'])
        score_text = self.font.render(f'Score: {score}', True, COLORS['WHITE'])
        restart = self.font.render('Press R to Restart', True, COLORS['WHITE'])
        
        self.screen.blit(game_over, (CONFIG['window']['width']//2 - game_over.get_width()//2, 150))
        self.screen.blit(score_text, (CONFIG['window']['width']//2 - score_text.get_width()//2, 250))
        self.screen.blit(restart, (CONFIG['window']['width']//2 - restart.get_width()//2, 350))

class TetrisGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((CONFIG['window']['width'], CONFIG['window']['height']))
        pygame.display.set_caption('Tetris')
        
        self.grid_width = 10
        self.grid_height = 20
        self.block_size = 30
        self.grid = [[0] * self.grid_width for _ in range(self.grid_height)]
        
        # Calculate grid position
        self.grid_x = (CONFIG['window']['width'] - self.grid_width * self.block_size) // 2
        self.grid_y = 50
        
        self.clock = pygame.time.Clock()
        self.audio = AudioManager()
        self.leaderboard = Leaderboard()
        
        self.menu = Menu(self.screen, self.grid_x, self.grid_y, self.grid_width, self.grid_height, self.block_size)
        
        self.current_piece = None
        self.current_piece_x = 0
        self.current_piece_y = 0
        self.score = 0
        self.game_state = "MENU"  # MENU, PLAYING, GAME_OVER
        
    def new_piece(self):
        self.current_piece = random.choice(SHAPES)
        self.current_piece_x = self.grid_width // 2 - len(self.current_piece[0]) // 2
        self.current_piece_y = 0
        
        if self.check_collision():
            self.game_state = "GAME_OVER"
            self.audio.play_sound('gameover')
            
    def check_collision(self):
        for y, row in enumerate(self.current_piece):
            for x, cell in enumerate(row):
                if cell:
                    if (self.current_piece_y + y >= self.grid_height or
                        self.current_piece_x + x < 0 or
                        self.current_piece_x + x >= self.grid_width or
                        self.grid[self.current_piece_y + y][self.current_piece_x + x]):
                        return True
        return False
        
    def rotate_piece(self):
        old_piece = self.current_piece
        self.current_piece = list(zip(*self.current_piece[::-1]))
        if self.check_collision():
            self.current_piece = old_piece
        else:
            self.audio.play_sound('rotate')
            
    def clear_lines(self):
        lines_cleared = 0
        y = self.grid_height - 1
        while y >= 0:
            if all(self.grid[y]):
                self.grid.pop(y)
                self.grid.insert(0, [0] * self.grid_width)
                lines_cleared += 1
            else:
                y -= 1
        if lines_cleared:
            self.score += (lines_cleared * 100) * lines_cleared  # Bonus for multiple lines
            self.audio.play_sound('clear')
            
    def draw(self):
        self.screen.fill(COLORS['BLACK'])
        
        # Draw grid borders (left, right, bottom)
        border_color = COLORS['WHITE']
        border_thickness = 2
        
        # Left border
        pygame.draw.line(self.screen, border_color,
                        (self.grid_x, self.grid_y),
                        (self.grid_x, self.grid_y + self.grid_height * self.block_size),
                        border_thickness)
        
        # Right border
        pygame.draw.line(self.screen, border_color,
                        (self.grid_x + self.grid_width * self.block_size, self.grid_y),
                        (self.grid_x + self.grid_width * self.block_size, self.grid_y + self.grid_height * self.block_size),
                        border_thickness)
        
        # Bottom border
        pygame.draw.line(self.screen, border_color,
                        (self.grid_x, self.grid_y + self.grid_height * self.block_size),
                        (self.grid_x + self.grid_width * self.block_size, self.grid_y + self.grid_height * self.block_size),
                        border_thickness)
        
        # Draw grid
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.grid[y][x]:
                    pygame.draw.rect(self.screen, COLORS['WHITE'],
                                  (self.grid_x + x * self.block_size, self.grid_y + y * self.block_size,
                                   self.block_size - 1, self.block_size - 1))
                    
        # Draw current piece
        if self.current_piece:
            for y, row in enumerate(self.current_piece):
                for x, cell in enumerate(row):
                    if cell:
                        pygame.draw.rect(self.screen, COLORS['CYAN'],
                                      (self.grid_x + (self.current_piece_x + x) * self.block_size,
                                       self.grid_y + (self.current_piece_y + y) * self.block_size,
                                       self.block_size - 1, self.block_size - 1))
                                       
        # Draw score
        font = pygame.font.Font(None, 36)
        score_text = font.render(f'Score: {self.score}', True, COLORS['WHITE'])
        self.screen.blit(score_text, (10, 10))
        
    def run(self):
        last_drop_time = time.time()
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                    
                if event.type == pygame.KEYDOWN:
                    if self.game_state == "MENU":
                        if event.key == pygame.K_RETURN:
                            self.game_state = "PLAYING"
                            self.new_piece()
                        elif event.key == pygame.K_q:
                            pygame.quit()
                            sys.exit()
                    
                    elif self.game_state == "PLAYING":
                        if event.key == pygame.K_LEFT:
                            self.current_piece_x -= 1
                            if self.check_collision():
                                self.current_piece_x += 1
                        elif event.key == pygame.K_RIGHT:
                            self.current_piece_x += 1
                            if self.check_collision():
                                self.current_piece_x -= 1
                        elif event.key == pygame.K_UP:
                            self.rotate_piece()
                        elif event.key == pygame.K_DOWN:
                            self.current_piece_y += 1
                            if self.check_collision():
                                self.current_piece_y -= 1
                        elif event.key == pygame.K_SPACE:
                            while not self.check_collision():
                                self.current_piece_y += 1
                            self.current_piece_y -= 1
                            
                    elif self.game_state == "GAME_OVER":
                        if event.key == pygame.K_r:
                            self.grid = [[0] * self.grid_width for _ in range(self.grid_height)]
                            self.score = 0
                            self.game_state = "PLAYING"
                            self.new_piece()
            
            if self.game_state == "MENU":
                self.menu.draw_main_menu()
            
            elif self.game_state == "PLAYING":
                # Auto-drop piece
                if time.time() - last_drop_time > 0.5:
                    self.current_piece_y += 1
                    if self.check_collision():
                        self.current_piece_y -= 1
                        # Lock piece in place
                        for y, row in enumerate(self.current_piece):
                            for x, cell in enumerate(row):
                                if cell:
                                    self.grid[self.current_piece_y + y][self.current_piece_x + x] = 1
                        self.audio.play_sound('drop')
                        self.clear_lines()
                        self.new_piece()
                    last_drop_time = time.time()
                
                self.draw()
            
            elif self.game_state == "GAME_OVER":
                self.menu.draw_game_over(self.score)
                
            pygame.display.flip()
            self.clock.tick(60)

if __name__ == "__main__":
    game = TetrisGame()
    game.run()