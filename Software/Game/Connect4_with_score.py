import pygame
import sys
import math
import time
import random
import threading
import json
import os
from typing import List, Optional, Tuple

# ==========================================
# 1. CONFIGURATIE & CONSTANTEN
# ==========================================

# Kleuren & Styling
BG_COLOR = (30, 30, 30)
BOARD_COLOR = (40, 60, 150)
HOLE_COLOR = (20, 20, 20)
PLAYER1_COLOR = (230, 50, 50)  # Rood
PLAYER2_COLOR = (240, 220, 0)  # Geel
TEXT_COLOR = (255, 255, 255)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER = (100, 160, 210)
ICON_LINE_COLOR = (0, 0, 0)
SLIDER_BG_COLOR = (80, 80, 80)
SLIDER_FILL_COLOR = (100, 160, 210)
SLIDER_KNOB_COLOR = (220, 220, 220)
LEADERBOARD_BG = (45, 45, 55)

# Bord info
ROWS = 6
COLUMNS = 7

# Spelers ID
EMPTY = 0
P1 = 1
P2 = 2

# Game States
STATE_MENU = 0
STATE_PLAYING = 1
STATE_GAMEOVER = 2
STATE_INPUT = 3

# Game Modes
MODE_PvAI = 1
MODE_PvP = 2
MODE_AIvAI = 3

# AI Config
AI_MAX_DEPTH = 20     
INF = 100000000000000
LEADERBOARD_FILE = "leaderboard_full.json"

# ==========================================
# 2. SPEL LOGICA (BACKEND)
# ==========================================

def create_board():
    return [[EMPTY] * COLUMNS for _ in range(ROWS)]

def is_valid_location(board, col):
    return board[0][col] == EMPTY

def get_next_open_row(board, col):
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == EMPTY:
            return r
    return None

def drop_piece(board, row, col, piece):
    board[row][col] = piece

def get_valid_locations(board):
    return [c for c in range(COLUMNS) if is_valid_location(board, c)]

def winning_move(board, piece):
    for c in range(COLUMNS - 3):
        for r in range(ROWS):
            if board[r][c] == piece and board[r][c+1] == piece and board[r][c+2] == piece and board[r][c+3] == piece: return True
    for c in range(COLUMNS):
        for r in range(ROWS - 3):
            if board[r][c] == piece and board[r+1][c] == piece and board[r+2][c] == piece and board[r+3][c] == piece: return True
    for c in range(COLUMNS - 3):
        for r in range(ROWS - 3):
            if board[r][c] == piece and board[r+1][c+1] == piece and board[r+2][c+2] == piece and board[r+3][c+3] == piece: return True
    for c in range(COLUMNS - 3):
        for r in range(3, ROWS):
            if board[r][c] == piece and board[r-1][c+1] == piece and board[r-2][c+2] == piece and board[r-3][c+3] == piece: return True
    return False

def get_winning_coords(board, piece):
    coords = []
    for c in range(COLUMNS - 3):
        for r in range(ROWS):
            if board[r][c] == piece and board[r][c+1] == piece and board[r][c+2] == piece and board[r][c+3] == piece:
                coords.extend([(r, c), (r, c+1), (r, c+2), (r, c+3)])
    for c in range(COLUMNS):
        for r in range(ROWS - 3):
            if board[r][c] == piece and board[r+1][c] == piece and board[r+2][c] == piece and board[r+3][c] == piece:
                coords.extend([(r, c), (r+1, c), (r+2, c), (r+3, c)])
    for c in range(COLUMNS - 3):
        for r in range(ROWS - 3):
            if board[r][c] == piece and board[r+1][c+1] == piece and board[r+2][c+2] == piece and board[r+3][c+3] == piece:
                coords.extend([(r, c), (r+1, c+1), (r+2, c+2), (r+3, c+3)])
    for c in range(COLUMNS - 3):
        for r in range(3, ROWS):
            if board[r][c] == piece and board[r-1][c+1] == piece and board[r-2][c+2] == piece and board[r-3][c+3] == piece:
                coords.extend([(r, c), (r-1, c+1), (r-2, c+2), (r-3, c+3)])
    return list(set(coords))

# --- AI PUNTENTELLING ---
def evaluate_window(window, piece, opp_piece):
    score = 0
    my_count = window.count(piece)
    empty_count = window.count(EMPTY)
    opp_count = window.count(opp_piece)

    if my_count == 4: score += 100000000
    elif my_count == 3 and empty_count == 1: score += 10000
    elif my_count == 2 and empty_count == 2: score += 500
    
    if opp_count == 3 and empty_count == 1: score -= 800000 
    elif opp_count == 2 and empty_count == 2: score -= 10000

    return score

