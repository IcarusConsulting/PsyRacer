class_name RaceWorld
extends Node3D

static var start_difficulty: RaceSim.Difficulty = RaceSim.Difficulty.MEDIUM

const LANE_HALF := 7.0
const ROAD_HALF := 7.6
const LOOK_AHEAD := 220.0
const LOOK_BEHIND := 18.0
const Z_STEP := 2.0
const SIGN_SPACING := 2000
const SIGN_PLACES := [
	["新宿", "SHINJUKU"],
	["渋谷", "SHIBUYA"],
	["横浜", "YOKOHAMA"],
	["東京", "TOKYO"],
	["秋葉原", "AKIHABARA"],
	["お台場", "ODAIBA"],
]

var sim: RaceSim
var _player: HyperCar
var _ai_nodes: Array[HyperCar] = []
var _camera: Camera3D
var _road: MeshInstance3D
var _skyline: MeshInstance3D
var _rain: MeshInstance3D
var _env: Environment
var _hud_speed: Label
var _hud_place: Label
var _hud_dist: Label
var _hud_count: Label
var _scenery: Node3D
var _last_mesh_z: float = -999.0
var _finish_hold := 0.0
var _lamp_root: Node3D
var _prev_player_x := 0.0
var _prev_ai_x: Array[float] = []


func _ready() -> void:
	sim = RaceSim.new()
	sim.setup(start_difficulty)
	_build_world()
	_build_hud()
	_update_horizon()


func _build_world() -> void:
	var we := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.012, 0.016, 0.04)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.15, 0.22, 0.4)
	env.ambient_light_energy = 0.4
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.tonemap_exposure = 1.05
	env.glow_enabled = true
	env.glow_intensity = 0.85
	env.glow_bloom = 0.18
	env.fog_enabled = true
	env.fog_light_color = Color(0.03, 0.04, 0.1)
	env.fog_density = 0.01
	env.fog_sky_affect = 0.6
	env.volumetric_fog_enabled = true
	env.volumetric_fog_density = 0.018
	env.volumetric_fog_albedo = Color(0.55, 0.62, 0.78)
	env.volumetric_fog_emission = Color(0.03, 0.04, 0.07)
	env.volumetric_fog_emission_energy = 0.35
	env.volumetric_fog_anisotropy = 0.45
	env.volumetric_fog_length = 64.0
	env.volumetric_fog_ambient_inject = 0.12
	_env = env
	we.environment = env
	add_child(we)

	var moon := DirectionalLight3D.new()
	moon.rotation_degrees = Vector3(-42, 30, 0)
	moon.light_color = Color(0.45, 0.6, 1.0)
	moon.light_energy = 0.35
	moon.light_volumetric_fog_energy = 0.08
	moon.shadow_enabled = false
	add_child(moon)

	_road = MeshInstance3D.new()
	_road.name = "Road"
	add_child(_road)
	_rebuild_road(true)

	_player = HyperCar.new()
	_player.is_player = true
	_player.number = 1
	add_child(_player)

	var ai_look := [
		[Color(0.03, 0.04, 0.05), Color(1.0, 0.35, 0.7), Color(0.4, 0.9, 1.0)],
		[Color(0.04, 0.03, 0.05), Color(0.4, 1.0, 0.7), Color(1.0, 0.5, 0.15)],
		[Color(0.05, 0.04, 0.03), Color(1.0, 0.85, 0.2), Color(0.3, 0.8, 1.0)],
		[Color(0.04, 0.05, 0.04), Color(1.0, 0.25, 0.2), Color(0.5, 0.9, 1.0)],
		[Color(0.03, 0.03, 0.05), Color(0.7, 0.4, 1.0), Color(1.0, 0.45, 0.15)],
	]
	for i in sim.cars.size():
		var car := HyperCar.new()
		car.number = sim.cars[i].number
		car.body = ai_look[i][0]
		car.orange = ai_look[i][1]
		car.cyan = ai_look[i][2]
		add_child(car)
		_ai_nodes.append(car)
		_prev_ai_x.append(sim.cars[i].x)

	_skyline = MeshInstance3D.new()
	_skyline.name = "HorizonCity"
	var quad := QuadMesh.new()
	quad.size = Vector2(640, 36)
	_skyline.mesh = quad
	var sky_mat := ShaderMaterial.new()
	sky_mat.shader = load("res://shaders/skyline.gdshader")
	sky_mat.set_shader_parameter("skyline_tex", load("res://assets/sprites/horizon_skyline.png"))
	sky_mat.set_shader_parameter("brightness", 16.0)
	_skyline.material_override = sky_mat
	add_child(_skyline)

	_rain = MeshInstance3D.new()
	_rain.name = "MatrixRain"
	var rain_cyl := CylinderMesh.new()
	rain_cyl.top_radius = 200.0
	rain_cyl.bottom_radius = 200.0
	rain_cyl.height = 140.0
	rain_cyl.radial_segments = 48
	rain_cyl.rings = 1
	rain_cyl.cap_top = false
	rain_cyl.cap_bottom = false
	_rain.mesh = rain_cyl
	var rain_mat := ShaderMaterial.new()
	rain_mat.shader = load("res://shaders/matrix_rain.gdshader")
	rain_mat.set_shader_parameter("glyph_atlas", load("res://assets/ascii/matrix_glyphs.png"))
	rain_mat.set_shader_parameter("brightness", 16.0)
	rain_mat.set_shader_parameter("columns", 180.0)
	rain_mat.set_shader_parameter("rows", 52.0)
	_rain.material_override = rain_mat
	_rain.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_rain)

	_scenery = Node3D.new()
	_scenery.name = "Scenery"
	add_child(_scenery)
	_lamp_root = Node3D.new()
	add_child(_lamp_root)

	_camera = Camera3D.new()
	_camera.fov = 62.0
	_camera.near = 0.15
	_camera.far = 520.0
	add_child(_camera)
	_camera.current = true


