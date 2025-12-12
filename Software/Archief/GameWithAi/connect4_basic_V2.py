import pygame
import sys
import math
import time
import random
import threading
from typing import List, Optional, Tuple, Dict

# ================================
#  Configuratie
# ================================
AI_DEPTH = 6                 # standaard target diepte voor iterative deepening
AI_TIME_LIMIT = 2.0          # seconden time limit per AI-zet (iterative deepening)
AI_PLAYER = 2
HUMAN_PLAYER = 1
ROWS = 6
COLUMNS = 7
WINDOW_LENGTH = 4

# Transposition table flags
EXACT = 0
LOWERBOUND = 1
UPPERBOUND = 2

INF = float('inf')

# ================================
#  Board helpers (schoon & efficiënt)
# ================================

def create_board() -> List[List[int]]:
    """Maak een lege bordrepresentatie: list of rows (0 = empty)."""
    return [[0] * COLUMNS for _ in range(ROWS)]


def is_valid_location(board: List[List[int]], col: int) -> bool:
    return 0 <= col < COLUMNS and board[0][col] == 0


def get_valid_locations(board: List[List[int]]) -> List[int]:
    return [c for c in range(COLUMNS) if is_valid_location(board, c)]


def get_next_open_row(board: List[List[int]], col: int) -> Optional[int]:
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == 0:
            return r
    return None


def apply_move(board: List[List[int]], col: int, piece: int) -> Optional[int]:
    """Plaats stuk in kolom en retourneer de rij (of None als ongeldig)."""
    r = get_next_open_row(board, col)
    if r is None:
        return None
    board[r][col] = piece
    return r


def undo_move(board: List[List[int]], row: int, col: int) -> None:
    board[row][col] = 0


def drop_piece(board: List[List[int]], row: int, col: int, piece: int) -> None:
    board[row][col] = piece


def winning_move(board: List[List[int]], piece: int) -> bool:
    # horizontaal
    for r in range(ROWS):
        for c in range(COLUMNS - 3):
            if board[r][c] == piece and board[r][c + 1] == piece and board[r][c + 2] == piece and board[r][c + 3] == piece:
                return True
    # verticaal
    for c in range(COLUMNS):
        for r in range(ROWS - 3):
            if board[r][c] == piece and board[r + 1][c] == piece and board[r + 2][c] == piece and board[r + 3][c] == piece:
                return True
    # diag /
    for r in range(3, ROWS):
        for c in range(COLUMNS - 3):
            if board[r][c] == piece and board[r - 1][c + 1] == piece and board[r - 2][c + 2] == piece and board[r - 3][c + 3] == piece:
                return True
    # diag \
    for r in range(ROWS - 3):
        for c in range(COLUMNS - 3):
            if board[r][c] == piece and board[r + 1][c + 1] == piece and board[r + 2][c + 2] == piece and board[r + 3][c + 3] == piece:
                return True
    return False


def is_terminal_node(board: List[List[int]]) -> bool:
    return winning_move(board, HUMAN_PLAYER) or winning_move(board, AI_PLAYER) or len(get_valid_locations(board)) == 0

# ================================
#  Heuristiek (score functie)
# ================================

def evaluate_window(window: List[int], piece: int) -> int:
    score = 0
    opp_piece = HUMAN_PLAYER if piece == AI_PLAYER else AI_PLAYER

    if window.count(piece) == 4:
        score += 10000
    elif window.count(piece) == 3 and window.count(0) == 1:
        score += 50
    elif window.count(piece) == 2 and window.count(0) == 2:
        score += 10

    if window.count(opp_piece) == 3 and window.count(0) == 1:
        score -= 80

    return score


