#version 330
in vec3 in_position;
in vec3 in_color;
in float in_size;
in float in_power;
in float in_phase;
uniform mat4 u_vp;
uniform vec3 u_camera;
uniform float u_height;
uniform float u_time;
uniform float u_size;
uniform int u_cloud;
out vec3 v_color;
out float v_power;
out float v_phase;
void main() {
    vec3 pos = in_position;
    if (u_cloud == 1) {
        pos += vec3(sin(u_time*0.07+in_phase*31.0),
                    cos(u_time*0.05+in_phase*23.0),
                    sin(u_time*0.04+in_phase*17.0))*0.2;
    }
    vec4 projected = u_vp * vec4(pos, 1.0);
    gl_Position = projected;
    float diameter = in_size * u_height * 0.96 / max(projected.w, 0.1);
    float maxSize = u_cloud == 1 ? 180.0 : 72.0;
    gl_PointSize = clamp(diameter * u_size, u_cloud == 1 ? 2.0 : 1.0, maxSize);
    float nearFade = smoothstep(0.1, u_cloud == 1 ? 5.0 : 0.35, distance(pos, u_camera));
    v_color = in_color;
    v_power = in_power * nearFade;
    v_phase = in_phase;
}
