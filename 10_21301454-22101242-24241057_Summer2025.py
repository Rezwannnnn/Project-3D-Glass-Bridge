from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
import math, random, time, sys

# Rezwan
Window_Width = 1000
Window_Height = 700
FovY = 60.0

Camera_distance = 90.0

c_min_v = -10.0
c_max_v = 80.0
c_angle_h = 180.0
c_angle_v = 22.0

fst_prs = False

# Farhan (Bridge Mechanics)
ROWS = 20
COLS = 2
TILE_SIZE = 4.5
COL_SPACING = TILE_SIZE * 1.05
BRIDGE_Z0 = TILE_SIZE * 2

START_LIVES = 3
ROUND_TIME = 120
SAFE_SCORE = 10

tile_type = [random.randint(0, COLS - 1) for _ in range(ROWS)]
tile_broken = [[False for _ in range(COLS)] for _ in range(ROWS)]

# (all members interacted here)
p_row = -1
p_col = 0
p_x = 0.0
p_y = 1.0
p_z = 0.0

falling = False
fall_vz = 0.0
fall_start = 0.0

# Nusfat (Obstacles)
BALL_RADIUS = 0.6
balls = []

# (Rezwan_overall management)
score = 0
lives = START_LIVES
start_time = time.time()
time_left = ROUND_TIME
paused = False
running = True
gameover = False
flag = False

# Cheats (Farhan bridge reveal)
cheat_flash_timer = 0.0
last_time = time.time()


# Farhan (Bridge Mechanics)
def row_to_z(r):
    return BRIDGE_Z0 + r * TILE_SIZE

def col_to_x(c):
    mid = (COLS - 1) * 0.5
    return (c - mid) * COL_SPACING

def get_player_row():
    row = int((p_z - BRIDGE_Z0 + 0.5 * TILE_SIZE) / TILE_SIZE)
    return max(0, min(ROWS - 1, row))


# Rezwan (HUD/Text)
def draw_text(x, y, s):
    glColor3f(1, 1, 1)
    glRasterPos2f(x, y)
    for ch in s:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))


def draw_cube(size=1.0):
    glutSolidCube(size)


def draw_sphere(r=1.0):
    glutSolidSphere(r, 18, 16)


def draw_cylinder(r=0.2, h=1.0):
    q = gluNewQuadric()
    gluCylinder(q, r, r, h, 12, 3)


# Farhan (Bridge Platforms):
def draw_start_platform():
    glColor3f(0.9, 0.1, 0.1)
    half = COLS * TILE_SIZE * 0.55
    depth = TILE_SIZE * 2

    glBegin(GL_QUADS)
    glVertex3f(-half, 0, 0)
    glVertex3f(half, 0, 0)
    glVertex3f(half, 0, depth)
    glVertex3f(-half, 0, depth)
    glEnd()


def draw_end_platform():
    glColor3f(0.1, 0.1, 0.9)
    half = COLS * TILE_SIZE * 0.55
    depth = TILE_SIZE * 2
    zoff = row_to_z(ROWS)

    glBegin(GL_QUADS)
    glVertex3f(-half, 0, zoff)
    glVertex3f(half, 0, zoff)
    glVertex3f(half, 0, zoff + depth)
    glVertex3f(-half, 0, zoff + depth)
    glEnd()


# Farhan (Bridge Tiles):
def draw_bridge_tiles():
    global cheat_flash_timer
    for r in range(ROWS):
        for c in range(COLS):
            x, z = col_to_x(c), row_to_z(r)
            strong = (tile_type[r] == c)
            broken = tile_broken[r][c]

            glPushMatrix()
            glTranslatef(x, 0.03, z)
            if cheat_flash_timer > 0.0 and strong and not broken:
                glColor3f(0.1, 1.0, 0.1)  # reveal strong
            else:
                if broken:
                    glColor3f(0.0, 0.0, 0.0)  # broken = black
                else:
                    glColor3f(0.25, 0.9, 0.95)  # intact tile

            half = TILE_SIZE * 0.45
            glBegin(GL_QUADS)
            glVertex3f(-half, 0, -half)
            glVertex3f(half, 0, -half)
            glVertex3f(half, 0, half)
            glVertex3f(-half, 0, half)
            glEnd()
            glPopMatrix()


