// 最简测试 - 不依赖任何顶点输入以外的数据
#version 150

uniform sampler2D tex;
in vec2 texCoord;
in vec4 glcolor;

layout(location = 0) out vec4 fragColor;

void main() {
    vec4 albedo = texture(tex, texCoord) * glcolor;
    // 先直接输出原版颜色，不做任何处理
    fragColor = albedo;
}
