
import math
import random
import time
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import numpy as np


ARENA_RADIUS = 35.0
GRID_SIZE = 70      
CELL_SIZE = (2 * ARENA_RADIUS) / GRID_SIZE
OBSTACLE_DENSITY = 0.15
MAX_BOMBS = 3
BOMB_TIMER = 3.0
PLAYER_SPEED = 0.2
POWERUP_CHANCE = 0.4


class GameState:
    def __init__(self):
        self.camera_pos = [0.0, 18.0, -10.0]  
        self.invincible = False 
        self.player_pos = [0.0, 0.0, 0.0]
        self.player_bombs = 1
        self.player_range = 2
        self.player_speed = PLAYER_SPEED
        self.player_visible = True
        self.active_bombs = []
        self.obstacles = []    
        self.powerups = []      
        self.enemies = []
        self.enemy_speed = PLAYER_SPEED * 0.1
        self.boss_speed = PLAYER_SPEED * 0.2
        self.last_update = time.time()
        self.keys_pressed = set()
        self.game_running = True
        self.game_over_time = None
        self.camera_pos = [0.0, 18.0, 24.0]
        self.camera_look_at = [0.0, 0.0, 0.0]
        self.score = 0
        self.player_facing = 0.0
        self.boss_defeated_time = None
        self.boss_defeats = 0
        self.boss_active = False
        self.boss = None 
        self.boss_respawns_left = 2 
        self.snow_particles = []
        self.boss_snow_intensity = 0.0
        self.grid = {}
        self.initialize_arena()
      
    def initialize_arena(self):
        obstacle_size = 0.8
        obstacle_radius = obstacle_size / 2
        enemy_radius = 0.35

        available_cells = []
        for i in range(-GRID_SIZE // 2, GRID_SIZE // 2 + 1):
            for j in range(-GRID_SIZE // 2, GRID_SIZE // 2 + 1):
                x = i * CELL_SIZE
                z = j * CELL_SIZE
                distance = math.hypot(x, z)
                if distance + obstacle_radius <= ARENA_RADIUS:
                    self.grid[(i, j)] = [x, 0.0, z]
                    if (i, j) != (0, 0):
                        available_cells.append((i, j))

        obstacle_count = int(len(available_cells) * OBSTACLE_DENSITY)
        obstacle_cells = random.sample(available_cells, obstacle_count)
        for (i, j) in obstacle_cells:
            x, y, z = self.grid[(i, j)]
            self.obstacles.append([x, 0.0, z])

        obstacle_positions = set(obstacle_cells)
        forbidden_cells = obstacle_positions | {(0, 0)}
        enemy_cells_candidates = [cell for cell in available_cells if cell not in forbidden_cells]

        self.enemies = []
        max_enemies = 5
        max_attempts = 100

        for _ in range(max_enemies):
            for attempt in range(max_attempts):
                cell = random.choice(enemy_cells_candidates)
                x, y, z = self.grid[cell]
                too_close = False
                for other in self.enemies:
                    ex, _, ez, _ = other
                    if math.hypot(ex - x, ez - z) < 2 * enemy_radius:
                        too_close = True
                        break
                if not too_close:
                    direction = random.uniform(0, 2 * math.pi)
                    self.enemies.append([x, 0.0, z, direction])
                    enemy_cells_candidates.remove(cell)
                    break

game = GameState()


def init_snow_particles():
    game.snow_particles = []
    for _ in range(300):
        game.snow_particles.append([
            random.uniform(-ARENA_RADIUS, ARENA_RADIUS),
            random.uniform(15, 25),
            random.uniform(-ARENA_RADIUS, ARENA_RADIUS),
            random.uniform(0.5, 1.5)
        ])

def update_snow_particles():
    if game.boss_active and game.boss_snow_intensity < 1.0:
        game.boss_snow_intensity = min(1.0, game.boss_snow_intensity + 0.02)
    elif not game.boss_active and game.boss_snow_intensity > 0.0:
        game.boss_snow_intensity = max(0.0, game.boss_snow_intensity - 0.02)

    for i, p in enumerate(game.snow_particles):
        if game.boss_snow_intensity > 0.0:
            p[1] -= p[3] * game.boss_snow_intensity
            if p[1] < -1:
                p[1] = random.uniform(15, 25)
                p[0] = random.uniform(-ARENA_RADIUS, ARENA_RADIUS)
                p[2] = random.uniform(-ARENA_RADIUS, ARENA_RADIUS)
                
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glMatrixMode(GL_PROJECTION)   
    glPushMatrix()
    glLoadIdentity()  
    gluOrtho2D(0, 1000, 0, 800)  
    glMatrixMode(GL_MODELVIEW)   
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)   
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def game_over(reason):
    print(f"{reason} Game over!")
    game.game_running = False
    game.game_over_time = time.time()

def draw_cube(x, y, z, size, color):
    half_size = size / 2.0

    glPushMatrix()
    glTranslatef(x, y, z)
    glColor3f(*color)

    glBegin(GL_QUADS)
    
    # Front face 
    glVertex3f(-half_size, -half_size,  half_size)
    glVertex3f( half_size, -half_size,  half_size)
    glVertex3f( half_size,  half_size,  half_size)
    glVertex3f(-half_size,  half_size,  half_size)

    # Back face 
    glVertex3f(-half_size, -half_size, -half_size)
    glVertex3f(-half_size,  half_size, -half_size)
    glVertex3f( half_size,  half_size, -half_size)
    glVertex3f( half_size, -half_size, -half_size)

    # Left face 
    glVertex3f(-half_size, -half_size, -half_size)
    glVertex3f(-half_size, -half_size,  half_size)
    glVertex3f(-half_size,  half_size,  half_size)
    glVertex3f(-half_size,  half_size, -half_size)

    # Right face 
    glVertex3f( half_size, -half_size, -half_size)
    glVertex3f( half_size,  half_size, -half_size)
    glVertex3f( half_size,  half_size,  half_size)
    glVertex3f( half_size, -half_size,  half_size)

    # Top face (y = +half_size)
    glVertex3f(-half_size,  half_size, -half_size)
    glVertex3f(-half_size,  half_size,  half_size)
    glVertex3f( half_size,  half_size,  half_size)
    glVertex3f( half_size,  half_size, -half_size)

    # Bottom face (y = -half_size)
    glVertex3f(-half_size, -half_size, -half_size)
    glVertex3f( half_size, -half_size, -half_size)
    glVertex3f( half_size, -half_size,  half_size)
    glVertex3f(-half_size, -half_size,  half_size)

    glEnd()
    
    glPopMatrix()

def draw_sphere(x, y, z, radius, color):
    glPushMatrix()
    glTranslatef(x, y, z)
    glColor3f(*color)
    
    quadric = gluNewQuadric()
    gluSphere(quadric, radius, 16, 16)
    glPopMatrix()

def draw_cylinder(x, y, z, radius, height, color):
    glPushMatrix()
    glTranslatef(x, y, z)
    glColor3f(*color)
    
    quadric = gluNewQuadric()
    gluCylinder(quadric, radius, radius, height, 16, 4)
    glPopMatrix()

def draw_arena():

    base_color = np.array([0.3, 0.7, 0.3]) * (1 - game.boss_snow_intensity) + \
                np.array([0.8, 0.9, 1.0]) * game.boss_snow_intensity
    
    glColor3f(*base_color)

    glBegin(GL_TRIANGLES)
    glNormal3f(0.0, 1.0, 0.0)
    
    segments = 256
    center = (0.0, -0.1, 0.0)
    
    for i in range(segments):
        angle1 = 2.0 * math.pi * i / segments
        angle2 = 2.0 * math.pi * (i + 1) / segments
        
        x1 = ARENA_RADIUS * math.cos(angle1)
        z1 = ARENA_RADIUS * math.sin(angle1)
        
        x2 = ARENA_RADIUS * math.cos(angle2)
        z2 = ARENA_RADIUS * math.sin(angle2)
        
        glVertex3f(*center)

        glVertex3f(x1, -0.1, z1)
        
        glVertex3f(x2, -0.1, z2)
    
    glEnd()


def draw_player():
    if not game.player_visible:
        return
    scale = 1.15
    x, y, z = game.player_pos
    facing = game.player_facing

    # Cheat mode colors
    body_color = (1.0, 0.84, 0.0) if game.invincible else (0.25, 0.45, 1.0)
    head_color = (1.0, 0.9, 0.5) if game.invincible else (1.0, 0.95, 0.75)
    detail_color = (0.98, 0.45, 0.8) if not game.invincible else (0.9, 0.3, 0.3)

    glPushMatrix()
    glTranslatef(x, y, z)
    glScalef(scale, scale, scale)
    glRotatef(-math.degrees(facing), 0, 1, 0)

    quadric = gluNewQuadric()

    # Head
    glPushMatrix()
    glTranslatef(0, 1.07, 0)
    glColor3f(*head_color)
    glScalef(1.0, 1.2, 1.0)
    gluSphere(quadric, 0.37, 21, 15)
    glPopMatrix()
    
    # Body
    glPushMatrix()
    glColor3f(*body_color)
    glTranslatef(0, 0.67, 0)
    glScalef(1.0, 1.15, 1.0)
    gluSphere(quadric, 0.29, 20, 14)
    glPopMatrix()
    
    # Eyes
    for ex in [-0.11, 0.11]:
        glPushMatrix()
        glTranslatef(ex, 1.14, 0.35)
        glScalef(0.10, 0.15, 0.10)
        glColor3f(0.14, 0.14, 0.17)
        gluSphere(quadric, 1.0, 9, 7)
        glPopMatrix()

    # Arms
    for armdir, armx in [(1, 0.24), (-1, -0.24)]:
        glPushMatrix()
        glColor3f(*body_color)
        glTranslatef(armx, 0.93, 0.0)
        glRotatef(90, 0, 0, 1)
        gluCylinder(quadric, 0.07, 0.05, 0.22, 11, 1)
        glColor3f(*detail_color)
        glTranslatef(0, 0, 0.22)
        gluSphere(quadric, 0.09, 8, 7)
        glPopMatrix()
    
    # Legs
    for legx in [-0.08, 0.08]:
        glPushMatrix()
        glColor3f(*body_color)
        glTranslatef(legx, 0.22, 0.0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(quadric, 0.085, 0.07, 0.11, 9, 1)
        glTranslatef(0, 0, 0.11)
        glRotatef(18, 1, 0, 0)
        gluCylinder(quadric, 0.07, 0.06, 0.11, 9, 1)
        glTranslatef(0, 0, 0.11)
        glColor3f(*detail_color)
        gluSphere(quadric, 0.11, 8, 7)
        glPopMatrix()
    
    glPopMatrix()

def draw_boss():
    if not game.boss_active or game.boss is None:
        return
    x, y, z, direction, health = game.boss
    boss_scale = 2.5
    glPushMatrix()
    glTranslatef(x, y + 0.9 * boss_scale, z)
    glScalef(boss_scale, boss_scale, boss_scale)
    quadric = gluNewQuadric()
    glColor3f(1.0, 0.15, 0.15)

    gluSphere(quadric, 0.25, 24, 18)
    for eye_x in [-0.1, 0.1]:
        glPushMatrix()
        glTranslatef(eye_x, 0.1, 0.22)
        glScalef(1, 1.3, 1)
        glColor3f(0.0, 0.0, 0.0)
        gluSphere(quadric, 0.06, 9, 8)
        glPopMatrix()
    glPopMatrix()

def draw_bombs():
    for bomb in game.active_bombs:
        x, y, z, timer, _ = bomb
        pulse = (math.sin(timer * 10) + 1) * 0.25 + 0.5
        draw_sphere(x, y + 0.3, z, 0.3, (0.8, 0.1 + pulse, 0.1))

def draw_obstacles():
    for obstacle in game.obstacles:
        x, y, z = obstacle
        base_color = np.array([0.6, 0.4, 0.2]) * (1 - game.boss_snow_intensity) + \
                     np.array([0.5, 0.7, 1.0]) * game.boss_snow_intensity
        draw_cube(x, y + 0.5, z, 0.8, base_color)

def draw_snow_particles():
    
    if game.boss_snow_intensity <= 0.0:
        return
    for p in game.snow_particles:
        glPushMatrix()
        glTranslatef(p[0], p[1], p[2])
        glColor3f(1, 1, 1)
        gluSphere(gluNewQuadric(), 0.1, 5, 5)
        glPopMatrix()
    
    for p in game.snow_particles:
        alpha = min(1.0, p[1]/15.0) * game.boss_snow_intensity
        glColor4f(1, 1, 1, alpha)
        
        glPushMatrix()
        glTranslatef(p[0], p[1], p[2])
        glutSolidSphere(0.1, 5, 5)
        glPopMatrix()

def draw_enemies():
    alien_scale = 1.45
    for enemy in game.enemies:
        x, y, z, _ = enemy
        glColor3f(0.3, 1.0, 0.3)
        quadric = gluNewQuadric()
        
        glPushMatrix()
        glTranslatef(x, y + 0.73 * alien_scale, z)
        gluSphere(quadric, 0.23 * alien_scale, 14, 14)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(x, y + 0.5 * alien_scale, z)
        gluSphere(quadric, 0.16 * alien_scale, 12, 10)
        glPopMatrix()
        
        for i in [-1, 1]:
            glPushMatrix()
            glColor3f(0.28, 0.93, 0.2)
            glTranslatef(x + i * 0.19 * alien_scale, y + 0.585 * alien_scale, z)
            glRotatef(30 * i, 0, 0, 1)
            gluCylinder(quadric, 0.04 * alien_scale, 0.038 * alien_scale, 0.14 * alien_scale, 8, 2)
            glPopMatrix()
            
            glPushMatrix()
            glColor3f(0.21, 0.7, 0.13)
            glTranslatef(x + i * 0.07 * alien_scale, y + 0.44 * alien_scale, z)
            glRotatef(-90, 1, 0, 0)
            gluCylinder(quadric, 0.037 * alien_scale, 0.03 * alien_scale, 0.13 * alien_scale, 8, 2)
            glPopMatrix()
        
        for eye_x in [-0.09 * alien_scale, 0.09 * alien_scale]:
            glPushMatrix()
            glTranslatef(x + eye_x, y + 0.78 * alien_scale, z + 0.15 * alien_scale)
            glScalef(1, 1.3, 1)
            glColor3f(0.0, 0.0, 0.0)
            gluSphere(quadric, 0.045 * alien_scale, 8, 8)
            glPopMatrix()
        
        for ant_x in [-0.08 * alien_scale, 0.08 * alien_scale]:
            glPushMatrix()
            glTranslatef(x + ant_x, y + 0.93 * alien_scale, z)
            glColor3f(0.6, 1.0, 0.3)
            glRotatef(-60 if ant_x < 0 else 60, 0, 0, 1)
            gluCylinder(quadric, 0.02 * alien_scale, 0.01 * alien_scale, 0.15 * alien_scale, 6, 2)
            glTranslatef(0, 0, 0.15 * alien_scale)
            glColor3f(1.0, 1.0, 0.2)
            gluSphere(quadric, 0.03 * alien_scale, 7, 7)
            glPopMatrix()

def draw_powerups():
    for powerup in game.powerups:
        x, y, z, type_id = powerup
        
        card_width = 0.5
        card_height = 0.05
        card_depth = 0.7
        
        glPushMatrix()
        glTranslatef(x, y + 0.2, z)
        rot_angle = math.degrees(math.atan2(game.player_pos[2] - z, game.player_pos[0] - x))
        glRotatef(rot_angle, 0, 1, 0)
        
        glColor3f(0.9, 0.9, 0.9)
        glBegin(GL_QUADS)
        glNormal3f(0.0, 0.0, 1.0)
        glVertex3f(-card_width/2, -card_height/2, card_depth/2)
        glVertex3f(card_width/2, -card_height/2, card_depth/2)
        glVertex3f(card_width/2, card_height/2, card_depth/2)
        glVertex3f(-card_width/2, card_height/2, card_depth/2)
        glEnd()
        
        glBegin(GL_QUADS)
        glNormal3f(0.0, 0.0, -1.0)
        glVertex3f(-card_width/2, -card_height/2, -card_depth/2)
        glVertex3f(-card_width/2, card_height/2, -card_depth/2)
        glVertex3f(card_width/2, card_height/2, -card_depth/2)
        glVertex3f(card_width/2, -card_height/2, -card_depth/2)
        glEnd()
        
        glBegin(GL_QUADS)
        glNormal3f(0.0, 1.0, 0.0)
        glVertex3f(-card_width/2, card_height/2, -card_depth/2)
        glVertex3f(-card_width/2, card_height/2, card_depth/2)
        glVertex3f(card_width/2, card_height/2, card_depth/2)
        glVertex3f(card_width/2, card_height/2, -card_depth/2)
        glEnd()
        
        glBegin(GL_QUADS)
        glNormal3f(0.0, -1.0, 0.0)
        glVertex3f(-card_width/2, -card_height/2, -card_depth/2)
        glVertex3f(card_width/2, -card_height/2, -card_depth/2)
        glVertex3f(card_width/2, -card_height/2, card_depth/2)
        glVertex3f(-card_width/2, -card_height/2, card_depth/2)
        glEnd()
        
        glBegin(GL_QUADS)
        glNormal3f(1.0, 0.0, 0.0)
        glVertex3f(card_width/2, -card_height/2, -card_depth/2)
        glVertex3f(card_width/2, card_height/2, -card_depth/2)
        glVertex3f(card_width/2, card_height/2, card_depth/2)
        glVertex3f(card_width/2, -card_height/2, card_depth/2)
        glEnd()
        
        glBegin(GL_QUADS)
        glNormal3f(-1.0, 0.0, 0.0)
        glVertex3f(-card_width/2, -card_height/2, -card_depth/2)
        glVertex3f(-card_width/2, -card_height/2, card_depth/2)
        glVertex3f(-card_width/2, card_height/2, card_depth/2)
        glVertex3f(-card_width/2, card_height/2, -card_depth/2)
        glEnd()
        
        if type_id == 0:
            glColor3f(1.0, 0.5, 0.0)
            quadric = gluNewQuadric()
            glTranslatef(0, 0.1, 0)
            gluSphere(quadric, 0.2, 8, 8)
            glColor3f(0.8, 0.8, 0.2)
            glTranslatef(0, 0.2, 0)
            gluCylinder(quadric, 0.05, 0.02, 0.15, 8, 2)
            
        elif type_id == 1:
            glColor3f(1.0, 0.0, 0.0)
            glBegin(GL_TRIANGLES)
            num_points = 8
            inner_radius = 0.1
            outer_radius = 0.25
            for i in range(num_points*2):
                angle = math.pi * i / num_points
                if i % 2 == 0:
                    x = outer_radius * math.cos(angle)
                    z = outer_radius * math.sin(angle)
                else:
                    x = inner_radius * math.cos(angle)
                    z = inner_radius * math.sin(angle)
                
                glVertex3f(0, 0.1, 0)
                glVertex3f(x, 0.1, z)
                
                if i < num_points*2 - 1:
                    angle_next = math.pi * (i+1) / num_points
                    if (i+1) % 2 == 0:
                        x_next = outer_radius * math.cos(angle_next)
                        z_next = outer_radius * math.sin(angle_next)
                    else:
                        x_next = inner_radius * math.cos(angle_next)
                        z_next = inner_radius * math.sin(angle_next)
                else:
                    angle_next = 0
                    x_next = outer_radius
                    z_next = 0
                
                glVertex3f(x_next, 0.1, z_next)
            glEnd()
            
        elif type_id == 2:
            glColor3f(0.0, 0.8, 1.0)
            glBegin(GL_TRIANGLES)
            glVertex3f(0, 0.1, 0.2)
            glVertex3f(-0.15, 0.1, 0.1)
            glVertex3f(-0.05, 0.1, 0.05)
            
            glVertex3f(-0.05, 0.1, 0.05)
            glVertex3f(0.05, 0.1, -0.05)
            glVertex3f(-0.15, 0.1, 0.1)
            
            glVertex3f(0.05, 0.1, -0.05)
            glVertex3f(-0.05, 0.1, -0.15)
            glVertex3f(0.15, 0.1, -0.2)
            
            glVertex3f(0.05, 0.1, -0.05)
            glVertex3f(0.15, 0.1, -0.2)
            glVertex3f(0.05, 0.1, -0.15)
            glEnd()
        
        glPopMatrix()
        game.powerups[game.powerups.index(powerup)][1] = y + 0.03 * math.sin(time.time() * 2.0)



def draw_explosions():
    for bomb in game.active_bombs:
        if bomb[3] <= 0:
            x, y, z, _, explosion_range = bomb
            explosion_radius = explosion_range * CELL_SIZE

            glPushMatrix()
            glTranslatef(x, y + 0.01, z)
            glColor3f(1, 1, 0)
            quad = gluNewQuadric()
            glRotatef(90, 1, 0, 0)
            gluCylinder(quad, explosion_radius, explosion_radius, 0.01, 64, 1)
            
            glPushMatrix()
            glColor3f(1, 0.5, 0)
            gluSphere(gluNewQuadric(), explosion_radius * 0.3, 16, 16)
            glPopMatrix()
            
            glPopMatrix()

def display():
    glClear(GL_COLOR_BUFFER_BIT)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    x, y, z = game.player_pos
    camera_x = x + game.camera_pos[0]
    camera_y = y + game.camera_pos[1]
    camera_z = z + game.camera_pos[2]
    
    gluLookAt(
        camera_x, camera_y, camera_z,
        x, y, z,
        0.0, 1.0, 0.0
    )
    
    draw_arena()
    draw_obstacles()
    draw_snow_particles()
    draw_powerups()
    draw_bombs()
    draw_explosions()
    draw_player()
    draw_enemies()
    draw_boss()

    if game.invincible and game.game_running:
        glColor3f(1.0, 0.84, 0.0)
        draw_text(15, 700, "CHEATS ENABLED", GLUT_BITMAP_TIMES_ROMAN_24)

    if not game.game_running and game.game_over_time:
        glColor3f(1, 0, 0)
        draw_text(15, 770, f"Game Over")
        draw_text(15, 740, f"Press \"P\" to Play Again.")
    elif game.boss_defeats == 3:
        glColor3f(1, 0, 0) 
        draw_text(15, 770, "Congratulations! You killed the master enemy!")
        draw_text(15, 740, f"Press \"P\" to Play Again.")

    glutSwapBuffers()

def reshape(width, height):
    if height == 0:
        height = 1
        
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, width / height, 0.1, 300.0)
    glMatrixMode(GL_MODELVIEW)

def keyboard(key, x, y):
    if key == b'\x1b':
        game.game_running = False
        glutLeaveMainLoop()
    elif key == b' ':
        if game.game_running:
            place_bomb()
    elif key == b'p':
        if not game.game_running:
            reset_game()
    elif key == b'i':  
        game.invincible = not game.invincible
        status = "ENABLED" if game.invincible else "DISABLED"
        print(f"Invincibility {status}")
    
    glutPostRedisplay()
    
    if game.game_running:
        if key == b'w':
            game.keys_pressed.add('up')
        elif key == b's':
            game.keys_pressed.add('down')
        elif key == b'a':
            game.keys_pressed.add('left')
        elif key == b'd':
            game.keys_pressed.add('right')

def keyboard_up(key, x, y):
    if key == b'w':
        game.keys_pressed.discard('up')
    elif key == b's': 
        game.keys_pressed.discard('down')
    elif key == b'a':
        game.keys_pressed.discard('left')
    elif key == b'd':
        game.keys_pressed.discard('right')



def special(key, x, y):
    if game.game_running:
        move_speed = 1.0
        max_offset = 60.0  
        min_y_offset = 10.0  
        max_y_offset = 25.0  
        
        default_pos = [0.0, 18.0, -10.0]
        
        if key == GLUT_KEY_UP:
            game.camera_pos[1] = min(default_pos[1] + max_y_offset, game.camera_pos[1] + move_speed)
        elif key == GLUT_KEY_DOWN:
            # Move camera down  (surface er niche jabe na)
            game.camera_pos[1] = max(default_pos[1] - min_y_offset, game.camera_pos[1] - move_speed)
        elif key == GLUT_KEY_LEFT:
            # Move camera left 
            new_x = max(default_pos[0] - max_offset, game.camera_pos[0] - move_speed)
            game.camera_pos[0] = new_x
        elif key == GLUT_KEY_RIGHT:
            # Move camera right 
            new_x = min(default_pos[0] + max_offset, game.camera_pos[0] + move_speed)
            game.camera_pos[0] = new_x
            
        glutPostRedisplay()

def can_move_to(x, z):
    if math.sqrt(x*x + z*z) > ARENA_RADIUS - 0.4:
        return False
    
    for obstacle in game.obstacles:
        ox, _, oz = obstacle
        dist = math.sqrt((x - ox)**2 + (z - oz)**2)
        if dist < CELL_SIZE * 0.8:
            return False
    
    return True

def place_bomb():
    active_bomb_count = len([b for b in game.active_bombs if b[3] > 0])
    if active_bomb_count >= game.player_bombs:
        return
    
    x, y, z = game.player_pos
    grid_x = round(x / CELL_SIZE) * CELL_SIZE
    grid_z = round(z / CELL_SIZE) * CELL_SIZE
    
    for bomb in game.active_bombs:
        bx, _, bz, _, _ = bomb
        if abs(bx - grid_x) < 0.1 and abs(bz - grid_z) < 0.1:
            return
    
    bomb = [grid_x, y, grid_z, BOMB_TIMER, game.player_range]
    game.active_bombs.append(bomb)

def handle_powerup_collision():
    x, y, z = game.player_pos
    for i in range(len(game.powerups) - 1, -1, -1):
        px, py, pz, ptype = game.powerups[i]
        dist = math.sqrt((x - px)**2 + (z - pz)**2)
        if dist < 0.6:
            if ptype == 0:
                game.player_bombs += 1
                if game.player_bombs > MAX_BOMBS:
                    game.player_bombs = MAX_BOMBS
            elif ptype == 1:
                game.player_range += 1
            elif ptype == 2:
                game.player_speed *= 1.2
            
            game.powerups.pop(i)
            game.score += 100

def process_explosions():
    player_dead = False
    
    for bomb_idx in range(len(game.active_bombs) - 1, -1, -1):
        bomb = game.active_bombs[bomb_idx]
        bomb[3] -= game.elapsed_time

        x, y, z, _, explosion_range = bomb
        explosion_radius = explosion_range * CELL_SIZE

        if bomb[3] <= 0 and bomb[3] > -0.5:
            # Destroy obstacles
            for obs_idx in range(len(game.obstacles) - 1, -1, -1):
                ox, oy, oz = game.obstacles[obs_idx]
                dist = math.sqrt((ox - x)**2 + (oz - z)**2)
                if dist <= explosion_radius + CELL_SIZE * 0.4:
                    # Remove obstacle and possibly spawn powerup
                    game.obstacles.pop(obs_idx)
                    game.score += 50
                    if random.random() < POWERUP_CHANCE:
                        powerup_type = random.randint(0, 2)
                        game.powerups.append([ox, 2, oz, powerup_type])

            # Player damage check
            px, py, pz = game.player_pos
            player_dist = math.sqrt((px - x)**2 + (pz - z)**2)
            if player_dist < explosion_radius + 0.4 and not player_dead:
                if not game.invincible:
                    player_dead = True
                    bomb[3] = -0.1
                    game_over("Player hit by explosion! Game over!")
                    game.player_visible = False 

            # Destroy enemies
            for enemy_idx in range(len(game.enemies) - 1, -1, -1):
                ex, ey, ez, _ = game.enemies[enemy_idx]
                enemy_dist = math.sqrt((ex - x)**2 + (ez - z)**2)
                if enemy_dist < explosion_radius + 0.4:
                    game.enemies.pop(enemy_idx)
                    game.score += 200

            # Boss damage
            if game.boss_active and game.boss is not None:
                bx, by, bz, bdir, bhp = game.boss
                boss_dist = math.sqrt((bx - x)**2 + (bz - z)**2)
                boss_radius = 0.7 * 2.5  # Match boss size
                if boss_dist < explosion_radius + boss_radius:
                    game.boss[4] -= 1
                    game.score += 500
                    if game.boss[4] <= 0:
                        game.boss_defeats += 1  
                        
                        if game.boss_defeats >= 3:  # Check if 3 defeats reached
                            game.score += 1000
                            game.boss = None
                            game.boss_active = False
                            game.boss_defeated_time = time.time()
                            game.game_running = False  # Freeze the game
                            print("Boss defeated 3 times! Game over!")
                        elif game.boss_respawns_left > 0:
                            # Existing respawn logic
                            game.boss_respawns_left -= 1
                            max_attempts = 100
                            boss_spawned = False
                            player_x, _, player_z = game.player_pos
                            for _ in range(max_attempts):
                                angle = random.uniform(0, 2 * math.pi)
                                radius = random.uniform(ARENA_RADIUS * 0.3, ARENA_RADIUS * 0.8)
                                spawn_x = radius * math.cos(angle)
                                spawn_z = radius * math.sin(angle)
                                if math.hypot(spawn_x, spawn_z) + 1.0 > ARENA_RADIUS:
                                    continue
                                obstacle_collision = False
                                for ox, _, oz in game.obstacles:
                                    if math.hypot(ox - spawn_x, oz - spawn_z) < 1.5:
                                        obstacle_collision = True
                                        break
                                if obstacle_collision:
                                    continue
                                if math.hypot(spawn_x - player_x, spawn_z - player_z) < 5.0:
                                    continue
                                game.boss = [spawn_x, 0.0, spawn_z, random.uniform(0, 2*math.pi), 3]
                                boss_spawned = True
                                break
                            if not boss_spawned:
                                game.boss = [0.0, 0.0, 0.0, random.uniform(0, 2*math.pi), 3]
                            game.boss_active = True
                            init_snow_particles()
                        else:
                            game.score += 1000
                            game.boss = None
                            game.boss_active = False
                            game.boss_defeated_time = time.time()
    
        if bomb[3] < -0.5:
            game.active_bombs.pop(bomb_idx)

def move_enemies():
    for i, enemy in enumerate(game.enemies):
        x, y, z, direction = enemy
        
        px, _, pz = game.player_pos
        dx = px - x
        dz = pz - z
        
        desired_dir = math.atan2(dz, dx)
        max_turn = 0.2
        
        angle_diff = (desired_dir - direction) % (2 * math.pi)
        if angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        
        if angle_diff > max_turn:
            direction += max_turn
        elif angle_diff < -max_turn:
            direction -= max_turn
        else:
            direction = desired_dir
        
        direction %= 2 * math.pi
        
        speed = game.enemy_speed
        new_x = x + math.cos(direction) * speed
        new_z = z + math.sin(direction) * speed
        
        boundary_dist = math.sqrt(new_x**2 + new_z**2)
        if boundary_dist > ARENA_RADIUS - 0.4:
            direction = math.atan2(-z, -x) + random.uniform(-0.5, 0.5)
            direction %= 2 * math.pi
            continue
        
        collision = False
        for obstacle in game.obstacles:
            ox, _, oz = obstacle
            if (abs(new_x - ox) < CELL_SIZE * 0.8 and 
                abs(new_z - oz) < CELL_SIZE * 0.8):
                collision = True
                break
        
        if collision:
            direction += random.uniform(0.5, 1.0)
            direction %= 2 * math.pi
        else:
            enemy[0] = new_x
            enemy[2] = new_z
            enemy[3] = direction
        
        enemy[3] = direction
        
        player_dist = math.sqrt((x - px)**2 + (z - pz)**2)
        if player_dist < 0.8 and not game.invincible:  # Cheat check
            game_over("Enemy caught you! Game over!")
            return
        
def move_boss():
    if not game.boss_active or game.boss is None:
        return
    x, y, z, direction, health = game.boss
    px, _, pz = game.player_pos
    dx = px - x
    dz = pz - z
    dist = math.hypot(dx, dz)
    if dist > 0.01:
        dir_to_player = math.atan2(dz, dx)
        speed = game.boss_speed
        x += math.cos(dir_to_player) * speed
        z += math.sin(dir_to_player) * speed
        game.boss[0] = x
        game.boss[2] = z
        game.boss[3] = dir_to_player

    if math.sqrt((x-px)**2 + (z-pz)**2) < 1.1 and not game.invincible:  # Cheat check
        game_over("The boss crushed you! Game over!")
        return
    
def reset_game():
    global game
    game = GameState()
    game.player_visible = True
    game.boss_defeats = 0

def update():
    current_time = time.time()
    game.elapsed_time = current_time - game.last_update
    game.last_update = current_time
    update_snow_particles()

    process_explosions()

    if not game.game_running:
        glutPostRedisplay()
        return

    move_dist = game.player_speed * game.elapsed_time * 60

    x, y, z = game.player_pos
    new_x, new_z = x, z
    dx, dz = 0, 0

    if 'up' in game.keys_pressed: dz -= 1
    if 'down' in game.keys_pressed: dz += 1
    if 'left' in game.keys_pressed: dx -= 1
    if 'right' in game.keys_pressed: dx += 1

    if dx != 0 or dz != 0:
        length = math.hypot(dx, dz)
        norm_dx = dx / length
        norm_dz = dz / length
        cand_x = x + norm_dx * move_dist
        cand_z = z + norm_dz * move_dist
        
        if can_move_to(cand_x, z): new_x = cand_x
        if can_move_to(x, cand_z): new_z = cand_z
        
        game.player_facing = math.atan2(-norm_dx, norm_dz)

    game.player_pos[0] = new_x
    game.player_pos[2] = new_z

    handle_powerup_collision()
    move_enemies()
    
    if game.boss_active and game.boss is not None and game.game_running:
        move_boss()

    if (len(game.enemies) == 0 
        and not game.boss_active 
        and game.boss is None 
        and (game.boss_defeated_time is None 
            or (current_time - game.boss_defeated_time) >= 5)):
        
        max_attempts = 100
        boss_spawned = False
        player_x, _, player_z = game.player_pos
        
        for _ in range(max_attempts):
            angle = random.uniform(0, 2*math.pi)
            radius = random.uniform(ARENA_RADIUS*0.3, ARENA_RADIUS*0.8)
            spawn_x = radius * math.cos(angle)
            spawn_z = radius * math.sin(angle)
            
            if (math.hypot(spawn_x, spawn_z) + 1.0 > ARENA_RADIUS or 
                math.hypot(spawn_x-player_x, spawn_z-player_z) < 5.0):
                continue
                
            obstacle_collision = False
            for ox, _, oz in game.obstacles:
                if math.hypot(ox-spawn_x, oz-spawn_z) < 1.5:
                    obstacle_collision = True
                    break
            if obstacle_collision:
                continue
                
            game.boss = [
                spawn_x, 
                0.0, 
                spawn_z, 
                random.uniform(0, 2*math.pi), 
                2
            ]
            game.boss_active = True
            boss_spawned = True
            break

        if not boss_spawned:
            game.boss = [0.0, 0.0, 0.0, random.uniform(0, 2*math.pi), 2]
            game.boss_active = True

    glutPostRedisplay()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(1280, 960)
    glutCreateWindow(b"Bomb Arena")
    
    # Register callback functions
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutKeyboardUpFunc(keyboard_up)
    glutSpecialFunc(special)
    glutIdleFunc(update)
    
    
    init_snow_particles()
    
    
    glutMainLoop()

if __name__ == "__main__":
    main()
