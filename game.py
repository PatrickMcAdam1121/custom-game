import sys
import os
import json
import datetime
import traceback
import random

# --- Error Logging ---
def log_error_txt(error_message):
    log_file = "error_log.txt"
    timestamp = datetime.datetime.now().isoformat()
    entry = f"[{timestamp}]\n{error_message}\n\n"
    try:
        with open(log_file, "a") as f:
            f.write(entry)
    except Exception as e:
        print(f"Failed to write to error log: {e}")

try:
    from ursina import *
    from player import ImprovedFirstPersonController
    from shaders import create_shaders, apply_shader
except Exception as e:
    tb = traceback.format_exc()
    log_error_txt(f"Import error: {str(e)}\n{tb}")
    print("Import error. See error_log.txt for details.")
    sys.exit(1)

# --- Game Constants ---
ROOM_SIZE = 8
NUM_ROOMS = 8
DIRS = {'N': (0, 0, ROOM_SIZE), 'S': (0, 0, -ROOM_SIZE), 'E': (ROOM_SIZE, 0, 0), 'W': (-ROOM_SIZE, 0, 0)}
OPPOSITE = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}

# --- Room Class ---
class Room3D:
    def __init__(self, pos, id, has_stairs=False):
        try:
            self.id = id
            self.pos = pos
            self.doors = {}
            self.enemy = None
            self.loot = None
            self.wall_entities = {}
            self.door_defs = set()
            self.entities = []
            self.has_stairs = has_stairs
            
            # Create shaders with error handling
            try:
                self.lighting_shader, self.wall_shader = create_shaders()
            except Exception as e:
                log_error(f"Failed to create shaders: {str(e)}")
                self.lighting_shader = None
                self.wall_shader = None
            
            self.create_walls()
            
            if has_stairs:
                try:
                    self.stairs = Entity(
                        model='cube',
                        color=color.lime,
                        scale=(2, 2, 2),
                        position=(self.pos[0], 1, self.pos[2] - 2),
                        collider='box',
                        enabled=False
                    )
                    apply_shader(self.stairs, self.lighting_shader)
                    self.entities.append(self.stairs)
                except Exception as e:
                    log_error(f"Failed to create stairs: {str(e)}")
                    self.stairs = None
            else:
                self.stairs = None
                
        except Exception as e:
            log_error(f"Error in Room3D initialization: {str(e)}")
            raise

    def create_walls(self):
        try:
            wall_thickness = 0.5
            wall_height = 5
            
            # Create floor
            try:
                floor = Entity(
                    model='quad',
                    rotation_x=90,
                    scale=(ROOM_SIZE, ROOM_SIZE, 1),
                    position=(self.pos[0], 0, self.pos[2]),
                    color=color.dark_gray
                )
                apply_shader(floor, self.wall_shader)
                self.entities.append(floor)
            except Exception as e:
                log_error(f"Failed to create floor: {str(e)}")
            
            # Create walls
            walls = {
                'N': (self.pos[0], wall_height/2, self.pos[2] + ROOM_SIZE/2),
                'S': (self.pos[0], wall_height/2, self.pos[2] - ROOM_SIZE/2),
                'E': (self.pos[0] + ROOM_SIZE/2, wall_height/2, self.pos[2]),
                'W': (self.pos[0] - ROOM_SIZE/2, wall_height/2, self.pos[2])
            }
            
            for direction, pos in walls.items():
                try:
                    scale = (ROOM_SIZE, wall_height, wall_thickness) if direction in ['N', 'S'] else (wall_thickness, wall_height, ROOM_SIZE)
                    wall = Entity(
                        model='cube',
                        color=color.rgb(120, 70, 30),
                        scale=scale,
                        position=pos,
                        collider='box',
                        enabled=True
                    )
                    apply_shader(wall, self.wall_shader)
                    self.wall_entities[direction] = wall
                    self.entities.append(wall)
                except Exception as e:
                    log_error(f"Failed to create {direction} wall: {str(e)}")
                    
        except Exception as e:
            log_error(f"Error in create_walls: {str(e)}")
            raise

    def add_door(self, direction):
        self.door_defs.add(direction)

    def finalize_doors(self):
        door_width = 2
        door_height = 4
        wall_height = 5
        wall_thickness = 0.5
        for direction in self.door_defs:
            if direction == 'N':
                destroy(self.wall_entities['N'])
                left = Entity(model='cube', color=color.rgb(120, 70, 30),
                              scale=((ROOM_SIZE - door_width) / 2, wall_height, wall_thickness),
                              position=(self.pos[0] - (door_width / 2 + (ROOM_SIZE - door_width) / 4), wall_height / 2,
                                        self.pos[2] + ROOM_SIZE / 2),
                              collider='box', enabled=True)
                right = Entity(model='cube', color=color.rgb(120, 70, 30),
                               scale=((ROOM_SIZE - door_width) / 2, wall_height, wall_thickness),
                               position=(self.pos[0] + (door_width / 2 + (ROOM_SIZE - door_width) / 4), wall_height / 2,
                                         self.pos[2] + ROOM_SIZE / 2),
                               collider='box', enabled=True)
                door_pos = (self.pos[0], door_height / 2, self.pos[2] + ROOM_SIZE / 2 + 0.01)
                door = Entity(model='cube', color=color.yellow, scale=(door_width, door_height, 0.3),
                              position=door_pos, collider=None, enabled=True)
                self.entities += [left, right, door]
            elif direction == 'S':
                destroy(self.wall_entities['S'])
                left = Entity(model='cube', color=color.rgb(120, 70, 30),
                              scale=((ROOM_SIZE - door_width) / 2, wall_height, wall_thickness),
                              position=(self.pos[0] - (door_width / 2 + (ROOM_SIZE - door_width) / 4), wall_height / 2,
                                        self.pos[2] - ROOM_SIZE / 2),
                              collider='box', enabled=True)
                right = Entity(model='cube', color=color.rgb(120, 70, 30),
                               scale=((ROOM_SIZE - door_width) / 2, wall_height, wall_thickness),
                               position=(self.pos[0] + (doorWidth / 2 + (ROOM_SIZE - door_width) / 4), wall_height / 2,
                                         self.pos[2] - ROOM_SIZE / 2),
                               collider='box', enabled=True)
                door_pos = (self.pos[0], door_height / 2, self.pos[2] - ROOM_SIZE / 2 - 0.01)
                door = Entity(model='cube', color=color.yellow, scale=(door_width, door_height, 0.3),
                              position=door_pos, collider=None, enabled=True)
                self.entities += [left, right, door]
            elif direction == 'E':
                destroy(self.wall_entities['E'])
                left = Entity(model='cube', color=color.rgb(120, 70, 30),
                              scale=(wall_thickness, wall_height, (ROOM_SIZE - door_width) / 2),
                              position=(self.pos[0] + ROOM_SIZE / 2, wall_height / 2,
                                        self.pos[2] - (door_width / 2 + (ROOM_SIZE - door_width) / 4)),
                              collider='box', enabled=True)
                right = Entity(model='cube', color=color.rgb(120, 70, 30),
                               scale=(wall_thickness, wall_height, (ROOM_SIZE - door_width) / 2),
                               position=(self.pos[0] + ROOM_SIZE / 2, wall_height / 2,
                                         self.pos[2] + (door_width / 2 + (ROOM_SIZE - door_width) / 4)),
                               collider='box', enabled=True)
                door_pos = (self.pos[0] + ROOM_SIZE / 2 + 0.01, door_height / 2, self.pos[2])
                door = Entity(model='cube', color=color.yellow, scale=(0.3, door_height, door_width),
                              position=door_pos, collider=None, enabled=True)
                self.entities += [left, right, door]
            elif direction == 'W':
                destroy(self.wall_entities['W'])
                left = Entity(model='cube', color=color.rgb(120, 70, 30),
                              scale=(wall_thickness, wall_height, (ROOM_SIZE - door_width) / 2),
                              position=(self.pos[0] - ROOM_SIZE / 2, wall_height / 2,
                                        self.pos[2] - (door_width / 2 + (ROOM_SIZE - door_width) / 4)),
                              collider='box', enabled=True)
                right = Entity(model='cube', color=color.rgb(120, 70, 30),
                               scale=(wall_thickness, wall_height, (ROOM_SIZE - door_width) / 2),
                               position=(self.pos[0] - ROOM_SIZE / 2, wall_height / 2,
                                         self.pos[2] + (doorWidth / 2 + (ROOM_SIZE - door_width) / 4)),
                               collider='box', enabled=True)
                door_pos = (self.pos[0] - ROOM_SIZE / 2 - 0.01, door_height / 2, self.pos[2])
                door = Entity(model='cube', color=color.yellow, scale=(0.3, door_height, door_width),
                              position=door_pos, collider=None, enabled=True)
                self.entities += [left, right, door]
            self.doors[direction] = door

    def spawn_loot(self):
        self.loot = Entity(model='cube', color=color.green, scale=(0.7, 0.7, 0.7),
                           position=(self.pos[0] + 2, 1, self.pos[2]), collider='box', enabled=False)
        self.entities.append(self.loot)

    def set_visible(self, visible: bool):
        for e in self.entities:
            try:
                e.enabled = visible
            except AssertionError:
                print(f"Warning: Could not set visibility for entity {e}")
        if self.loot:
            self.loot.enabled = visible
        if self.has_stairs and self.stairs:
            self.stairs.enabled = visible

    def set_doors_visible(self, visible: bool):
        for direction, door in self.doors.items():
            if door:
                try:
                    door.enabled = visible
                except Exception as ex:
                    print(f"Warning: Could not set door visibility: {ex}")

