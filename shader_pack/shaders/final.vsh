// 灵动:视效 - final vertex (全屏三角形)
#version 150

out vec2 texCoord;

void main() {
    float x = float((gl_VertexID & 1) << 2) - 1.0;
    float y = float((gl_VertexID & 2) << 1) - 1.0;
    gl_Position = vec4(x, y, 0.0, 1.0);
    texCoord = vec2((x + 1.0) * 0.5, 1.0 - (y + 1.0) * 0.5);
}
