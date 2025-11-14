import pygame
import sys
import math
import time

class VierOpEenRij:
    def __init__(self):

        pygame.init()
        
        # Constants
        self.RIJEN = 6
        self.KOLOMMEN = 7
        self.SQUARESIZE = 100
        self.WIDTH = self.KOLOMMEN * self.SQUARESIZE
        self.HEIGHT = (self.RIJEN + 1) * self.SQUARESIZE  # Extra row for piece animation
        self.RADIUS = int(self.SQUARESIZE/2 - 5)
        
        # Colors
        self.BLUE = (0, 0, 255)
        self.BLACK = (0, 0, 0)
        self.RED = (255, 0, 0)
        self.YELLOW = (255, 255, 0)
        
        # Game state
        self.bord = [[0 for _ in range(self.KOLOMMEN)] for _ in range(self.RIJEN)]
        self.huidige_speler = 1
        self.game_over = False
        
        # Pygame setup
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.SCALED)
        pygame.display.set_caption('Vier op een Rij')
        self.font = pygame.font.SysFont('monospace', 75)
        
        # Animation properties
        self.animating = False
        self.anim_piece = None
        self.anim_y = 0
        self.target_y = 0
        self.anim_x = 0
        self.anim_speed = 15
        
        # Game over properties
        self.win_time = 0
        self.show_new_game_prompt = False
        self.klein_font = pygame.font.SysFont('monospace', 40)

    def teken_bord(self):
        """Teken het speelbord"""
        # Clear the screen
        self.screen.fill(self.BLACK)
        
        # Draw the game board
        for c in range(self.KOLOMMEN):
            for r in range(self.RIJEN):
                # Draw blue rectangle for each cell
                pygame.draw.rect(self.screen, self.BLUE, 
                               (c * self.SQUARESIZE, (r + 1) * self.SQUARESIZE, 
                                self.SQUARESIZE, self.SQUARESIZE))
                # Draw empty circle
                pygame.draw.circle(self.screen, self.BLACK,
                                 (int(c * self.SQUARESIZE + self.SQUARESIZE/2),
                                  int((r + 1) * self.SQUARESIZE + self.SQUARESIZE/2)),
                                 self.RADIUS)
        
        # Draw the pieces
        for c in range(self.KOLOMMEN):
            for r in range(self.RIJEN):
                if self.bord[r][c] == 1:
                    color = self.RED
                elif self.bord[r][c] == 2:
                    color = self.YELLOW
                else:
                    continue
                    
                pygame.draw.circle(self.screen, color,
                                 (int(c * self.SQUARESIZE + self.SQUARESIZE/2),
                                  int((r + 1) * self.SQUARESIZE + self.SQUARESIZE/2)),
                                 self.RADIUS)
        
        # Draw the animated piece if there is one
        if self.animating and self.anim_piece:
            color = self.RED if self.huidige_speler == 1 else self.YELLOW
            pygame.draw.circle(self.screen, color,
                             (int(self.anim_x), int(self.anim_y)),
                             self.RADIUS)
        
        # Draw the hovering piece
        if not self.animating and not self.game_over:
            posx = pygame.mouse.get_pos()[0]
            color = self.RED if self.huidige_speler == 1 else self.YELLOW
            pygame.draw.circle(self.screen, color, (posx, int(self.SQUARESIZE/2)), self.RADIUS)
        
        # Show game over messages
        if self.game_over:
            # Always show winner message
            if hasattr(self, 'win_message'):
                self.screen.blit(self.win_message, (40, 10))
            
            # Check if we should show the new game prompt
            if not self.show_new_game_prompt and time.time() - self.win_time >= 5:
                self.show_new_game_prompt = True
            
            if self.show_new_game_prompt:
                new_game_text = self.klein_font.render("Druk SPATIE voor nieuw spel", True, (255, 255, 255))
                self.screen.blit(new_game_text, (40, self.HEIGHT - 60))
        
        pygame.display.update()

    def is_geldige_zet(self, kolom):
        """Controleert of een zet geldig is"""
        return 0 <= kolom < self.KOLOMMEN and self.bord[0][kolom] == 0

    def animate_piece(self, kolom, target_row):
        """Animate the piece falling"""
        self.animating = True
        self.anim_x = kolom * self.SQUARESIZE + self.SQUARESIZE/2
        self.anim_y = self.SQUARESIZE/2
        self.target_y = (target_row + 1) * self.SQUARESIZE + self.SQUARESIZE/2
        self.anim_piece = self.huidige_speler
        
        # Animation loop
        while self.anim_y < self.target_y:
            self.anim_y += self.anim_speed
            if self.anim_y > self.target_y:
                self.anim_y = self.target_y
            self.teken_bord()
            pygame.time.wait(10)
        
        self.animating = False
        self.anim_piece = None

    def plaats_fiche(self, kolom):
        """Plaatst een fiche in de aangegeven kolom"""
        if not self.is_geldige_zet(kolom):
            return False
        
        # Find the lowest empty row
        for rij in range(self.RIJEN-1, -1, -1):
            if self.bord[rij][kolom] == 0:
                # Animate the piece falling
                self.animate_piece(kolom, rij)
                # Update the board
                self.bord[rij][kolom] = self.huidige_speler
                return True
        return False

    def controleer_winst(self):
        """Controleert of er een winnaar is"""
        # Horizontale check
        for rij in range(self.RIJEN):
            for kolom in range(self.KOLOMMEN-3):
                if (self.bord[rij][kolom] == self.huidige_speler and
                    self.bord[rij][kolom+1] == self.huidige_speler and
                    self.bord[rij][kolom+2] == self.huidige_speler and
                    self.bord[rij][kolom+3] == self.huidige_speler):
                    return True

        # Verticale check
        for rij in range(self.RIJEN-3):
            for kolom in range(self.KOLOMMEN):
                if (self.bord[rij][kolom] == self.huidige_speler and
                    self.bord[rij+1][kolom] == self.huidige_speler and
                    self.bord[rij+2][kolom] == self.huidige_speler and
                    self.bord[rij+3][kolom] == self.huidige_speler):
                    return True

        # Diagonale check (/)
        for rij in range(3, self.RIJEN):
            for kolom in range(self.KOLOMMEN-3):
                if (self.bord[rij][kolom] == self.huidige_speler and
                    self.bord[rij-1][kolom+1] == self.huidige_speler and
                    self.bord[rij-2][kolom+2] == self.huidige_speler and
                    self.bord[rij-3][kolom+3] == self.huidige_speler):
                    return True

        # Diagonale check (\)
        for rij in range(self.RIJEN-3):
            for kolom in range(self.KOLOMMEN-3):
                if (self.bord[rij][kolom] == self.huidige_speler and
                    self.bord[rij+1][kolom+1] == self.huidige_speler and
                    self.bord[rij+2][kolom+2] == self.huidige_speler and
                    self.bord[rij+3][kolom+3] == self.huidige_speler):
                    return True

        return False

    def controleer_gelijkspel(self):
        """Controleert of het spel in gelijkspel is geëindigd"""
        return all(self.bord[0][kolom] != 0 for kolom in range(self.KOLOMMEN))

    def wissel_speler(self):
        """Wisselt de huidige speler"""
        self.huidige_speler = 3 - self.huidige_speler  # Wisselt tussen 1 en 2

    def toon_winnaar(self, tekst):
        """Toon het winnaarsbericht"""
        # Render het winnaarsbericht
        self.win_message = self.font.render(tekst, True, self.RED if self.huidige_speler == 1 else self.YELLOW)
        
        # Start timer voor wanneer we de 'new game' tekst moeten tonen
        self.win_time = time.time()
        self.show_new_game_prompt = False
        
        # Teken het bord met het winnaarsbericht
        self.teken_bord()

def main():
    spel = VierOpEenRij()
    
    while True:
        spel.teken_bord()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEMOTION and not spel.game_over:
                spel.teken_bord()
            
            if event.type == pygame.MOUSEBUTTONDOWN and not spel.game_over:
                # Get the mouse x position
                posx = event.pos[0]
                kolom = int(math.floor(posx/spel.SQUARESIZE))
                
                if spel.plaats_fiche(kolom):
                    if spel.controleer_winst():
                        winner_text = "ROOD" if spel.huidige_speler == 1 else "GEEL"
                        spel.toon_winnaar(f"{winner_text} WINT!!")
                        spel.game_over = True
                    elif spel.controleer_gelijkspel():
                        spel.toon_winnaar("GELIJKSPEL!")
                        spel.game_over = True
                    else:
                        spel.wissel_speler()
            
            # Reset game with spacebar
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and spel.game_over:
                    spel = VierOpEenRij()

if __name__ == "__main__":
    main()