# --- Dungeon Generation ---
rooms = {}

def generate_dungeon():
    rooms.clear()
    stairs_room = random.randint(1, NUM_ROOMS - 1)
    rooms[0] = Room3D((0, 0, 0), 0)
    for i in range(1, NUM_ROOMS):
        has_stairs = (i == stairs_room)
        while True:
            base_id = random.choice(list(rooms.keys()))
            base_pos = rooms[base_id].pos
            dir = random.choice(list(DIRS.keys()))
            new_pos = tuple(base_pos[j] + DIRS[dir][j] for j in range(3))
            if new_pos not in [r.pos for r in rooms.values()]:
                rooms[i] = Room3D(new_pos, i, has_stairs=has_stairs)
                rooms[base_id].add_door(dir)
                rooms[i].add_door(OPPOSITE[dir])
                break
    for i, room in rooms.items():
        if i != 0:
            if random.random() < 0.7:
                room.spawn_loot()
    for room in rooms.values():
        room.finalize_doors()
        room.set_visible(False)
    rooms[0].set_visible(True)
    rooms[0].set_doors_visible(True)

def preload_rooms(current_room_id, max_rooms=4):
    current_room = rooms[current_room_id]
    loaded_count = 0
    for i, room in rooms.items():
        if i != current_room_id:
            if (abs(room.pos[0] - current_room.pos[0]) < ROOM_SIZE * 2 and
                    abs(room.pos[2] - current_room.pos[2]) < ROOM_SIZE * 2):
                room.set_visible(True)
                room.set_doors_visible(True)
                loaded_count += 1
                if loaded_count >= max_rooms:
                    break