func _build_hud() -> void:
	var hud := CanvasLayer.new()
	hud.layer = 20
	add_child(hud)
	var root := Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud.add_child(root)

	_hud_speed = _make_label(root, Vector2(40, 28), 28)
	_hud_place = _make_label(root, Vector2(40, 68), 22)
	_hud_dist = _make_label(root, Vector2(40, 100), 22)
	_hud_count = _make_label(root, Vector2(0, 360), 72)
	_hud_count.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_hud_count.set_anchors_preset(Control.PRESET_TOP_WIDE)
	_hud_count.offset_top = 340
	_hud_count.offset_bottom = 430

	var hint := _make_label(root, Vector2(40, 1000), 16)
	hint.text = "ESC menu    M music"
	hint.modulate = Color(0.55, 0.85, 1.0, 0.7)


func _make_label(parent: Control, pos: Vector2, size: int) -> Label:
	var l := Label.new()
	l.position = pos
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", Color(0.55, 0.95, 1.0))
	l.add_theme_color_override("font_outline_color", Color(0.02, 0.04, 0.1))
	l.add_theme_constant_override("outline_size", 6)
	parent.add_child(l)
	return l


func _unhandled_input(event: InputEvent) -> void:
	if event.is_pressed() and event is InputEventKey:
		var k := event as InputEventKey
		if k.physical_keycode == KEY_ESCAPE:
			get_tree().change_scene_to_file("res://scenes/boot.tscn")
			get_viewport().set_input_as_handled()


func _process(delta: float) -> void:
	var steer := 0.0
	var throttle := 0.0
	var brake := 0.0
	if Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT):
		steer += 1.0
	if Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT):
		steer -= 1.0
	if Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP):
		throttle = 1.0
	if Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN):
		brake = 1.0

	sim.tick(delta, steer, throttle, brake)
	_sync_transforms(delta)
	_rebuild_road(false)
	_update_scenery()
	_update_horizon()
	_update_hud()

	if sim.finished:
		_finish_hold += delta
		if _finish_hold > 2.2:
			get_tree().change_scene_to_file("res://scenes/boot.tscn")


