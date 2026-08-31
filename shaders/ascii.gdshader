shader_type canvas_item;

uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_linear;
uniform sampler2D fill_tex : filter_nearest, repeat_disable;
uniform sampler2D edge_tex : filter_nearest, repeat_disable;
uniform float cell_size = 8.0;
uniform float blend_base = 0.7;
uniform float edge_threshold = 0.12;
uniform float exposure = 1.15;
uniform float attenuation = 0.9;
uniform vec3 ascii_tint = vec3(0.45, 0.92, 1.0);
uniform vec3 background_color = vec3(0.01, 0.015, 0.04);
uniform bool enabled = true;

float luma(vec3 c) {
	return dot(c, vec3(0.2127, 0.7152, 0.0722));
}

void fragment() {
	vec3 passthrough = texture(screen_texture, SCREEN_UV).rgb;
	if (!enabled) {
		COLOR = vec4(passthrough, 1.0);
	} else {
	vec2 pixel = SCREEN_UV / SCREEN_PIXEL_SIZE;
	vec2 cell_id = floor(pixel / cell_size);
	vec2 local = pixel - cell_id * cell_size;
	vec2 center_uv = (cell_id * cell_size + vec2(cell_size * 0.5)) * SCREEN_PIXEL_SIZE;
	vec2 texel = SCREEN_PIXEL_SIZE * cell_size;

	vec3 src = texture(screen_texture, center_uv).rgb;
	float lum = pow(clamp(luma(src) * exposure, 0.0, 1.0), attenuation);

	float n  = luma(texture(screen_texture, center_uv + vec2(0.0, -texel.y)).rgb);
	float s  = luma(texture(screen_texture, center_uv + vec2(0.0,  texel.y)).rgb);
	float w  = luma(texture(screen_texture, center_uv + vec2(-texel.x, 0.0)).rgb);
	float e  = luma(texture(screen_texture, center_uv + vec2( texel.x, 0.0)).rgb);
	float gx = e - w;
	float gy = n - s;
	float mag = length(vec2(gx, gy));
	float angle = atan(gy, gx);

	float glyph = 0.0;
	if (mag > edge_threshold) {
		float abs_t = abs(angle) / 3.14159265;
		float dir = 0.0;
		if (abs_t < 0.05 || abs_t > 0.9) {
			dir = 0.0;
		} else if (abs_t > 0.45 && abs_t < 0.55) {
			dir = 1.0;
		} else if (abs_t < 0.45) {
			dir = angle > 0.0 ? 3.0 : 2.0;
		} else {
			dir = angle > 0.0 ? 2.0 : 3.0;
		}
		float gx_atlas = local.x + (dir + 1.0) * 8.0;
		vec2 euv = vec2((gx_atlas + 0.5) / 40.0, (7.5 - local.y) / 8.0);
		glyph = texture(edge_tex, euv).r;
	} else {
		float idx = max(0.0, floor(lum * 10.0) - 1.0);
		idx = clamp(idx, 0.0, 9.0);
		float gx_atlas = local.x + idx * 8.0;
		vec2 fuv = vec2((gx_atlas + 0.5) / 80.0, (local.y + 0.5) / 8.0);
		glyph = texture(fill_tex, fuv).r;
	}

	glyph = step(0.12, glyph);
	vec3 ink = mix(ascii_tint, src, blend_base);
	vec3 col = mix(background_color, ink, glyph);
	COLOR = vec4(col, 1.0);
	}
}
