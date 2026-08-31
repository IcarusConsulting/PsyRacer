shader_type canvas_item;

uniform float hue_speed = 0.28;
uniform float sat = 0.82;
uniform float val = 1.0;
uniform float sweep = 0.16;

vec3 hsv2rgb(vec3 c) {
	vec3 p = abs(fract(c.xxx + vec3(0.0, 0.6666667, 0.3333333)) * 6.0 - 3.0);
	return c.z * mix(vec3(1.0), clamp(p - 1.0, 0.0, 1.0), c.y);
}

void fragment() {
	vec4 tex = texture(TEXTURE, UV);
	float hue = fract(TIME * hue_speed + UV.x * sweep);
	COLOR = vec4(hsv2rgb(vec3(hue, sat, val)), tex.a);
}