func _sync_transforms(delta: float) -> void:
	var ppos := sim.world_pos(sim.distance, sim.player_x)
	ppos.y = 0.0
	_player.global_position = ppos
	var heading := -RaceSim.road_curve(sim.distance + 6.0) * 0.45
	var dt := maxf(delta, 0.0001)
	var player_slide := clampf((sim.player_x - _prev_player_x) / dt * 1.6, -1.0, 1.0)
	_prev_player_x = sim.player_x
	_player.pose(heading, player_slide, delta)

	for i in _ai_nodes.size():
		var r: RaceSim.Racer = sim.cars[i]
		var apos := sim.world_pos(r.z, r.x)
		_ai_nodes[i].global_position = apos
		var ai_heading := -RaceSim.road_curve(r.z + 6.0) * 0.45
		var ai_slide := clampf((r.x - _prev_ai_x[i]) / dt * 1.6, -1.0, 1.0)
		_prev_ai_x[i] = r.x
		_ai_nodes[i].pose(ai_heading, ai_slide, delta)
		_ai_nodes[i].visible = (r.z - sim.distance) > -8.0 and (r.z - sim.distance) < LOOK_AHEAD

	var cam_back := Vector3(sin(heading) * 8.2, 2.15, -cos(heading) * 8.2)
	var cam_pos := ppos + cam_back + Vector3(0, 0, 0)
	cam_pos.y = 2.15
	var look := ppos + Vector3(-sin(heading) * 14.0, 0.7, cos(heading) * 14.0)
	_camera.look_at_from_position(cam_pos, look, Vector3.UP)


func _road_mat(color: Color, rough: float) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.metallic = 0.35
	m.roughness = rough
	return m


func _rebuild_road(force: bool) -> void:
	if not force and absf(sim.distance - _last_mesh_z) < 1.5:
		return
	_last_mesh_z = sim.distance
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var z0 := sim.distance - LOOK_BEHIND
	var z1 := sim.distance + LOOK_AHEAD
	var z := z0
	while z < z1:
		var z2 := z + Z_STEP
		var c0 := RaceSim.road_center(z)
		var c1 := RaceSim.road_center(z2)
		var l0 := Vector3(c0 - ROAD_HALF, 0.0, z)
		var r0 := Vector3(c0 + ROAD_HALF, 0.0, z)
		var l1 := Vector3(c1 - ROAD_HALF, 0.0, z2)
		var r1 := Vector3(c1 + ROAD_HALF, 0.0, z2)
		_quad(st, l0, r0, r1, l1)
		z = z2
	var mesh := st.commit()
	var mat := _road_mat(Color(0.07, 0.075, 0.09), 0.18)
	mesh.surface_set_material(0, mat)
	_road.mesh = mesh

	# Shoulder / grass as a second strip via child
	var shoulder := _road.get_node_or_null("Shoulder") as MeshInstance3D
	if shoulder == null:
		shoulder = MeshInstance3D.new()
		shoulder.name = "Shoulder"
		_road.add_child(shoulder)
	var ss := SurfaceTool.new()
	ss.begin(Mesh.PRIMITIVE_TRIANGLES)
	z = z0
	while z < z1:
		var z2 := z + Z_STEP
		var c0 := RaceSim.road_center(z)
		var c1 := RaceSim.road_center(z2)
		for side: float in [-1.0, 1.0]:
			var a := Vector3(c0 + side * ROAD_HALF, -0.02, z)
			var b := Vector3(c0 + side * (ROAD_HALF + 18.0), -0.02, z)
			var c := Vector3(c1 + side * (ROAD_HALF + 18.0), -0.02, z2)
			var d := Vector3(c1 + side * ROAD_HALF, -0.02, z2)
			if side > 0.0:
				_quad(ss, a, b, c, d)
			else:
				_quad(ss, a, d, c, b)
		z = z2
	var sm := ss.commit()
	sm.surface_set_material(0, _road_mat(Color(0.02, 0.03, 0.05), 0.7))
	shoulder.mesh = sm

	var marks := _road.get_node_or_null("Marks") as MeshInstance3D
	if marks == null:
		marks = MeshInstance3D.new()
		marks.name = "Marks"
		_road.add_child(marks)
	var ms := SurfaceTool.new()
	ms.begin(Mesh.PRIMITIVE_TRIANGLES)
	z = z0
	while z < z1:
		var dash_on := int(floor(z / 4.0)) % 2 == 0
		if dash_on:
			var z2 := minf(z + 2.4, z1)
			var c0 := RaceSim.road_center(z)
			var c1 := RaceSim.road_center(z2)
			var w := 0.12
			_quad(ms,
				Vector3(c0 - w, 0.03, z),
				Vector3(c0 + w, 0.03, z),
				Vector3(c1 + w, 0.03, z2),
				Vector3(c1 - w, 0.03, z2))
			for side: float in [-1.0, 1.0]:
				var e0: float = c0 + side * (ROAD_HALF - 0.18)
				var e1: float = c1 + side * (ROAD_HALF - 0.18)
				_quad(ms,
					Vector3(e0 - 0.08, 0.03, z),
					Vector3(e0 + 0.08, 0.03, z),
					Vector3(e1 + 0.08, 0.03, z2),
					Vector3(e1 - 0.08, 0.03, z2))
		z += 2.0
	var mm := ms.commit()
	var mark_mat := _road_mat(Color(0.95, 0.85, 0.25), 0.4)
	mark_mat.emission_enabled = true
	mark_mat.emission = Color(1.0, 0.8, 0.2)
	mark_mat.emission_energy_multiplier = 0.6
	mm.surface_set_material(0, mark_mat)
	marks.mesh = mm


