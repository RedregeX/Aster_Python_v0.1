#version 330
in vec3 in_position;
uniform mat4 u_vp;
out float v_dummy;
void main() {gl_Position=u_vp*vec4(in_position,1.0); v_dummy=1.0;}
