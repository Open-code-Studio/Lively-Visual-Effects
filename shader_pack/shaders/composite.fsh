// 最简测试 - 直接输出
#version 150

uniform sampler2D gcolor;
uniform sampler2D depthtex0;

in vec2 texCoord;

layout(location = 0) out vec4 fragColor;

void main() {
    float depth = texture(depthtex0, texCoord).r;
    
    // 天空
    if (depth > 0.9999) {
        fragColor = vec4(0.3, 0.5, 1.0, 1.0);  // 纯蓝色天空
        return;
    }
    
    // 地面：直接输出
    fragColor = texture(gcolor, texCoord);
}