app = Ursina()

# --- UI Panels ---
def create_start_panel():
    return WindowPanel(
        title='Procedural Dungeon',
        content=(Text("Press SPACE to start", scale=2),),
        position=(0, 0),
        popup=True
    )

def create_tutorial_panel():
    return WindowPanel(
        title='Tutorial',
        content=(
            Text("Welcome to the Dungeon!", scale=1.5),
            Text("Controls:", scale=1.2),
            Text("WASD - Move", scale=1),
            Text("Mouse - Look around", scale=1),
            Text("E - Attack enemies (disabled)", scale=1),
            Text("ESC - Pause menu", scale=1),
            Text("Touch doors to enter new rooms", scale=1),
            Text("Collect gold and avoid enemies", scale=1),
            Button(text='Start Game', scale=(0.2, 0.05), on_click=lambda: start_game()),
            Button(text='Quit', scale=(0.2, 0.05), on_click=lambda: sys.exit()),
        ),
        position=(0, 0),
        popup=True
    )

def create_pause_menu():
    return WindowPanel(
        title='Pause Menu',
        content=(
            Text("PAUSED", scale=2),
            Button(text='Resume', scale=(0.2, 0.05), on_click=lambda: toggle_pause()),
            Button(text='Quit', scale=(0.2, 0.05), on_click=lambda: sys.exit()),
        ),
        position=(0, 0),
        popup=True
    )

