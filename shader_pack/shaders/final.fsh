// 灵动:视效 - final (最终输出)
#version 150

uniform sampler2D composite;
uniform sampler2D depthtex0;
uniform float viewWidth;
uniform float viewHeight;

in vec2 texCoord;

/* DRAWBUFFERS: 0 */
layout(location = 0) out vec4 fragColor;

void main() {
    vec3 color = texture(composite, texCoord).rgb;
    
    // Gamma校正
    color = pow(color, vec3(1.0 / 2.2));
    
    // 防色带抖动
    float dither = fract(sin(dot(texCoord * viewWidth, vec2(12.9898, 78.233))) * 43758.5453);
    color += dither / 255.0;
    
    fragColor = vec4(clamp(color, 0.0, 1.0), 1.0);
}
