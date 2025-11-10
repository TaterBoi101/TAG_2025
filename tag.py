import pygame
import random
import math
import dataclasses
from typing import Optional

pygame.init()

WIDTH, HEIGHT = 1400, 1400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Polygon Collision (Any Shape)')
font = pygame.font.SysFont(None, 40)

# --- COLORS ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
SKYBLUE = (135, 206, 235)
GREEN = (0, 255, 0)
GRASSGREEN = (34, 139, 34)
PURPLE = (180, 0, 255)

clock = pygame.time.Clock()
font = pygame.font.SysFont("Comic Sans MS", 50)
FPS = 60
gravity = 0.5
playerMaxFall = 15
player2MaxFall = 15

# --- LEVEL OBJECTS (unchanged) ---
level_objects = [
    # Level 0: Snow
    [
        [(0, HEIGHT-100), (0, HEIGHT), (WIDTH, HEIGHT), (WIDTH, HEIGHT-100)],
    ],
    # Level 1: Desert
    [
        [(0, HEIGHT-100), (0, HEIGHT), (WIDTH, HEIGHT), (WIDTH, HEIGHT-100)],
    ],
    # Level 2: Plains (original layout)
    [
        [(0, HEIGHT - 100), (0, HEIGHT), (WIDTH, HEIGHT), (WIDTH, HEIGHT - 100)],
    ],
    # Level 3: Gravity Level
    [
        [(0, 100), (0, 0), (WIDTH, 0), (WIDTH, 100)],
    ]
]

level_configs = [
    # Level 0: Snow
    {
        "objects": level_objects[0],
        "gravity": 0.5,
        "playerJump": 15,
        "playerSize": 10,
        "playerSpeed": 50,
        "playerMaxFall": 15
    },
    # Level 1: Desert
    {
        "objects": level_objects[1],
        "gravity": 0.6,
        "playerJump": 18,
        "playerSize": 25,
        "playerSpeed": 8,
        "playerMaxFall": 18
    },
    # Level 2: Plains
    {
        "objects": level_objects[2],
        "gravity": 0.5,
        "playerJump": 15,
        "playerSize": 22,
        "playerSpeed": 7,
        "playerMaxFall": 15
    },
    # Level 3: Gravity
    {
        "objects": level_objects[3],
        "gravity": -0.7,
        "playerJump": 20,
        "playerSize": 20,
        "playerSpeed": 9,
        "playerMaxFall": 20
    }
]

# --- LOAD LEVEL TEXTURES ---
# If you don't have these images, comment these lines out or provide placeholder surfaces.
snow_texture = pygame.image.load("snowLevel.png").convert_alpha()
desert_texture = pygame.image.load("desertLevel.png").convert_alpha()
plain_texture = pygame.image.load("plainLevel.png").convert_alpha()
gravity_texture = pygame.image.load("gravityLevel.png").convert_alpha()
level_textures = [snow_texture, desert_texture, plain_texture, gravity_texture]

# --- SCALE LEVEL TEXTURES ---
levelWidth, levelHeight = 300, 300
for i in range(len(level_textures)):
    level_textures[i] = pygame.transform.scale(level_textures[i], (levelWidth, levelHeight))

# --- PORTAL SIZE + ANIMATION SETUP (put this before loading images) ---
portal_radius = 30           # <-- must be defined before scaling frames
bobbing_time = 0
portal_frame_index = 0.0     # use float so you can advance by fractional steps
PORTAL_FRAME_COUNT = 8       # portal0.png .. portal7.png

# --- Load portal animation frames ---
portal_frames = []
for i in range(PORTAL_FRAME_COUNT):
    path = f"portal{i}.png"
    try:
        img = pygame.image.load(path).convert_alpha()
    except Exception as e:
        # fallback: make a simple circle surface if file missing (avoids crashes)
        img = pygame.Surface((portal_radius*2, portal_radius*2), pygame.SRCALPHA)
        pygame.draw.circle(img, PURPLE, (portal_radius, portal_radius), portal_radius)
    # scale to match portal_radius (use smoothscale for nicer quality)
    img = pygame.transform.scale(img, (int(portal_radius*2), int(portal_radius*2)))

    portal_frames.append(img)

