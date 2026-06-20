// 灵动:视效 - textured vertex (Iris modern)
#version 150

in vec3 vaPosition;
in vec4 vaColor;
in vec2 vaUV0;
in vec2 vaUV2;

uniform mat4 gbufferModelView;
uniform mat4 gbufferProjection;

out vec2 texCoord;
out vec2 lmCoord;
out vec4 glcolor;

void main() {
    vec4 pos = gbufferModelView * vec4(vaPosition, 1.0);
    gl_Position = gbufferProjection * pos;
    texCoord = vaUV0;
    lmCoord = vaUV2;
    glcolor = vaColor;
}
