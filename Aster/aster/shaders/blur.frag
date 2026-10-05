#version 330
in vec2 uv;
uniform sampler2D u_image;
uniform vec2 u_direction;
uniform int u_extract;
out vec4 fragColor;
vec3 sampleAt(vec2 p) {
    vec3 c=texture(u_image,p).rgb;
    if (u_extract == 1) c *= smoothstep(0.20,0.85,max(c.r,max(c.g,c.b)));
    return c;
}
void main() {
    vec3 c = sampleAt(uv)*0.227027;
    c += sampleAt(uv+u_direction*1.384615)*0.316216;
    c += sampleAt(uv-u_direction*1.384615)*0.316216;
    c += sampleAt(uv+u_direction*3.230769)*0.070270;
    c += sampleAt(uv-u_direction*3.230769)*0.070270;
    fragColor = vec4(c,1);
}
