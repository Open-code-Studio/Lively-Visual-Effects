// 灵动:视效 - gbuffers_water (水面)
#version 150

uniform sampler2D texture;
uniform sampler2D noisetex;
uniform vec3 sunPosition;
uniform vec3 cameraPosition;
uniform float frameTimeCounter;
uniform float rainStrength;

in vec2 texCoord;
in vec3 worldPos;
in vec4 glcolor;

/* DRAWBUFFERS: 0 */
layout(location = 0) out vec4 fragColor;

void main() {
    vec4 albedo = texture(texture, texCoord) * glcolor;
    
    // 水面颜色加深
    vec3 waterColor = albedo.rgb * vec3(0.85, 0.95, 1.1);
    
    // 动态波纹
    float time = frameTimeCounter * 2.0;
    float wave1 = sin(worldPos.x * 3.0 + time) * cos(worldPos.z * 2.5 + time * 0.7) * 0.06;
    float wave2 = sin(worldPos.z * 4.0 - time * 0.9) * cos(worldPos.x * 3.5 + time * 0.6) * 0.05;
    float wave = wave1 + wave2;
    
    // 太阳反射高光
    vec3 sunDir = normalize(sunPosition);
    vec3 viewDir = normalize(cameraPosition - worldPos);
    vec3 normal = normalize(vec3(wave, 1.0, wave * 0.5));
    vec3 halfVec = normalize(sunDir + viewDir);
    
    float spec = pow(max(dot(normal, halfVec), 0.0), 256.0);
    spec *= max(dot(normal, sunDir), 0.0) * 2.0;
    
    // 菲涅尔效果
    float fresnel = pow(1.0 - abs(dot(normal, viewDir)), 3.0);
    
    vec3 color = waterColor * 0.7 + vec3(0.2, 0.4, 0.65) * fresnel * 0.4;
    color += vec3(1.0, 0.9, 0.6) * spec * 1.5;
    
    // 雨天水面变暗
    color = mix(color, color * 0.7, rainStrength * 0.5);
    
    fragColor = vec4(color, albedo.a * 0.85);
}
