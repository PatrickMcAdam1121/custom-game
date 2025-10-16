from ursina import *

def create_shaders():
    try:
        # Basic lighting shader with simpler implementation
        lighting_shader = Shader(
            name='basic_lighting',
            language=Shader.GLSL,
            vertex='''
            #version 130
            uniform mat4 p3d_ModelViewProjectionMatrix;
            in vec4 p3d_Vertex;
            in vec3 p3d_Normal;
            out vec3 vNormal;
            
            void main() {
                gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
                vNormal = p3d_Normal;
            }
            ''',
            fragment='''
            #version 130
            in vec3 vNormal;
            uniform vec4 p3d_Color;
            out vec4 fragColor;
            
            void main() {
                vec3 norm = normalize(vNormal);
                float diff = max(dot(norm, vec3(0.0, 1.0, 0.0)), 0.3);
                fragColor = vec4(p3d_Color.rgb * diff, p3d_Color.a);
            }
            '''
        )
        
        # Simplified wall shader
        wall_shader = Shader(
            name='basic_wall',
            language=Shader.GLSL,
            vertex='''
            #version 130
            uniform mat4 p3d_ModelViewProjectionMatrix;
            in vec4 p3d_Vertex;
            
            void main() {
                gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
            }
            ''',
            fragment='''
            #version 130
            uniform vec4 p3d_Color;
            out vec4 fragColor;
            
            void main() {
                fragColor = p3d_Color;
            }
            '''
        )
        
        return lighting_shader, wall_shader
        
    except Exception as e:
        print(f"Failed to create shaders: {str(e)}")
        # Return None values if shader creation fails
        return None, None

def apply_shader(entity, shader):
    """Safely apply a shader to an entity"""
    if shader is not None:
        try:
            entity.shader = shader
        except Exception as e:
            print(f"Failed to apply shader: {str(e)}")
            # Fall back to no shader
            entity.shader = None