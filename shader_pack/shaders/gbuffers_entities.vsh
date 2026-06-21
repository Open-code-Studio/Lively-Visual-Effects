// 灵动:视效 - entities vertex (Iris Core Profile)
#version 150

in vec3 vaPosition;
in vec4 vaColor;
in vec2 vaUV0;
in ivec2 vaUV2;

uniform mat4 gbufferModelView;
uniform mat4 gbufferProjection;

out vec2 texCoord;
out vec2 lmCoord;
out vec4 glcolor;

void main() {
    vec4 pos = gbufferModelView * vec4(vaPosition, 1.0);
    gl_Position = gbufferProjection * pos;
    texCoord = vaUV0;
    lmCoord = vec2(vaUV2) / 256.0;
    glcolor = vaColor;
}
