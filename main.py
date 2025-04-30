import pygame
import random
import sys
import math

# Initialize Pygame
pygame.init()
pygame.mixer.init()  # Initialize the sound mixer

# Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
PLAYER_SPEED = 8
ENEMY_SPEED = 3
BULLET_SPEED = 10
ENEMY_BULLET_SPEED = 5
ENEMY_SHOOT_CHANCE = 0.001  # 0.1% chance per frame
ENEMY_ROWS = 5
ENEMY_COLS = 10
ENEMY_SPACING = 80
ENEMY_DROP = 40
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
        self.width = 80
        self.height = 50
        self.x = SCREEN_WIDTH // 2 - self.width // 2
        self.y = SCREEN_HEIGHT - self.height - 30
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
        # Visual effects
        self.thruster_particles = []  # For engine particle effects

    def draw(self):
        # Draw thruster particles
        for particle in self.thruster_particles[:]:
            # Each particle is [x, y, size, lifetime, color]
            pygame.draw.circle(screen, particle[4], (int(particle[0]), int(particle[1])), int(particle[2]))
            # Reduce size and lifetime
            particle[2] -= 0.2
            particle[3] -= 1
            if particle[3] <= 0 or particle[2] <= 0:
                self.thruster_particles.remove(particle)

        # Draw shield effect if active
        if self.has_shield:
            # Create a semi-transparent shield around the player
            shield_radius = max(self.width, self.height) + 15
            # Create a surface for the shield with per-pixel alpha
            shield_surface = pygame.Surface((shield_radius * 2, shield_radius * 2), pygame.SRCALPHA)
            # Draw the shield on the surface with gradient effect
            for r in range(shield_radius, shield_radius - 5, -1):
                alpha = self.shield_alpha - (shield_radius - r) * 10
                pygame.draw.circle(shield_surface, (0, 100, 255, alpha), 
                                  (shield_radius, shield_radius), r, 2)
            # Blit the surface onto the screen
            screen.blit(shield_surface, 
                       (self.x + self.width // 2 - shield_radius, 
                        self.y + self.height // 2 - shield_radius))

        # Draw player ship body with color change if speed boost is active
        ship_color = YELLOW if self.has_speed_boost else self.color
        highlight_color = WHITE if self.has_speed_boost else LIGHT_BLUE

        # Draw main hull
        pygame.draw.polygon(screen, ship_color, [
            (self.x + self.width // 2, self.y - 20),  # Nose
            (self.x, self.y + self.height - 10),      # Bottom left
            (self.x + self.width, self.y + self.height - 10)  # Bottom right
        ])

        # Draw hull highlight
        pygame.draw.polygon(screen, highlight_color, [
            (self.x + self.width // 2, self.y - 20),  # Nose
            (self.x + self.width // 2 - 10, self.y + 10),  # Left middle
            (self.x + self.width // 2 + 10, self.y + 10)   # Right middle
        ], 1)

        # Draw cockpit (more detailed)
        pygame.draw.ellipse(screen, self.accent_color, 
                           (self.x + self.width // 2 - 12, self.y, 24, 30))
        # Cockpit glass reflection
        pygame.draw.ellipse(screen, highlight_color, 
                           (self.x + self.width // 2 - 8, self.y + 5, 16, 10), 1)

        # Draw wings (more detailed)
        # Left wing
        pygame.draw.polygon(screen, ship_color, [
            (self.x, self.y + self.height - 10),       # Top left
            (self.x - 25, self.y + self.height + 15),  # Bottom left
            (self.x + 20, self.y + self.height - 10)   # Bottom right
        ])
        # Left wing detail
        pygame.draw.line(screen, highlight_color, 
                        (self.x, self.y + self.height - 5),
                        (self.x - 15, self.y + self.height + 10), 2)

        # Right wing
        pygame.draw.polygon(screen, ship_color, [
            (self.x + self.width, self.y + self.height - 10),  # Top right
            (self.x + self.width + 25, self.y + self.height + 15), # Bottom right
            (self.x + self.width - 20, self.y + self.height - 10)   # Bottom left
        ])
        # Right wing detail
        pygame.draw.line(screen, highlight_color, 
                        (self.x + self.width, self.y + self.height - 5),
                        (self.x + self.width + 15, self.y + self.height + 10), 2)

        # Draw engine flames (with enhanced animation)
        self.engine_flicker = (self.engine_flicker + 1) % 8
        flame_height = 15 + self.engine_flicker

        # Bigger flames if speed boost is active
        if self.has_speed_boost:
            flame_height += 10
            flame_color = WHITE  # Hotter flame color
            inner_flame_color = LIGHT_BLUE
        else:
            flame_color = self.engine_color
            inner_flame_color = YELLOW

        # Left engine
        pygame.draw.polygon(screen, flame_color, [
            (self.x + 20, self.y + self.height - 10),
            (self.x + 10, self.y + self.height + flame_height),
            (self.x + 30, self.y + self.height - 10)
        ])
        # Inner flame
        pygame.draw.polygon(screen, inner_flame_color, [
            (self.x + 20, self.y + self.height - 5),
            (self.x + 15, self.y + self.height + flame_height - 10),
            (self.x + 25, self.y + self.height - 5)
        ])

        # Right engine
        pygame.draw.polygon(screen, flame_color, [
            (self.x + self.width - 20, self.y + self.height - 10),
            (self.x + self.width - 10, self.y + self.height + flame_height),
            (self.x + self.width - 30, self.y + self.height - 10)
        ])
        # Inner flame
        pygame.draw.polygon(screen, inner_flame_color, [
            (self.x + self.width - 20, self.y + self.height - 5),
            (self.x + self.width - 15, self.y + self.height + flame_height - 10),
            (self.x + self.width - 25, self.y + self.height - 5)
        ])

        # Add thruster particles
        if random.random() < 0.3:  # 30% chance each frame
            # Left thruster
            particle_x = self.x + 20 + random.uniform(-5, 5)
            particle_y = self.y + self.height + random.uniform(0, flame_height)
            particle_size = random.uniform(1.5, 3)
            particle_lifetime = random.randint(10, 20)
            particle_color = random.choice([ORANGE, YELLOW, RED])
            self.thruster_particles.append([particle_x, particle_y, particle_size, particle_lifetime, particle_color])

            # Right thruster
            particle_x = self.x + self.width - 20 + random.uniform(-5, 5)
            particle_y = self.y + self.height + random.uniform(0, flame_height)
            particle_size = random.uniform(1.5, 3)
            particle_lifetime = random.randint(10, 20)
            particle_color = random.choice([ORANGE, YELLOW, RED])
            self.thruster_particles.append([particle_x, particle_y, particle_size, particle_lifetime, particle_color])

        # Draw bullets with different color if weapon upgrade is active
        bullet_color = RED if self.has_weapon_upgrade else YELLOW
        inner_color = ORANGE if self.has_weapon_upgrade else WHITE
        glow_color = (255, 100, 100, 100) if self.has_weapon_upgrade else (255, 255, 100, 100)

        for bullet in self.bullets:
            # Draw bullet glow effect
            bullet_surface = pygame.Surface((14, 14), pygame.SRCALPHA)
            pygame.draw.circle(bullet_surface, glow_color, (7, 7), 6)
            screen.blit(bullet_surface, (int(bullet[0]) - 7, int(bullet[1]) - 7))

            # Draw main bullet
            pygame.draw.circle(screen, bullet_color, (int(bullet[0]), int(bullet[1])), 4)
            pygame.draw.circle(screen, inner_color, (int(bullet[0]), int(bullet[1])), 2)

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
        self.width = 60
        self.height = 45
        self.x = x
        self.y = y
        self.row = row
        # Different colors based on row
        if row == 0:
            self.color = PURPLE
            self.glow_color = (180, 100, 255)  # Light purple glow
        elif row == 1:
            self.color = RED
            self.glow_color = (255, 100, 100)  # Light red glow
        elif row == 2:
            self.color = ORANGE
            self.glow_color = (255, 180, 100)  # Light orange glow
        elif row == 3:
            self.color = YELLOW
            self.glow_color = (255, 255, 100)  # Light yellow glow
        else:
            self.color = GREEN
            self.glow_color = (100, 255, 100)  # Light green glow

        self.direction = 1  # 1 for right, -1 for left
        self.animation_state = 0
        self.animation_speed = 0.1
        self.pulse_size = 0
        self.pulse_direction = 1
        self.tentacle_particles = []  # For tentacle particle effects

    def draw(self):
        # Animate the enemy by oscillating between states
        self.animation_state = (self.animation_state + self.animation_speed) % 2

        # Pulse animation for body size
        if self.pulse_direction == 1:
            self.pulse_size += 0.05
            if self.pulse_size >= 1:
                self.pulse_direction = -1
        else:
            self.pulse_size -= 0.05
            if self.pulse_size <= -1:
                self.pulse_direction = 1

        pulse_width = self.width + self.pulse_size * 2
        pulse_height = self.height + self.pulse_size * 2

        # Draw glow effect
        glow_surface = pygame.Surface((int(pulse_width + 20), int(pulse_height + 20)), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surface, (*self.glow_color, 100), 
                           (10, 10, int(pulse_width), int(pulse_height)))
        screen.blit(glow_surface, (int(self.x - 10), int(self.y - 10)))

        # Draw the main body
        pygame.draw.ellipse(screen, self.color, 
                           (int(self.x), int(self.y), int(pulse_width), int(pulse_height)))

        # Draw body pattern/texture
        pattern_color = tuple(min(255, c + 50) for c in self.color)
        for i in range(3):
            pygame.draw.ellipse(screen, pattern_color, 
                               (int(self.x + pulse_width/4 + i*10), 
                                int(self.y + pulse_height/3), 
                                int(pulse_width/6), int(pulse_height/4)), 
                               1)

        # Draw the eyes (larger and more detailed)
        eye_color = WHITE
        eye_size = 8
        left_eye_x = int(self.x + pulse_width/4)
        right_eye_x = int(self.x + 3*pulse_width/4)
        eye_y = int(self.y + pulse_height/3)

        # Eye whites
        pygame.draw.circle(screen, eye_color, (left_eye_x, eye_y), eye_size)
        pygame.draw.circle(screen, eye_color, (right_eye_x, eye_y), eye_size)

        # Eye highlights
        pygame.draw.circle(screen, (200, 200, 255), 
                          (left_eye_x - 2, eye_y - 2), 2)
        pygame.draw.circle(screen, (200, 200, 255), 
                          (right_eye_x - 2, eye_y - 2), 2)

        # Draw pupils (they move for animation)
        pupil_offset = 3 * math.sin(self.animation_state * math.pi)
        pupil_size = 3
        pygame.draw.circle(screen, BLACK, 
                          (int(left_eye_x + pupil_offset), eye_y), pupil_size)
        pygame.draw.circle(screen, BLACK, 
                          (int(right_eye_x + pupil_offset), eye_y), pupil_size)

        # Draw tentacles with improved animation
        tentacle_count = 5
        tentacle_spacing = pulse_width / (tentacle_count + 1)
        tentacle_base_height = 8 + 4 * math.sin(self.animation_state * math.pi * 2)

        for i in range(tentacle_count):
            # Calculate tentacle position with wave effect
            x_pos = self.x + (i + 1) * tentacle_spacing
            wave_offset = 3 * math.sin(self.animation_state * math.pi * 2 + i)

            # Draw main tentacle
            tentacle_height = tentacle_base_height + i % 3 * 2
            pygame.draw.line(screen, self.color, 
                            (x_pos, self.y + pulse_height),
                            (x_pos + wave_offset, self.y + pulse_height + tentacle_height), 
                            4)

            # Draw tentacle suction cup
            pygame.draw.circle(screen, pattern_color, 
                              (int(x_pos + wave_offset), 
                               int(self.y + pulse_height + tentacle_height)), 
                              3)

            # Add tentacle particles occasionally
            if random.random() < 0.02:  # 2% chance per tentacle per frame
                particle_x = x_pos + wave_offset
                particle_y = self.y + pulse_height + tentacle_height
                particle_size = random.uniform(1, 2)
                particle_lifetime = random.randint(5, 15)
                particle_color = self.glow_color
                self.tentacle_particles.append([particle_x, particle_y, particle_size, particle_lifetime, particle_color])

        # Draw tentacle particles
        for particle in self.tentacle_particles[:]:
            # Each particle is [x, y, size, lifetime, color]
            pygame.draw.circle(screen, particle[4], (int(particle[0]), int(particle[1])), int(particle[2]))
            # Move particle down slightly
            particle[1] += 0.5
            # Reduce size and lifetime
            particle[2] -= 0.1
            particle[3] -= 1
            if particle[3] <= 0 or particle[2] <= 0:
                self.tentacle_particles.remove(particle)

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

        # Calculate total width and height of enemy grid
        total_width = ENEMY_COLS * ENEMY_SPACING
        total_height = ENEMY_ROWS * ENEMY_SPACING

        # Calculate starting positions to center the grid both horizontally and vertically
        start_x = (SCREEN_WIDTH - total_width) // 2
        start_y = (SCREEN_HEIGHT - total_height) // 3  # Position in the top third of the screen

        # Create grid of enemies
        for row in range(ENEMY_ROWS):
            for col in range(ENEMY_COLS):
                x = start_x + col * ENEMY_SPACING
                y = start_y + row * ENEMY_SPACING
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
        bullet_hit = False
        for enemy in enemy_group.enemies[:]:
            if (bullet[0] >= enemy.x and bullet[0] <= enemy.x + enemy.width and
                bullet[1] >= enemy.y and bullet[1] <= enemy.y + enemy.height):
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

                # Remove enemy and update score
                enemy_group.enemies.remove(enemy)
                player.score += 10

                # Increment enemies killed counter if provided
                if enemies_killed is not None:
                    enemies_killed[0] += 1

                bullet_hit = True
                break

        # Remove bullet if it hit an enemy
        if bullet_hit and bullet in player.bullets:
            player.bullets.remove(bullet)

    # Check enemy bullets hitting player
    for bullet in enemy_group.bullets[:]:
        if (bullet[0] >= player.x and bullet[0] <= player.x + player.width and
            bullet[1] >= player.y and bullet[1] <= player.y + player.height):
            # Remove the bullet
            if bullet in enemy_group.bullets:
                enemy_group.bullets.remove(bullet)

            # Create impact effect at bullet position
            explosion_x = bullet[0]
            explosion_y = bullet[1]

            # If player has shield, don't lose a life
            if player.has_shield:
                # Create a shield impact effect (blue)
                explosion_size = 10
                explosion_lifetime = 10
                enemy_group.explosions.append([explosion_x, explosion_y, explosion_size, explosion_lifetime])
                # Play shield impact sound
                shield_sound.play()
            else:
                # Create a hit effect (red)
                explosion_size = 15
                explosion_lifetime = 15
                enemy_group.explosions.append([explosion_x, explosion_y, explosion_size, explosion_lifetime])
                # Reduce player lives
                player.lives -= 1
                # Play explosion sound
                explosion_sound.play()

                # Create a screen flash effect when player is hit
                flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                flash_surface.fill(RED)
                flash_surface.set_alpha(100)  # Semi-transparent
                screen.blit(flash_surface, (0, 0))
                pygame.display.flip()
                pygame.time.delay(30)  # Brief flash
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
    # Create starfield background for game over screen
    stars = [Star() for _ in range(150)]  # More stars for dramatic effect

    # Create explosion particles at player position
    explosion_particles = []
    for _ in range(100):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1, 5)
        size = random.uniform(1, 4)
        lifetime = random.randint(30, 90)
        color = random.choice([RED, ORANGE, YELLOW, WHITE])
        particle = {
            'x': SCREEN_WIDTH // 2,
            'y': SCREEN_HEIGHT - 100,
            'dx': math.cos(angle) * speed,
            'dy': math.sin(angle) * speed,
            'size': size,
            'lifetime': lifetime,
            'color': color
        }
        explosion_particles.append(particle)

    waiting = True
    return_to_menu = False
    start_time = pygame.time.get_ticks()

    # For pulsating text effect
    pulse_value = 0
    pulse_direction = 1

    while waiting:
        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - start_time

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    waiting = False
                elif event.key == pygame.K_m:
                    waiting = False
                    return_to_menu = True
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        # Update pulsating effect
        pulse_value += 0.05 * pulse_direction
        if pulse_value >= 1.0:
            pulse_direction = -1
        elif pulse_value <= 0.0:
            pulse_direction = 1

        # Calculate pulsating size and color
        pulse_size = int(50 + 10 * pulse_value)
        pulse_color = (255, int(50 + 150 * pulse_value), int(50 * pulse_value))

        # Draw background
        screen.fill(BLACK)

        # Update and draw stars with parallax effect
        for star in stars:
            star.update()
            star.draw()

        # Update and draw explosion particles
        for particle in explosion_particles[:]:
            particle['x'] += particle['dx']
            particle['y'] += particle['dy']
            particle['lifetime'] -= 1
            particle['size'] -= 0.03

            if particle['lifetime'] <= 0 or particle['size'] <= 0:
                explosion_particles.remove(particle)
            else:
                pygame.draw.circle(screen, particle['color'], 
                                  (int(particle['x']), int(particle['y'])), 
                                  int(particle['size']))

        # Draw game over text with pulsating effect
        title_font = pygame.font.SysFont(None, pulse_size)
        title_text = title_font.render("GAME OVER", True, pulse_color)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 70))
        screen.blit(title_text, title_rect)

        # Draw score with shadow effect
        score_text = f"Final Score: {player.score}"
        shadow_offset = 2
        draw_text(score_text, BLACK, SCREEN_WIDTH // 2 - 100 + shadow_offset, SCREEN_HEIGHT // 2 + shadow_offset)
        draw_text(score_text, WHITE, SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2)

        # Draw instructions with highlight effect based on time
        highlight_color = YELLOW if (elapsed_time // 500) % 2 == 0 else WHITE
        draw_text("Press SPACE to play again", highlight_color, SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 50)
        draw_text("Press M to return to main menu", WHITE, SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 100)
        draw_text("Press ESC to quit", WHITE, SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 150)

        pygame.display.flip()
        clock.tick(60)  # Higher framerate for smoother animations

    return return_to_menu

def main_menu():
    # Create starfield background for menu
    stars = [Star() for _ in range(100)]

    # Menu options
    menu_options = ["Start Game", "Instructions", "Quit"]
    selected_option = 0

    # Title font (larger than regular font)
    title_font = pygame.font.SysFont(None, 72)

    # Animation variables for decorative spaceship
    ship_x = SCREEN_WIDTH // 4
    ship_y = SCREEN_HEIGHT // 2
    ship_direction = 1
    ship_speed = 1
    ship_angle = 0
    ship_angle_speed = 1

    # Menu loop
    menu_active = True
    while menu_active:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(menu_options)
                elif event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(menu_options)
                elif event.key == pygame.K_RETURN:
                    if selected_option == 0:  # Start Game
                        return True  # Return to main to start the game
                    elif selected_option == 1:  # Instructions
                        show_instructions()
                    elif selected_option == 2:  # Quit
                        pygame.quit()
                        sys.exit()

        # Draw background
        screen.fill(BLACK)

        # Update and draw stars
        for star in stars:
            star.update()
            star.draw()

        # Update decorative spaceship position
        ship_x += ship_speed * ship_direction
        if ship_x > SCREEN_WIDTH * 3 // 4 or ship_x < SCREEN_WIDTH // 4:
            ship_direction *= -1

        # Update ship angle for rotation effect
        ship_angle = (ship_angle + ship_angle_speed) % 360

        # Draw decorative animated spaceship
        ship_color = CYAN
        ship_width = 60
        ship_height = 40

        # Calculate ship points with rotation
        angle_rad = math.radians(ship_angle)
        cos_val = math.cos(angle_rad) * 0.2  # Reduce rotation effect

        # Draw ship body
        pygame.draw.polygon(screen, ship_color, [
            (ship_x + ship_width // 2, ship_y - 15 - 5 * cos_val),  # Nose
            (ship_x, ship_y + ship_height - 5 + 3 * cos_val),       # Bottom left
            (ship_x + ship_width, ship_y + ship_height - 5 + 3 * cos_val)  # Bottom right
        ])

        # Draw cockpit
        pygame.draw.ellipse(screen, BLUE, 
                           (ship_x + ship_width // 2 - 8, ship_y, 16, 20))

        # Draw wings
        pygame.draw.polygon(screen, ship_color, [
            (ship_x, ship_y + ship_height - 5),       # Top left
            (ship_x - 15, ship_y + ship_height + 10), # Bottom left
            (ship_x + 15, ship_y + ship_height - 5)   # Bottom right
        ])
        pygame.draw.polygon(screen, ship_color, [
            (ship_x + ship_width, ship_y + ship_height - 5),  # Top right
            (ship_x + ship_width + 15, ship_y + ship_height + 10), # Bottom right
            (ship_x + ship_width - 15, ship_y + ship_height - 5)   # Bottom left
        ])

        # Draw engine flames with animation
        flame_height = 10 + (pygame.time.get_ticks() % 6)
        flame_color = ORANGE

        pygame.draw.polygon(screen, flame_color, [
            (ship_x + 15, ship_y + ship_height - 5),
            (ship_x + 10, ship_y + ship_height + flame_height),
            (ship_x + 20, ship_y + ship_height - 5)
        ])
        pygame.draw.polygon(screen, flame_color, [
            (ship_x + ship_width - 15, ship_y + ship_height - 5),
            (ship_x + ship_width - 10, ship_y + ship_height + flame_height),
            (ship_x + ship_width - 20, ship_y + ship_height - 5)
        ])

        # Draw title with pulsing effect
        pulse = math.sin(pygame.time.get_ticks() / 300) * 10
        title_color = (255, 255, max(0, int(pulse)))  # Slightly pulsing yellow
        title_surface = title_font.render("SPACE INVADERS", True, title_color)
        screen.blit(title_surface, (SCREEN_WIDTH // 2 - title_surface.get_width() // 2, 100))

        # Draw menu options
        for i, option in enumerate(menu_options):
            if i == selected_option:
                color = CYAN  # Highlight selected option
                # Draw a selector arrow with animation
                arrow_offset = math.sin(pygame.time.get_ticks() / 200) * 5
                pygame.draw.polygon(screen, CYAN, [
                    (SCREEN_WIDTH // 2 - 130 - arrow_offset, 250 + i * 60),
                    (SCREEN_WIDTH // 2 - 110 - arrow_offset, 260 + i * 60),
                    (SCREEN_WIDTH // 2 - 130 - arrow_offset, 270 + i * 60)
                ])
            else:
                color = WHITE

            draw_text(option, color, SCREEN_WIDTH // 2 - 80, 250 + i * 60)

        # Draw footer text
        draw_text("Use UP/DOWN arrows to select and ENTER to confirm", WHITE, 
                 SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT - 50)

        # Draw enemy for decoration on the right side
        enemy_x = SCREEN_WIDTH * 3 // 4
        enemy_y = SCREEN_HEIGHT // 3
        enemy_color = PURPLE

        # Draw the main body of enemy
        pygame.draw.ellipse(screen, enemy_color, (enemy_x, enemy_y, 40, 30))

        # Draw the eyes
        eye_color = WHITE
        pygame.draw.circle(screen, eye_color, (int(enemy_x + 12), int(enemy_y + 12)), 5)
        pygame.draw.circle(screen, eye_color, (int(enemy_x + 28), int(enemy_y + 12)), 5)

        # Draw pupils with animation
        pupil_offset = math.sin(pygame.time.get_ticks() / 500) * 2
        pygame.draw.circle(screen, BLACK, (int(enemy_x + 12 + pupil_offset), int(enemy_y + 12)), 2)
        pygame.draw.circle(screen, BLACK, (int(enemy_x + 28 + pupil_offset), int(enemy_y + 12)), 2)

        # Draw tentacles with animation
        tentacle_height = 5 + math.sin(pygame.time.get_ticks() / 300) * 3
        for i in range(3):
            pygame.draw.line(screen, enemy_color, 
                            (enemy_x + 10 + i*10, enemy_y + 30),
                            (enemy_x + 10 + i*10, enemy_y + 30 + tentacle_height), 
                            3)

        pygame.display.flip()
        clock.tick(30)

def show_instructions():
    # Create starfield background for instructions screen
    stars = [Star() for _ in range(100)]

    # Instructions loop
    instructions_active = True
    while instructions_active:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                    instructions_active = False

        # Draw background
        screen.fill(BLACK)

        # Update and draw stars
        for star in stars:
            star.update()
            star.draw()

        # Draw title
        draw_text("INSTRUCTIONS", YELLOW, SCREEN_WIDTH // 2 - 100, 80)

        # Draw instructions
        instructions = [
            "CONTROLS:",
            "LEFT/RIGHT ARROW: Move ship",
            "SPACE: Shoot",
            "P: Pause game",
            "",
            "POWER-UPS:",
            "BLUE: Shield - Protects from enemy bullets",
            "CYAN: Speed Boost - Increases movement speed",
            "RED: Weapon Upgrade - Triple shot",
            "GREEN: Extra Life - Adds one life",
            "",
            "OBJECTIVE:",
            "Destroy all aliens before they reach your position",
            "Advance through increasingly difficult levels"
        ]

        for i, line in enumerate(instructions):
            draw_text(line, WHITE, SCREEN_WIDTH // 2 - 200, 150 + i * 30)

        # Draw footer
        draw_text("Press ESC or ENTER to return to menu", WHITE, SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT - 50)

        pygame.display.flip()
        clock.tick(30)

def pause_game():
    paused = True
    return_to_menu = False

    # Create starfield background for pause screen
    stars = [Star() for _ in range(100)]

    while paused:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    paused = False
                elif event.key == pygame.K_m:
                    paused = False
                    return_to_menu = True
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        # Draw background
        screen.fill(BLACK)

        # Update and draw stars
        for star in stars:
            star.update()
            star.draw()

        # Display pause message
        draw_text("PAUSED", YELLOW, SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT // 2 - 50)
        draw_text("Press P to continue", WHITE, SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 + 20)
        draw_text("Press M to return to main menu", WHITE, SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2 + 60)
        draw_text("Press ESC to quit", WHITE, SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 100)

        pygame.display.flip()
        clock.tick(30)

    return return_to_menu

def main():
    global ENEMY_SHOOT_CHANCE, ENEMY_ROWS, ENEMY_COLS
    # Try to load and play background music
    try:
        pygame.mixer.music.load("background_music.mp3")
        pygame.mixer.music.set_volume(0.5)  # Set volume to 50%
        pygame.mixer.music.play(-1)  # -1 means loop indefinitely
    except:
        print("Background music file not found. Continuing without music.")

    # Show main menu first
    if not main_menu():
        return  # Exit if player quits from menu

    # Initialize game after menu
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
                    return_to_menu = pause_game()
                    if return_to_menu:
                        # Return to main menu
                        if not main_menu():
                            return  # Exit if player quits from menu
                        # Initialize game again after returning from menu
                        player = Player()
                        # Reset enemy grid to initial values
                        ENEMY_ROWS = 5  # Reset to initial value
                        ENEMY_COLS = 10  # Reset to initial value
                        enemy_group = EnemyGroup()
                        game_over = False
                        current_level = 1
                        enemies_killed = 0
                        ENEMY_SHOOT_CHANCE = 0.002  # Reset difficulty
                        continue

        if game_over:
            # Show game over screen and check if player wants to return to menu
            return_to_menu = game_over_screen(player)

            if return_to_menu:
                # Return to main menu
                if not main_menu():
                    return  # Exit if player quits from menu
                # Initialize game again after returning from menu
                player = Player()
                # Reset enemy grid to initial values
                ENEMY_ROWS = 5  # Reset to initial value
                ENEMY_COLS = 10  # Reset to initial value
                enemy_group = EnemyGroup()
                game_over = False
                current_level = 1
                enemies_killed = 0
                ENEMY_SHOOT_CHANCE = 0.002  # Reset difficulty
            else:
                # Reset game completely and continue playing from scratch
                player = Player()
                # Reset enemy grid to initial values
                ENEMY_ROWS = 5  # Reset to initial value
                ENEMY_COLS = 10  # Reset to initial value
                enemy_group = EnemyGroup()
                game_over = False
                current_level = 1
                enemies_killed = 0
                ENEMY_SHOOT_CHANCE = 0.002  # Reset difficulty

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

            # More balanced scaling formula for enemies needed to level up
            # Uses square root function to make scaling more gradual at higher levels
            enemies_to_next_level = int(15 + 10 * math.sqrt(current_level))

            # Adjust ENEMY_ROWS and ENEMY_COLS based on level
            # This will create more enemies as the level increases

            # Increase rows and columns gradually with level, but cap at reasonable values
            # to prevent the game from becoming too crowded or too difficult
            ENEMY_ROWS = min(8, 3 + int(math.sqrt(current_level)))
            ENEMY_COLS = min(12, 8 + int(math.sqrt(current_level)))

            # Create a new wave of enemies with increased difficulty
            enemy_group = EnemyGroup()

            # More balanced speed scaling - logarithmic to prevent it from becoming too fast
            # Base speed + logarithmic increase based on level
            enemy_group.speed = ENEMY_SPEED + 0.5 * math.log(current_level + 1, 2)

            # More balanced shoot chance scaling - logarithmic with a reasonable cap
            # This makes early levels easier and prevents later levels from becoming impossible
            ENEMY_SHOOT_CHANCE = min(0.004, 0.001 + 0.0003 * math.log(current_level + 1, 2))
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
            # Increase difficulty slightly (less than level progression)
            # Use a small logarithmic increase to keep it balanced
            enemy_group.speed += 0.1 * math.log(current_level + 1, 2)
            # Slightly increase enemy shoot chance (but less than level progression)
            # Use a small logarithmic increase to keep it balanced
            ENEMY_SHOOT_CHANCE = min(0.004, ENEMY_SHOOT_CHANCE + 0.0001 * math.log(current_level + 1, 2))

            # Display wave cleared message
            screen.fill(BLACK)
            draw_text("Wave Cleared!", YELLOW, SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2)
            draw_text("Get ready for the next wave!", WHITE, SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 50)
            pygame.display.flip()
            pygame.time.delay(1000)  # Pause for 1 second to show message

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