func _quad(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, d: Vector3) -> void:
	var n := (b - a).cross(d - a).normalized()
	st.set_normal(n)
	st.add_vertex(a)
	st.add_vertex(b)
	st.add_vertex(c)
	st.add_vertex(a)
	st.add_vertex(c)
	st.add_vertex(d)


func _race_progress() -> float:
	return clampf(sim.distance / maxf(sim.finish_distance, 1.0), 0.0, 1.0)


func _update_horizon() -> void:
	var t := _race_progress()
	var ease := t * t * (3.0 - 2.0 * t)
	# Stay a thin far band early; rush in over the last third.
	var approach := pow(ease, 1.15)
	var dist_ahead := lerpf(310.0, 38.0, approach)
	var city_h := lerpf(34.0, 128.0, approach)
	var city_w := lerpf(620.0, 240.0, approach)

	(_skyline.mesh as QuadMesh).size = Vector2(city_w, city_h)

	var z := sim.distance + dist_ahead
	var x := RaceSim.road_center(z)
	var heading := -RaceSim.road_curve(sim.distance + 6.0) * 0.45
	# Quad faces +Z; rotate so the city faces the incoming camera.
	var face := heading + PI
	_skyline.global_position = Vector3(x, city_h * 0.5, z)
	_skyline.rotation = Vector3(0.0, face, 0.0)

	# Rain cylinder around the camera: falls from the top of the view and wraps
	# left/right into the distance, dying at the horizon (y = 0).
	var radius := dist_ahead + 12.0
	var rain_h: float = maxf(48.0, radius * 0.72)
	var cyl := _rain.mesh as CylinderMesh
	cyl.top_radius = radius
	cyl.bottom_radius = radius
	cyl.height = rain_h
	var cam := _camera.global_position
	_rain.global_position = Vector3(cam.x, rain_h * 0.5, cam.z)
	_rain.rotation = Vector3.ZERO

	if _env:
		_env.fog_density = lerpf(0.012, 0.0035, approach)
		_env.fog_aerial_perspective = lerpf(0.4, 0.08, approach)


func _update_scenery() -> void:
	var want: Dictionary = {}
	var z := int(sim.distance) - 8
	var endz := int(sim.distance + LOOK_AHEAD)
	z -= z % 4
	while z < endz:
		if z % 32 == 0:
			want["l%d" % z] = [z, 1.16, true]
		if z % 32 == 16:
			want["r%d" % z] = [z, -1.16, true]
		if z >= SIGN_SPACING and z % SIGN_SPACING == 0:
			want["s%d" % z] = [z, 0.0, true]
		z += 4

	for child in _scenery.get_children():
		if not want.has(child.name):
			child.queue_free()

	for key: String in want:
		if _scenery.has_node(NodePath(key)):
			var n := _scenery.get_node(key) as Node3D
			var spec: Array = want[key]
			var sz := float(spec[0])
			n.global_position = sim.world_pos(sz, float(spec[1]))
			n.position.y = 0.0
			if key.begins_with("s"):
				n.rotation.y = -RaceSim.road_curve(sz + 6.0) * 0.45
			continue
		var spec2: Array = want[key]
		var zz := int(spec2[0])
		var lane := float(spec2[1])
		if key.begins_with("s"):
			_scenery.add_child(_make_sign(key, zz))
		else:
			_scenery.add_child(_make_lamp(key, zz, lane))


