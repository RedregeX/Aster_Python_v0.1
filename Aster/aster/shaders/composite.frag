#version 330
in vec2 uv;
uniform sampler2D u_scene;
uniform sampler2D u_glow;
uniform float u_bloom;
uniform float u_exposure;
out vec4 fragColor;
void main() {
    vec3 color = texture(u_scene,uv).rgb + texture(u_glow,uv).rgb*u_bloom;
    color = vec3(1.0)-exp(-color*u_exposure);
    color = pow(color,vec3(1.0/2.2));
    vec2 p = uv*2.0-1.0;
    color *= 1.0-0.18*dot(p,p);
    fragColor = vec4(color,1);
}
