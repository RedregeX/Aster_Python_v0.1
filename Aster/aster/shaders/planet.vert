#version 330
in vec3 in_position;
uniform mat4 u_vp;
uniform vec3 u_center;
uniform float u_radius;
uniform float u_rotation;
out vec3 v_normal;
out vec3 v_world;
void main() {
    float c=cos(u_rotation), s=sin(u_rotation);
    vec3 p=vec3(c*in_position.x+s*in_position.z,in_position.y,
                -s*in_position.x+c*in_position.z);
    v_normal=p;
    v_world=p*u_radius+u_center;
    gl_Position=u_vp*vec4(v_world,1);
}