# --- HUD Panel ---
hud_panel = Panel(
    parent=camera.ui,
    model='quad',
    color=color.black.tint(-0.7),
    scale=(0.5, 0.25),
    position=(-0.7, 0.4),
    enabled=True
)

fps_text = Text(
    parent=hud_panel,
    text='FPS: 0',
    position=(-0.22, 0.08),
    scale=1.2,
    background=False,
    color=color.white,
    origin=(0, 0),
    enabled=True
)

hp_text = Text(
    parent=hud_panel,
    text='HP: 30',
    position=(-0.22, 0.02),
    scale=1.2,
    background=False,
    color=color.red,
    enabled=True
)

gold_text = Text(
    parent=hud_panel,
    text='Gold: 0',
    position=(-0.22, -0.04),
    scale=1.2,
    background=False,
    color=color.yellow,
    enabled=True
)

lore_text = Text(
    parent=hud_panel,
    text='',
    position=(-0.22, -0.10),
    scale=1,
    background=False,
    color=color.white,
    enabled=True
)

# --- Minimap Feature ---
minimap_panel = Panel(
    parent=camera.ui,
    model='quad',
    color=color.black.tint(-0.7),
    scale=(0.18, 0.18),
    position=(0.7, 0.4),
    enabled=True
)
minimap_entities = []

def update_minimap(player_pos):
    # Clear previous minimap entities
    for e in minimap_entities:
        destroy(e)
    minimap_entities.clear()
    # Draw rooms
    for i, room in rooms.items():
        room_dot = Entity(
            parent=minimap_panel,
            model='circle',
            color=color.gray if i != current_room else color.azure,
            scale=0.02,
            position=(room.pos[0] / (ROOM_SIZE * NUM_ROOMS / 2), room.pos[2] / (ROOM_SIZE * NUM_ROOMS / 2), 0)
        )
        minimap_entities.append(room_dot)
    # Draw player
    player_dot = Entity(
        parent=minimap_panel,
        model='circle',
        color=color.orange,
        scale=0.025,
        position=(player_pos[0] / (ROOM_SIZE * NUM_ROOMS / 2), player_pos[2] / (ROOM_SIZE * NUM_ROOMS / 2), 0)
    )
    minimap_entities.append(player_dot)

game_started = False
game_paused = False
player = None
player_hp = 30
player_gold = 0
current_room = 0
lore_msgs = [
    "The blade whispers of betrayal.",
    "A journal entry: 'They sealed it behind the third door...'",
    "The gem pulses with forgotten sorrow."
]
lore_msg = ""

cursor = Entity(
    parent=camera.ui,
    model='quad',
    color=color.white,
    scale=.02,
    position=(0, 0)
)
cursor.visible = True

floor = Entity(
    model='plane',
    color=color.gray,
    scale=(ROOM_SIZE * 10, 1, ROOM_SIZE * 10),
    position=(0, -0.5, 0),
    collider='box',
    double_sided=True,
    enabled=True
)

window.vsync = True
window.shadows = False

tutorial_panel = create_tutorial_panel()
pause_menu = create_pause_menu()
pause_menu.enabled = False

def toggle_pause():
    global game_paused
    game_paused = not game_paused
    pause_menu.enabled = game_paused
    hud_panel.enabled = not game_paused
    minimap_panel.enabled = not game_paused
    if game_paused:
        mouse.locked = False
        cursor.visible = True
        if player:
            player.enabled = False
    else:
        mouse.locked = True
        cursor.visible = False
        if player:
            player.enabled = True

