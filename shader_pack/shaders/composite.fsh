// 灵动:视效 - composite (超明显天空版)
#version 150

uniform sampler2D gcolor;
uniform sampler2D depthtex0;

uniform vec3 sunPosition;
uniform vec3 moonPosition;
uniform float sunAngle;
uniform float rainStrength;
uniform float frameTimeCounter;

in vec2 texCoord;

/* DRAWBUFFERS: 0 */
layout(location = 0) out vec4 fragColor;

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void main() {
    float depth = texture(depthtex0, texCoord).r;
    
    // ===== 超级明显的天空效果 =====
    if (depth > 0.999) {
        vec2 uv = texCoord * 2.0 - 1.0;
        vec3 viewDir = normalize(vec3(uv, 0.6));
        
        // 夸张的渐变：顶深蓝 → 地平线亮橙
        float h = smoothstep(-0.1, 0.5, viewDir.y);
        vec3 skyTop = vec3(0.15, 0.35, 0.8);
        vec3 skyMid = vec3(0.4, 0.65, 1.0);
        vec3 skyHor = vec3(0.7, 0.85, 1.0);
        vec3 sky = mix(skyHor, mix(skyMid, skyTop, h), h);
        
        // 大太阳
        vec3 sunDir = normalize(sunPosition);
        float sunDot = dot(viewDir, sunDir);
        float sunDisc = smoothstep(0.995, 0.998, sunDot);
        float sunGlow = exp((sunDot - 1.0) * 20.0);
        
        if (sunAngle > -0.1) {
            sky += vec3(1.0, 0.8, 0.2) * sunDisc * 5.0;
            sky += vec3(1.0, 0.6, 0.1) * sunGlow * 2.0;
        } else {
            sky += vec3(0.8, 0.85, 1.0) * sunDisc * 2.0;
            sky += vec3(0.5, 0.6, 1.0) * sunGlow * 0.8;
            // 星星
            float star = hash(floor(viewDir.xz * 400.0));
            star = smoothstep(0.996, 0.998, star) * smoothstep(0.05, 0.5, viewDir.y);
            sky += vec3(1.0, 0.95, 0.9) * star * (-sunAngle) * 1.2;
        }
        
        // 地平线雾
        sky = mix(sky, vec3(0.75, 0.8, 0.9), (1.0 - h) * 0.5);
        
        fragColor = vec4(sky, 1.0);
        return;
    }
    
    // 地面：色调映射
    vec3 color = texture(gcolor, texCoord).rgb;
    
    // ACES
    color = (color * (2.51 * color + 0.03)) / (color * (2.43 * color + 0.59) + 0.14);
    
    // 强暗角
    vec2 uv = texCoord * 2.0 - 1.0;
    color *= 1.0 - dot(uv, uv) * 0.4;
    
    // 饱和度增强
    float lum = dot(color, vec3(0.299, 0.587, 0.114));
    color = mix(vec3(lum), color, 1.2);
    
    fragColor = vec4(color, 1.0);
}
