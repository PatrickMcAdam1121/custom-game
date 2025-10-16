from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import math

class ImprovedFirstPersonController(FirstPersonController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.speed = 2
        self.jump_height = 2
        self.jump_duration = 0.5
        self.jumping = False
        self.jump_start = 0
        self.gravity = 1
        self.air_time = 0
        self.previous_height = self.y
        self.momentum = Vec3(0, 0, 0)
        self.acceleration = 20
        self.friction = 0.7
        self.mouse_sensitivity = Vec2(40, 40)
        
    def update(self):
        if not self.enabled:
            return

        # Ground check
        if self.y > 0:
            # Apply gravity
            self.air_time += time.dt
            self.y = max(0, self.y - (self.gravity * self.air_time * self.air_time))
        else:
            self.air_time = 0
            self.y = 0

        # Handle movement with momentum
        direction = Vec3(0, 0, 0)
        
        if held_keys['w']: direction.z += 1
        if held_keys['s']: direction.z -= 1
        if held_keys['a']: direction.x -= 1
        if held_keys['d']: direction.x += 1
        
        # Normalize direction vector
        if direction.length() > 0:
            direction = direction.normalized()
            
        # Rotate direction based on camera angle
        rotation_y = Entity(rotation_y=self.rotation_y)
        direction = rotation_y.forward * direction.z + rotation_y.right * direction.x
        destroy(rotation_y)

        # Apply acceleration and friction
        target_speed = direction * self.speed
        self.momentum = lerp(self.momentum, target_speed, time.dt * self.acceleration)
        
        if direction.length() == 0:
            self.momentum *= max(0, 1 - time.dt * self.friction)
            
        # Move the player
        self.position += self.momentum * time.dt
        
        # Camera rotation
        if mouse.locked:
            self.rotation_x -= mouse.velocity[1] * self.mouse_sensitivity[1] * time.dt
            self.rotation_y += mouse.velocity[0] * self.mouse_sensitivity[0] * time.dt
            self.rotation_x = clamp(self.rotation_x, -90, 90)

    def input(self, key):
        super().input(key)
        if key == 'space':
            if not self.jumping and self.y == 0:  # Only jump if on ground
                self.jumping = True
                self.jump_start = time.time()
                self.air_time = 0
                self.y += self.jump_height

                # Install Ursina if not already installed
                try:
                    import ursina
                except ImportError:
                    print("Ursina is not installed. Installing...")
                    import pip
                    pip.main(['install', 'ursina'])
                    print("Ursina has been installed. Please restart the script.")
                    exit()