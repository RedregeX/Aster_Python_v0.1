#version 330
in vec2 uv;
uniform sampler2D u_ui;
out vec4 fragColor;
void main() {fragColor=texture(u_ui,vec2(uv.x,1.0-uv.y));}
