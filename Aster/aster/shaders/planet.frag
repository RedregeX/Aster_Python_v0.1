#version 330
in vec3 v_normal;
in vec3 v_world;
uniform vec3 u_color;
uniform vec3 u_camera;
uniform int u_kind;
out vec4 fragColor;
void main() {
    vec3 n=normalize(v_normal);
    vec3 light=normalize(-v_world);
    float diffuse=max(dot(n,light),0.0);
    float bands=sin(n.y*42.0+sin(n.x*13.0+n.z*7.0)*1.2)*0.5+0.5;
    vec3 albedo=u_color*(0.55+bands*0.45);
    if(u_kind==1) {
        float continents=sin(n.x*14.0+sin(n.z*9.0))*sin(n.y*17.0+n.z*12.0);
        albedo=mix(vec3(0.06,0.2,0.50),vec3(0.16,0.40,0.26),smoothstep(0.1,0.4,continents));
        float clouds=sin(n.x*32.0+sin(n.z*16.0))*sin(n.y*25.0+n.x*19.0);
        albedo=mix(albedo,vec3(0.85),smoothstep(0.45,0.85,clouds)*0.6);
    }
    float rim=pow(1.0-max(dot(n,normalize(u_camera-v_world)),0.0),3.0);
    vec3 color=albedo*(0.07+diffuse*1.4)+u_color*rim*0.18;
    fragColor=vec4(color,1);
}