# Rezwan (Player rendering)
def draw_player_model():
    while fst_prs:
        return

    if not fst_prs:
        glPushMatrix()
        glTranslatef(p_x, p_y, p_z)
        glColor3f(0.2, 0.8, 0.45)
        glPushMatrix()
        glScalef(1.0, 1.5, 0.6)
        draw_cube(1.2)
        glPopMatrix()
        glColor3f(0.95, 0.85, 0.7)
        glPushMatrix()
        glTranslatef(0.0, 1.6, 0.0)
        draw_sphere(0.45)
        glPopMatrix()
        glColor3f(0.2, 0.6, 0.35)

        for dx in (-0.75, 0.75):
            glPushMatrix()
            glTranslatef(dx, 0.7, 0.0)
            glRotatef(90, 1, 0, 0)
            draw_cylinder(0.16, 1.1)
            glPopMatrix()
        glColor3f(0.95, 0.85, 0.7)

        for dx in (-0.32, 0.32):
            glPushMatrix()
            glTranslatef(dx, -1.0, 0.0)
            glRotatef(-90, 1, 0, 0)
            draw_cylinder(0.18, 1.6)
            glPopMatrix()
        glPopMatrix()


# Nusfat (Obstacles system)
def init_balls():
    balls.clear()
    lanes = sorted(random.sample(range(2, ROWS - 1), k=min(3, ROWS - 3)))
    for i, r in enumerate(lanes):
        z = row_to_z(r)
        x_range = abs(col_to_x(1)) * 1.8
        x = random.uniform(-x_range, x_range)
        vx = random.uniform(2.0, 4.0) * (1 if i % 2 == 0 else -1)
        balls.append([x, z, BALL_RADIUS, vx])


def draw_balls():
    glColor3f(1.0, 0.3, 0.2)
    for x, z, r, vx in balls:
        glPushMatrix()
        glTranslatef(x, 0.6, z)
        draw_sphere(r)
        glPopMatrix()


def update_balls(dt):
    half = abs(col_to_x(1)) * 1.8
    for i in range(len(balls)):
        x, z, r, vx = balls[i]
        x += vx * dt
        if vx > 0 and x > half:
            x = -half
        elif vx < 0 and x < -half:
            x = half
        balls[i][0] = x


def check_ball_collision():
    if falling:
        return
    px = p_x
    pz = p_z
    pr = 0.8
    for x, z, r, vx in balls:
        dx = px - x
        dz = pz - z
        if dx * dx + dz * dz <= (pr + r) ** 2:
            start_fall()
            break


# Farhan (Bridge Mechanics)
def try_move(row_delta = 0, col_delta =0, ignore_weak = False):
    global p_row, p_col, p_x, p_z, score

    if falling or paused or gameover: return
    target = p_row + row_delta

    if target > ROWS - 1:
        p_row = ROWS
        p_x, p_z = 0, row_to_z(ROWS) + TILE_SIZE
        finish_win()
        return

    nr = max(-1, min(ROWS - 1, target))
    nc = max(0, min(COLS - 1, p_col + col_delta))
    p_col, p_row = nc, nr
    p_x, p_z = col_to_x(p_col), (0.0 if p_row < 0 else row_to_z(p_row))

    if p_row < 0: return
    actual_row = get_player_row()
    strong_index = tile_type[actual_row]

    if p_col != strong_index and not ignore_weak:
        tile_broken[actual_row][p_col] = True
        start_fall()

    else:
        score += SAFE_SCORE
        tile_broken[actual_row][strong_index] = False


# Rezwan (Player fall/respawn)
def start_fall():
    global falling, fall_vz, fall_start
    falling = True
    fall_vz = -8.0
    fall_start = time.time()


def update_fall(dt):
    global p_y, fall_vz, falling
    fall_vz -= 30.0 * dt
    p_y += fall_vz * dt

    if p_y < -60.0:
        on_death()


def on_death():
    global lives, falling, p_row, p_col, p_x, p_y, p_z, fall_vz, gameover, running
    lives -= 1

    if lives > 0:
        p_row = -1
        p_col = 0
        p_x = col_to_x(p_col)
        p_y = 1.0
        p_z = 0.0
        fall_vz = 0.0
        falling = False

    if lives <= 0:
        gameover = True
        running = False
        falling = False
        return


def finish_win():
    global flag, running
    flag = True
    running = True


