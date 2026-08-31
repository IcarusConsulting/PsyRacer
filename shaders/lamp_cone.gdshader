shader_type spatial;
render_mode unshaded, cull_disabled, blend_add, depth_draw_never, shadows_disabled;

uniform vec3 glow_color = vec3(0.55, 0.85, 1.0);
uniform float density = 0.42;

void fragment() {
	// Volume look: brighter on the silhouette, softer down the shaft.
	float ndotv = abs(dot(normalize(NORMAL), normalize(VIEW)));
	float rim = pow(1.0 - ndotv, 0.7);
	float core = pow(ndotv, 1.4) * 0.45;
	float along = UV.y;
	float shaft = smoothstep(0.0, 0.08, along) * (1.0 - smoothstep(0.72, 1.0, along));
	float a = (rim * 0.35 + core) * shaft * density;
	if (a < 0.01) {
		discard;
	}
	ALBEDO = glow_color;
	ALPHA = a;
}