def score_position(board: List[List[int]], piece: int) -> int:
    score = 0
    # center column preference
    center_col = COLUMNS // 2
    center_array = [board[r][center_col] for r in range(ROWS)]
    center_count = center_array.count(piece)
    score += center_count * 6

    # horizontal
    for r in range(ROWS):
        row_array = [board[r][c] for c in range(COLUMNS)]
        for c in range(COLUMNS - 3):
            window = row_array[c:c + WINDOW_LENGTH]
            score += evaluate_window(window, piece)

    # vertical
    for c in range(COLUMNS):
        col_array = [board[r][c] for r in range(ROWS)]
        for r in range(ROWS - 3):
            window = col_array[r:r + WINDOW_LENGTH]
            score += evaluate_window(window, piece)

    # positive diagonal \
    for r in range(ROWS - 3):
        for c in range(COLUMNS - 3):
            window = [board[r + i][c + i] for i in range(WINDOW_LENGTH)]
            score += evaluate_window(window, piece)

    # negative diagonal /
    for r in range(3, ROWS):
        for c in range(COLUMNS - 3):
            window = [board[r - i][c + i] for i in range(WINDOW_LENGTH)]
            score += evaluate_window(window, piece)

    return score

# ================================
#  Zobrist hashing + Transposition Table
# ================================

# Pre-generate random 64-bit ints for each cell and piece (2 pieces)
ZOBRIST = [[[random.getrandbits(64) for _ in range(2)] for _ in range(COLUMNS)] for _ in range(ROWS)]


def compute_zobrist_hash(board: List[List[int]]) -> int:
    h = 0
    for r in range(ROWS):
        for c in range(COLUMNS):
            piece = board[r][c]
            if piece != 0:
                idx = 0 if piece == 1 else 1
                h ^= ZOBRIST[r][c][idx]
    return h

# ================================
#  Move ordering helpers
# ================================

def order_moves(board: List[List[int]], moves: List[int], piece: int) -> List[int]:
    # Prioritiseer: directe winnende zetten -> blokkeren van tegenstander -> centrum
    center = COLUMNS // 2
    wins = []
    blocks = []
    others = []

    opp = HUMAN_PLAYER if piece == AI_PLAYER else AI_PLAYER
    for col in moves:
        r = get_next_open_row(board, col)
        if r is None:
            continue
        board[r][col] = piece
        if winning_move(board, piece):
            wins.append(col)
            board[r][col] = 0
            continue
        board[r][col] = opp
        if winning_move(board, opp):
            blocks.append(col)
            board[r][col] = 0
            continue
        board[r][col] = 0
        others.append(col)

    # sort others by distance to center (prefer center)
    others.sort(key=lambda c: abs(c - center))
    ordered = wins + blocks + others
    return ordered

# ================================
# alpha-beta pruning + TT (in-place)
# ================================

def minimax_search(board: List[List[int]], depth: int, alpha: float, beta: float, maximizingPlayer: bool,
                   zobrist_hash: int, tt: Dict[int, Tuple[int, float, int, Optional[int]]], start_time: float,
                   time_limit: float) -> Tuple[Optional[int], float]:
    """
    Retourneer (beste_kolom, score). tt maps zobrist->(depth, score, flag, best_col)
    """
    # time check
    if time.time() - start_time > time_limit:
        raise TimeoutError()

    valid_locations = get_valid_locations(board)
    is_terminal = is_terminal_node(board)

    # TT lookup
    if zobrist_hash in tt:
        entry_depth, entry_score, entry_flag, entry_best = tt[zobrist_hash]
        if entry_depth >= depth:
            if entry_flag == EXACT:
                return entry_best, entry_score
            elif entry_flag == LOWERBOUND:
                alpha = max(alpha, entry_score)
            elif entry_flag == UPPERBOUND:
                beta = min(beta, entry_score)
            if alpha >= beta:
                return entry_best, entry_score

    if depth == 0 or is_terminal:
        if is_terminal:
            if winning_move(board, AI_PLAYER):
                return None, INF
            elif winning_move(board, HUMAN_PLAYER):
                return None, -INF
            else:
                return None, 0
        else:
            return None, float(score_position(board, AI_PLAYER))

    best_col: Optional[int] = None
    original_alpha = alpha

    if maximizingPlayer:
        value = -INF
        # move ordering
        moves = order_moves(board, valid_locations, AI_PLAYER)
        for col in moves:
            r = apply_move(board, col, AI_PLAYER)
            if r is None:
                continue
            new_hash = zobrist_hash ^ ZOBRIST[r][col][1]  # piece index 1 for AI (piece==2)
            try:
                _, new_score = minimax_search(board, depth - 1, alpha, beta, False, new_hash, tt, start_time, time_limit)
            except TimeoutError:
                undo_move(board, r, col)
                raise
            undo_move(board, r, col)

            if new_score > value:
                value = new_score
                best_col = col
            alpha = max(alpha, value)
            if alpha >= beta:
                break
    else:
        value = INF
        moves = order_moves(board, valid_locations, HUMAN_PLAYER)
        for col in moves:
            r = apply_move(board, col, HUMAN_PLAYER)
            if r is None:
                continue
            new_hash = zobrist_hash ^ ZOBRIST[r][col][0]  # piece index 0 for human (piece==1)
            try:
                _, new_score = minimax_search(board, depth - 1, alpha, beta, True, new_hash, tt, start_time, time_limit)
            except TimeoutError:
                undo_move(board, r, col)
                raise
            undo_move(board, r, col)

            if new_score < value:
                value = new_score
                best_col = col
            beta = min(beta, value)
            if alpha >= beta:
                break

    # store in TT
    flag = EXACT
    if value <= original_alpha:
        flag = UPPERBOUND
    elif value >= beta:
        flag = LOWERBOUND
    tt[zobrist_hash] = (depth, value, flag, best_col)

    return best_col, value