# Nusfat (Camera control)
def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(FovY, Window_Width / float(Window_Height), 0.1, 1000.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if fst_prs:
        eye_x = p_x
        eye_y = p_y + 1.5
        eye_z = p_z + 0.5
        look_distance = 8.0
        center_x = p_x
        center_y = p_y + 1.5
        center_z = p_z + look_distance
        gluLookAt(eye_x, eye_y, eye_z, center_x, center_y, center_z, 0, 1, 0)

    else:
        center_x = 0.0
        center_y = 0.0
        center_z = row_to_z(ROWS) * 0.5
        ch = math.radians(c_angle_h)
        cv = math.radians(c_angle_v)
        rx = Camera_distance * math.cos(cv) * math.sin(ch)
        ry = Camera_distance * math.cos(cv) * math.cos(ch)
        rz = Camera_distance * math.sin(cv)
        eye_x = center_x + rx
        eye_y = center_y + rz + 10.0
        eye_z = center_z + ry
        gluLookAt(eye_x, eye_y, eye_z, center_x, center_y, center_z, 0, 1, 0)


# Rezwan (HUD system)
def draw_hud():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, Window_Width, 0, Window_Height)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    draw_text(10, Window_Height - 20, f"Score: {score} Lives: {lives} Time: {int(time_left)}s")
    if paused:
        draw_text(Window_Width // 2 - 40, Window_Height // 2, "PAUSED")
    if gameover:
        draw_text(Window_Width // 2 - 90, Window_Height // 2, "GAME OVER - Press R")
    if flag:
        draw_text(Window_Width // 2 - 90, Window_Height // 2, "YOU MADE IT! - Press R")

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


# Rezwan (ties all together)
def display():
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, Window_Width, Window_Height)
    setupCamera()
    draw_start_platform()
    draw_bridge_tiles()
    draw_end_platform()
    draw_balls()
    draw_player_model()
    draw_hud()
    glutSwapBuffers()


# Nusfat (time + updates)
def idle():
    global last_time, time_left, cheat_flash_timer, start_time, gameover, running
    now = time.time()
    dt = now - last_time
    last_time = now
    if not running or paused: glutPostRedisplay(); return
    if falling: update_fall(dt)
    update_balls(dt)
    check_ball_collision()
    time_left = max(0, ROUND_TIME - (now - start_time))
    if time_left <= 0 and not gameover: gameover = True; running = False
    if cheat_flash_timer > 0.0: cheat_flash_timer = max(0.0, cheat_flash_timer - dt)
    glutPostRedisplay()


# Rezwan (Keyboard)
def keyboard(key, x, y):
    global paused, cheat_flash_timer, fst_prs

    if key == b'p':
        paused = not paused;
        return
    if key == b'r':
        reset_game()
        return
    if paused or not running or gameover:
        return

    if key == b'w':
        try_move(1, 0)
    elif key == b's':
        try_move(-1, 0)
    elif key == b'a':
        try_move(0, 1)
    elif key == b'd':
        try_move(0, -1)
    elif key == b'q':
        try_move(1, 1)
    elif key == b'e':
        try_move(1, -1)
    elif key == b'z':
        try_move(-1, 1)
    elif key == b'x':
        try_move(-1, -1)

    elif key == b'f':
        try_move(1, 0, ignore_weak = True)  # Farhan: cheat jump

    elif key == b'v':
        cheat_flash_timer = 2.0  # Farhan: cheat reveal

    elif key == b'c':
        fst_prs = not fst_prs


# Nusfat (special keys)
def special_key(key, x, y):
    global c_angle_h, c_angle_v
    if key == GLUT_KEY_LEFT:
        c_angle_h = (c_angle_h - 5) % 360
    elif key == GLUT_KEY_RIGHT:
        c_angle_h = (c_angle_h + 5) % 360
    elif key == GLUT_KEY_UP:
        c_angle_v = min(c_max_v, c_angle_v + 3)
    elif key == GLUT_KEY_DOWN:
        c_angle_v = max(c_min_v, c_angle_v - 3)


# Farhan (Bridge reset)
def reset_game():
    global p_row, p_col, p_x, p_y, p_z, falling, fall_vz
    global score, lives, start_time, time_left, gameover, flag, running
    global tile_type, tile_broken, cheat_flash_timer, balls, fst_prs

    p_row = -1
    p_col = 0
    p_x = col_to_x(p_col)
    p_y = 1.0
    p_z = 0.0
    falling = False
    fall_vz = 0.0
    score = 0
    lives = START_LIVES
    start_time = time.time()
    time_left = ROUND_TIME
    gameover = False
    flag = False
    running = True
    cheat_flash_timer = 0.0
    fst_prs = False
    tile_type[:] = [random.randint(0, COLS - 1) for _ in range(ROWS)]
    tile_broken[:] = [[False for _ in range(COLS)] for _ in range(ROWS)]
    init_balls()


def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(Window_Width, Window_Height)
    glutCreateWindow(b"3D Glass Bridge Game")
    glEnable(GL_DEPTH_TEST)
    glutDisplayFunc(display)
    glutIdleFunc(idle)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_key)
    reset_game()
    glutMainLoop()


if __name__ == "__main__":
    main()