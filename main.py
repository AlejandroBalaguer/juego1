import pygame
import random
import sys
import math

# Initialize Pygame
pygame.init()
pygame.mixer.init()  # Initialize the sound mixer

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_SPEED = 5
ENEMY_SPEED = 2
BULLET_SPEED = 7
ENEMY_BULLET_SPEED = 4
ENEMY_SHOOT_CHANCE = 0.002  # 0.2% chance per frame
ENEMY_ROWS = 5
ENEMY_COLS = 10
ENEMY_SPACING = 60
ENEMY_DROP = 30
ENEMY_MOVE_TIME = 1000  # milliseconds between enemy movements

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
DARK_BLUE = (0, 0, 128)
LIGHT_BLUE = (173, 216, 230)

# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Invaders")

# Clock for controlling frame rate
clock = pygame.time.Clock()

# Font for text
font = pygame.font.SysFont(None, 36)

# Load sounds
try:
    shoot_sound = pygame.mixer.Sound("shoot.wav")
    explosion_sound = pygame.mixer.Sound("explosion.wav")
    powerup_sound = pygame.mixer.Sound("powerup.wav")
    shield_sound = pygame.mixer.Sound("shield.wav")
    speed_sound = pygame.mixer.Sound("speed.wav")
    weapon_sound = pygame.mixer.Sound("weapon.wav")
    life_sound = pygame.mixer.Sound("life.wav")
    levelup_sound = pygame.mixer.Sound("levelup.wav")
except:
    # If sound files are missing, create dummy sound objects
    class DummySound:
        def play(self): pass
    shoot_sound = explosion_sound = powerup_sound = DummySound()
    shield_sound = speed_sound = weapon_sound = life_sound = DummySound()
    levelup_sound = DummySound()

# Star class for background
class Star:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.size = random.randint(1, 3)
        self.color = random.choice([WHITE, LIGHT_BLUE, CYAN])
        self.speed = random.uniform(0.1, 0.5)

    def update(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT:
            self.y = 0
            self.x = random.randint(0, SCREEN_WIDTH)

    def draw(self):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)

