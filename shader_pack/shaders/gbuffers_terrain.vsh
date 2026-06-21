// 灵动:视效 - terrain vertex (Iris Core Profile)
#version 150

in vec3 vaPosition;
in vec4 vaColor;
in vec2 vaUV0;
in ivec2 vaUV2;

uniform mat4 gbufferModelView;
uniform mat4 gbufferProjection;
uniform mat4 gbufferModelViewInverse;
uniform vec3 cameraPosition;

out vec2 texCoord;
out vec2 lmCoord;
out vec3 worldPos;
out vec4 glcolor;

void main() {
    vec4 viewPos = gbufferModelView * vec4(vaPosition, 1.0);
    gl_Position = gbufferProjection * viewPos;
    worldPos = (gbufferModelViewInverse * viewPos).xyz;
    texCoord = vaUV0;
    lmCoord = vec2(vaUV2) / 256.0;
    glcolor = vaColor;
}