# ================================
#  AI entry: iterative deepening met time limit en TT
#  Deze versie publiceert alleen "best_so_far" maar schrijft een
#  expliciete final_col op het einde zodat main thread alleen die gebruikt.
# ================================

def ai_think_iterative(board_snapshot: List[List[int]], max_depth: int, time_limit: float, result_container: dict):
    start_time = time.time()
    end_time = start_time + time_limit
    tt: Dict[int, Tuple[int, float, int, Optional[int]]] = {}
    best_move = None
    best_score = -INF
    base_hash = compute_zobrist_hash(board_snapshot)

    try:
        for depth in range(1, max_depth + 1):
            if time.time() > end_time:
                break
            try:
                col, score = minimax_search(board_snapshot, depth, -INF, INF, True, base_hash, tt, start_time, time_limit)
            except TimeoutError:
                break
            if col is not None:
                best_move = col
                best_score = score
                # publiceer beste tussenresultaat (optioneel) - maar main gebruikt het niet
                result_container['best_so_far_col'] = best_move
                result_container['best_so_far_score'] = best_score
        # einde iterative deepening: schrijf final
        result_container['final_col'] = best_move
        result_container['final_score'] = best_score
    except Exception:
        # zorg dat main thread weet dat AI klaar is, ook bij fout
        result_container['final_col'] = best_move
        result_container['final_score'] = best_score

