// 灵动:视效 - gbuffers_terrain (超明显效果版)
#version 150

uniform sampler2D texture;
uniform sampler2D normals;
uniform sampler2D specular;

uniform vec3 sunPosition;
uniform float sunAngle;
uniform float rainStrength;

uniform mat4 gbufferModelView;
uniform mat4 gbufferModelViewInverse;
uniform mat4 gbufferProjection;
uniform vec3 cameraPosition;

in vec2 texCoord;
in vec2 lmCoord;
in vec4 glcolor;
in vec3 worldPos;

/* DRAWBUFFERS: 0 */
layout(location = 0) out vec4 fragColor;

void main() {
    vec4 albedo = texture(texture, texCoord) * glcolor;
    
    float blockLight = lmCoord.x;
    float skyLight = lmCoord.y;
    
    // PBR法线
    vec4 nTex = texture(normals, texCoord);
    vec3 N = nTex.a > 0.0 ? normalize(nTex.rgb * 2.0 - 1.0) : vec3(0.0, 0.0, 1.0);
    
    // 太阳方向光照
    vec3 sunDir = normalize(sunPosition);
    float NdotL = dot(N, sunDir) * 0.5 + 0.5;
    
    // 镜面高光
    float specMask = texture(specular, texCoord).a;
    vec3 viewDir = normalize(cameraPosition - worldPos);
    vec3 halfVec = normalize(sunDir + viewDir);
    float spec = pow(max(dot(N, halfVec), 0.0), 64.0) * specMask;
    
    vec3 color = albedo.rgb;
    
    // 冷色天空光
    color *= vec3(0.6, 0.7, 1.0) * skyLight * 0.55;
    // 暖色方块光  
    color *= vec3(1.0, 0.7, 0.4) * blockLight * 0.45;
    // 环境光
    color *= vec3(0.15, 0.12, 0.08);
    
    // 方向光贡献
    color += albedo.rgb * vec3(1.0, 0.85, 0.5) * NdotL * skyLight * 0.3;
    
    // 镜面高光
    color += vec3(1.0, 0.9, 0.5) * spec * skyLight * 0.5;
    
    // AO
    float ao = 0.4 + blockLight * 0.3 + skyLight * 0.3;
    color *= ao;
    
    // 雨天
    color = mix(color, color * vec3(0.65, 0.75, 1.0), rainStrength * 0.5);
    
    fragColor = vec4(color, albedo.a);
}
