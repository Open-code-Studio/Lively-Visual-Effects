// 灵动:视效 - shadow vertex (Iris modern)
#version 150

in vec3 vaPosition;
in vec4 vaColor;
in vec2 vaUV0;

uniform mat4 gbufferModelView;
uniform mat4 gbufferProjection;

out vec2 texCoord;
out vec4 glcolor;

void main() {
    vec4 pos = gbufferModelView * vec4(vaPosition, 1.0);
    gl_Position = gbufferProjection * pos;
    texCoord = vaUV0;
    glcolor = vaColor;
}