# ================================
#  Pygame (UI)
# ================================
class VierOpEenRij:
    def __init__(self, ai_enabled: bool = True):
        pygame.init()

        # Constants & Colors
        self.RIJEN = ROWS
        self.KOLOMMEN = COLUMNS
        self.SQUARESIZE = 100
        self.WIDTH = self.KOLOMMEN * self.SQUARESIZE
        self.HEIGHT = (self.RIJEN + 1) * self.SQUARESIZE
        self.RADIUS = int(self.SQUARESIZE / 2 - 5)

        self.BLUE = (0, 0, 255)
        self.BLACK = (0, 0, 0)
        self.RED = (255, 0, 0)
        self.YELLOW = (255, 255, 0)
        self.WHITE = (255, 255, 255)

        # Game state
        self.bord = create_board()
        self.huidige_speler = 1
        self.game_over = False
        self.ai_enabled = ai_enabled

        # AI threading state
        self.ai_thinking = False
        self.ai_result = None
        self.ai_thread: Optional[threading.Thread] = None

        # Pygame
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.SCALED)
        pygame.display.set_caption('Vier op een Rij')
        try:
            icon = pygame.image.load('icon.ico')
            pygame.display.set_icon(icon)
        except Exception:
            # geen icoon is geen probleem
            pass
        self.font = pygame.font.SysFont('monospace', 75)
        self.klein_font = pygame.font.SysFont('monospace', 40)

        # Animation props
        self.animating = False
        self.anim_piece = None
        self.anim_y = 0
        self.target_y = 0
        self.anim_x = 0
        self.anim_speed = 20

        self.win_time = 0
        self.show_new_game_prompt = False

    def teken_bord(self) -> None:
        self.screen.fill(self.BLACK)

        # Draw board rects & holes
        for c in range(self.KOLOMMEN):
            for r in range(self.RIJEN):
                pygame.draw.rect(self.screen, self.BLUE,
                                 (c * self.SQUARESIZE, (r + 1) * self.SQUARESIZE, self.SQUARESIZE, self.SQUARESIZE))
                pygame.draw.circle(self.screen, self.BLACK,
                                   (int(c * self.SQUARESIZE + self.SQUARESIZE / 2),
                                    int((r + 1) * self.SQUARESIZE + self.SQUARESIZE / 2)),
                                   self.RADIUS)

        # Draw pieces
        for c in range(self.KOLOMMEN):
            for r in range(self.RIJEN):
                if self.bord[r][c] == 1:
                    color = self.RED
                elif self.bord[r][c] == 2:
                    color = self.YELLOW
                else:
                    continue
                pygame.draw.circle(self.screen, color,
                                   (int(c * self.SQUARESIZE + self.SQUARESIZE / 2),
                                    int((r + 1) * self.SQUARESIZE + self.SQUARESIZE / 2)),
                                   self.RADIUS)

        # Draw animated falling piece
        if self.animating and self.anim_piece:
            color = self.RED if self.anim_piece == 1 else self.YELLOW
            pygame.draw.circle(self.screen, color, (int(self.anim_x), int(self.anim_y)), self.RADIUS)

        # Hover piece for human when not animating and not game_over and human's turn
        if not self.animating and not self.game_over and self.huidige_speler == HUMAN_PLAYER:
            posx = pygame.mouse.get_pos()[0]
            color = self.RED
            pygame.draw.circle(self.screen, color, (posx, int(self.SQUARESIZE / 2)), self.RADIUS)

        # Game over messages
        if self.game_over:
            if hasattr(self, 'win_message'):
                # center top
                msg_surf = self.win_message
                x = (self.WIDTH - msg_surf.get_width()) // 2
                y = max(6, int(self.SQUARESIZE * 0.06))
                # draw background for contrast
                pad = max(8, int(self.SQUARESIZE * 0.15))
                bg = pygame.Surface((msg_surf.get_width() + pad * 2, msg_surf.get_height() + pad), pygame.SRCALPHA)
                bg.fill((0, 0, 0, 200))
                self.screen.blit(bg, (x - pad, y - pad // 2))
                self.screen.blit(msg_surf, (x, y))

            if not self.show_new_game_prompt and time.time() - self.win_time >= 1.0:
                self.show_new_game_prompt = True
            if self.show_new_game_prompt:
                new_game_text = self.klein_font.render('Press SPACE To Restart', True, (255, 255, 255))
                pad = max(6, int(self.SQUARESIZE * 0.12))
                ix = (self.WIDTH - new_game_text.get_width()) // 2
                iy = y + msg_surf.get_height() + pad
                ibg = pygame.Surface((new_game_text.get_width() + pad * 2, new_game_text.get_height() + pad), pygame.SRCALPHA)
                ibg.fill((50, 50, 50, 220))
                self.screen.blit(ibg, (ix - pad, iy - pad // 2))
                self.screen.blit(new_game_text, (ix, iy))

        pygame.display.update()

    def animate_piece(self, kolom: int, target_row: int, piece: int) -> None:
        self.animating = True
        self.anim_piece = piece
        self.anim_x = kolom * self.SQUARESIZE + self.SQUARESIZE / 2
        self.anim_y = self.SQUARESIZE / 2
        self.target_y = (target_row + 1) * self.SQUARESIZE + self.SQUARESIZE / 2

        while self.anim_y < self.target_y:
            self.anim_y += self.anim_speed
            if self.anim_y > self.target_y:
                self.anim_y = self.target_y
            self.teken_bord()
            pygame.time.wait(10)

        self.animating = False
        self.anim_piece = None

    def plaats_fiche(self, kolom: int, speler: int) -> bool:
        if not is_valid_location(self.bord, kolom):
            return False
        rij = get_next_open_row(self.bord, kolom)
        if rij is None:
            return False
        # animate and place
        self.animate_piece(kolom, rij, speler)
        drop_piece(self.bord, rij, kolom, speler)
        return True

    def toon_winnaar(self, tekst: str, speler: int) -> None:
        # speler == 0 betekent gelijkspel -> witte tekst
        if speler == 1:
            kleur = self.RED
        elif speler == 2:
            kleur = self.YELLOW
        else:
            kleur = self.WHITE
        self.win_message = self.font.render(tekst, True, kleur)
        self.win_time = time.time()
        self.show_new_game_prompt = False
        self.teken_bord()

    def reset(self) -> None:
        # reset spelstatus en stop lopende AI-thread flags (de daemon thread mag uitlopen)
        self.bord = create_board()
        self.huidige_speler = 1
        self.game_over = False
        self.show_new_game_prompt = False
        self.ai_thinking = False
        self.ai_result = None
        self.ai_thread = None

# ================================
# Main-loop
# ================================

def main() -> None:
    spel = VierOpEenRij(ai_enabled=True)

    clock = pygame.time.Clock()

    while True:
        spel.teken_bord()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Mouse move redraw for hover
            if event.type == pygame.MOUSEMOTION and not spel.game_over:
                spel.teken_bord()

            # Human click
            if event.type == pygame.MOUSEBUTTONDOWN and not spel.game_over and spel.huidige_speler == HUMAN_PLAYER:
                posx = event.pos[0]
                kolom = int(math.floor(posx / spel.SQUARESIZE))
                if spel.plaats_fiche(kolom, HUMAN_PLAYER):
                    if winning_move(spel.bord, HUMAN_PLAYER):
                        spel.toon_winnaar("ROOD WINT!!", HUMAN_PLAYER)
                        spel.game_over = True
                    elif len(get_valid_locations(spel.bord)) == 0:
                        spel.toon_winnaar("GELIJKSPEL!", 0)
                        spel.game_over = True
                    else:
                        spel.huidige_speler = AI_PLAYER

            # Restart with space
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and spel.game_over:
                    spel.reset()

        # AI's turn (non-blocking): start thread once to compute best move with iterative deepening
        if not spel.game_over and spel.huidige_speler == AI_PLAYER and spel.ai_enabled:
            # start thinking only once per AI-turn
            if not spel.ai_thinking and spel.ai_thread is None:
                board_snapshot = [row[:] for row in spel.bord]
                result_container: dict = {}
                spel.ai_thinking = True
                spel.ai_result = result_container
                t = threading.Thread(target=ai_think_iterative, args=(board_snapshot, AI_DEPTH, AI_TIME_LIMIT, result_container), daemon=True)
                spel.ai_thread = t
                t.start()

            # place move ONLY when thread finished (synchronization)
            if spel.ai_thread is not None and not spel.ai_thread.is_alive():
                # thread done — read final result
                final_col = None
                if spel.ai_result is not None:
                    # prefer final_col, fallback to best_so_far
                    final_col = spel.ai_result.get('final_col') if 'final_col' in spel.ai_result else spel.ai_result.get('best_so_far_col')
                if final_col is None:
                    valid = get_valid_locations(spel.bord)
                    if valid:
                        final_col = random.choice(valid)

                # plaats AI zet (in main thread)
                if final_col is not None and spel.plaats_fiche(final_col, AI_PLAYER):
                    if winning_move(spel.bord, AI_PLAYER):
                        spel.toon_winnaar("GEEL (AI) WINT!!", AI_PLAYER)
                        spel.game_over = True
                    elif len(get_valid_locations(spel.bord)) == 0:
                        spel.toon_winnaar("GELIJKSPEL!", 0)
                        spel.game_over = True
                    else:
                        spel.huidige_speler = HUMAN_PLAYER

                # cleanup
                spel.ai_result = None
                spel.ai_thread = None
                spel.ai_thinking = False

        clock.tick(60)


if __name__ == "__main__":
    main()