#buff textures
buff_img = pygame.image.load("jumpbuff.png").convert_alpha()
BUFF_RADIUS = 40  # size of the buff on screen
buff_img = pygame.transform.scale(buff_img, (BUFF_RADIUS * 2, BUFF_RADIUS * 2))




# --- LEVEL BUTTONS (2x2 GRID) ---
levelNumber = len(level_textures)
levels = []

cols = 2
rows = math.ceil(levelNumber / cols)
levelSpacing = 80

# Compute total width/height for grid
totalWidth = cols * levelWidth + (cols - 1) * levelSpacing
totalHeight = rows * levelHeight + (rows - 1) * levelSpacing

startX = (WIDTH - totalWidth) // 2
startY = (HEIGHT - totalHeight) // 2

for i in range(levelNumber):
    row = i // cols
    col = i % cols
    x = startX + col * (levelWidth + levelSpacing)
    y = startY + row * (levelHeight + levelSpacing)
    levels.append(pygame.Rect(x, y, levelWidth, levelHeight))

# --- LEVEL SELECT SCREEN ---
settingUp = True
selectedLevel = None
while settingUp:
    screen.fill(SKYBLUE)
    mouse_pos = pygame.mouse.get_pos()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(levels):
                if rect.collidepoint(mouse_pos):
                    selectedLevel = i
                    settingUp = False
    for i, rect in enumerate(levels):
        hovered = rect.collidepoint(mouse_pos)
        screen.blit(level_textures[i], rect.topleft)
        outline_rect = rect.copy()
        if hovered:
            outline_rect.inflate_ip(10, 10)
        pygame.draw.rect(screen, BLACK, outline_rect, 6)

    pygame.display.flip()
    clock.tick(FPS)

# --- SET SELECTED LEVEL OBJECTS & CONFIG ---
selected_config = level_configs[selectedLevel]
objects = selected_config["objects"]
gravity = selected_config["gravity"]
playerJump = selected_config["playerJump"]
player2Jump = selected_config["playerJump"]
playerSize = selected_config["playerSize"]
player2Size = selected_config["playerSize"]

playerSpeed = selected_config["playerSpeed"]
player2Speed = selected_config["playerSpeed"]
playerMaxFall = selected_config["playerMaxFall"]
player2MaxFall = selected_config["playerMaxFall"]