func _make_sign(key: String, z: int) -> Node3D:
	# NEXCO-style overhead gantry: green plate, white gothic type, route badge.
	var n := Node3D.new()
	n.name = key
	n.position = sim.world_pos(float(z), 0.0)
	n.rotation.y = -RaceSim.road_curve(float(z) + 6.0) * 0.45
	var metal := StandardMaterial3D.new()
	metal.albedo_color = Color(0.08, 0.09, 0.11)
	metal.metallic = 0.8
	metal.roughness = 0.38
	var green := StandardMaterial3D.new()
	green.albedo_color = Color(0.0, 0.38, 0.24)
	green.metallic = 0.15
	green.roughness = 0.45
	green.emission_enabled = true
	green.emission = Color(0.0, 0.55, 0.32)
	green.emission_energy_multiplier = 0.45
	var white := StandardMaterial3D.new()
	white.albedo_color = Color(0.92, 0.95, 0.92)
	white.emission_enabled = true
	white.emission = Color(0.85, 0.95, 0.88)
	white.emission_energy_multiplier = 0.25

	var post_x := ROAD_HALF + 0.85
	for side: float in [-1.0, 1.0]:
		var post := MeshInstance3D.new()
		var pm := CylinderMesh.new()
		pm.top_radius = 0.12
		pm.bottom_radius = 0.16
		pm.height = 7.4
		post.mesh = pm
		post.position = Vector3(side * post_x, 3.7, 0.0)
		post.material_override = metal
		n.add_child(post)

	var beam := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(post_x * 2.0 + 0.4, 0.28, 0.28)
	beam.mesh = bm
	beam.position = Vector3(0.0, 7.35, 0.0)
	beam.material_override = metal
	n.add_child(beam)

	var plate := MeshInstance3D.new()
	var pb := BoxMesh.new()
	pb.size = Vector3(13.2, 1.85, 0.1)
	plate.mesh = pb
	plate.position = Vector3(0.0, 6.35, -0.18)
	plate.material_override = green
	n.add_child(plate)

	var border := MeshInstance3D.new()
	var bb := BoxMesh.new()
	bb.size = Vector3(13.45, 2.05, 0.06)
	border.mesh = bb
	border.position = Vector3(0.0, 6.35, -0.12)
	border.material_override = white
	n.add_child(border)

	var badge := MeshInstance3D.new()
	var badge_mesh := BoxMesh.new()
	badge_mesh.size = Vector3(1.35, 1.15, 0.08)
	badge.mesh = badge_mesh
	badge.position = Vector3(-5.4, 6.35, -0.26)
	badge.material_override = white
	n.add_child(badge)

	var font: Font = _highway_font()
	var idx := int(z / SIGN_SPACING) % SIGN_PLACES.size()
	var place: Array = SIGN_PLACES[idx]
	var km := maxi(1, int(round((sim.finish_distance - float(z)) / 1000.0)))

	var jp := Label3D.new()
	jp.text = "方面  %s" % str(place[0])
	jp.font = font
	jp.font_size = 96
	jp.pixel_size = 0.012
	jp.modulate = Color.WHITE
	jp.outline_size = 6
	jp.outline_modulate = Color(0.0, 0.15, 0.08)
	jp.position = Vector3(-0.6, 6.55, -0.28)
	jp.rotation.y = PI
	jp.shaded = false
	n.add_child(jp)

	var en := Label3D.new()
	en.text = "%s    出口  %d km" % [str(place[1]), km]
	en.font = font
	en.font_size = 48
	en.pixel_size = 0.012
	en.modulate = Color(0.95, 1.0, 0.95)
	en.outline_size = 4
	en.position = Vector3(-0.4, 6.12, -0.28)
	en.rotation.y = PI
	en.shaded = false
	n.add_child(en)

	var route := Label3D.new()
	route.text = "C1"
	route.font = font
	route.font_size = 64
	route.pixel_size = 0.012
	route.modulate = Color(0.0, 0.32, 0.2)
	route.position = Vector3(-5.4, 6.35, -0.32)
	route.rotation.y = PI
	route.shaded = false
	n.add_child(route)
	return n


