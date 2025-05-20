// Waterfall Shader (from https://www.shadertoy.com/view/XdS3RW)
// Externalizable constants (will be overridden via controls.json)
const float flowScale        = 0.03;   // UV scaling for flow noise
const float scrollSpeed      = 0.01;   // vertical scroll speed for flow UV
const float flowmapStrength  = 0.006;  // strength of flowmap displacement
const float timeMultiplier   = 0.8;    // global time multiplier for flow
const float radialScale      = 0.01;   // scale factor for radial spray UV
const float radialTimeOffset = 0.002;  // time offset multiplier for radial spray
const float bottomWidth      = 0.2;    // mask lower width threshold
const float topWidth         = 0.6;    // mask upper width threshold

// Shadertoy uniforms
uniform vec3 iResolution;
uniform float iTime;
uniform sampler2D iChannel0; // noise texture
uniform sampler2D iChannel1; // background texture

// Simple screen blend
vec3 screen_blend(vec3 s, vec3 d) {
    return s + d - s * d;
}

// Mask for waterfall shape
float get_mask(vec2 uv) {
    uv.x *= iResolution.x / iResolution.y;
    // slanted waterfall edges (fixed slope)
    uv.x += sign(uv.x) * uv.y * 0.2;
    uv.x = abs(uv.x);
    // smooth mask between bottomWidth and topWidth
    return clamp(1.0 - smoothstep(bottomWidth, topWidth, uv.x), 0.0, 1.0);
}

// Flow function helper
vec2 flow(vec2 uv, vec2 flowmap, float phase, float t, out float weight) {
    float progress = fract(t + phase);
    vec2 displacement = flowmap * progress;
    weight = 1.0 - abs(progress * 2.0 - 1.0);
    return uv + displacement;
}

// Fractional Brownian Motion (fbm) on texture
float fbm(sampler2D sampler, vec2 p) {
    float value = 0.0;
    float amplitude = 0.5;
    float frequency = 1.0;
    for (int i = 0; i < 5; i++) {
        value += amplitude * texture(sampler, p * frequency).r;
        frequency *= 2.0;
        amplitude *= 0.5;
    }
    return value;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord.xy / iResolution.xy;
    uv.x = uv.x * 2.0 - 1.0;

    // Flow UV and noise
    vec2 flowuv = uv * flowScale + vec2(0.0, iTime * scrollSpeed);
    float noise = fbm(iChannel0, flowuv);
    vec2 flowmap = vec2(0.0, smoothstep(0.2, 1.0, noise)) * flowmapStrength;
    float weightA, weightB;
    float t = iTime * timeMultiplier;
    vec2 uvA = flow(flowuv, flowmap, 0.0, t, weightA);
    vec2 uvB = flow(flowuv, flowmap, 0.5, t, weightB);
    float flowA = fbm(iChannel0, uvA) * weightA;
    float flowB = fbm(iChannel0, uvB) * weightB;
    float flowVal = flowA + flowB;

    // Masks for waterfall and spray
    float waterfall_mask = get_mask(uv);
    float spray_mask = 1.0 - length(vec2(uv.x * 0.8, pow(uv.y, 0.5)) * 1.7);
    uv.y += 0.5;
    vec2 radial_uv = radialScale * vec2(atan(uv.x, uv.y), length(uv)) + vec2(0.0, -iTime * radialTimeOffset);
    float spray = fbm(iChannel0, radial_uv);

    // Background and color mixing
    vec3 background = texture(iChannel1, uv).rgb;
    vec3 blue = vec3(0.6, 0.6, 0.9);
    vec3 waterfallCol = ((1.0 - flowVal) * blue + smoothstep(0.0, 1.0, flowVal)) * waterfall_mask;
    vec3 col = mix(background, waterfallCol, waterfall_mask);
    col += vec3(spray_mask * spray * (1.0 - waterfall_mask));
    spray_mask = clamp(spray_mask, 0.0, 1.0);
    col = screen_blend(vec3(spray * spray_mask * 2.5), col);

    fragColor = vec4(col, 1.0);
}