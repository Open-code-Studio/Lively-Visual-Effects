// 灵动:视效 - water vertex (Iris modern)
#version 150

in vec3 vaPosition;
in vec4 vaColor;
in vec2 vaUV0;

uniform mat4 gbufferModelView;
uniform mat4 gbufferModelViewInverse;
uniform mat4 gbufferProjection;

out vec2 texCoord;
out vec3 worldPos;
out vec4 glcolor;

void main() {
    vec4 viewPos = gbufferModelView * vec4(vaPosition, 1.0);
    gl_Position = gbufferProjection * viewPos;
    worldPos = (gbufferModelViewInverse * viewPos).xyz;
    texCoord = vaUV0;
    glcolor = vaColor;
}
