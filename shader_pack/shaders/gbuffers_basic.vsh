// 灵动:视效 - basic vertex (Iris Core Profile)
// vaUV2 必须是 ivec2，不是 vec2！
#version 150

in vec3 vaPosition;
in vec4 vaColor;
in vec2 vaUV0;
in ivec2 vaUV2;      // 整数类型！

uniform mat4 gbufferModelView;
uniform mat4 gbufferProjection;
uniform mat4 gbufferModelViewInverse;

out vec2 texCoord;
out vec2 lmCoord;
out vec4 glcolor;

void main() {
    vec4 viewPos = gbufferModelView * vec4(vaPosition, 1.0);
    gl_Position = gbufferProjection * viewPos;
    texCoord = vaUV0;
    lmCoord = vec2(vaUV2) / 256.0;  // 整数转浮点
    glcolor = vaColor;
}
