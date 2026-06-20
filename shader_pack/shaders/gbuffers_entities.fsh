// 灵动:视效 - gbuffers_entities
#version 150

uniform sampler2D texture;
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
    
    vec3 color = albedo.rgb;
    color *= vec3(0.65, 0.75, 1.0) * skyLight * 0.6;
    color *= vec3(1.0, 0.75, 0.45) * blockLight * 0.5;
    color *= vec3(0.18, 0.14, 0.1);
    
    float ao = 0.45 + blockLight * 0.3 + skyLight * 0.25;
    color *= ao;
    color = mix(color, color * vec3(0.7, 0.8, 1.0), rainStrength * 0.5);
    
    fragColor = vec4(color, albedo.a);
}
