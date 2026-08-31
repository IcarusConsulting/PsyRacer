shader_type spatial;
render_mode unshaded, cull_front, depth_draw_never, blend_add, shadows_disabled;

uniform sampler2D glyph_atlas : source_color, filter_nearest, repeat_disable;
uniform float columns = 180.0;
uniform float rows = 52.0;
uniform float hue_speed = 0.28;
uniform float fall_speed = 0.55;
uniform float brightness = 16.0;
uniform int atlas_cols = 16;
uniform int atlas_rows = 4;

vec3 hsv2rgb(vec3 c) {
	vec3 p = abs(fract(c.xxx + vec3(0.0, 0.6666667, 0.3333333)) * 6.0 - 3.0);
	return c.z * mix(vec3(1.0), clamp(p - 1.0, 0.0, 1.0), c.y);
}

void fragment() {
	// Cylinder V: 0 at the top of the sky, 1 at the horizon.
	vec2 uv = UV;
	float horizon_fade = 1.0 - smoothstep(0.82, 0.995, uv.y);
	if (horizon_fade < 0.02) {
		discard;
	}

	vec2 grid = vec2(columns, rows);
	vec2 cell = floor(uv * grid);
	vec2 local = fract(uv * grid);
	float col_id = cell.x;
	float skip = fract(sin(col_id * 12.9898) * 43758.5453);
	if (skip < 0.18) {
		discard;
	}

	float speed = 0.45 + fract(sin(col_id * 78.233) * 921.31) * 1.35;
	float trail = 8.0 + floor(fract(sin(col_id * 4.1) * 63.2) * 12.0);
	float cycle = rows + trail;
	float head = mod(TIME * fall_speed * speed * rows + col_id * 17.0, cycle);
	float dist = head - cell.y;
	if (dist < 0.0 || dist > trail) {
		discard;
	}

	float fade = 1.0 - dist / trail;
	if (fade < 0.1) {
		discard;
	}

	float glyph_count = float(atlas_cols * atlas_rows);
	float gi = mod(col_id * 13.0 + cell.y * 7.0 + floor(TIME * 14.0) + skip * 8.0, glyph_count);
	vec2 atlas = vec2(mod(gi, float(atlas_cols)), floor(gi / float(atlas_cols)));
	vec2 auv = (atlas + local) / vec2(float(atlas_cols), float(atlas_rows));
	float g = texture(glyph_atlas, auv).r;
	if (g < 0.15) {
		discard;
	}

	bool head_cell = dist < 1.15;
	float hue = fract(TIME * hue_speed + col_id * 0.017 - dist * 0.028);
	float sat = head_cell ? 0.35 : 0.92;
	float val = head_cell ? 1.0 : (0.22 + 0.78 * fade);
	vec3 col = hsv2rgb(vec3(hue, sat, val));
	ALBEDO = col * (head_cell ? 1.35 : 1.0) * brightness;
	ALPHA = horizon_fade * fade * g * (head_cell ? 1.0 : 0.85);
}
