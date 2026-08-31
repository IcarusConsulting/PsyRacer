shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_opaque, shadows_disabled;

uniform sampler2D skyline_tex : source_color, filter_linear, repeat_disable;
uniform float brightness = 16.0;
uniform float alpha_cut = 0.12;

void fragment() {
	vec4 c = texture(skyline_tex, UV);
	if (c.a < alpha_cut) {
		discard;
	}
	ALBEDO = c.rgb * brightness;
	ALPHA = 1.0;
}
