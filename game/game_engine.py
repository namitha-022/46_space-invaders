import pygame
import random
import math
from array import array

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

        # Create sounds
        self.create_sounds()

        # Create initial game
        self.reset_game()

        # Fonts
        self.font = pygame.font.SysFont("Arial", 30)
        self.game_over_font = pygame.font.SysFont("Arial", 60)
        self.final_score_font = pygame.font.SysFont("Arial", 36)
        self.instruction_font = pygame.font.SysFont("Arial", 26)

    # --------------------------------------------------
    # SOUND
    # --------------------------------------------------

    def create_beep(self, frequency, duration, volume=0.4):
        """
        Generate a simple sine-wave beep in memory.
        No external sound file is required.
        """

        sample_rate = 44100
        samples = int(sample_rate * duration)

        buffer = array("h")

        for i in range(samples):
            time = i / sample_rate

            # Sine wave
            value = math.sin(
                2 * math.pi * frequency * time
            )

            # Fade out at the end to avoid clicking
            fade = 1.0

            fade_samples = int(sample_rate * 0.01)

            if i < fade_samples:
                fade = i / fade_samples

            elif i > samples - fade_samples:
                fade = (samples - i) / fade_samples

            sample = int(
                value * 32767 * volume * fade
            )

            buffer.append(sample)

        return pygame.mixer.Sound(buffer=buffer.tobytes())

    def create_sounds(self):
        """
        Create all game sounds in memory.
        """

        # Fire: short high-pitched beep
        self.fire_sound = self.create_beep(
            frequency=700,
            duration=0.08,
            volume=0.35
        )

        # Enemy destroyed: slightly lower beep
        self.enemy_destroyed_sound = self.create_beep(
            frequency=350,
            duration=0.12,
            volume=0.45
        )

        # Game over: longer low beep
        self.game_over_sound = self.create_beep(
            frequency=180,
            duration=0.5,
            volume=0.5
        )

    # --------------------------------------------------
    # GAME RESET
    # --------------------------------------------------

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

        # Reset shooting cooldown
        self._shoot_cooldown = 0

        # Reset enemy fire rate
        self.enemy_fire_chance = settings[
            "enemy_fire_chance"
        ]

        # Reset score
        self.score = 0

        # Reset state
        self.state = "playing"

        # Allow game-over sound to play again
        self.game_over_sound_played = False

    def start_new_game(self, difficulty):
        """
        Start a completely new game with the selected difficulty.
        """

        self.difficulty = difficulty
        self.reset_game()

    # --------------------------------------------------
    # INPUT
    # --------------------------------------------------

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
                elif (
                    event.key == pygame.K_q
                    or event.key == pygame.K_ESCAPE
                ):
                    pygame.event.post(
                        pygame.event.Event(
                            pygame.QUIT
                        )
                    )

            return

        # Normal gameplay controls
        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_SPACE:

                if self._shoot_cooldown <= 0:

                    bullet_x = (
                        self.player.center_x() - 2
                    )

                    self.player_bullets.append(
                        Bullet(
                            bullet_x,
                            self.player.y,
                            direction=-1
                        )
                    )

                    # Play firing sound
                    self.fire_sound.play()

                    self._shoot_cooldown = 15

    def handle_input(self):

        # No movement after game over
        if self.state == "game_over":
            return

        keys = pygame.key.get_pressed()

        if (
            keys[pygame.K_LEFT]
            or keys[pygame.K_a]
        ):
            self.player.move(
                -self.player.speed,
                self.width
            )

        if (
            keys[pygame.K_RIGHT]
            or keys[pygame.K_d]
        ):
            self.player.move(
                self.player.speed,
                self.width
            )

    # --------------------------------------------------
    # UPDATE
    # --------------------------------------------------

    def update(self):

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

                bullet_x = (
                    enemy.x + enemy.width // 2
                )

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

                if bullet.rect().colliderect(
                    enemy.rect()
                ):

                    enemy.alive = False
                    self.score += 1
                    bullet_hit = True

                    # Play enemy destroyed sound
                    self.enemy_destroyed_sound.play()

                    # One bullet hits only one enemy
                    break

            if not bullet_hit:
                remaining_player_bullets.append(
                    bullet
                )

        # Replace list after iteration
        self.player_bullets = (
            remaining_player_bullets
        )

        # --------------------------------------------------
        # ENEMY BULLET -> PLAYER COLLISION
        # --------------------------------------------------

        for bullet in self.enemy_bullets:

            if bullet.rect().colliderect(
                self.player.rect()
            ):
                self.end_game()
                return

        # --------------------------------------------------
        # ENEMIES REACHED BOTTOM
        # --------------------------------------------------

        if self.enemy_grid.reached_bottom(
            self.player.y
        ):
            self.end_game()
            return

    # --------------------------------------------------
    # GAME OVER
    # --------------------------------------------------

    def end_game(self):
        """
        Switch to game-over state and play the
        game-over sound exactly once.
        """

        if self.state != "game_over":

            self.state = "game_over"

            if not self.game_over_sound_played:

                self.game_over_sound.play()

                self.game_over_sound_played = True

    # --------------------------------------------------
    # RENDER
    # --------------------------------------------------

    def render(self, screen):

        screen.fill(BLACK)

        if self.state == "playing":

            # Player
            pygame.draw.rect(
                screen,
                GREEN,
                self.player.rect()
            )

            # Enemies
            for enemy in (
                self.enemy_grid.alive_enemies()
            ):
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

        elif self.state == "game_over":

            self.render_game_over(screen)

    def render_game_over(self, screen):

        screen.fill(BLACK)

        # GAME OVER
        game_over_text = (
            self.game_over_font.render(
                "GAME OVER",
                True,
                RED
            )
        )

        screen.blit(
            game_over_text,
            game_over_text.get_rect(
                center=(
                    self.width // 2,
                    120
                )
            )
        )

        # Final score
        score_text = (
            self.final_score_font.render(
                f"Final Score: {self.score}",
                True,
                WHITE
            )
        )

        screen.blit(
            score_text,
            score_text.get_rect(
                center=(
                    self.width // 2,
                    200
                )
            )
        )

        # Difficulty
        difficulty_text = (
            self.instruction_font.render(
                f"Difficulty: "
                f"{self.difficulty.capitalize()}",
                True,
                WHITE
            )
        )

        screen.blit(
            difficulty_text,
            difficulty_text.get_rect(
                center=(
                    self.width // 2,
                    250
                )
            )
        )

        # Options
        options = [
            ("1 - Easy", 330),
            ("2 - Medium", 380),
            ("3 - Hard", 430),
            ("Q / ESC - Quit", 500)
        ]

        for text, y in options:

            option_text = (
                self.instruction_font.render(
                    text,
                    True,
                    WHITE
                )
            )

            screen.blit(
                option_text,
                option_text.get_rect(
                    center=(
                        self.width // 2,
                        y
                    )
                )
            )