def score_position(board, piece):
    opp_piece = P1 if piece == P2 else P2
    score = 0
    center_array = [board[r][COLUMNS//2] for r in range(ROWS)]
    score += center_array.count(piece) * 200

    for r in range(ROWS):
        for c in range(COLUMNS - 3):
            score += evaluate_window(board[r][c:c+4], piece, opp_piece)
    for c in range(COLUMNS):
        for r in range(ROWS - 3):
            score += evaluate_window([board[r+i][c] for i in range(4)], piece, opp_piece)
    for r in range(ROWS - 3):
        for c in range(COLUMNS - 3):
            score += evaluate_window([board[r+i][c+i] for i in range(4)], piece, opp_piece)
    for r in range(3, ROWS):
        for c in range(COLUMNS - 3):
            score += evaluate_window([board[r-i][c+i] for i in range(4)], piece, opp_piece)
    return score

# Transposition Table
memo = {}
TT_EXACT = 0; TT_LOWER = 1; TT_UPPER = 2

def minimax(board, depth, alpha, beta, maximizingPlayer, piece, opp_piece, start_time, time_limit):
    if time.time() - start_time > time_limit: return None, 0
    
    board_tuple = tuple(tuple(row) for row in board)
    if board_tuple in memo:
        entry_depth, entry_score, entry_flag = memo[board_tuple]
        if entry_depth >= depth:
            if entry_flag == TT_EXACT: return None, entry_score
            elif entry_flag == TT_LOWER: alpha = max(alpha, entry_score)
            elif entry_flag == TT_UPPER: beta = min(beta, entry_score)
            if alpha >= beta: return None, entry_score

    valid_locations = get_valid_locations(board)
    is_terminal = winning_move(board, piece) or winning_move(board, opp_piece) or len(valid_locations) == 0
    
    if depth == 0 or is_terminal:
        if is_terminal:
            if winning_move(board, piece): return None, INF + depth 
            elif winning_move(board, opp_piece): return None, -INF - depth
            else: return None, 0
        else: return None, score_position(board, piece)

    valid_locations.sort(key=lambda x: abs(x - COLUMNS//2))
    if not valid_locations: return None, 0

    best_col = random.choice(valid_locations)

    if maximizingPlayer:
        value = -math.inf
        for col in valid_locations:
            row = get_next_open_row(board, col)
            b_copy = [r[:] for r in board]
            drop_piece(b_copy, row, col, piece)
            new_score = minimax(b_copy, depth-1, alpha, beta, False, piece, opp_piece, start_time, time_limit)[1]
            
            if new_score == 0 and time.time() - start_time > time_limit and depth > 1:
                 return None, 0

            if new_score > value:
                value = new_score
                best_col = col
            alpha = max(alpha, value)
            if alpha >= beta: break
    else:
        value = math.inf
        for col in valid_locations:
            row = get_next_open_row(board, col)
            b_copy = [r[:] for r in board]
            drop_piece(b_copy, row, col, opp_piece)
            new_score = minimax(b_copy, depth-1, alpha, beta, True, piece, opp_piece, start_time, time_limit)[1]
            
            if new_score == 0 and time.time() - start_time > time_limit and depth > 1:
                 return None, 0

            if new_score < value:
                value = new_score
                best_col = col
            beta = min(beta, value)
            if alpha >= beta: break
    
    flag = TT_EXACT
    if value <= alpha: flag = TT_UPPER
    elif value >= beta: flag = TT_LOWER
    memo[board_tuple] = (depth, value, flag)

    return best_col, value

def ai_thread_func(board_copy, result_container, my_piece, opp_piece, time_limit):
    try:
        start_time = time.time()
        memo.clear()
        valid_moves = get_valid_locations(board_copy)
        
        if not valid_moves:
            result_container['col'] = None
            result_container['done'] = True
            return

        # 1. KILLER
        for col in valid_moves:
            row = get_next_open_row(board_copy, col)
            board_copy[row][col] = my_piece
            if winning_move(board_copy, my_piece):
                result_container['col'] = col; result_container['done'] = True; return
            board_copy[row][col] = EMPTY
            
        # 2. BLOCK
        for col in valid_moves:
            row = get_next_open_row(board_copy, col)
            board_copy[row][col] = opp_piece
            if winning_move(board_copy, opp_piece):
                result_container['col'] = col; result_container['done'] = True; return
            board_copy[row][col] = EMPTY

        # 3. THINK
        best_col = random.choice(valid_moves)
        limit = AI_MAX_DEPTH
        if time_limit < 0.2:
            limit = 2

        for depth in range(1, limit + 1):
            col, score = minimax(board_copy, depth, -math.inf, math.inf, True, my_piece, opp_piece, start_time, time_limit)
            
            if time.time() - start_time > time_limit: break
            if col is not None: best_col = col
            if score > INF // 2: break

        result_container['col'] = best_col
        result_container['done'] = True
    except Exception as e:
        print(f"AI Error: {e}")
        result_container['col'] = None
        result_container['done'] = True

# ==========================================
# 3. LEADERBOARD MANAGER
# ==========================================
class LeaderboardManager:
    def __init__(self):
        self.data = {"fame": [], "shame": []}
        self.load_scores()

    def load_scores(self):
        if os.path.exists(LEADERBOARD_FILE):
            try:
                with open(LEADERBOARD_FILE, 'r') as f:
                    content = json.load(f)
                    if isinstance(content, list):
                        self.data = {"fame": content, "shame": []}
                    else:
                        self.data = content
            except:
                self.data = {"fame": [], "shame": []}
        else:
            self.data = {"fame": [], "shame": []}

    def save_scores(self):
        with open(LEADERBOARD_FILE, 'w') as f:
            json.dump(self.data, f)

    def add_fame(self, name, moves):
        found = False
        for entry in self.data['fame']:
            if entry['name'] == name:
                found = True
                if moves < entry['moves']:
                    entry['moves'] = moves
                break 
        
        if not found:
            self.data['fame'].append({'name': name, 'moves': moves})
        
        self.data['fame'].sort(key=lambda x: x['moves'])
        self.data['fame'] = self.data['fame'][:5]
        self.save_scores()

    def add_shame(self, name, moves):
        found = False
        for entry in self.data['shame']:
            if entry['name'] == name:
                found = True
                if moves < entry['moves']:
                    entry['moves'] = moves
                break
        
        if not found:
            self.data['shame'].append({'name': name, 'moves': moves})
            
        self.data['shame'].sort(key=lambda x: x['moves'])
        self.data['shame'] = self.data['shame'][:5]
        self.save_scores()

    def get_fame(self):
        return self.data.get('fame', [])
    
    def get_shame(self):
        return self.data.get('shame', [])

# ==========================================
# 4. DE UI & GAME ENGINE
# ==========================================

class GameApp:
    def __init__(self):
        pygame.init()
        
        # --- AUDIO SETUP ---
        pygame.mixer.init()
        self.sounds = {}
        sound_files = {
            "drop":   ("drop_coin_fx.wav", 0.6),
            "win":    ("win.mp3", 0.6),
            "lose":   ("lose.mp3", 0.7),
            "draw":   ("draw.wav", 0.7),
            "select": ("select.mp3", 0.5)
        }

        print("--- Geluiden laden ---")
        for key, (filename, volume) in sound_files.items():
            try:
                # Pad: sounds/bestandsnaam
                path = os.path.join("sounds", filename)
                self.sounds[key] = pygame.mixer.Sound(path)
                self.sounds[key].set_volume(volume)
                print(f"[OK] {filename}")
            except Exception as e:
                print(f"[FOUT] Kon {filename} niet laden: {e}")
        print("----------------------")
        
        info = pygame.display.Info()
        self.SCREEN_W = info.current_w
        self.SCREEN_H = info.current_h
        self.screen = pygame.display.set_mode((self.SCREEN_W, self.SCREEN_H), pygame.NOFRAME)
        pygame.display.set_caption("Connect 4 Ultimate")
        
        self.SQUARESIZE = int(self.SCREEN_H * 0.65 / (ROWS + 1))
        self.RADIUS = int(self.SQUARESIZE / 2 - 5)
        self.BOARD_W = COLUMNS * self.SQUARESIZE
        self.BOARD_H = (ROWS + 1) * self.SQUARESIZE
        self.OFFSET_X = (self.SCREEN_W - self.BOARD_W) // 2
        self.OFFSET_Y = (self.SCREEN_H - self.BOARD_H) // 2 + self.SQUARESIZE//2
        
        self.font_L = pygame.font.SysFont("Arial", int(self.SCREEN_H * 0.08), bold=True)
        self.font_M = pygame.font.SysFont("Arial", int(self.SCREEN_H * 0.04), bold=True)
        self.font_S = pygame.font.SysFont("Arial", int(self.SCREEN_H * 0.03))
        self.font_Mono = pygame.font.SysFont("Consolas", int(self.SCREEN_H * 0.03), bold=True)

        btn_w, btn_h = 350, 80
        cx, cy = self.SCREEN_W // 2, self.SCREEN_H // 2
        self.menu_rects = {
            MODE_PvAI: pygame.Rect(cx - btn_w//2, cy - 120, btn_w, btn_h),
            MODE_PvP:  pygame.Rect(cx - btn_w//2, cy, btn_w, btn_h),
            MODE_AIvAI:pygame.Rect(cx - btn_w//2, cy + 120, btn_w, btn_h)
        }
        
        sb_size = 60
        self.btn_home = pygame.Rect(self.SCREEN_W - 150, 40, sb_size, sb_size)
        self.btn_restart = pygame.Rect(self.SCREEN_W - 70, 40, sb_size, sb_size)

        self.slider_width = self.BOARD_W
        self.slider_height = 20
        self.slider_rect = pygame.Rect(self.OFFSET_X, self.SCREEN_H - 80, self.slider_width, self.slider_height)
        
        knob_w = 20
        knob_h = 40
        self.slider_knob_rect = pygame.Rect(self.slider_rect.centerx - knob_w//2, self.slider_rect.centery - knob_h//2, knob_w, knob_h)
        
        self.dragging_slider = False
        self.demo_delay = 1000     
        self.demo_ai_time = 1.0    

        self.state = STATE_MENU
        self.game_mode = MODE_PvAI
        
        self.leaderboard = LeaderboardManager()
        self.input_name = ""
        self.input_type = "FAME"
        self.move_count = 0 
        self.game_over_time = 0 
        
        self.reset_board()
        self.update_speed_from_slider()

    def update_speed_from_slider(self):
        pct = (self.slider_knob_rect.centerx - self.slider_rect.x) / self.slider_rect.width
        self.demo_delay = int(pct * 2000)
        self.demo_ai_time = max(0.1, pct * 2.5)

    def reset_board(self):
        self.board = create_board()
        self.turn = P1
        self.winner = None
        self.win_coords = []
        self.game_over = False
        self.game_over_time = 0
        self.move_count = 0 
        
        if self.state == STATE_GAMEOVER:
             self.state = STATE_PLAYING
        if self.state == STATE_INPUT:
             self.state = STATE_MENU
        
        self.ai_thinking = False
        self.ai_thread = None
        self.ai_result = {}
        self.animating = False
        self.anim_col = 0
        self.anim_row = 0
        self.anim_y = 0
        self.anim_player = 0
        self.last_move_time = pygame.time.get_ticks()
        
    def start_game(self, mode):
        self.game_mode = mode
        self.state = STATE_PLAYING
        self.reset_board()

    # --- DRAWING ---
    def draw_home_icon(self, center_x, center_y, radius):
        mx, my = pygame.mouse.get_pos()
        dist = math.hypot(mx - center_x, my - center_y)
        color = BUTTON_HOVER if dist < radius else BUTTON_COLOR
        pygame.draw.circle(self.screen, color, (center_x, center_y), radius)
        pygame.draw.circle(self.screen, (200, 200, 200), (center_x, center_y), radius, 3)
        body_w = int(radius * 0.9); body_h = int(radius * 0.7); roof_h = int(radius * 0.6)
        p1 = (center_x, center_y - 5 - roof_h); p2 = (center_x - body_w//1.8, center_y - 5); p3 = (center_x + body_w//1.8, center_y - 5)
        pygame.draw.polygon(self.screen, ICON_LINE_COLOR, [p1, p2, p3])
        pygame.draw.rect(self.screen, ICON_LINE_COLOR, (center_x - body_w//2, center_y - 5, body_w, body_h))
        pygame.draw.rect(self.screen, color, (center_x - body_w//6, center_y + body_h - body_h//1.5 - 5, body_w//3, body_h//1.5))

    def draw_restart_icon(self, center_x, center_y, radius):
        mx, my = pygame.mouse.get_pos()
        dist = math.hypot(mx - center_x, my - center_y)
        color = BUTTON_HOVER if dist < radius else BUTTON_COLOR
        pygame.draw.circle(self.screen, color, (center_x, center_y), radius)
        pygame.draw.circle(self.screen, (200, 200, 200), (center_x, center_y), radius, 3)
        icon_r = int(radius * 0.55)
        pygame.draw.circle(self.screen, ICON_LINE_COLOR, (center_x, center_y), icon_r, 4)
        gap_pos = (center_x + int(icon_r*0.7), center_y - int(icon_r*0.7))
        pygame.draw.circle(self.screen, color, gap_pos, 12) 
        p1 = (gap_pos[0] - 5, gap_pos[1] - 10); p2 = (gap_pos[0] + 10, gap_pos[1] + 5); p3 = (gap_pos[0] - 12, gap_pos[1] + 5)
        pygame.draw.polygon(self.screen, ICON_LINE_COLOR, [p1, p2, p3])

    def draw_menu_btn(self, rect, text, subtext="", hover=False):
        color = BUTTON_HOVER if hover else BUTTON_COLOR
        pygame.draw.rect(self.screen, color, rect, border_radius=15)
        pygame.draw.rect(self.screen, (255,255,255), rect, 3, border_radius=15)
        txt = self.font_M.render(text, True, (255,255,255))
        self.screen.blit(txt, txt.get_rect(center=(rect.centerx, rect.centery - (10 if subtext else 0))))
        if subtext:
            sub = self.font_S.render(subtext, True, (220,220,220))
            self.screen.blit(sub, sub.get_rect(center=(rect.centerx, rect.centery + 20)))

    def draw_slider(self):
        if self.game_mode == MODE_AIvAI and not self.game_over:
            pygame.draw.rect(self.screen, SLIDER_BG_COLOR, self.slider_rect, border_radius=10)
            fill_rect = pygame.Rect(self.slider_rect.x, self.slider_rect.y, self.slider_knob_rect.centerx - self.slider_rect.x, self.slider_rect.height)
            pygame.draw.rect(self.screen, SLIDER_FILL_COLOR, fill_rect, border_radius=10)
            pygame.draw.rect(self.screen, SLIDER_KNOB_COLOR, self.slider_knob_rect, border_radius=10)
            txt_turbo = self.font_S.render("Turbo", True, TEXT_COLOR)
            self.screen.blit(txt_turbo, (self.slider_rect.x - 100, self.slider_rect.y - 5))
            txt_slow = self.font_S.render("Traag", True, TEXT_COLOR)
            self.screen.blit(txt_slow, (self.slider_rect.right + 20, self.slider_rect.y - 5))

    def draw_board_graphics(self):
        self.screen.fill(BG_COLOR)
        header_text = ""
        header_color = TEXT_COLOR
        if self.game_over:
            if self.winner == P1: header_text = "ROOD WINT!"; header_color = PLAYER1_COLOR
            elif self.winner == P2: header_text = "GEEL WINT!"; header_color = PLAYER2_COLOR
            else: header_text = "GELIJKSPEL"
        else:
            if self.game_mode == MODE_AIvAI:
                header_text = f"DEMO - AI vs AI"
            elif self.game_mode == MODE_PvAI:
                if self.turn == P1: header_text = "Jouw beurt (Rood)"
                else: header_text = "AI denkt na..."
            else:
                header_text = f"Beurt: {'Speler 1 (Rood)' if self.turn == P1 else 'Speler 2 (Geel)'}"

        title = self.font_L.render(header_text, True, header_color)
        self.screen.blit(title, title.get_rect(center=(self.SCREEN_W//2, 35)))
        
        if self.game_mode == MODE_PvAI:
             move_txt = self.font_M.render(f"Jouw zetten: {self.move_count}", True, (200,200,200))
             self.screen.blit(move_txt, move_txt.get_rect(center=(self.SCREEN_W//2, 90)))

        radius = self.btn_home.width // 2
        self.draw_home_icon(self.btn_home.centerx, self.btn_home.centery, radius)
        self.draw_restart_icon(self.btn_restart.centerx, self.btn_restart.centery, radius)

        board_rect = (self.OFFSET_X, self.OFFSET_Y, self.BOARD_W, self.BOARD_H - self.SQUARESIZE)
        pygame.draw.rect(self.screen, BOARD_COLOR, board_rect, border_radius=20)
        
        for c in range(COLUMNS):
            for r in range(ROWS):
                cx = self.OFFSET_X + c * self.SQUARESIZE + self.SQUARESIZE // 2
                cy = self.OFFSET_Y + r * self.SQUARESIZE + self.SQUARESIZE // 2
                pygame.draw.circle(self.screen, HOLE_COLOR, (cx, cy), self.RADIUS)
                piece = self.board[r][c]
                if piece != EMPTY:
                    color = PLAYER1_COLOR if piece == P1 else PLAYER2_COLOR
                    if self.game_over and (r,c) in self.win_coords:
                        if (pygame.time.get_ticks() // 300) % 2 == 0: color = (255, 255, 255)
                    pygame.draw.circle(self.screen, (0,0,0), (cx, cy+3), self.RADIUS) 
                    pygame.draw.circle(self.screen, color, (cx, cy), self.RADIUS)

        if self.animating:
            color = PLAYER1_COLOR if self.anim_player == P1 else PLAYER2_COLOR
            cx = self.OFFSET_X + self.anim_col * self.SQUARESIZE + self.SQUARESIZE // 2
            cy = self.OFFSET_Y + self.anim_y + self.SQUARESIZE // 2
            pygame.draw.circle(self.screen, color, (cx, cy), self.RADIUS)
            
        is_human_turn = False
        if self.game_mode == MODE_PvP: is_human_turn = True
        if self.game_mode == MODE_PvAI and self.turn == P1: is_human_turn = True
        
        if not self.game_over and not self.animating and not self.ai_thinking and is_human_turn:
            mx, my = pygame.mouse.get_pos()
            if self.OFFSET_X <= mx <= self.OFFSET_X + self.BOARD_W:
                col = int((mx - self.OFFSET_X) // self.SQUARESIZE)
                col = max(0, min(COLUMNS-1, col))
                cx = self.OFFSET_X + col * self.SQUARESIZE + self.SQUARESIZE // 2
                cy = self.OFFSET_Y - self.SQUARESIZE // 2
                pygame.draw.circle(self.screen, PLAYER1_COLOR if self.turn == P1 else PLAYER2_COLOR, (cx, cy), self.RADIUS)

        self.draw_slider()

    def draw_leaderboard_overlay(self):
        lb_w = 400
        lb_h = 700
        x = self.SCREEN_W - lb_w - 50
        y = self.SCREEN_H // 2 - lb_h // 2
        
        rect = pygame.Rect(x, y, lb_w, lb_h)
        pygame.draw.rect(self.screen, LEADERBOARD_BG, rect, border_radius=15)
        pygame.draw.rect(self.screen, (100,100,100), rect, 2, border_radius=15)
        
        fame_y = rect.y + 20
        title_f = self.font_M.render("HALL OF FAME", True, (255, 215, 0))
        self.screen.blit(title_f, title_f.get_rect(center=(rect.centerx, fame_y)))
        
        headers_y = fame_y + 40
        h_rank = self.font_S.render("#", True, (150,150,150))
        h_name = self.font_S.render("NAAM", True, (150,150,150))
        h_move = self.font_S.render("ZETTEN", True, (150,150,150))
        self.screen.blit(h_rank, (rect.x + 30, headers_y))
        self.screen.blit(h_name, (rect.x + 80, headers_y))
        self.screen.blit(h_move, (rect.right - 100, headers_y))
        
        fame_scores = self.leaderboard.get_fame()
        for i, s in enumerate(fame_scores):
            row_y = headers_y + 35 + (i * 30)
            color = (255, 215, 0) if i == 0 else TEXT_COLOR
            
            rank_txt = self.font_Mono.render(str(i+1), True, color)
            name_txt = self.font_Mono.render(s['name'], True, color)
            move_txt = self.font_Mono.render(str(s['moves']), True, color)
            
            self.screen.blit(rank_txt, (rect.x + 35, row_y))
            self.screen.blit(name_txt, (rect.x + 80, row_y))
            self.screen.blit(move_txt, (rect.right - 80, row_y))

        if not fame_scores:
            msg = self.font_S.render("Nog geen helden...", True, (100,100,100))
            self.screen.blit(msg, msg.get_rect(center=(rect.centerx, headers_y + 80)))

        shame_start_y = rect.centery + 20
        pygame.draw.line(self.screen, (100,100,100), (rect.x + 20, shame_start_y - 20), (rect.right - 20, shame_start_y - 20), 1)

        title_s = self.font_M.render("HALL OF SHAME", True, (230, 50, 50))
        self.screen.blit(title_s, title_s.get_rect(center=(rect.centerx, shame_start_y)))
        
        sub_s = self.font_S.render("(Snelste verlies)", True, (150,150,150))
        self.screen.blit(sub_s, sub_s.get_rect(center=(rect.centerx, shame_start_y + 25)))

        shame_headers_y = shame_start_y + 60
        self.screen.blit(h_rank, (rect.x + 30, shame_headers_y))
        self.screen.blit(h_name, (rect.x + 80, shame_headers_y))
        self.screen.blit(h_move, (rect.right - 100, shame_headers_y))
        
        shame_scores = self.leaderboard.get_shame()
        for i, s in enumerate(shame_scores):
            row_y = shame_headers_y + 35 + (i * 30)
            color = (200, 100, 100) if i == 0 else (180,180,180)
            
            rank_txt = self.font_Mono.render(str(i+1), True, color)
            name_txt = self.font_Mono.render(s['name'], True, color)
            move_txt = self.font_Mono.render(str(s['moves']), True, color)
            
            self.screen.blit(rank_txt, (rect.x + 35, row_y))
            self.screen.blit(name_txt, (rect.x + 80, row_y))
            self.screen.blit(move_txt, (rect.right - 80, row_y))

        if not shame_scores:
            msg = self.font_S.render("Nog geen verliezers...", True, (100,100,100))
            self.screen.blit(msg, msg.get_rect(center=(rect.centerx, shame_headers_y + 80)))


    def draw_input_screen(self):
        self.draw_board_graphics()
        overlay = pygame.Surface((self.SCREEN_W, self.SCREEN_H))
        overlay.fill((0,0,0)); overlay.set_alpha(230)
        self.screen.blit(overlay, (0,0))
        
        if self.input_type == "FAME":
            t1 = self.font_L.render("GEWONNEN!", True, (255, 215, 0))
            t_sub = self.font_M.render("Welkom in de Hall of Fame", True, (200,200,200))
        else:
            t1 = self.font_L.render("VERLOREN...", True, (230, 50, 50))
            t_sub = self.font_M.render("Dat ging snel! Hall of Shame waardig.", True, (200,200,200))

        self.screen.blit(t1, t1.get_rect(center=(self.SCREEN_W//2, self.SCREEN_H//2 - 120)))
        self.screen.blit(t_sub, t_sub.get_rect(center=(self.SCREEN_W//2, self.SCREEN_H//2 - 60)))
        
        t2 = self.font_M.render("Voer je naam in:", True, TEXT_COLOR)
        self.screen.blit(t2, t2.get_rect(center=(self.SCREEN_W//2, self.SCREEN_H//2 + 10)))
        
        input_rect = pygame.Rect(0, 0, 400, 80)
        input_rect.center = (self.SCREEN_W//2, self.SCREEN_H//2 + 80)
        pygame.draw.rect(self.screen, (255,255,255), input_rect, border_radius=10)
        
        name_surf = self.font_L.render(self.input_name + "_", True, (0,0,0))
        self.screen.blit(name_surf, name_surf.get_rect(center=input_rect.center))
        
        t3 = self.font_S.render("Druk op ENTER", True, (150,150,150))
        self.screen.blit(t3, t3.get_rect(center=(self.SCREEN_W//2, self.SCREEN_H//2 + 150)))

    def draw_menu(self):
        self.draw_board_graphics()
        overlay = pygame.Surface((self.SCREEN_W, self.SCREEN_H))
        overlay.fill((0,0,0)); overlay.set_alpha(200)
        self.screen.blit(overlay, (0,0))
        
        center_x = self.SCREEN_W // 2 - 200 
        
        t1 = self.font_L.render("VIER OP EEN RIJ", True, (255,255,255))
        self.screen.blit(t1, t1.get_rect(center=(center_x, self.SCREEN_H//2 - 250)))
        t2 = self.font_S.render("Kies een spelmodus", True, (200,200,200))
        self.screen.blit(t2, t2.get_rect(center=(center_x, self.SCREEN_H//2 - 180)))

        mx, my = pygame.mouse.get_pos()
        
        self.menu_rects[MODE_PvAI].centerx = center_x
        self.menu_rects[MODE_PvP].centerx = center_x
        self.menu_rects[MODE_AIvAI].centerx = center_x

        self.draw_menu_btn(self.menu_rects[MODE_PvAI], "1 SPELER", "Mens vs Computer", self.menu_rects[MODE_PvAI].collidepoint((mx,my)))
        self.draw_menu_btn(self.menu_rects[MODE_PvP], "2 SPELERS", "Mens vs Mens", self.menu_rects[MODE_PvP].collidepoint((mx,my)))
        self.draw_menu_btn(self.menu_rects[MODE_AIvAI], "DEMO MODE", "Computer vs Computer", self.menu_rects[MODE_AIvAI].collidepoint((mx,my)))
        
        self.draw_leaderboard_overlay()

    def animate_drop(self, col, row, player):
        if "drop" in self.sounds:
            self.sounds["drop"].play()

        self.animating = True
        self.anim_col = col; self.anim_row = row; self.anim_player = player
        self.anim_y = -self.SQUARESIZE; target_y = row * self.SQUARESIZE
        speed = 0; gravity = 0.8
        while self.anim_y < target_y:
            speed += gravity; self.anim_y += speed
            if self.anim_y >= target_y: self.anim_y = target_y
            self.draw_board_graphics()
            pygame.display.update()
            pygame.time.Clock().tick(60)
        self.animating = False
        self.last_move_time = pygame.time.get_ticks()

    def run(self):
        clock = pygame.time.Clock()
        while True:
            current_time = pygame.time.get_ticks()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                
                if self.state == STATE_INPUT:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            if len(self.input_name) > 0:
                                if self.input_type == "FAME":
                                    self.leaderboard.add_fame(self.input_name, self.move_count)
                                else:
                                    self.leaderboard.add_shame(self.input_name, self.move_count)
                                self.state = STATE_MENU
                                self.reset_board()
                        elif event.key == pygame.K_BACKSPACE:
                            self.input_name = self.input_name[:-1]
                        else:
                            if len(self.input_name) < 12 and event.unicode.isprintable():
                                self.input_name += event.unicode
                    continue

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == STATE_MENU: pygame.quit(); sys.exit()
                        else: self.state = STATE_MENU
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    
                    if self.game_mode == MODE_AIvAI and self.slider_knob_rect.collidepoint((mx, my)):
                        self.dragging_slider = True
                    
                    if self.state in [STATE_PLAYING, STATE_GAMEOVER]:
                        if math.hypot(mx - self.btn_home.centerx, my - self.btn_home.centery) < self.btn_home.width//2: self.state = STATE_MENU; continue
                        if math.hypot(mx - self.btn_restart.centerx, my - self.btn_restart.centery) < self.btn_restart.width//2: self.reset_board(); continue
                    if self.state == STATE_MENU:
                        if self.menu_rects[MODE_PvAI].collidepoint((mx,my)):
                            if "select" in self.sounds: self.sounds["select"].play()
                            self.start_game(MODE_PvAI)
                        elif self.menu_rects[MODE_PvP].collidepoint((mx,my)):
                            if "select" in self.sounds: self.sounds["select"].play()
                            self.start_game(MODE_PvP)
                        elif self.menu_rects[MODE_AIvAI].collidepoint((mx,my)):
                            if "select" in self.sounds: self.sounds["select"].play()
                            self.start_game(MODE_AIvAI)
                    elif self.state == STATE_PLAYING and not self.game_over and not self.animating and not self.ai_thinking:
                        is_human = False
                        if self.game_mode == MODE_PvP: is_human = True
                        if self.game_mode == MODE_PvAI and self.turn == P1: is_human = True
                        if is_human:
                            if self.OFFSET_X <= mx <= self.OFFSET_X + self.BOARD_W:
                                col = int((mx - self.OFFSET_X) // self.SQUARESIZE)
                                if is_valid_location(self.board, col):
                                    row = get_next_open_row(self.board, col)
                                    self.animate_drop(col, row, self.turn)
                                    drop_piece(self.board, row, col, self.turn)
                                    
                                    if self.turn == P1: self.move_count += 1
                                    
                                    if winning_move(self.board, self.turn):
                                        self.game_over = True
                                        self.winner = self.turn
                                        self.win_coords = get_winning_coords(self.board, self.turn)
                                        self.game_over_time = pygame.time.get_ticks()
                                    else: 
                                        self.turn = P1 if self.turn == P2 else P2

                                    if not self.game_over and not get_valid_locations(self.board):
                                        self.game_over = True; self.winner = None; self.state = STATE_GAMEOVER
                                        # Voor gelijkspel: ook delay
                                        self.game_over_time = pygame.time.get_ticks()
                
                if event.type == pygame.MOUSEBUTTONUP:
                    self.dragging_slider = False

                if event.type == pygame.MOUSEMOTION:
                    if self.dragging_slider:
                        mx, my = pygame.mouse.get_pos()
                        new_x = max(self.slider_rect.x, min(mx, self.slider_rect.right - self.slider_knob_rect.width))
                        self.slider_knob_rect.x = new_x
                        self.update_speed_from_slider()
            
            if self.game_over and self.state == STATE_PLAYING:
                if current_time - self.game_over_time > 2000: # wacht 2000ms
                    
                    # --- GELUIDEN AFSPELEN NA DELAY ---
                    if self.winner is None:
                        if "draw" in self.sounds: self.sounds["draw"].play()
                    elif self.game_mode == MODE_PvAI:
                        if self.winner == P1:
                            if "win" in self.sounds: self.sounds["win"].play()
                        elif self.winner == P2:
                            if "lose" in self.sounds: self.sounds["lose"].play()
                    elif self.game_mode == MODE_PvP:
                        if "win" in self.sounds: self.sounds["win"].play()

                    # --- TRANSITIES NAAR INPUT OF GAMEOVER ---
                    if self.game_mode == MODE_PvAI and ((self.winner == P1) or (self.winner == P2)):
                         self.state = STATE_INPUT
                         self.input_name = ""
                         if self.winner == P1: self.input_type = "FAME"
                         else: self.input_type = "SHAME"
                    else:
                         self.state = STATE_GAMEOVER

            if self.state == STATE_PLAYING and not self.game_over and not self.animating:
                ai_turn = False
                my_piece = self.turn
                opp_piece = P1 if self.turn == P2 else P2
                if self.game_mode == MODE_PvAI and self.turn == P2: ai_turn = True
                if self.game_mode == MODE_AIvAI: ai_turn = True
                if ai_turn:
                    if not self.ai_thinking:
                        if self.game_mode == MODE_AIvAI and (current_time - self.last_move_time < self.demo_delay):
                             pass
                        else:
                            limit = 2.5
                            if self.game_mode == MODE_AIvAI: limit = self.demo_ai_time
                            self.ai_thinking = True
                            board_copy = [r[:] for r in self.board]
                            self.ai_thread = threading.Thread(target=ai_thread_func, args=(board_copy, self.ai_result, my_piece, opp_piece, limit))
                            self.ai_thread.start()

                    elif self.ai_result.get('done'):
                        col = self.ai_result.get('col')
                        if col is None and not self.game_over: 
                            valid = get_valid_locations(self.board)
                            if valid: col = random.choice(valid)
                        if col is not None and is_valid_location(self.board, col):
                            row = get_next_open_row(self.board, col)
                            self.animate_drop(col, row, self.turn)
                            drop_piece(self.board, row, col, self.turn)
                            
                            if winning_move(self.board, self.turn):
                                self.game_over = True
                                self.winner = self.turn
                                self.win_coords = get_winning_coords(self.board, self.turn)
                                # Zet tijdstip voor delay
                                self.game_over_time = pygame.time.get_ticks()
                                
                            else: self.turn = P1 if self.turn == P2 else P2
                        if not self.game_over and not get_valid_locations(self.board):
                             self.game_over = True; self.winner = None; self.state = STATE_GAMEOVER
                             self.game_over_time = pygame.time.get_ticks()
                        self.ai_thinking = False; self.ai_result = {}
                        self.last_move_time = pygame.time.get_ticks()

            if self.state == STATE_MENU: self.draw_menu()
            elif self.state == STATE_INPUT: self.draw_input_screen()
            else: self.draw_board_graphics()
            pygame.display.update(); clock.tick(60)

if __name__ == "__main__":
    GameApp().run()