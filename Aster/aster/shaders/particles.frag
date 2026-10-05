#version 330
in vec3 v_color;
in float v_power;
in float v_phase;
uniform int u_cloud;
uniform float u_time;
out vec4 fragColor;
float hash(vec2 p) {return fract(sin(dot(p, vec2(127.1, 311.7)))*43758.5453);}
float noise(vec2 p) {
    vec2 i=floor(p), f=fract(p); f=f*f*(3.0-2.0*f);
    return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),
               mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);
}
void main() {
    vec2 p = gl_PointCoord*2.0-1.0;
    float r2 = dot(p,p);
    if (r2 > 1.0) discard;
    float alpha;
    if (u_cloud == 1) {
        vec2 q = p*3.0+v_phase*43.0;
        float textureNoise = noise(q)*0.60 + noise(q*2.1)*0.25 + noise(q*4.3)*0.15;
        alpha = exp(-r2*4.8) * (1.0-smoothstep(0.65,1.0,r2)) * (0.28+textureNoise*0.85);
    } else {
        float core = exp(-r2*20.0);
        float halo = exp(-r2*4.0)*0.13;
        float spikes = (exp(-abs(p.x)*65.0)*exp(-abs(p.y)*5.0)
                       +exp(-abs(p.y)*65.0)*exp(-abs(p.x)*5.0))*0.10;
        alpha = (core+halo+spikes)*(1.0-smoothstep(0.7,1.0,r2));
        alpha *= 0.94+0.06*sin(u_time*0.8+v_phase*90.0);
    }
    fragColor = vec4(v_color*v_power, alpha);
}