class Player:
    def __init__(self):
        self.width = 50
        self.height = 30
        self.x = SCREEN_WIDTH // 2 - self.width // 2
        self.y = SCREEN_HEIGHT - self.height - 20
        self.speed = PLAYER_SPEED
        self.color = CYAN
        self.accent_color = BLUE
        self.engine_color = ORANGE
        self.bullets = []
        self.lives = 3
        self.score = 0
        self.engine_flicker = 0
        # Power-up effects
        self.has_shield = False
        self.shield_time = 0
        self.has_speed_boost = False
        self.speed_boost_time = 0
        self.has_weapon_upgrade = False
        self.weapon_upgrade_time = 0
        self.shield_alpha = 128  # For shield transparency

    def draw(self):
        # Draw shield effect if active
        if self.has_shield:
            # Create a semi-transparent shield around the player
            shield_radius = max(self.width, self.height) + 10
            # Create a surface for the shield with per-pixel alpha
            shield_surface = pygame.Surface((shield_radius * 2, shield_radius * 2), pygame.SRCALPHA)
            # Draw the shield on the surface
            pygame.draw.circle(shield_surface, (0, 100, 255, self.shield_alpha), 
                              (shield_radius, shield_radius), shield_radius)
            # Blit the surface onto the screen
            screen.blit(shield_surface, 
                       (self.x + self.width // 2 - shield_radius, 
                        self.y + self.height // 2 - shield_radius))

        # Draw player ship body with color change if speed boost is active
        ship_color = YELLOW if self.has_speed_boost else self.color

        pygame.draw.polygon(screen, ship_color, [
            (self.x + self.width // 2, self.y - 15),  # Nose
            (self.x, self.y + self.height - 5),       # Bottom left
            (self.x + self.width, self.y + self.height - 5)  # Bottom right
        ])

        # Draw cockpit
        pygame.draw.ellipse(screen, self.accent_color, 
                           (self.x + self.width // 2 - 8, self.y, 16, 20))

        # Draw wings
        pygame.draw.polygon(screen, ship_color, [
            (self.x, self.y + self.height - 5),       # Top left
            (self.x - 15, self.y + self.height + 10), # Bottom left
            (self.x + 15, self.y + self.height - 5)   # Bottom right
        ])
        pygame.draw.polygon(screen, ship_color, [
            (self.x + self.width, self.y + self.height - 5),  # Top right
            (self.x + self.width + 15, self.y + self.height + 10), # Bottom right
            (self.x + self.width - 15, self.y + self.height - 5)   # Bottom left
        ])

        # Draw engine flames (with animation)
        self.engine_flicker = (self.engine_flicker + 1) % 6
        flame_height = 10 + self.engine_flicker

        # Bigger flames if speed boost is active
        if self.has_speed_boost:
            flame_height += 5
            flame_color = WHITE  # Hotter flame color
        else:
            flame_color = self.engine_color

        pygame.draw.polygon(screen, flame_color, [
            (self.x + 15, self.y + self.height - 5),
            (self.x + 10, self.y + self.height + flame_height),
            (self.x + 20, self.y + self.height - 5)
        ])
        pygame.draw.polygon(screen, flame_color, [
            (self.x + self.width - 15, self.y + self.height - 5),
            (self.x + self.width - 10, self.y + self.height + flame_height),
            (self.x + self.width - 20, self.y + self.height - 5)
        ])

        # Draw bullets with different color if weapon upgrade is active
        bullet_color = RED if self.has_weapon_upgrade else YELLOW
        inner_color = ORANGE if self.has_weapon_upgrade else WHITE

        for bullet in self.bullets:
            pygame.draw.circle(screen, bullet_color, (int(bullet[0]), int(bullet[1])), 3)
            pygame.draw.circle(screen, inner_color, (int(bullet[0]), int(bullet[1])), 1)

    def move(self, direction):
        if direction == "left" and self.x > 0:
            self.x -= self.speed
        if direction == "right" and self.x < SCREEN_WIDTH - self.width:
            self.x += self.speed

    def shoot(self):
        # Base bullet position
        bullet_y = self.y - 10

        if self.has_weapon_upgrade:
            # Triple shot when weapon upgrade is active
            self.bullets.append([self.x + self.width // 2 - 1.5, bullet_y])  # Center bullet
            self.bullets.append([self.x + 10, bullet_y])                     # Left bullet
            self.bullets.append([self.x + self.width - 10, bullet_y])        # Right bullet
        else:
            # Single bullet
            bullet_x = self.x + self.width // 2 - 1.5
            self.bullets.append([bullet_x, bullet_y])

    def update_bullets(self):
        # Move bullets up and remove those that go off screen
        for bullet in self.bullets[:]:
            bullet[1] -= BULLET_SPEED
            if bullet[1] < 0:
                self.bullets.remove(bullet)

    def update_power_ups(self, current_time):
        # Update power-up timers and deactivate expired power-ups

        # Shield power-up
        if self.has_shield and current_time > self.shield_time:
            self.has_shield = False

        # Speed boost power-up
        if self.has_speed_boost and current_time > self.speed_boost_time:
            self.has_speed_boost = False
            self.speed = PLAYER_SPEED  # Reset speed to normal

        # Weapon upgrade power-up
        if self.has_weapon_upgrade and current_time > self.weapon_upgrade_time:
            self.has_weapon_upgrade = False

        # Make shield pulse for visual effect
        if self.has_shield:
            self.shield_alpha = 128 + int(30 * math.sin(current_time / 200))

class Enemy:
    def __init__(self, x, y, row):
        self.width = 40
        self.height = 30
        self.x = x
        self.y = y
        self.row = row
        # Different colors based on row
        if row == 0:
            self.color = PURPLE
        elif row == 1:
            self.color = RED
        elif row == 2:
            self.color = ORANGE
        elif row == 3:
            self.color = YELLOW
        else:
            self.color = GREEN
        self.direction = 1  # 1 for right, -1 for left
        self.animation_state = 0
        self.animation_speed = 0.1

    def draw(self):
        # Animate the enemy by oscillating between states
        self.animation_state = (self.animation_state + self.animation_speed) % 2

        # Draw the main body
        pygame.draw.ellipse(screen, self.color, (self.x, self.y, self.width, self.height))

        # Draw the eyes
        eye_color = WHITE
        pygame.draw.circle(screen, eye_color, (int(self.x + 12), int(self.y + 12)), 5)
        pygame.draw.circle(screen, eye_color, (int(self.x + 28), int(self.y + 12)), 5)

        # Draw pupils (they move slightly for animation)
        pupil_offset = 2 if self.animation_state > 1 else -2
        pygame.draw.circle(screen, BLACK, (int(self.x + 12 + pupil_offset), int(self.y + 12)), 2)
        pygame.draw.circle(screen, BLACK, (int(self.x + 28 + pupil_offset), int(self.y + 12)), 2)

        # Draw tentacles (they move for animation)
        tentacle_height = 5 if self.animation_state > 1 else 8
        for i in range(3):
            pygame.draw.line(screen, self.color, 
                            (self.x + 10 + i*10, self.y + self.height),
                            (self.x + 10 + i*10, self.y + self.height + tentacle_height), 
                            3)

class PowerUp:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 20
        self.height = 20
        self.speed = 2
        # Randomly choose a power-up type
        self.type = random.choice(["speed", "weapon", "shield", "life"])
        # Set color based on type
        if self.type == "speed":
            self.color = CYAN  # Speed boost - cyan
        elif self.type == "weapon":
            self.color = RED   # Weapon upgrade - red
        elif self.type == "shield":
            self.color = BLUE  # Shield - blue
        elif self.type == "life":
            self.color = GREEN # Extra life - green
        self.pulse_size = 0
        self.pulse_direction = 1

    def update(self):
        # Move down
        self.y += self.speed

        # Pulse animation
        if self.pulse_direction == 1:
            self.pulse_size += 0.2
            if self.pulse_size >= 5:
                self.pulse_direction = -1
        else:
            self.pulse_size -= 0.2
            if self.pulse_size <= 0:
                self.pulse_direction = 1

    def draw(self):
        # Draw the power-up with a pulsing effect
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(10 + self.pulse_size))

        # Draw an icon inside based on the power-up type
        if self.type == "speed":
            # Draw lightning bolt
            pygame.draw.line(screen, WHITE, (self.x - 5, self.y - 3), (self.x + 3, self.y + 3), 2)
            pygame.draw.line(screen, WHITE, (self.x + 3, self.y + 3), (self.x - 3, self.y + 8), 2)
        elif self.type == "weapon":
            # Draw crosshair
            pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), 5, 1)
            pygame.draw.line(screen, WHITE, (self.x - 8, self.y), (self.x + 8, self.y), 1)
            pygame.draw.line(screen, WHITE, (self.x, self.y - 8), (self.x, self.y + 8), 1)
        elif self.type == "shield":
            # Draw shield icon
            pygame.draw.arc(screen, WHITE, (self.x - 5, self.y - 5, 10, 10), 0.5, 2.5, 2)
        elif self.type == "life":
            # Draw heart
            pygame.draw.circle(screen, WHITE, (int(self.x - 3), int(self.y - 2)), 3)
            pygame.draw.circle(screen, WHITE, (int(self.x + 3), int(self.y - 2)), 3)
            pygame.draw.polygon(screen, WHITE, [
                (self.x - 6, self.y - 1),
                (self.x, self.y + 5),
                (self.x + 6, self.y - 1)
            ])

class EnemyGroup:
    def __init__(self):
        self.enemies = []
        self.bullets = []
        self.explosions = []  # List to store explosion effects
        self.power_ups = []   # List to store power-ups
        self.direction = 1  # 1 for right, -1 for left
        self.drop_flag = False
        self.last_move_time = pygame.time.get_ticks()
        self.speed = ENEMY_SPEED

        # Create grid of enemies
        for row in range(ENEMY_ROWS):
            for col in range(ENEMY_COLS):
                x = 100 + col * ENEMY_SPACING
                y = 50 + row * ENEMY_SPACING
                self.enemies.append(Enemy(x, y, row))

    def draw(self):
        for enemy in self.enemies:
            enemy.draw()

        # Draw enemy bullets
        for bullet in self.bullets:
            # Draw a more interesting bullet (small red circle with a tail)
            pygame.draw.circle(screen, RED, (int(bullet[0]), int(bullet[1])), 3)
            pygame.draw.circle(screen, YELLOW, (int(bullet[0]), int(bullet[1] - 5)), 1)

        # Draw explosions
        for explosion in self.explosions[:]:
            # Each explosion is [x, y, size, lifetime]
            pygame.draw.circle(screen, ORANGE, (explosion[0], explosion[1]), explosion[2])
            pygame.draw.circle(screen, YELLOW, (explosion[0], explosion[1]), explosion[2] - 3)

            # Reduce lifetime and remove if expired
            explosion[3] -= 1
            if explosion[3] <= 0:
                self.explosions.remove(explosion)

        # Draw power-ups
        for power_up in self.power_ups:
            power_up.draw()

    def move(self):
        current_time = pygame.time.get_ticks()

        # Move enemies at regular intervals
        if current_time - self.last_move_time > ENEMY_MOVE_TIME:
            self.last_move_time = current_time

            # Check if any enemy would hit the edge
            move_down = False
            for enemy in self.enemies:
                if (enemy.x + enemy.width + self.speed > SCREEN_WIDTH and self.direction > 0) or \
                   (enemy.x - self.speed < 0 and self.direction < 0):
                    move_down = True
                    break

            # Move enemies
            for enemy in self.enemies:
                if move_down:
                    enemy.y += ENEMY_DROP
                else:
                    enemy.x += self.speed * self.direction

            # Change direction if needed
            if move_down:
                self.direction *= -1

    def shoot(self):
        # Randomly select enemies to shoot
        for enemy in self.enemies:
            if random.random() < ENEMY_SHOOT_CHANCE:
                bullet_x = enemy.x + enemy.width // 2 - 1.5
                bullet_y = enemy.y + enemy.height
                self.bullets.append([bullet_x, bullet_y])

    def update_bullets(self):
        # Move bullets down and remove those that go off screen
        for bullet in self.bullets[:]:
            bullet[1] += ENEMY_BULLET_SPEED
            if bullet[1] > SCREEN_HEIGHT:
                self.bullets.remove(bullet)

    def update_power_ups(self):
        # Update power-ups and remove those that go off screen
        for power_up in self.power_ups[:]:
            power_up.update()
            if power_up.y > SCREEN_HEIGHT:
                self.power_ups.remove(power_up)

def check_collisions(player, enemy_group, enemies_killed=None):
    # Check player bullets hitting enemies
    for bullet in player.bullets[:]:
        for enemy in enemy_group.enemies[:]:
            if (bullet[0] >= enemy.x and bullet[0] <= enemy.x + enemy.width and
                bullet[1] >= enemy.y and bullet[1] <= enemy.y + enemy.height):
                if bullet in player.bullets:
                    player.bullets.remove(bullet)

                # Create explosion effect
                explosion_x = enemy.x + enemy.width // 2
                explosion_y = enemy.y + enemy.height // 2
                explosion_size = 15
                explosion_lifetime = 15
                enemy_group.explosions.append([explosion_x, explosion_y, explosion_size, explosion_lifetime])

                # Play explosion sound
                explosion_sound.play()

                # Chance to spawn a power-up (20% probability)
                if random.random() < 0.2:
                    power_up = PowerUp(explosion_x, explosion_y)
                    enemy_group.power_ups.append(power_up)

                enemy_group.enemies.remove(enemy)
                player.score += 10

                # Increment enemies killed counter if provided
                if enemies_killed is not None:
                    enemies_killed[0] += 1

                break

    # Check enemy bullets hitting player
    for bullet in enemy_group.bullets[:]:
        if (bullet[0] >= player.x and bullet[0] <= player.x + player.width and
            bullet[1] >= player.y and bullet[1] <= player.y + player.height):
            enemy_group.bullets.remove(bullet)

            # If player has shield, don't lose a life
            if player.has_shield:
                # Create a shield impact effect
                explosion_x = bullet[0]
                explosion_y = bullet[1]
                explosion_size = 10
                explosion_lifetime = 10
                enemy_group.explosions.append([explosion_x, explosion_y, explosion_size, explosion_lifetime])
            else:
                player.lives -= 1
            break

    # Check player collecting power-ups
    current_time = pygame.time.get_ticks()
    power_up_duration = 10000  # 10 seconds

    for power_up in enemy_group.power_ups[:]:
        # Check if player collides with power-up
        if (power_up.x >= player.x and power_up.x <= player.x + player.width and
            power_up.y >= player.y and power_up.y <= player.y + player.height):

            # Apply power-up effect based on type
            if power_up.type == "speed":
                player.has_speed_boost = True
                player.speed_boost_time = current_time + power_up_duration
                player.speed = PLAYER_SPEED * 1.5  # 50% speed boost
                speed_sound.play()

            elif power_up.type == "weapon":
                player.has_weapon_upgrade = True
                player.weapon_upgrade_time = current_time + power_up_duration
                weapon_sound.play()

            elif power_up.type == "shield":
                player.has_shield = True
                player.shield_time = current_time + power_up_duration
                shield_sound.play()

            elif power_up.type == "life":
                player.lives += 1  # Extra life
                life_sound.play()

            # Play general power-up collection sound
            powerup_sound.play()

            # Create a collection effect
            explosion_x = power_up.x
            explosion_y = power_up.y
            explosion_size = 15
            explosion_lifetime = 10
            enemy_group.explosions.append([explosion_x, explosion_y, explosion_size, explosion_lifetime])

            # Remove the collected power-up
            enemy_group.power_ups.remove(power_up)
            break

    # Check if enemies reached the player's level
    for enemy in enemy_group.enemies:
        if enemy.y + enemy.height >= player.y:
            return True  # Game over

    return False  # Game continues

def draw_text(text, color, x, y):
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (x, y))

def game_over_screen(player):
    screen.fill(BLACK)
    draw_text("GAME OVER", RED, SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50)
    draw_text(f"Final Score: {player.score}", WHITE, SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2)
    draw_text("Press SPACE to play again", WHITE, SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 50)
    draw_text("Press ESC to quit", WHITE, SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 100)
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    waiting = False
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
        clock.tick(30)

def pause_game():
    paused = True

    # Display pause message
    screen.fill(BLACK)
    draw_text("PAUSED", WHITE, SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT // 2 - 30)
    draw_text("Press P to continue", WHITE, SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 + 30)
    pygame.display.flip()

    while paused:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    paused = False
        clock.tick(30)

def main():
    # Try to load and play background music
    try:
        pygame.mixer.music.load("background_music.mp3")
        pygame.mixer.music.set_volume(0.5)  # Set volume to 50%
        pygame.mixer.music.play(-1)  # -1 means loop indefinitely
    except:
        print("Background music file not found. Continuing without music.")

    player = Player()
    enemy_group = EnemyGroup()

    # Create starfield background
    stars = [Star() for _ in range(100)]

    # Game state
    game_over = False
    paused = False
    last_shot_time = 0
    shot_cooldown = 300  # milliseconds
    current_level = 1
    enemies_killed = 0
    enemies_to_next_level = 20  # Number of enemies to kill to advance to next level

    # Main game loop
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not game_over:
                    current_time = pygame.time.get_ticks()
                    if current_time - last_shot_time > shot_cooldown:
                        player.shoot()
                        shoot_sound.play()
                        last_shot_time = current_time

                # Pause game when P is pressed
                if event.key == pygame.K_p:
                    pause_game()

        if game_over:
            game_over_screen(player)
            # Reset game
            player = Player()
            enemy_group = EnemyGroup()
            game_over = False
            continue

        # Get keyboard state for continuous movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player.move("left")
        if keys[pygame.K_RIGHT]:
            player.move("right")

        # Update game state
        current_time = pygame.time.get_ticks()
        player.update_bullets()
        player.update_power_ups(current_time)
        enemy_group.move()
        enemy_group.shoot()
        enemy_group.update_bullets()
        enemy_group.update_power_ups()

        # Check collisions
        # Pass enemies_killed as a list to allow it to be modified by reference
        enemies_killed_ref = [enemies_killed]
        game_over = check_collisions(player, enemy_group, enemies_killed_ref)
        enemies_killed = enemies_killed_ref[0]

        # Check if player should advance to next level
        if enemies_killed >= enemies_to_next_level:
            current_level += 1
            enemies_killed = 0
            # Create a new wave of enemies with increased difficulty
            enemy_group = EnemyGroup()
            # Increase difficulty based on level
            enemy_group.speed += 0.2 * current_level
            # Increase enemy shoot chance with level (cap at a reasonable value)
            global ENEMY_SHOOT_CHANCE
            ENEMY_SHOOT_CHANCE = min(0.01, 0.002 + 0.001 * current_level)
            # Play level up sound
            levelup_sound.play()

            # Create a flash effect
            flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flash_surface.fill(YELLOW)
            for alpha in range(0, 128, 8):  # Fade in
                flash_surface.set_alpha(alpha)
                screen.blit(flash_surface, (0, 0))
                pygame.display.flip()
                pygame.time.delay(20)

            # Display level up message
            screen.fill(BLACK)
            draw_text(f"LEVEL {current_level}!", YELLOW, SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT // 2)
            draw_text("Get ready for more enemies!", WHITE, SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 50)
            pygame.display.flip()
            pygame.time.delay(1500)  # Pause for 1.5 seconds to show level up message

            for alpha in range(128, 0, -8):  # Fade out
                flash_surface.set_alpha(alpha)
                screen.fill(BLACK)
                draw_text(f"LEVEL {current_level}!", YELLOW, SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT // 2)
                draw_text("Get ready for more enemies!", WHITE, SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 50)
                screen.blit(flash_surface, (0, 0))
                pygame.display.flip()
                pygame.time.delay(20)

        # Check if player lost all lives
        if player.lives <= 0:
            game_over = True

        # Check if all enemies are destroyed
        if len(enemy_group.enemies) == 0:
            # Create a new wave of enemies
            enemy_group = EnemyGroup()
            # Increase difficulty
            enemy_group.speed += 0.5

        # Draw everything
        screen.fill(BLACK)

        # Draw starfield background
        for star in stars:
            star.update()
            star.draw()

        player.draw()
        enemy_group.draw()

        # Draw HUD
        draw_text(f"Score: {player.score}", WHITE, 10, 10)
        draw_text(f"Lives: {player.lives}", WHITE, SCREEN_WIDTH - 100, 10)
        draw_text(f"Level: {current_level}", YELLOW, SCREEN_WIDTH // 2 - 40, 10)

        # Draw level progress bar
        progress_width = 200
        progress_height = 10
        progress_x = SCREEN_WIDTH // 2 - progress_width // 2
        progress_y = 40
        progress_fill = int((enemies_killed / enemies_to_next_level) * progress_width)

        # Draw progress bar background
        pygame.draw.rect(screen, DARK_BLUE, (progress_x, progress_y, progress_width, progress_height))
        # Draw progress bar fill
        pygame.draw.rect(screen, GREEN, (progress_x, progress_y, progress_fill, progress_height))
        # Draw progress bar border
        pygame.draw.rect(screen, WHITE, (progress_x, progress_y, progress_width, progress_height), 1)

        # Draw power-up indicators
        if player.has_shield:
            remaining = max(0, (player.shield_time - current_time) / 1000)
            draw_text(f"Shield: {remaining:.1f}s", BLUE, 10, 70)

        if player.has_speed_boost:
            remaining = max(0, (player.speed_boost_time - current_time) / 1000)
            draw_text(f"Speed: {remaining:.1f}s", CYAN, 10, 100)

        if player.has_weapon_upgrade:
            remaining = max(0, (player.weapon_upgrade_time - current_time) / 1000)
            draw_text(f"Weapon: {remaining:.1f}s", RED, 10, 130)

        # Update display
        pygame.display.flip()

        # Cap the frame rate
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