# Re-create player rects & masks with the new size
player = pygame.Rect(WIDTH // 2 + 20, HEIGHT // 2, playerSize, playerSize)
player_surf = pygame.Surface((playerSize, playerSize), pygame.SRCALPHA)
pygame.draw.rect(player_surf, WHITE, (0, 0, playerSize, playerSize))
player_mask = pygame.mask.from_surface(player_surf)

player2 = pygame.Rect(WIDTH // 2 - 20, HEIGHT // 2, player2Size, player2Size)
player2_surf = pygame.Surface((player2Size, player2Size), pygame.SRCALPHA)
pygame.draw.rect(player2_surf, WHITE, (0, 0, player2Size, player2Size))
player2_mask = pygame.mask.from_surface(player2_surf)

# --- CREATE MASKS FOR OBJECTS ---
object_surfaces = []
object_masks = []
for verts in objects:
    surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.polygon(surf, WHITE, verts)
    mask = pygame.mask.from_surface(surf)
    object_surfaces.append(surf)
    object_masks.append(mask)

# --- PLAYER SETUP (APPLY LEVEL CONFIG) ---
playerColor = RED
playerVelY = 0
player_surf = pygame.Surface((playerSize, playerSize), pygame.SRCALPHA)
pygame.draw.rect(player_surf, WHITE, (0, 0, playerSize, playerSize))
player_mask = pygame.mask.from_surface(player_surf)

player2Color = BLUE
player2VelY = 0
player2_surf = pygame.Surface((player2Size, player2Size), pygame.SRCALPHA)
pygame.draw.rect(player2_surf, WHITE, (0, 0, player2Size, player2Size))
player2_mask = pygame.mask.from_surface(player2_surf)

tagger = random.randint(1, 2)
tagging = False
roundTime = 60

# --- MISSING GLOBALS (added) ---
screen_rect = pygame.Rect(0, 0, WIDTH, HEIGHT)
portal_radius = 20
bobbing_time = 0

# Teleport placeholders
player_teleport = {"active": False, "target": None, "progress": 0}
player2_teleport = {"active": False, "target": None, "progress": 0}

# ceiling flags (needed before first jump checks)
on_ground = False
on_ground2 = False
on_ceiling = False
on_ceiling2 = False

# -- BUFFS (refactor) ---
BUFF_RADIUS = 12
MAX_ACTIVE_BUFFS = 3  # unchanged

@dataclasses.dataclass
class BuffInstance:
    pos: list            # [x, y]
    type_name: str
    active: bool         # on-ground (not applied)
    timer: int           # countdown while applied (0 if not applied)
    bobbing_offset: float
    config: dict
    applied_to: Optional[str] = None  # "player1" or "player2" or None

# buff base values for restore
playerBaseSpeed = selected_config["playerSpeed"]
playerBaseJump = selected_config["playerJump"]
playerBaseSize = playerSize
player2BaseSpeed = selected_config["playerSpeed"]
player2BaseJump = selected_config["playerJump"]
player2BaseSize = player2Size

def _apply_speed(player_num, player_rect, player_stats, conf):
    player_stats["speed"] *= conf["multiplier"]
    return None

def _remove_speed(player_num, player_rect, player_stats, conf):
    if player_num == 1:
        player_stats["speed"] = playerBaseSpeed
    else:
        player_stats["speed"] = player2BaseSpeed
    return None

def _apply_jump(player_num, player_rect, player_stats, conf):
    player_stats["jump"] *= conf["multiplier"]
    return None

def _remove_jump(player_num, player_rect, player_stats, conf):
    if player_num == 1:
        player_stats["jump"] = playerBaseJump
    else:
        player_stats["jump"] = player2BaseJump
    return None

def _apply_size(player_num, player_rect, player_stats, conf):
    old_bottom = player_rect.bottom
    old_centerx = player_rect.centerx
    w_inflate, h_inflate = conf["inflate"]

    # new size
    new_width = player_rect.width + w_inflate
    new_height = player_rect.height + h_inflate

    # update rect size but keep horizontal center & bottom (so player grows upward)
    player_rect.width = new_width
    player_rect.height = new_height
    player_rect.centerx = old_centerx
    player_rect.bottom = old_bottom

    # create new surface and mask
    surf = pygame.Surface((player_rect.width, player_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, WHITE, (0, 0, player_rect.width, player_rect.height))
    new_mask = pygame.mask.from_surface(surf)

    # If this new size intersects level geometry, nudge the player up until it fits.
    # Use a loop with a safety cap so we don't get stuck in an infinite loop.
    attempts = 0
    max_attempts = 200
    while attempts < max_attempts:
        collided = False
        for mask in object_masks:
            if mask.overlap(new_mask, (player_rect.x, player_rect.y)):
                collided = True
                break
        if not collided:
            break
        player_rect.y -= 1
        attempts += 1

    # If we couldn't resolve overlap, move the player a little higher as a fallback.
    if attempts == max_attempts:
        player_rect.y -= 10

    return new_mask


def _remove_size(player_num, player_rect, player_stats, conf):
    # restore base size
    if player_num == 1:
        base = playerBaseSize
    else:
        base = player2BaseSize

    old_bottom = player_rect.bottom
    old_centerx = player_rect.centerx

    player_rect.width = base
    player_rect.height = base
    player_rect.bottom = old_bottom
    player_rect.centerx = old_centerx

    surf = pygame.Surface((player_rect.width, player_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, WHITE, (0, 0, player_rect.width, player_rect.height))
    return pygame.mask.from_surface(surf)


def _apply_shield(player_num, player_rect, player_stats, conf):
    player_stats["shield"] = True
    return None

def _remove_shield(player_num, player_rect, player_stats, conf):
    player_stats.pop("shield", None)
    return None

def _apply_freeze(player_num, player_rect, player_stats, conf):
    enemy = player_stats["enemy_stats"]
    enemy["speed"] *= conf["slow_factor"]
    enemy["frozen"] = True
    print(f"Freeze applied to player {'2' if player_num == 1 else '1'}! New speed: {enemy['speed']}")



def _remove_freeze(player_num, player_rect, player_stats, conf):
    # Restore the other player’s speed
    if player_num == 1:
        enemy_stats = player_stats["enemy_stats"]
    else:
        enemy_stats = player_stats["enemy_stats"]

    if "frozen" in enemy_stats:
        enemy_stats["speed"] = enemy_stats["base_speed"]
        del enemy_stats["frozen"]


buff_defs = {
    "speed": {
        "color": (255, 215, 0),
        "duration": FPS * 5,
        "multiplier": 2,
        "apply": _apply_speed,
        "remove": _remove_speed
    },
    "jump": {
        "color": (0, 255, 255),
        "duration": FPS * 5,
        "multiplier": 1.5,
        "apply": _apply_jump,
        "remove": _remove_jump
    },
    "size": {
        "color": (255, 0, 255),
        "duration": FPS * 5,
        "inflate": (15, 15),
        "apply": _apply_size,
        "remove": _remove_size
    },
    "shield": {
        "color": (150, 150, 255),
        "duration": FPS * 10,
        "apply": _apply_shield,
        "remove": _remove_shield
    },
    "freeze": {
        "color": (100, 200, 255),
        "duration": FPS * 3,        # lasts 3 seconds
        "slow_factor": 0.1,         # slows opponent to 10% of normal speed
        "apply": _apply_freeze,
        "remove": _remove_freeze
    }

}

# --- Buff Textures ---
BUFF_RADIUS = 30  # visual size of buffs

def load_buff_image(path):
    try:
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.scale(img, (BUFF_RADIUS * 2, BUFF_RADIUS * 2))
        # keep pixel art crisp
        img = pygame.transform.scale(img, (BUFF_RADIUS * 2, BUFF_RADIUS * 2))
    except Exception as e:
        print(f"[!] Could not load image {path}: {e}")
        img = pygame.Surface((BUFF_RADIUS * 2, BUFF_RADIUS * 2), pygame.SRCALPHA)
        pygame.draw.circle(img, (100, 200, 255), (BUFF_RADIUS, BUFF_RADIUS), BUFF_RADIUS)
        pygame.draw.circle(img, (0, 0, 0), (BUFF_RADIUS, BUFF_RADIUS), BUFF_RADIUS, 3)
        pygame.draw.line(img, (255, 255, 255), (5, BUFF_RADIUS), (BUFF_RADIUS*2-5, BUFF_RADIUS), 3)

    return img

jump_buff_img = load_buff_image("jumpbuff.png")
freeze_buff_img = load_buff_image("freezebuff.png")
grow_buff_img = load_buff_image("growbuff.png")
shield_buff_img = load_buff_image("shieldbuff.png")
speed_buff_img = load_buff_image("speedbuff.png")

buffs = []

def spawn_buff(objects, gravity=0.5):
    verts = random.choice(objects)
    min_x = min(x for x, _ in verts)
    max_x = max(x for x, _ in verts)

    if gravity >= 0:
        # spawn above the platform (normal)
        y = min(y for _, y in verts) - 20
    else:
        # spawn below the platform (gravity flipped)
        y = max(y for _, y in verts) + 20

    # clamp so buffs don't spawn off-screen
    y = max(BUFF_RADIUS, min(HEIGHT - BUFF_RADIUS, y))
    x = random.randint(min_x + 20, max_x - 20)
    
    type_name = random.choice(list(buff_defs.keys()))
    conf = buff_defs[type_name]
    return BuffInstance(
        pos=[x, y],
        type_name=type_name,
        active=True,
        timer=0,
        bobbing_offset=random.uniform(0, 2*math.pi),
        config=conf,
        applied_to=None
    )



def draw_buffs():
    for buff in buffs:
        if not buff.active:
            continue
        x, y = int(buff.pos[0]), int(buff.pos[1])
        if buff.type_name == "jump":
            screen.blit(jump_buff_img, jump_buff_img.get_rect(center=(x, y)))
        elif buff.type_name == "freeze":
            screen.blit(freeze_buff_img, freeze_buff_img.get_rect(center=(x, y)))
        elif buff.type_name == "size":
            screen.blit(grow_buff_img, grow_buff_img.get_rect(center=(x, y)))
        elif buff.type_name == "shield":
            screen.blit(shield_buff_img, shield_buff_img.get_rect(center=(x, y)))
        elif buff.type_name == "speed":
            screen.blit(speed_buff_img, speed_buff_img.get_rect(center=(x, y)))


        else:
            pygame.draw.circle(screen, buff.config["color"], (x, y), BUFF_RADIUS)
            pygame.draw.circle(screen, BLACK, (x, y), BUFF_RADIUS, 2)



def update_buffs(player1_stats, player2_stats, player, player2):
    global player_mask, player2_mask
    for buff in buffs:
        # bobbing
        buff.pos[1] += math.sin(pygame.time.get_ticks() * 0.005 + buff.bobbing_offset) * 0.5

        if buff.timer > 0:
            buff.timer -= 1
            if buff.timer <= 0:
                if buff.applied_to is not None:
                    player_num = 1 if buff.applied_to == "player1" else 2
                    if player_num == 1:
                        maybe_mask = buff.config["remove"](player_num, player, player1_stats, buff.config)
                        if maybe_mask is not None:
                            player_mask = maybe_mask
                    else:
                        maybe_mask = buff.config["remove"](player_num, player2, player2_stats, buff.config)
                        if maybe_mask is not None:
                            player2_mask = maybe_mask
                buff.active = False
                buff.applied_to = None
                buff.timer = 0



def check_player_pickup(player_rect, player_stats, current_mask, player_num=1):
    global buffs
    for buff in buffs:
        if not buff.active:
            continue
        bx, by = buff.pos
        buff_rect = pygame.Rect(int(bx - BUFF_RADIUS), int(by - BUFF_RADIUS), BUFF_RADIUS*2, BUFF_RADIUS*2)
        if player_rect.colliderect(buff_rect) and buff.timer == 0:
            buff.active = False
            buff.timer = buff.config["duration"]
            buff.applied_to = "player1" if player_num == 1 else "player2"

            if player_num == 1:
                maybe_mask = buff.config["apply"](player_num, player_rect, player_stats, buff.config)
                if maybe_mask is not None:
                    current_mask = maybe_mask
            else:
                maybe_mask = buff.config["apply"](player_num, player_rect, player_stats, buff.config)
                if maybe_mask is not None:
                    current_mask = maybe_mask
    return current_mask

# player stats dictionary
player1_stats = {"speed": playerSpeed, "jump": playerJump}
player2_stats = {"speed": player2Speed, "jump": player2Jump}

# link each player's stats to the other's
player1_stats["enemy_stats"] = player2_stats
player2_stats["enemy_stats"] = player1_stats

# store base speed for unfreezing later
player1_stats["base_speed"] = playerSpeed
player2_stats["base_speed"] = player2Speed


def get_random_portal_position(objects, offset_y=15):
    verts = random.choice(objects)
    top_y = min(y for _, y in verts)
    min_x = min(x for x, _ in verts)
    max_x = max(x for x, _ in verts)
    x = random.randint(min_x + 20, max_x - 20)
    y = top_y - offset_y
    return [x, y]

portals = {"active": True, "positions": [get_random_portal_position(objects), get_random_portal_position(objects)], "cooldown": 0}

def resolve_collision(rect, rect_mask, object_masks, dx, dy, gravity, max_fall, max_jump=None, step_height=10):
    on_ground = False
    on_ceiling = False  # for upward collision

    # --- HORIZONTAL MOVE ---
    if dx != 0:
        rect.x += dx
        collided = any(mask.overlap(rect_mask, (rect.x, rect.y)) for mask in object_masks)
        if collided:
            for step in range(1, step_height + 1):
                rect.y -= 1
                for mask in object_masks:
                    if mask.overlap(rect_mask, (rect.x, rect.y)):
                        break
                else:
                    collided = False
                    break
            if collided:
                rect.x -= dx
                rect.y += step

    # --- VERTICAL MOVE (step-by-step) ---
    dy += gravity

    # cap downward (fall) velocity
    if dy > max_fall:
        dy = max_fall

    # cap upward (jump) velocity with a separate limit if provided
    if max_jump is None:
        # default behavior: symmetric cap (old behavior)
        if dy < -max_fall:
            dy = -max_fall
    else:
        if dy < -abs(max_jump):
            dy = -abs(max_jump)

    step = int(abs(dy))
    if step == 0:
        step = 1
    step_sign = 1 if dy > 0 else -1

    for _ in range(step):
        rect.y += step_sign
        for mask in object_masks:
            if mask.overlap(rect_mask, (rect.x, rect.y)):
                # Undo the last step
                rect.y -= step_sign
                dy = 0
                if step_sign > 0:
                    on_ground = True   # landing on floor
                else:
                    on_ceiling = True  # hitting ceiling
                break
        else:
            continue
        break  # collision happened, stop moving

    return rect, dy, on_ground, on_ceiling


def handle_portal_teleport(player, teleport, portals):
    if teleport["active"]:
        teleport["progress"] += 0.02
        if teleport["progress"] >= 1:
            teleport["active"] = False
            teleport["progress"] = 0
            player.center = teleport["target"]
        else:
            player.centerx += (teleport["target"][0] - player.centerx) * 0.1
            player.centery += (teleport["target"][1] - player.centery) * 0.1
        return
    if not portals["active"]:
        return
    px, py = player.center
    for i, (px_portal, py_portal) in enumerate(portals["positions"]):
        dist = ((px - px_portal) ** 2 + (py - py_portal) ** 2) ** 0.5
        if dist < portal_radius + player.width // 2:
            teleport["active"] = True
            teleport["progress"] = 0
            teleport["target"] = (
                portals["positions"][1][0], portals["positions"][1][1] - 30
            ) if i == 0 else (
                portals["positions"][0][0], portals["positions"][0][1] - 30
            )
            portals["active"] = False
            portals["cooldown"] = FPS * 10
            break

# --- MAIN GAME LOOP ---
startTime = pygame.time.get_ticks()
running = True

while running:
    # spawn control: only spawn simple on-screen buffs if fewer than MAX_ACTIVE_BUFFS active and not applied
    if random.random() < 0.01 and len([b for b in buffs if b.active and b.timer == 0]) < MAX_ACTIVE_BUFFS:
        buffs.append(spawn_buff(objects, gravity))


    # update buffs and pickups
    update_buffs(player1_stats, player2_stats, player, player2)
    player_mask = check_player_pickup(player, player1_stats, player_mask, player_num=1)
    player2_mask = check_player_pickup(player2, player2_stats, player2_mask, player_num=2)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    # extra random spawn (keeps original behaviour)
    if random.random() < 0.005 and len(buffs) < 3:
        buffs.append(spawn_buff(objects))

    # --- PLAYER 1 MOVEMENT ---
    dx = -player1_stats["speed"] if keys[pygame.K_a] else player1_stats["speed"] if keys[pygame.K_d] else 0
    if keys[pygame.K_w]:
        jump_strength = player1_stats["jump"]
        if gravity > 0 and on_ground:
            playerVelY = -abs(jump_strength)
            on_ground = False
        elif gravity < 0 and on_ceiling:
            playerVelY = abs(jump_strength)
            on_ceiling = False


    if not player_teleport["active"]:
        # compute a max_jump that's at least as large as the default cap so small jumps are unchanged
        player_max_jump = max(abs(player1_stats["jump"]), playerMaxFall)
        player, playerVelY, on_ground, on_ceiling = resolve_collision(player, player_mask, object_masks, dx, playerVelY, gravity, playerMaxFall, max_jump=player_max_jump)

    else:
        on_ground = False

    # --- PLAYER 2 MOVEMENT ---
    dx2 = -player2_stats["speed"] if keys[pygame.K_LEFT] else player2_stats["speed"] if keys[pygame.K_RIGHT] else 0
    if keys[pygame.K_UP]:
        if gravity > 0 and on_ground2:
            player2VelY = -abs(player2_stats["jump"])
            on_ground2 = False
        elif gravity < 0 and on_ceiling2:
            player2VelY = abs(player2_stats["jump"])
            on_ceiling2 = False

    if not player2_teleport["active"]:
        player2_max_jump = max(abs(player2_stats["jump"]), player2MaxFall)
        player2, player2VelY, on_ground2, on_ceiling2 = resolve_collision(player2, player2_mask, object_masks, dx2, player2VelY, gravity, player2MaxFall, max_jump=player2_max_jump)

    else:
        on_ground2 = False

    # clamp
    player.clamp_ip(screen_rect)
    player2.clamp_ip(screen_rect)

    # --- Tagging with shield logic ---
    p1_shield = player1_stats.get("shield", False)
    p2_shield = player2_stats.get("shield", False)

    if player.colliderect(player2) and tagging:
        tagging = False
        # Check shields: tag only if the player being tagged has no shield
        if tagger == 1 and not p2_shield:
            tagger = 2
        elif tagger == 2 and not p1_shield:
            tagger = 1
    
    if not player.colliderect(player2):
        tagging = True

    taggerTri = ([(player.x, player.y - 30), (player.x + (playerSize // 2), player.y - 20), (player.x + playerSize, player.y - 30)]
                 if tagger == 1 else
                 [(player2.x, player2.y - 30), (player2.x + (player2Size // 2), player2.y - 20), (player2.x + player2Size, player2.y - 30)])

    # update time
    currentTime = pygame.time.get_ticks() - startTime
    timeSurface = font.render(str(currentTime // 1000), True, BLACK)
    if roundTime * 1000 <= currentTime:
        running = False

    # portals
    handle_portal_teleport(player, player_teleport, portals)
    handle_portal_teleport(player2, player2_teleport, portals)
    if not portals["active"]:
        if portals["cooldown"] > 0:
            portals["cooldown"] -= 1
        else:
            portals["positions"] = [get_random_portal_position(objects), get_random_portal_position(objects)]
            portals["active"] = True

    # --- DRAW EVERYTHING ---
    screen.fill(SKYBLUE)
    for verts in objects:
        pygame.draw.polygon(screen, GRASSGREEN, verts)
        pygame.draw.polygon(screen, BLACK, verts, 3)
    pygame.draw.polygon(screen, WHITE, taggerTri)
    pygame.draw.polygon(screen, BLACK, taggerTri, 1)

    # player 1 draw
    if player_teleport["active"]:
        size = int(playerSize * (1 - player_teleport["progress"] * 0.8))
        pygame.draw.rect(screen, WHITE, pygame.Rect(player.centerx - size // 2, player.centery - size // 2, size, size))
    else:
        pygame.draw.rect(screen, playerColor, player)
        pygame.draw.rect(screen, BLACK, player, 2)

    # player 2 draw
    if player2_teleport["active"]:
        size = int(player2Size * (1 - player2_teleport["progress"] * 0.8))
        pygame.draw.rect(screen, WHITE, pygame.Rect(player2.centerx - size // 2, player2.centery - size // 2, size, size))
    else:
        pygame.draw.rect(screen, player2Color, player2)
        pygame.draw.rect(screen, BLACK, player2, 2)

    # --- draw portals ---
    if portals["active"]:
        bobbing_time += 0.05
        bob_offset = math.sin(bobbing_time) * 5

        # Update frame index (speed controls animation speed)
        portal_frame_index = (portal_frame_index + 0.2) % len(portal_frames)
        current_frame = portal_frames[int(portal_frame_index)]

        # Calculate bob positions
        portal1_draw = (portals["positions"][0][0], portals["positions"][0][1] + bob_offset)
        portal2_draw = (portals["positions"][1][0], portals["positions"][1][1] - bob_offset)

        # Draw both portals
        rect1 = current_frame.get_rect(center=portal1_draw)
        rect2 = current_frame.get_rect(center=portal2_draw)
        screen.blit(current_frame, rect1)
        screen.blit(current_frame, rect2)



    # draw buffs (new system)
    draw_buffs()

    screen.blit(timeSurface, (WIDTH // 2, 10))
    pygame.display.flip()
    clock.tick(FPS)

# --- GAME OVER ---
print(f"PLAYER {2 if tagger == 1 else 1} WINS")
pygame.quit()