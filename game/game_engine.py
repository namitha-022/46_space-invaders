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

        # Difficulty settings
        self.difficulties = {
            "easy": {
                "enemy_speed": 1.0,
                "enemy_fire_chance": 0.005
            },
            "medium": {
                "enemy_speed": 1.5,
                "enemy_fire_chance": 0.01
            },
            "hard": {
                "enemy_speed": 2.5,
                "enemy_fire_chance": 0.02
            }
        }

        self.difficulty = "medium"

        # Create the initial game
        self.reset_game()

        # Fonts
        self.font = pygame.font.SysFont("Arial", 30)
        self.game_over_font = pygame.font.SysFont("Arial", 60)
        self.final_score_font = pygame.font.SysFont("Arial", 36)
        self.instruction_font = pygame.font.SysFont("Arial", 26)

    def reset_game(self):
        """
        Completely reset the game using the selected difficulty.
        """

        settings = self.difficulties[self.difficulty]

        # Reset player
        self.player = Player(
            self.width // 2 - 20,
            self.height - 50,
            40,
            20
        )

        # Reset enemies
        self.enemy_grid = EnemyGrid(
            self.width,
            speed=settings["enemy_speed"]
        )

        # Reset bullets
        self.player_bullets = []
        self.enemy_bullets = []

        # Reset shooting
        self._shoot_cooldown = 0

        # Set enemy firing rate
        self.enemy_fire_chance = settings["enemy_fire_chance"]

        # Reset score
        self.score = 0

        # Start playing
        self.state = "playing"

    def start_new_game(self, difficulty):
        """
        Start a completely new game with the selected difficulty.
        """

        self.difficulty = difficulty
        self.reset_game()

    def handle_event(self, event):
        # Game-over controls
        if self.state == "game_over":
            if event.type == pygame.KEYDOWN:

                # Easy
                if event.key == pygame.K_1:
                    self.start_new_game("easy")

                # Medium
                elif event.key == pygame.K_2:
                    self.start_new_game("medium")

                # Hard
                elif event.key == pygame.K_3:
                    self.start_new_game("hard")

                # Quit
                elif event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                    pygame.event.post(
                        pygame.event.Event(pygame.QUIT)
                    )

            return

        # Normal gameplay controls
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
        # Do not allow movement during game over
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
        # Stop updating after game over
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

        # Move player bullets
        for bullet in self.player_bullets:
            bullet.move()

        # Move enemy bullets
        for bullet in self.enemy_bullets:
            bullet.move()

        # Remove off-screen player bullets
        self.player_bullets = [
            bullet
            for bullet in self.player_bullets
            if not bullet.off_screen(self.height)
        ]

        # Remove off-screen enemy bullets
        self.enemy_bullets = [
            bullet
            for bullet in self.enemy_bullets
            if not bullet.off_screen(self.height)
        ]

        # --------------------------------------------------
        # PLAYER BULLET -> ENEMY COLLISION
        # --------------------------------------------------

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

        # Replace list after iteration
        self.player_bullets = remaining_player_bullets

        # --------------------------------------------------
        # ENEMY BULLET -> PLAYER COLLISION
        # --------------------------------------------------

        for bullet in self.enemy_bullets:

            if bullet.rect().colliderect(
                self.player.rect()
            ):
                self.state = "game_over"
                return

        # --------------------------------------------------
        # ENEMIES REACHED BOTTOM
        # --------------------------------------------------

        if self.enemy_grid.reached_bottom(
            self.player.y
        ):
            self.state = "game_over"
            return

    def render(self, screen):
        screen.fill(BLACK)

        # --------------------------------------------------
        # GAMEPLAY SCREEN
        # --------------------------------------------------

        if self.state == "playing":

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

            # Score
            score_text = self.font.render(
                f"Score: {self.score}",
                True,
                WHITE
            )

            screen.blit(
                score_text,
                (10, 10)
            )

        # --------------------------------------------------
        # GAME OVER SCREEN
        # --------------------------------------------------

        elif self.state == "game_over":

            self.render_game_over(screen)

    def render_game_over(self, screen):

        # Dark background
        screen.fill(BLACK)

        # GAME OVER
        game_over_text = self.game_over_font.render(
            "GAME OVER",
            True,
            RED
        )

        game_over_rect = game_over_text.get_rect(
            center=(
                self.width // 2,
                120
            )
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
            center=(
                self.width // 2,
                200
            )
        )

        screen.blit(
            score_text,
            score_rect
        )

        # Difficulty
        difficulty_text = self.instruction_font.render(
            f"Difficulty: {self.difficulty.capitalize()}",
            True,
            WHITE
        )

        difficulty_rect = difficulty_text.get_rect(
            center=(
                self.width // 2,
                250
            )
        )

        screen.blit(
            difficulty_text,
            difficulty_rect
        )

        # Replay options
        easy_text = self.instruction_font.render(
            "1 - Easy",
            True,
            WHITE
        )

        medium_text = self.instruction_font.render(
            "2 - Medium",
            True,
            WHITE
        )

        hard_text = self.instruction_font.render(
            "3 - Hard",
            True,
            WHITE
        )

        quit_text = self.instruction_font.render(
            "Q / ESC - Quit",
            True,
            WHITE
        )

        # Draw options
        screen.blit(
            easy_text,
            easy_text.get_rect(
                center=(self.width // 2, 330)
            )
        )

        screen.blit(
            medium_text,
            medium_text.get_rect(
                center=(self.width // 2, 380)
            )
        )

        screen.blit(
            hard_text,
            hard_text.get_rect(
                center=(self.width // 2, 430)
            )
        )

        screen.blit(
            quit_text,
            quit_text.get_rect(
                center=(self.width // 2, 500)
            )
        )