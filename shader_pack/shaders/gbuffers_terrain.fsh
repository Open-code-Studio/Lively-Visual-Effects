// 最简测试 - 只渲原版颜色
#version 150

uniform sampler2D tex;
in vec2 texCoord;
in vec4 glcolor;

layout(location = 0) out vec4 fragColor;

void main() {
    fragColor = texture(tex, texCoord) * glcolor;
}