func _make_lamp(key: String, z: int, lane: float) -> Node3D:
	var n := Node3D.new()
	n.name = key
	n.position = sim.world_pos(float(z), lane)
	var metal := StandardMaterial3D.new()
	metal.albedo_color = Color(0.07, 0.08, 0.1)
	metal.metallic = 0.85
	metal.roughness = 0.35
	var pole := MeshInstance3D.new()
	var pole_mesh := CylinderMesh.new()
	pole_mesh.top_radius = 0.07
	pole_mesh.bottom_radius = 0.11
	pole_mesh.height = 6.4
	pole.mesh = pole_mesh
	pole.position.y = 3.2
	pole.material_override = metal
	n.add_child(pole)

	var inward := -signf(lane)
	var arm_len := 1.35
	var arm := MeshInstance3D.new()
	var arm_mesh := BoxMesh.new()
	arm_mesh.size = Vector3(arm_len, 0.07, 0.07)
	arm.mesh = arm_mesh
	arm.position = Vector3(inward * arm_len * 0.5, 6.38, 0.0)
	arm.material_override = metal
	n.add_child(arm)

	var led_x := inward * arm_len
	var led_y := 6.22
	var glow := Color(0.72, 0.92, 1.0)

	var diode := MeshInstance3D.new()
	var diode_mesh := SphereMesh.new()
	diode_mesh.radius = 0.11
	diode_mesh.height = 0.22
	diode.mesh = diode_mesh
	diode.position = Vector3(led_x, led_y, 0.0)
	var led_mat := StandardMaterial3D.new()
	led_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	led_mat.albedo_color = Color.WHITE
	led_mat.emission_enabled = true
	led_mat.emission = glow
	led_mat.emission_energy_multiplier = 3.2
	diode.material_override = led_mat
	n.add_child(diode)

	var lens := MeshInstance3D.new()
	var lens_mesh := SphereMesh.new()
	lens_mesh.radius = 0.24
	lens_mesh.height = 0.48
	lens.mesh = lens_mesh
	lens.position = Vector3(led_x, led_y, 0.0)
	var lens_mat := StandardMaterial3D.new()
	lens_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	lens_mat.albedo_color = Color(glow.r, glow.g, glow.b, 0.28)
	lens_mat.emission_enabled = true
	lens_mat.emission = glow
	lens_mat.emission_energy_multiplier = 0.7
	lens_mat.roughness = 0.15
	lens.material_override = lens_mat
	n.add_child(lens)

	var housing := MeshInstance3D.new()
	var house_mesh := CylinderMesh.new()
	house_mesh.top_radius = 0.16
	house_mesh.bottom_radius = 0.2
	house_mesh.height = 0.1
	housing.mesh = house_mesh
	housing.position = Vector3(led_x, led_y + 0.12, 0.0)
	housing.material_override = metal
	n.add_child(housing)

	var spot := SpotLight3D.new()
	spot.position = Vector3(led_x, led_y - 0.04, 0.0)
	spot.rotation_degrees = Vector3(-90.0, 0.0, 0.0)
	spot.light_color = glow
	spot.light_energy = 0.75
	spot.light_size = 0.62
	spot.light_specular = 0.12
	spot.light_volumetric_fog_energy = 0.0
	spot.spot_range = 16.0
	spot.spot_angle = 68.0
	spot.spot_angle_attenuation = 0.18
	spot.spot_attenuation = 0.55
	spot.shadow_enabled = false
	n.add_child(spot)
	return n


func _update_hud() -> void:
	var kmh := int(sim.speed * 180.0)
	_hud_speed.text = "%d KM/H" % kmh
	_hud_place.text = "P%d / 6" % sim.race_place()
	var left := maxf(0.0, sim.finish_distance - sim.distance)
	_hud_dist.text = "%d m" % int(left)
	if sim.countdown_text != "":
		_hud_count.text = sim.countdown_text
		_hud_count.modulate = Color(0.2, 1.0, 0.4) if sim.lights_stage == 4 else Color(1.0, 0.25, 0.2)
	elif sim.finished:
		_hud_count.text = "FINISH"
		_hud_count.modulate = Color(1.0, 0.85, 0.2)
	elif sim.crashed:
		_hud_count.text = "CONTACT"
		_hud_count.modulate = Color(1.0, 0.4, 0.15)
	else:
		_hud_count.text = ""


func _highway_font() -> Font:
	var bundled: Font = load("res://assets/fonts/YuGothR.ttc")
	if bundled != null:
		return bundled
	var sys := SystemFont.new()
	sys.font_names = PackedStringArray(["Yu Gothic", "Yu Gothic UI", "Meiryo", "MS Gothic", "Noto Sans CJK JP"])
	return sys

