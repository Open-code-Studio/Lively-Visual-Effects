// 灵动:视效 - composite vertex (全屏三角形，无需输入属性)
#version 150

out vec2 texCoord;

void main() {
    // 用 gl_VertexID 生成全屏三角形 (3个顶点覆盖整个屏幕)
    float x = float((gl_VertexID & 1) << 2) - 1.0;
    float y = float((gl_VertexID & 2) << 1) - 1.0;
    gl_Position = vec4(x, y, 0.0, 1.0);
    texCoord = vec2((x + 1.0) * 0.5, 1.0 - (y + 1.0) * 0.5);
}
