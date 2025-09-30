import sys
import os
import json
import datetime
import traceback
from ursina import *

app = Ursina()

# --- Robust JSON error logger ---
def log_error_json(error_message: str, error_type: str = "Exception"):
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "type": error_type,
        "message": error_message
    }
    log_file = "error_log.json"
    if os.path.exists(log_file):
        try:
            with open(log_file, "r") as f:
                data = json.load(f)
        except Exception:
            data = []
    else:
        data = []
    data.append(log_entry)
    with open(log_file, "w") as f:
        json.dump(data, f, indent=2)

try:
    from ursina.prefabs.first_person_controller import FirstPersonController
    import random

    # --- Game Constants ---
    ROOM_SIZE = 8
    NUM_ROOMS = 8
    DIRS = {'N': (0, 0, ROOM_SIZE), 'S': (0, 0, -ROOM_SIZE), 'E': (ROOM_SIZE, 0, 0), 'W': (-ROOM_SIZE, 0, 0)}
    OPPOSITE = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}

    # --- Room Class ---
    class Room3D:
        def __init__(self, pos, id, has_stairs=False):
            self.id = id
            self.pos = pos
            self.doors = {}
            self.enemy = None
            self.loot = None
            self.wall_entities = {}
            self.door_defs = set()
            self.entities = []
            self.has_stairs = has_stairs
            self.create_walls()
            if has_stairs:
                self.stairs = Entity(model='cube', color=color.lime, scale=(2,2,2), position=(self.pos[0],1,self.pos[2]-2), collider='box', enabled=False)
                self.entities.append(self.stairs)

        def create_walls(self):
            wall_thickness = 0.5
            wall_height = 5  # Increased from 3 to 5
            n = Entity(model='cube', color=color.rgb(120, 70, 30),
                       scale=(ROOM_SIZE, wall_height, wall_thickness),
                       position=(self.pos[0], wall_height/2, self.pos[2] + ROOM_SIZE/2), collider='box', enabled=False)
            s = Entity(model='cube', color=color.rgb(120, 70, 30),
                       scale=(ROOM_SIZE, wall_height, wall_thickness),
                       position=(self.pos[0], wall_height/2, self.pos[2] - ROOM_SIZE/2), collider='box', enabled=False)
            e = Entity(model='cube', color=color.rgb(120, 70, 30),
                       scale=(wall_thickness, wall_height, ROOM_SIZE),
                       position=(self.pos[0] + ROOM_SIZE/2, wall_height/2, self.pos[2]), collider='box', enabled=False)
            w = Entity(model='cube', color=color.rgb(120, 70, 30),
                       scale=(wall_thickness, wall_height, ROOM_SIZE),
                       position=(self.pos[0] - ROOM_SIZE/2, wall_height/2, self.pos[2]), collider='box', enabled=False)
            self.wall_entities = {'N': n, 'S': s, 'E': e, 'W': w}
            self.entities += [n, s, e, w]

        def add_door(self, direction):
            self.door_defs.add(direction)

        def finalize_doors(self):
            door_width = 2
            door_height = 4  # Increased from 2.5 to 4
            wall_height = 5  # Increased from 3 to 5
            wall_thickness = 0.5
            for direction in self.door_defs:
                if direction == 'N':
                    destroy(self.wall_entities['N'])
                    left = Entity(model='cube', color=color.rgb(120, 70, 30),
                                  scale=((ROOM_SIZE-door_width)/2, wall_height, wall_thickness),
                                  position=(self.pos[0] - (door_width/2 + (ROOM_SIZE-door_width)/4), wall_height/2, self.pos[2] + ROOM_SIZE/2), collider='box', enabled=False)
                    right = Entity(model='cube', color=color.rgb(120, 70, 30),
                                   scale=((ROOM_SIZE-door_width)/2, wall_height, wall_thickness),
                                   position=(self.pos[0] + (door_width/2 + (ROOM_SIZE-door_width)/4), wall_height/2, self.pos[2] + ROOM_SIZE/2), collider='box', enabled=False)
                    door_pos = (self.pos[0], door_height/2, self.pos[2] + ROOM_SIZE/2 + 0.01)
                    door = Entity(model='cube', color=color.yellow, scale=(door_width, door_height, 0.3),
                                  position=door_pos, collider='box', enabled=False)
                    self.entities += [left, right, door]
                elif direction == 'S':
                    destroy(self.wall_entities['S'])
                    left = Entity(model='cube', color=color.rgb(120, 70, 30),
                                  scale=((ROOM_SIZE-door_width)/2, wall_height, wall_thickness),
                                  position=(self.pos[0] - (door_width/2 + (ROOM_SIZE-door_width)/4), wall_height/2, self.pos[2] - ROOM_SIZE/2), collider='box', enabled=False)
                    right = Entity(model='cube', color=color.rgb(120, 70, 30),
                                   scale=((ROOM_SIZE-door_width)/2, wall_height, wall_thickness),
                                   position=(self.pos[0] + (door_width/2 + (ROOM_SIZE-door_width)/4), wall_height/2, self.pos[2] - ROOM_SIZE/2), collider='box', enabled=False)
                    door_pos = (self.pos[0], door_height/2, self.pos[2] - ROOM_SIZE/2 - 0.01)
                    door = Entity(model='cube', color=color.yellow, scale=(door_width, door_height, 0.3),
                                  position=door_pos, collider='box', enabled=False)
                    self.entities += [left, right, door]
                elif direction == 'E':
                    destroy(self.wall_entities['E'])
                    left = Entity(model='cube', color=color.rgb(120, 70, 30),
                                  scale=(wall_thickness, wall_height, (ROOM_SIZE-door_width)/2),
                                  position=(self.pos[0] + ROOM_SIZE/2, wall_height/2, self.pos[2] - (door_width/2 + (ROOM_SIZE-door_width)/4)), collider='box', enabled=False)
                    right = Entity(model='cube', color=color.rgb(120, 70, 30),
                                   scale=(wall_thickness, wall_height, (ROOM_SIZE-door_width)/2),
                                   position=(self.pos[0] + ROOM_SIZE/2, wall_height/2, self.pos[2] + (door_width/2 + (ROOM_SIZE-door_width)/4)), collider='box', enabled=False)
                    door_pos = (self.pos[0] + ROOM_SIZE/2 + 0.01, door_height/2, self.pos[2])
                    door = Entity(model='cube', color=color.yellow, scale=(0.3, door_height, door_width),
                                  position=door_pos, collider='box', enabled=False)
                    self.entities += [left, right, door]
                elif direction == 'W':
                    destroy(self.wall_entities['W'])
                    left = Entity(model='cube', color=color.rgb(120, 70, 30),
                                  scale=(wall_thickness, wall_height, (ROOM_SIZE-door_width)/2),
                                  position=(self.pos[0] - ROOM_SIZE/2, wall_height/2, self.pos[2] - (door_width/2 + (ROOM_SIZE-door_width)/4)), collider='box', enabled=False)
                    right = Entity(model='cube', color=color.rgb(120, 70, 30),
                                   scale=(wall_thickness, wall_height, (ROOM_SIZE-door_width)/2),
                                   position=(self.pos[0] - ROOM_SIZE/2, wall_height/2, self.pos[2] + (door_width/2 + (ROOM_SIZE-door_width)/4)), collider='box', enabled=False)
                    door_pos = (self.pos[0] - ROOM_SIZE/2 - 0.01, door_height/2, self.pos[2])
                    door = Entity(model='cube', color=color.yellow, scale=(0.3, door_height, door_width),
                                  position=door_pos, collider='box', enabled=False)
                    self.entities += [left, right, door]
                self.doors[direction] = door

        def spawn_enemy(self):
            self.enemy = Enemy(self.pos[0], 1, self.pos[2]+2)
            self.entities.append(self.enemy.entity)

        def spawn_loot(self):
            self.loot = Entity(model='cube', color=color.green, scale=(0.7,0.7,0.7), position=(self.pos[0]+2,1,self.pos[2]), collider='box', enabled=False)
            self.entities.append(self.loot)

        def set_visible(self, visible: bool):
            for e in self.entities:
                try:
                    e.enabled = visible
                except AssertionError:
                    print(f"Warning: Could not set visibility for entity {e}")
            if self.enemy and hasattr(self.enemy, 'entity') and hasattr(self.enemy.entity, 'node') and self.enemy.entity.node:
                self.enemy.entity.enabled = visible
            if self.loot and hasattr(self.loot, 'enabled') and hasattr(self.loot, 'node') and self.loot.node:
                self.loot.enabled = visible
            if self.has_stairs and hasattr(self, 'stairs') and hasattr(self.stairs, 'node') and self.stairs.node:
                self.stairs.enabled = visible

        def set_doors_visible(self, visible: bool):
            # Make sure doors are properly enabled when room is visible
            for direction, door in self.doors.items():
                if door:
                    try:
                        door.enabled = visible
                    except Exception as ex:
                        print(f"Warning: Could not set door visibility: {ex}")

    # --- Enemy Class ---
    class Enemy:
        def __init__(self, x, y, z):
            self.entity = Entity(model='cube', color=color.red, scale=(1,1,1), position=(x,y,z), collider='box', enabled=False)
            self.hp = 10
            self.attack_cooldown = 0

        def update(self, player):
            if not self.entity.enabled:
                return
            dist = distance(self.entity.position, player.position)
            if dist < 6:
                direction = (player.position - self.entity.position).normalized()
                self.entity.position += direction * 2 * time.dt
            if self.attack_cooldown > 0:
                self.attack_cooldown -= time.dt

        def take_damage(self, dmg):
            self.hp -= dmg
            if self.hp <= 0:
                self.entity.enabled = False

    # --- Dungeon Generation ---
    rooms = {}
    def generate_dungeon():
        rooms.clear()
        stairs_room = random.randint(1, NUM_ROOMS-1)
        rooms[0] = Room3D((0,0,0), 0)
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
                    room.spawn_enemy()
                if random.random() < 0.7:
                    room.spawn_loot()
        for room in rooms.values():
            room.finalize_doors()
            room.set_visible(False)
        rooms[0].set_visible(True)
        rooms[0].set_doors_visible(True)

    # --- Preload Rooms Function ---
    def preload_rooms(current_room_id, max_rooms=10):
        """Preload rooms around the current room"""
        current_room = rooms[current_room_id]
        loaded_count = 0
        
        # Preload rooms that are near the current room
        for i, room in rooms.items():
            if i != current_room_id:
                # Check if room is adjacent to current room
                if (abs(room.pos[0] - current_room.pos[0]) < ROOM_SIZE * 2 and 
                    abs(room.pos[2] - current_room.pos[2]) < ROOM_SIZE * 2):
                    room.set_visible(True)
                    room.set_doors_visible(True)
                    loaded_count += 1
                    if loaded_count >= max_rooms:
                        break

    # --- Ursina App Setup ---
    app = Ursina()
    game_started = False
    game_paused = False

    # --- Game State ---
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

    hp_text = None
    gold_text = None
    lore_text = None

    cursor = Entity(
        parent=camera.ui,
        model='quad',
        color=color.white,
        scale=.02,
        position=(0,0)
    )
    # To show/hide the cursor:
    cursor.visible = True

    # --- UI Panel (created after window is ready) ---
    def create_start_panel():
        return WindowPanel(
            title='Procedural Dungeon',
            content=(Text("Press SPACE to start", scale=2),),
            position=(0,0),  # Center of screen
            popup=True
        )

    # --- Tutorial Panel ---
    def create_tutorial_panel():
        return WindowPanel(
            title='Tutorial',
            content=(
                Text("Welcome to the Dungeon!", scale=1.5),
                Text("Controls:", scale=1.2),
                Text("WASD - Move", scale=1),
                Text("Mouse - Look around", scale=1),
                Text("E - Attack enemies", scale=1),
                Text("ESC - Pause menu", scale=1),
                Text("Touch doors to enter new rooms", scale=1),
                Text("Collect gold and avoid enemies", scale=1),
                Button(text='Start Game', scale=(0.2, 0.05), on_click=lambda: start_game()),
            ),
            position=(0,0),
            popup=True
        )

    # --- Pause Menu ---
    def create_pause_menu():
        return WindowPanel(
            title='Pause Menu',
            content=(
                Text("PAUSED", scale=2),
                Button(text='Resume', scale=(0.2, 0.05), on_click=lambda: toggle_pause()),
                Button(text='Quit', scale=(0.2, 0.05), on_click=lambda: sys.exit()),
            ),
            position=(0,0),
            popup=True
        )

    def toggle_pause():
        global game_paused
        game_paused = not game_paused
        if pause_menu:
            pause_menu.enabled = game_paused
        if game_paused:
            mouse.locked = False
            cursor.visible = True
            # Disable player movement
            if player:
                player.enabled = False
        else:
            mouse.locked = True
            cursor.visible = False
            # Enable player movement
            if player:
                player.enabled = True

    # --- Game Functions ---
    def start_game():
        global game_started, player, hp_text, gold_text, lore_text, current_room, player_hp, player_gold, lore_msg
        try:
            game_started = True
            tutorial_panel.enabled = False
            for room in rooms.values():
                room.set_visible(False)
            rooms[0].set_visible(True)
            rooms[0].set_doors_visible(True)
            current_room = 0
            player_hp = 30
            player_gold = 0
            lore_msg = ""
            if player is None:
                player = FirstPersonController(position=(0, 1, 0), model='cube', color=color.orange, scale=(1,2,1))
                player.cursor.visible = True
            else:
                player.position = (0, 1, 0)
            if hp_text is None:
                hp_text = Text(f'HP: {player_hp}', position=(-0.85,0.45), scale=2, background=True)
            if gold_text is None:
                gold_text = Text(f'Gold: {player_gold}', position=(-0.85,0.38), scale=2, background=True, color=color.yellow)
            if lore_text is None:
                lore_text = Text('', position=(-0.5,-0.45), scale=1.5, background=True)
            hp_text.enabled = True
            gold_text.enabled = True
            lore_text.enabled = True
            
            # Add solid floor that player cannot fall through
            floor = Entity(
                model='plane',
                color=color.gray,
                scale=(ROOM_SIZE * 2, 1, ROOM_SIZE * 2),
                position=(0, -0.5, 0),
                collider='box',
                enabled=True
            )
            
        except Exception as e:
            tb = traceback.format_exc()
            log_error_json(tb, type(e).__name__)
            print("Error in start_game:", e)
            print(tb)
            window.title = "Error in start_game - see error_log.json"

    def input(key):
        global game_started, lore_msg
        try:
            if not game_started and key == 'space':
                start_game()
            if not game_started:
                return
            if key == 'escape':
                toggle_pause()
            if key == 'e':
                room = rooms[current_room]
                if room.enemy and hasattr(room.enemy, 'entity') and room.enemy.entity.enabled:
                    if distance(player.position, room.enemy.entity.position) < 2:
                        room.enemy.take_damage(5)
                        lore_msg = "You hit the enemy!"
            if key == 'right mouse down':
                mouse.locked = True
            if key == 'right mouse up':
                mouse.locked = False
        except Exception as e:
            tb = traceback.format_exc()
            log_error_json(tb, type(e).__name__)
            print("Error in input:", e)
            print(tb)
            window.title = "Error in input - see error_log.json"

    def update():
        global player_hp, lore_msg, current_room, hp_text, lore_text, player_gold, gold_text
        if not game_started or player is None or game_paused:
            return
        try:
            # Check for door proximity to load new rooms
            player_pos = player.position
            room_loaded = False
            
            # Check all rooms for door proximity
            for i, room in rooms.items():
                if i != current_room:
                    # Check if player is near any door in this room
                    for direction, door in room.doors.items():
                        if door:  # Only check if door exists
                            door_pos = door.position
                            # Check if player is close enough to the door (proximity detection)
                            dist = distance(player_pos, door_pos)
                            if dist < 1.5:  # Reduced threshold for better detection
                                print(f"Door proximity detected! Loading room {i}")
                                # Load the new room
                                rooms[current_room].set_visible(False)
                                room.set_visible(True)
                                room.set_doors_visible(True)
                                current_room = i
                                room_loaded = True
                                break
                    if room_loaded:
                        break

            # Update room visibility based on player position
            for i, room in rooms.items():
                if abs(player.x - room.pos[0]) < ROOM_SIZE/2 and abs(player.z - room.pos[2]) < ROOM_SIZE/2:
                    if current_room != i:
                        print(f"Player entered room {i}")
                        rooms[current_room].set_visible(False)
                        room.set_visible(True)
                        room.set_doors_visible(True)
                        current_room = i
                    break

            # Preload nearby rooms
            preload_rooms(current_room, max_rooms=10)

            room = rooms[current_room]

            # Update enemy behavior
            if room.enemy and hasattr(room.enemy, 'entity') and room.enemy.entity.enabled:
                room.enemy.update(player)
                if distance(player.position, room.enemy.entity.position) < 2 and room.enemy.attack_cooldown <= 0:
                    player_hp -= 2
                    room.enemy.attack_cooldown = 1.0
                    lore_msg = "Enemy hit you!"

            # Handle loot collection
            if room.loot and player.intersects(room.loot).hit and room.loot.enabled:
                lore_msg = random.choice(lore_msgs)
                player_gold += random.randint(1, 5)
                room.loot.enabled = False

            # Handle stairs
            if hasattr(room, 'stairs') and room.stairs and distance(player.position, room.stairs.position) < 2:
                lore_msg = "You ascend the stairs!"
                player.position = (0,1,0)
                generate_dungeon()

            # Update UI
            if hp_text:
                hp_text.text = f'HP: {player_hp}'
            if gold_text:
                gold_text.text = f'Gold: {player_gold}'
            if lore_text:
                lore_text.text = lore_msg
                
        except Exception as e:
            tb = traceback.format_exc()
            log_error_json(tb, type(e).__name__)
            print("Error in update:", e)
            print(tb)
            window.title = "Error in update - see error_log.json"

    # --- Generate Dungeon Before Game Starts ---
    generate_dungeon()

    # --- Preload initial rooms ---
    preload_rooms(0, max_rooms=10)

    # --- Create UI Panels ---
    tutorial_panel = create_tutorial_panel()
    pause_menu = create_pause_menu()
    pause_menu.enabled = False

    # --- Run the Game ---
    app.run()

except Exception as e:
    tb = traceback.format_exc()
    log_error_json(tb, type(e).__name__)
    print("A fatal error occurred. See error_log.json for details.")
    print(tb)
    sys.exit(1)
