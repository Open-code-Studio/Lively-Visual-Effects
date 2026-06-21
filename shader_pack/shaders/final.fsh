#version 150
uniform sampler2D composite;
in vec2 texCoord;
layout(location = 0) out vec4 fragColor;
void main() { fragColor = texture(composite, texCoord); }