def start_game():
    global game_started, player, current_room, player_hp, player_gold, lore_msg, floor
    try:
        game_started = True
        tutorial_panel.enabled = False
        hud_panel.enabled = True
        minimap_panel.enabled = True

        # Initialize rooms
        try:
            for room in rooms.values():
                room.set_visible(False)
            rooms[0].set_visible(True)
            rooms[0].set_doors_visible(True)
        except Exception as e:
            log_error(f"Failed to initialize rooms: {str(e)}")

        current_room = 0
        player_hp = 30
        player_gold = 0
        lore_msg = ""

        # Create or reset player
        try:
            if player is None:
                player = ImprovedFirstPersonController(
                    position=(0, 1.5, 0),
                    model='capsule',
                    color=color.orange,
                    scale=(1, 2, 1)
                )
                player.collider = 'capsule'
                player.cursor.visible = True
            else:
                player.position = (0, 1.5, 0)
                player.enabled = True
        except Exception as e:
            log_error(f"Failed to create/reset player: {str(e)}")
            raise

        # Update UI
        try:
            floor.enabled = True
            hp_text.text = f'HP: {player_hp}'
            gold_text.text = f'Gold: {player_gold}'
            lore_text.text = ''
        except Exception as e:
            log_error(f"Failed to update UI: {str(e)}")

        # Set graphics options
        try:
            window.vsync = True
            window.fps_counter.enabled = True
            
            # Only enable shadows if the system supports it
            try:
                window.shadows_size = 2048
                window.shadows = True
            except Exception as shadow_error:
                log_error(f"Failed to enable shadows: {str(shadow_error)}")
                window.shadows = False
        except Exception as e:
            log_error(f"Failed to set graphics options: {str(e)}")

    except Exception as e:
        log_error(f"Fatal error in start_game: {str(e)}\n{traceback.format_exc()}")
        raise

def input(key):
    global game_started, lore_msg
    try:
        if not game_started and key == 'space':
            start_game()
        if not game_started:
            return
        if key == 'escape':
            toggle_pause()
        if key == 'right mouse down':
            mouse.locked = True
        if key == 'right mouse up':
            mouse.locked = False
    except Exception as e:
        tb = traceback.format_exc()
        log_error(tb)
        print("Error in input:", e)
        print(tb)
        window.title = "Error in input - see error_log.json"

def update():
    global player_hp, lore_msg, current_room, player_gold
    if not game_started or player is None or game_paused:
        fps_text.text = f'FPS: {int(1 / time.dt) if time.dt > 0 else "inf"}'
        return
    try:
        fps_text.text = f'FPS: {int(1 / time.dt) if time.dt > 0 else "inf"}'
        player_pos = player.position
        room_loaded = False
        for i, room in rooms.items():
            if i != current_room:
                for direction, door in room.doors.items():
                    if door:
                        dist = distance(player_pos, door.position)
                        if dist < 1.5:
                            rooms[current_room].set_visible(False)
                            room.set_visible(True)
                            room.set_doors_visible(True)
                            current_room = i
                            room_loaded = True
                            break
                if room_loaded:
                    break
        for i, room in rooms.items():
            if abs(player.x - room.pos[0]) < ROOM_SIZE / 2 and abs(player.z - room.pos[2]) < ROOM_SIZE / 2:
                if current_room != i:
                    rooms[current_room].set_visible(False)
                    room.set_visible(True)
                    room.set_doors_visible(True)
                    current_room = i
                break
        preload_rooms(current_room, max_rooms=4)
        room = rooms[current_room]
        if room.loot and player.intersects(room.loot).hit and room.loot.enabled:
            lore_msg = random.choice(lore_msgs)
            player_gold += random.randint(1, 5)
            room.loot.enabled = False
        if room.stairs and distance(player.position, room.stairs.position) < 2:
            lore_msg = "You ascend the stairs!"
            player.position = (0, 1, 0)
            generate_dungeon()
            preload_rooms(0, max_rooms=4)
        hp_text.text = f'HP: {player_hp}'
        gold_text.text = f'Gold: {player_gold}'
        lore_text.text = lore_msg
        update_minimap(player.position)
    except Exception as e:
        tb = traceback.format_exc()
        log_error(tb)
        print("Error in update:", e)
        print(tb)
        window.title = "Error in update - see error_log.json"

app.input = input
app.update = update

if __name__ == "__main__":
    try:
        generate_dungeon()
        preload_rooms(0, max_rooms=4)
        app.run()
    except Exception as e:
        tb = traceback.format_exc()
        log_error_txt(f"Fatal error: {str(e)}\n{tb}")
        print("Fatal error. See error_log.txt for details.")
        input("Press Enter to exit...")
        sys.exit(1)