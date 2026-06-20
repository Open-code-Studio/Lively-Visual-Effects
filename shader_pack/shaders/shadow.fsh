// 灵动:视效 - shadow (阴影贴图)
#version 150

uniform sampler2D texture;

in vec2 texCoord;
in vec4 glcolor;

layout(location = 0) out vec4 fragColor;

void main() {
    vec4 tex = texture(texture, texCoord) * glcolor;
    if (tex.a < 0.1) discard;
    fragColor = vec4(1.0);
}
