import pygame
import random
from .player import Player
from .enemy import EnemyGrid
from .bullet import Bullet


# Colors
WHITE = (255, 255, 255)
GREEN = (0, 200, 0)
RED = (220, 60, 60)
BLACK = (0, 0, 0)


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.player = Player(
            width // 2 - 20,
            height - 50,
            40,
            20
        )

        self.enemy_grid = EnemyGrid(width)

        self.player_bullets = []
        self.enemy_bullets = []

        self._shoot_cooldown = 0
        self.enemy_fire_chance = 0.01

        self.score = 0

        # Game states:
        # "playing" -> game is running
        # "game_over" -> game has ended
        self.state = "playing"

        # Fonts
        self.font = pygame.font.SysFont("Arial", 30)
        self.game_over_font = pygame.font.SysFont("Arial", 60)
        self.final_score_font = pygame.font.SysFont("Arial", 36)
        self.instruction_font = pygame.font.SysFont("Arial", 28)

    def handle_event(self, event):
        # Ignore game controls while game is over
        if self.state == "game_over":
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if self._shoot_cooldown <= 0:
                    bullet_x = self.player.center_x() - 2

                    self.player_bullets.append(
                        Bullet(
                            bullet_x,
                            self.player.y,
                            direction=-1
                        )
                    )

                    self._shoot_cooldown = 15

    def handle_input(self):
        # Do not allow movement after game over
        if self.state == "game_over":
            return

        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player.move(
                -self.player.speed,
                self.width
            )

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player.move(
                self.player.speed,
                self.width
            )

    def update(self):
        # Stop updating the game once game over occurs
        if self.state == "game_over":
            return

        # Shooting cooldown
        if self._shoot_cooldown > 0:
            self._shoot_cooldown -= 1

        # Move enemies
        self.enemy_grid.move()

        # Enemy shooting
        for enemy in self.enemy_grid.alive_enemies():
            if random.random() < self.enemy_fire_chance:
                bullet_x = enemy.x + enemy.width // 2

                self.enemy_bullets.append(
                    Bullet(
                        bullet_x,
                        enemy.y + enemy.height,
                        direction=1
                    )
                )

        # Move bullets
        for bullet in self.player_bullets:
            bullet.move()

        for bullet in self.enemy_bullets:
            bullet.move()

        # Remove off-screen bullets
        self.player_bullets = [
            bullet
            for bullet in self.player_bullets
            if not bullet.off_screen(self.height)
        ]

        self.enemy_bullets = [
            bullet
            for bullet in self.enemy_bullets
            if not bullet.off_screen(self.height)
        ]

        # Player bullet -> enemy collision
        remaining_player_bullets = []

        for bullet in self.player_bullets:
            bullet_hit = False

            for enemy in self.enemy_grid.alive_enemies():
                if bullet.rect().colliderect(enemy.rect()):
                    enemy.alive = False
                    self.score += 1
                    bullet_hit = True

                    # One bullet can hit only one enemy
                    break

            if not bullet_hit:
                remaining_player_bullets.append(bullet)

        self.player_bullets = remaining_player_bullets

        # Enemy bullet -> player collision
        player_hit = False

        for bullet in self.enemy_bullets:
            if bullet.rect().colliderect(self.player.rect()):
                player_hit = True
                break

        if player_hit:
            self.state = "game_over"
            return

        # Enemy reached bottom
        if self.enemy_grid.reached_bottom(self.player.y):
            self.state = "game_over"
            return

    def render(self, screen):
        # Always draw the game objects first
        screen.fill(BLACK)

        # Player
        pygame.draw.rect(
            screen,
            GREEN,
            self.player.rect()
        )

        # Enemies
        for enemy in self.enemy_grid.alive_enemies():
            pygame.draw.rect(
                screen,
                WHITE,
                enemy.rect()
            )

        # Player bullets
        for bullet in self.player_bullets:
            pygame.draw.rect(
                screen,
                WHITE,
                bullet.rect()
            )

        # Enemy bullets
        for bullet in self.enemy_bullets:
            pygame.draw.rect(
                screen,
                RED,
                bullet.rect()
            )

        # Score during gameplay
        score_text = self.font.render(
            f"Score: {self.score}",
            True,
            WHITE
        )

        screen.blit(score_text, (10, 10))

        # Game-over screen
        if self.state == "game_over":
            self.render_game_over(screen)

    def render_game_over(self, screen):
        # Dark overlay
        overlay = pygame.Surface(
            (self.width, self.height)
        )

        overlay.set_alpha(180)
        overlay.fill(BLACK)

        screen.blit(overlay, (0, 0))

        # GAME OVER
        game_over_text = self.game_over_font.render(
            "GAME OVER",
            True,
            RED
        )

        game_over_rect = game_over_text.get_rect(
            center=(self.width // 2, self.height // 2 - 80)
        )

        screen.blit(
            game_over_text,
            game_over_rect
        )

        # Final score
        score_text = self.final_score_font.render(
            f"Final Score: {self.score}",
            True,
            WHITE
        )

        score_rect = score_text.get_rect(
            center=(self.width // 2, self.height // 2)
        )

        screen.blit(
            score_text,
            score_rect
        )

        # Instruction
        instruction_text = self.instruction_font.render(
            "Press any key to continue",
            True,
            WHITE
        )

        instruction_rect = instruction_text.get_rect(
            center=(self.width // 2, self.height // 2 + 60)
        )

        screen.blit(
            instruction_text,
            instruction_rect
        )