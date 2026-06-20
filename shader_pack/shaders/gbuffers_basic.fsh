// 灵动:视效 - gbuffers_basic (超明显效果版)
#version 150

uniform sampler2D texture;

uniform vec3 sunPosition;
uniform float sunAngle;
uniform float rainStrength;

in vec2 texCoord;
in vec2 lmCoord;
in vec4 glcolor;

/* DRAWBUFFERS: 0 */
layout(location = 0) out vec4 fragColor;

void main() {
    vec4 albedo = texture(texture, texCoord) * glcolor;
    
    float blockLight = lmCoord.x;
    float skyLight = lmCoord.y;
    
    // 极端暖色调 — 让你明显感觉到光影不同
    vec3 color = albedo.rgb;
    
    // 天空光偏蓝
    color *= vec3(0.65, 0.75, 1.0) * skyLight * 0.6;
    // 方块光偏暖橙
    color *= vec3(1.0, 0.75, 0.45) * blockLight * 0.5;
    // 基础环境光
    color *= vec3(0.15, 0.12, 0.08);
    
    // 强AO效果
    float ao = 0.4 + blockLight * 0.3 + skyLight * 0.3;
    color *= ao;
    
    // 雨天偏蓝
    color = mix(color, color * vec3(0.7, 0.8, 1.0), rainStrength * 0.5);
    
    fragColor = vec4(color, albedo.a);
}
