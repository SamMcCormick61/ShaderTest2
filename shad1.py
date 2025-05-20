# pip install pygame-ce moderngl numpy

import pygame as pg
import moderngl as mgl
import numpy as np


VERTEX_SHADER_SOURCE = """
#version 330
in vec2 vert;
out vec2 fragCoord;
void main() {
    fragCoord = vert;
    // Place vertices in clip space (z = 0, w = 1)
    gl_Position = vec4(vert, 0.0, 1.0);
}
"""

FRAGMENT_SHADER_SOURCE = """
#version 330
// adapted from https://www.shadertoy.com/view/MdX3zr
uniform float iTime;
uniform vec2 iResolution;
uniform vec2 iMouse;
in vec2 fragCoord;

// HOVER MOUSE OVER COMPONENT WINDOW AND MOVE DOWN-UP TO CONTROL INTENSITY, LEFT-RIGHT FOR SPHERE SIZE

// Parameters affecting the flame shape
vec3 flameScale = vec3(1., 1.355, 1.);
vec4 sphereParams = vec4(.0, -7.0, .0, 1.);
float noiseEffectScale = .12;

// Function to generate noise
float noise(vec3 position)
{
    vec3 floorPosition = floor(position);
    vec4 noiseParams = dot(floorPosition, vec3(1., 57., 21.)) + vec4(0., 57., 21., 78.);

    // Compute cosine values to create smooth transitions
    vec3 cosineValues = cos((position - floorPosition) * acos(-1.)) * (-.5) + .5;

    // Interpolate noiseParams values using cosineValues
    noiseParams = mix(sin(cos(noiseParams) * noiseParams), sin(cos(1. + noiseParams) * (1. + noiseParams)), cosineValues.x);
    noiseParams.xy = mix(noiseParams.xz, noiseParams.yw, cosineValues.y);

    // Interpolate noiseParams.x and noiseParams.y using cosineValues.z
    return mix(noiseParams.x, noiseParams.y, cosineValues.z);
}

// Function to calculate the distance to a sphere
float sphere(vec3 position, vec4 sphereParams)
{
    // Scale the sphere based on the X position of the mouse
    float sphereScaleX = iMouse.x / iResolution.x + 0.7;

    // Calculate the distance from the sphere surface to the current position
    // and subtract the scaled radius of the sphere
    return length(sphereParams.xyz - position) - sphereScaleX * 12.0;
}

// Function to calculate the flame effect
float flame(vec3 position)
{
    // Scale the flame based on the Y position of the mouse
    float flameScaleY = flameScale.y + -iMouse.y / iResolution.y * 0.4 - 0.2;

    // Calculate the distance from the flame shape to the current position
    // by combining the scaled sphere distance and noise effect
    float sphereDistance = sphere(position * flameScaleY, sphereParams);
    return sphereDistance + (noise(position + vec3(.0, iTime * 2., .0)) + noise(position * 2.) * .5) * noiseEffectScale * position.y;
}

// Function to calculate the scene value
float scene(vec3 position)
{
    // Calculate the distance to the flame and cap it at a maximum value
    // to avoid infinite values
    return min(100. - length(position), abs(flame(position)));
}

// Function to perform raymarching
vec4 raymarch(vec3 origin, vec3 direction)
{
    float depth = 2.0, glow = 0.0, epsilon = 0.105;
    vec3 rayPosition = origin;
    bool hasGlowed = false;

    for (int i = 3; i < 44; i++)
    {
        // Perform scene distance estimation and add a small epsilon value
        // to prevent self-intersections
        depth = scene(rayPosition) + epsilon;

        // Move the ray position along the ray direction by the estimated distance
        rayPosition += depth * direction;

        if (depth > epsilon)
        {
            // Check if the flame has glowed by comparing its value to 0
            if (flame(rayPosition) < .0)
                hasGlowed = true;

            // Calculate the glow intensity based on the iteration count
            if (hasGlowed)
                glow = float(i) / 64.;
        }
    }

    return vec4(rayPosition, glow);
}

void main()
{
    vec2 screenPosition = fragCoord;

    vec3 rayOrigin = vec3(0., -9.5, 25.);
    vec3 rayDirection = normalize(vec3(screenPosition.x * 1.6, -screenPosition.y, -1.0));

    vec4 raymarchResult = raymarch(rayOrigin, rayDirection);
    float glow = raymarchResult.w;

    // Define the base color of the flame and the underwater color
    vec4 color = mix(vec4(1., .5, .1, 1.), vec4(0.1, .2, 1., 1.), raymarchResult.y * .02 + .4);

    // Apply the glow effect to the color using the glow intensity
    gl_FragColor = mix(vec4(0.), color, pow(glow * 2.5, 4.));
}
"""


def quit():
    pg.quit()
    exit()


def main():
    screen_size = (800, 600)

    # Initialize Pygame
    pg.init()

    # Create a resizable Pygame display with OpenGL support
    pg.display.set_mode(screen_size, pg.DOUBLEBUF | pg.OPENGL | pg.RESIZABLE)

    # Create a Pygame clock object to track time
    clock = pg.time.Clock()

    # Create a ModernGL context
    ctx = mgl.create_context()

    # Create a ModernGL shader program using the vertex and fragment shaders
    shader_prog = ctx.program(
        vertex_shader=VERTEX_SHADER_SOURCE,
        fragment_shader=FRAGMENT_SHADER_SOURCE
    )

    # Define vertices for 2 triangles (forming a square) covering the whole screen
    vertices = np.array([
        -1.0, -1.0, 
         1.0, -1.0, 
        -1.0,  1.0, 
        -1.0,  1.0, 
         1.0, -1.0, 
         1.0,  1.0], dtype='f4')

    # Create a vertex buffer object (VBO) and vertex array object (VAO)
    vbo = ctx.buffer(vertices)
    vao = ctx.simple_vertex_array(shader_prog, vbo, 'vert')

    while True:
        # Clear the context
        ctx.clear()

        # Check for Pygame quit events and exit the program if needed
        [quit() for e in pg.event.get() if e.type == pg.QUIT]

        # Get the current mouse position
        mouse_pos = pg.mouse.get_pos()
        # Reverse the Y-coordinate of the mouse position to match OpenGL coordinate system
        reversed_mouse_pos = (mouse_pos[0], screen_size[1] - mouse_pos[1])

        # Define the uniform variables for the shader program
        uniforms = {
            'iTime': pg.time.get_ticks() / 1000.0,  # Current time in seconds
            'iResolution': pg.display.get_window_size(),  # Resolution of the display window
            'iMouse': reversed_mouse_pos,  # Mouse position
        }

        # Set the uniform values in the shader program
        for uniform, value in uniforms.items():
            if uniform in FRAGMENT_SHADER_SOURCE:
                shader_prog[uniform].value = value

        # Render the vertex array object (VAO) as triangles
        vao.render(mgl.TRIANGLES)

        # Update the display
        clock.tick()
        pg.display.flip()

        # Set the window caption to display the frames per second (FPS)
        pg.display.set_caption(f'FPS: {clock.get_fps():.2f}')


if __name__ == "__main__":
    main()