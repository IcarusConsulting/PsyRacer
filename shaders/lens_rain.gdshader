shader_type canvas_item;

uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_linear;
uniform float density = 0.44;
uniform float drip_speed = 0.38;
uniform float refraction = 0.014;
uniform float highlight = 0.38;
uniform float drip_dir = 1.0;

float hash12(vec2 p) {
	vec3 p3 = fract(vec3(p.xyx) * 0.1031);
	p3 += dot(p3, p3.yzx + 33.33);
	return fract((p3.x + p3.y) * p3.z);
}

vec2 hash22(vec2 p) {
	float n = hash12(p);
	float m = hash12(p + 17.13);
	return vec2(n, m);
}

void layer(vec2 uv, float cols, float rows, float t, float size, float speed, float aspect_x, float gravity, inout vec2 offset, inout float spec, inout float mask) {
	vec2 grid = uv * vec2(cols * aspect_x, rows);
	vec2 id = floor(grid);
	vec2 gv = fract(grid) - 0.5;
	vec2 rnd = hash22(id + vec2(cols, 3.1));
	if (rnd.x > density) {
		return;
	}
	float life = fract(t * speed * (0.55 + rnd.y * 0.7) + rnd.x);
	// Hit, then travel. UV.y increases downward, so +dir is down the screen.
	float drip = smoothstep(0.06, 0.22, life);
	float y = mix(-0.42, 0.48, drip * drip) * gravity;
	vec2 center = vec2((rnd.y - 0.5) * 0.55, y);
	vec2 p = gv - center;
	float stretch = mix(1.0, 3.2, drip);
	p.y /= stretch;
	float r = size * mix(0.9, 0.55, drip) * mix(0.85, 1.15, rnd.x);
	float d = length(p);
	float blob = smoothstep(r, r * 0.35, d);
	if (blob < 0.01) {
		return;
	}
	vec2 dir = p / max(d, 0.0001);
	offset += dir * blob * refraction * (1.0 - drip * 0.35);
	float rim = smoothstep(r * 0.95, r * 0.55, d) * (1.0 - smoothstep(r * 0.45, r * 0.1, d));
	spec += rim * blob * (0.55 + 0.45 * (1.0 - drip));
	mask = max(mask, blob * 0.65);
}

void fragment() {
	vec2 uv = SCREEN_UV;
	vec2 offset = vec2(0.0);
	float spec = 0.0;
	float mask = 0.0;
	float t = TIME * drip_speed;
	float aspect_x = 16.0 / 9.0;

	layer(uv, 9.0, 6.0, t, 0.11, 0.85, aspect_x, drip_dir, offset, spec, mask);
	layer(uv + vec2(0.17, 0.31), 14.0, 9.0, t * 1.15 + 4.2, 0.07, 1.15, aspect_x, drip_dir, offset, spec, mask);
	layer(uv + vec2(0.41, 0.07), 20.0, 13.0, t * 0.7 + 9.1, 0.045, 0.55, aspect_x, drip_dir, offset, spec, mask);

	vec3 scene = texture(screen_texture, clamp(uv + offset, vec2(0.001), vec2(0.999))).rgb;
	vec3 drop_tint = mix(vec3(0.75, 0.92, 1.0), vec3(1.0, 0.82, 0.55), 0.25);
	vec3 col = scene + spec * highlight * drop_tint * 0.55;
	col = mix(scene, col, 0.85);
	COLOR = vec4(col, 1.0);
}
