class_name RaceWorld
extends Node3D

static var start_mode: RaceSim.Mode = RaceSim.Mode.STANDARD

const LANE_HALF := 7.0
const ROAD_HALF := 12.0
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
var _land: MeshInstance3D
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
var _camera_offset: Vector3 = Vector3(0.0, 2.35, -9.2)
var _skyline_heading := PI


func _ready() -> void:
	sim = RaceSim.new()
	sim.setup(start_mode)
	_build_world()
	_build_hud()
	_update_horizon()


func _build_world() -> void:
	var we := WorldEnvironment.new()
	var env := Environment.new()
	var sky := Sky.new()
	var sky_shader_mat := ShaderMaterial.new()
	sky_shader_mat.shader = load("res://assets/sky/SkyStar.gdshader")
	sky.sky_material = sky_shader_mat
	env.background_mode = Environment.BG_SKY
	env.sky = sky
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

	_land = MeshInstance3D.new()
	_land.name = "HorizonLand"
	var land_mesh := PlaneMesh.new()
	land_mesh.size = Vector2(2400.0, 2400.0)
	_land.mesh = land_mesh
	_land.material_override = _road_mat(Color(0.012, 0.018, 0.028), 0.92)
	_land.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_land)

	_player = HyperCar.new()
	_player.is_player = true
	_player.number = 1
	if start_mode == RaceSim.Mode.ENFORCEMENT:
		_player.model_path = "res://assets/cars/police.glb"
	else:
		_player.model_path = "res://assets/cars/player.glb"
	add_child(_player)
	if start_mode == RaceSim.Mode.ENFORCEMENT:
		_player.enable_lightbar()

	for i in sim.cars.size():
		var car := HyperCar.new()
		car.number = sim.cars[i].number
		if sim.cars[i].is_police:
			car.model_path = "res://assets/cars/police.glb"
		else:
			car.model_path = "res://assets/cars/ghost.glb"
		add_child(car)
		if sim.cars[i].is_police:
			car.enable_lightbar()
		_ai_nodes.append(car)
		_prev_ai_x.append(sim.cars[i].x)

	_skyline = MeshInstance3D.new()
	_skyline.name = "HorizonCity"
	var quad := QuadMesh.new()
	quad.size = Vector2(640, 36)
	_skyline.mesh = quad
	var city_mat := ShaderMaterial.new()
	city_mat.shader = load("res://shaders/skyline.gdshader")
	city_mat.set_shader_parameter("skyline_tex", load("res://assets/sprites/horizon_skyline.png"))
	city_mat.set_shader_parameter("brightness", 16.0)
	_skyline.material_override = city_mat
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
	_camera.fov = 66.0
	_camera.near = 0.15
	_camera.far = 520.0
	add_child(_camera)
	_camera.current = true
	_camera_offset = Vector3(0.0, 2.35, -9.2)
	_camera.position = _player.global_position + _camera_offset
	_skyline_heading = PI


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
	if not is_inside_tree():
		return
	if event.is_pressed() and event is InputEventKey:
		var k := event as InputEventKey
		if k.physical_keycode == KEY_ESCAPE:
			get_viewport().set_input_as_handled()
			_go_title()


func _go_title() -> void:
	if not is_inside_tree():
		return
	set_process(false)
	set_process_unhandled_input(false)
	get_tree().change_scene_to_file("res://scenes/boot.tscn")


func _process(delta: float) -> void:
	if not is_inside_tree():
		return
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
			_go_title()


func _wash_from_lightbars() -> void:
	var sources: Array[HyperCar] = []
	if _player.has_lightbar():
		sources.append(_player)
	for c in _ai_nodes:
		if c.has_lightbar():
			sources.append(c)
	if sources.is_empty():
		return
	var targets: Array[HyperCar] = [_player]
	for c in _ai_nodes:
		targets.append(c)
	for t in targets:
		var best := 0.0
		var col := Color.BLACK
		for s in sources:
			if t == s or not s.visible:
				continue
			var amt := clampf(1.0 - t.global_position.distance_to(s.global_position) / 14.0, 0.0, 1.0)
			amt *= amt
			if amt > best:
				best = amt
				col = s.lightbar_color
		t.set_proximity_wash(col, best)


func _sync_transforms(delta: float) -> void:
	var ppos := sim.world_pos(sim.distance, sim.player_x)
	_player.global_position = ppos
	var heading := -RaceSim.road_curve(sim.distance + 6.0) * 0.45
	var dt := maxf(delta, 0.0001)
	var player_slide := clampf((sim.player_x - _prev_player_x) / dt * 1.6, -1.0, 1.0)
	_prev_player_x = sim.player_x
	_player.pose(heading + (PI if sim.reversing else 0.0), player_slide, delta)

	for i in _ai_nodes.size():
		var r: RaceSim.Racer = sim.cars[i]
		if r.removed:
			_ai_nodes[i].visible = false
			continue
		var apos := sim.world_pos(r.z, r.x)
		_ai_nodes[i].global_position = apos
		var ai_heading := -RaceSim.road_curve(r.z + 6.0) * 0.45
		var ai_slide := clampf((r.x - _prev_ai_x[i]) / dt * 1.6, -1.0, 1.0)
		_prev_ai_x[i] = r.x
		_ai_nodes[i].pose(ai_heading, ai_slide, delta)
		_ai_nodes[i].visible = (r.z - sim.distance) > -8.0 and (r.z - sim.distance) < LOOK_AHEAD

	if start_mode == RaceSim.Mode.ENFORCEMENT or start_mode == RaceSim.Mode.CHASE:
		_wash_from_lightbars()

	var cam_offset := _camera_offset
	if sim.reversing:
		cam_offset = Vector3(0.0, 2.35, 9.2)
	var cam_pos := ppos + cam_offset
	cam_pos.y = ppos.y + cam_offset.y
	var look := ppos + Vector3(0.0, 0.9, -24.0 if sim.reversing else 24.0)
	_camera.global_position = cam_pos
	_camera.look_at(look, Vector3.UP)
	if _land:
		_land.global_position = Vector3(_camera.global_position.x, -12.0, _camera.global_position.z)


func _road_mat(color: Color, rough: float) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.metallic = 0.35
	m.roughness = rough
	return m


func _road_height(z: float) -> float:
	return sim.terrain_height(z)


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
		var y0 := _road_height(z)
		var y1 := _road_height(z2)
		var l0 := Vector3(c0 - ROAD_HALF, y0, z)
		var r0 := Vector3(c0 + ROAD_HALF, y0, z)
		var l1 := Vector3(c1 - ROAD_HALF, y1, z2)
		var r1 := Vector3(c1 + ROAD_HALF, y1, z2)
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
		var y0 := _road_height(z)
		var y1 := _road_height(z2)
		for side: float in [-1.0, 1.0]:
			var a := Vector3(c0 + side * ROAD_HALF, y0 - 0.02, z)
			var b := Vector3(c0 + side * (ROAD_HALF + 18.0), y0 - 0.02, z)
			var c := Vector3(c1 + side * (ROAD_HALF + 18.0), y1 - 0.02, z2)
			var d := Vector3(c1 + side * ROAD_HALF, y1 - 0.02, z2)
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
		var z2 := minf(z + 2.6, z1)
		var c0 := RaceSim.road_center(z)
		var c1 := RaceSim.road_center(z2)
		var y0 := _road_height(z)
		var y1 := _road_height(z2)
		var dash_on := int(floor(z / 4.0)) % 2 == 0
		for side: float in [-1.0, 1.0]:
			var outer0: float = c0 + side * (ROAD_HALF - 0.18)
			var outer1: float = c1 + side * (ROAD_HALF - 0.18)
			_quad(ms,
				Vector3(outer0 - 0.10, y0 + 0.03, z),
				Vector3(outer0 + 0.10, y0 + 0.03, z),
				Vector3(outer1 + 0.10, y1 + 0.03, z2),
				Vector3(outer1 - 0.10, y1 + 0.03, z2))
		var center0 := c0
		var center1 := c1
		_quad(ms,
			Vector3(center0 - 0.22, y0 + 0.03, z),
			Vector3(center0 - 0.08, y0 + 0.03, z),
			Vector3(center1 - 0.08, y1 + 0.03, z2),
			Vector3(center1 - 0.22, y1 + 0.03, z2))
		_quad(ms,
			Vector3(center0 + 0.08, y0 + 0.03, z),
			Vector3(center0 + 0.22, y0 + 0.03, z),
			Vector3(center1 + 0.22, y1 + 0.03, z2),
			Vector3(center1 + 0.08, y1 + 0.03, z2))
		if dash_on:
			for lane_sep: float in [-4.0, 4.0]:
				var d0: float = c0 + lane_sep * 1.5
				var d1: float = c1 + lane_sep * 1.5
				_quad(ms,
					Vector3(d0 - 0.08, y0 + 0.02, z),
					Vector3(d0 + 0.08, y0 + 0.02, z),
					Vector3(d1 + 0.08, y1 + 0.02, z2),
					Vector3(d1 - 0.08, y1 + 0.02, z2))
		z += 2.0
	var amber := _road_mat(Color(0.95, 0.72, 0.15), 0.45)
	amber.emission_enabled = true
	amber.emission = Color(1.0, 0.68, 0.14)
	amber.emission_energy_multiplier = 0.7
	var white := _road_mat(Color(0.95, 0.96, 0.97), 0.35)
	white.emission_enabled = true
	white.emission = Color(0.95, 0.97, 1.0)
	white.emission_energy_multiplier = 0.25
	var yellow := _road_mat(Color(0.96, 0.82, 0.18), 0.35)
	yellow.emission_enabled = true
	yellow.emission = Color(1.0, 0.80, 0.18)
	yellow.emission_energy_multiplier = 0.4
	var marking_mat := _road.get_node_or_null("MarkingMaterials") as Node3D
	if marking_mat == null:
		marking_mat = Node3D.new()
		marking_mat.name = "MarkingMaterials"
		_road.add_child(marking_mat)
	var amber_marks := _road.get_node_or_null("AmberCenter") as MeshInstance3D
	if amber_marks == null:
		amber_marks = MeshInstance3D.new()
		amber_marks.name = "AmberCenter"
		_road.add_child(amber_marks)
	var white_marks := _road.get_node_or_null("WhiteSeparators") as MeshInstance3D
	if white_marks == null:
		white_marks = MeshInstance3D.new()
		white_marks.name = "WhiteSeparators"
		_road.add_child(white_marks)
	var yellow_marks := _road.get_node_or_null("YellowShoulders") as MeshInstance3D
	if yellow_marks == null:
		yellow_marks = MeshInstance3D.new()
		yellow_marks.name = "YellowShoulders"
		_road.add_child(yellow_marks)
	var amber_st := SurfaceTool.new()
	var white_st := SurfaceTool.new()
	var yellow_st := SurfaceTool.new()
	amber_st.begin(Mesh.PRIMITIVE_TRIANGLES)
	white_st.begin(Mesh.PRIMITIVE_TRIANGLES)
	yellow_st.begin(Mesh.PRIMITIVE_TRIANGLES)
	z = z0
	while z < z1:
		var z2 := minf(z + 2.6, z1)
		var c0 := RaceSim.road_center(z)
		var c1 := RaceSim.road_center(z2)
		var y0 := _road_height(z) + 0.035
		var y1 := _road_height(z2) + 0.035
		for side: float in [-1.0, 1.0]:
			var edge0: float = c0 + side * (ROAD_HALF - 0.18)
			var edge1: float = c1 + side * (ROAD_HALF - 0.18)
			_quad(yellow_st, Vector3(edge0 - 0.10, y0, z), Vector3(edge0 + 0.10, y0, z), Vector3(edge1 + 0.10, y1, z2), Vector3(edge1 - 0.10, y1, z2))
		_quad(amber_st, Vector3(c0 - 0.22, y0, z), Vector3(c0 - 0.08, y0, z), Vector3(c1 - 0.08, y1, z2), Vector3(c1 - 0.22, y1, z2))
		_quad(amber_st, Vector3(c0 + 0.08, y0, z), Vector3(c0 + 0.22, y0, z), Vector3(c1 + 0.22, y1, z2), Vector3(c1 + 0.08, y1, z2))
		if int(floor(z / 4.0)) % 2 == 0:
			for lane_sep: float in [-4.0, 4.0]:
				var d0: float = c0 + lane_sep * 1.5
				var d1: float = c1 + lane_sep * 1.5
				_quad(white_st, Vector3(d0 - 0.08, y0, z), Vector3(d0 + 0.08, y0, z), Vector3(d1 + 0.08, y1, z2), Vector3(d1 - 0.08, y1, z2))
		z += 2.0
	var amber_mesh := amber_st.commit()
	var white_mesh := white_st.commit()
	var yellow_mesh := yellow_st.commit()
	amber_mesh.surface_set_material(0, amber)
	white_mesh.surface_set_material(0, white)
	yellow_mesh.surface_set_material(0, yellow)
	amber_marks.mesh = amber_mesh
	white_marks.mesh = white_mesh
	yellow_marks.mesh = yellow_mesh
	marks.visible = false

	var tunnel := _road.get_node_or_null("TunnelShell") as MeshInstance3D
	if tunnel == null:
		tunnel = MeshInstance3D.new()
		tunnel.name = "TunnelShell"
		_road.add_child(tunnel)
	var tunnel_st := SurfaceTool.new()
	tunnel_st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var tunnel_len := 1600.0
	var tunnel_center := sim.finish_distance * (1.0 / 3.0)
	var tunnel_start := tunnel_center - tunnel_len * 0.5
	var tunnel_end := tunnel_center + tunnel_len * 0.5
	var tunnel_z := tunnel_start
	while tunnel_z < tunnel_end:
		var tunnel_z2 := minf(tunnel_z + 16.0, tunnel_end)
		var ty0 := _road_height(tunnel_z)
		var ty1 := _road_height(tunnel_z2)
		for side: float in [-1.0, 1.0]:
			var wall_x := ROAD_HALF + 2.4
			var wall_a := Vector3(side * wall_x, ty0 - 4.0, tunnel_z)
			var wall_b := Vector3(side * wall_x, ty0 + 6.2, tunnel_z)
			var wall_c := Vector3(side * wall_x, ty1 + 6.2, tunnel_z2)
			var wall_d := Vector3(side * wall_x, ty1 - 4.0, tunnel_z2)
			_quad(tunnel_st, wall_a, wall_b, wall_c, wall_d)
		var roof_a := Vector3(-ROAD_HALF - 2.4, ty0 + 6.2, tunnel_z)
		var roof_b := Vector3(ROAD_HALF + 2.4, ty0 + 6.2, tunnel_z)
		var roof_c := Vector3(ROAD_HALF + 2.4, ty1 + 6.2, tunnel_z2)
		var roof_d := Vector3(-ROAD_HALF - 2.4, ty1 + 6.2, tunnel_z2)
		_quad(tunnel_st, roof_a, roof_b, roof_c, roof_d)
		tunnel_z += 16.0
	var tunnel_mesh := tunnel_st.commit()
	var tunnel_mat := _road_mat(Color(0.34, 0.37, 0.41), 0.84)
	tunnel_mat.albedo_color = Color(0.34, 0.37, 0.41)
	tunnel_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	tunnel_mesh.surface_set_material(0, tunnel_mat)
	tunnel.mesh = tunnel_mesh
	var tunnel_lights := _road.get_node_or_null("TunnelLights") as Node3D
	if tunnel_lights == null:
		tunnel_lights = Node3D.new()
		tunnel_lights.name = "TunnelLights"
		_road.add_child(tunnel_lights)
		var light_z := tunnel_start + 40.0
		while light_z < tunnel_end - 20.0:
			var fixture := MeshInstance3D.new()
			var fixture_mesh := BoxMesh.new()
			fixture_mesh.size = Vector3(1.2, 0.10, 0.35)
			fixture.mesh = fixture_mesh
			fixture.position = Vector3(0.0, _road_height(light_z) + 5.85, light_z)
			var fixture_mat := StandardMaterial3D.new()
			fixture_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			fixture_mat.albedo_color = Color(0.8, 0.9, 1.0)
			fixture_mat.emission_enabled = true
			fixture_mat.emission = Color(0.65, 0.82, 1.0)
			fixture_mat.emission_energy_multiplier = 3.0
			fixture.material_override = fixture_mat
			tunnel_lights.add_child(fixture)
			var cone := SpotLight3D.new()
			cone.position = Vector3(0.0, _road_height(light_z) + 5.65, light_z)
			cone.rotation_degrees = Vector3(90.0, 0.0, 0.0)
			cone.light_color = Color(0.65, 0.8, 1.0)
			cone.light_energy = 3.2
			cone.spot_range = 14.0
			cone.spot_angle = 95.0
			cone.spot_angle_attenuation = 0.65
			cone.shadow_enabled = false
			tunnel_lights.add_child(cone)
			light_z += 80.0

	var bridge := _road.get_node_or_null("BridgeShell") as MeshInstance3D
	if bridge == null:
		bridge = MeshInstance3D.new()
		bridge.name = "BridgeShell"
		_road.add_child(bridge)
	var bridge_st := SurfaceTool.new()
	bridge_st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var bridge_len := 1600.0
	var bridge_center := sim.finish_distance * (2.0 / 3.0)
	var bridge_start := bridge_center - bridge_len * 0.5
	var bridge_end := bridge_center + bridge_len * 0.5
	var bridge_z := bridge_start
	while bridge_z < bridge_end:
		var bridge_z2 := minf(bridge_z + 20.0, bridge_end)
		var by0 := _road_height(bridge_z)
		var by1 := _road_height(bridge_z2)
		var deck_a := Vector3(-ROAD_HALF, by0 - 0.34, bridge_z)
		var deck_b := Vector3(ROAD_HALF, by0 - 0.34, bridge_z)
		var deck_c := Vector3(ROAD_HALF, by1 - 0.34, bridge_z2)
		var deck_d := Vector3(-ROAD_HALF, by1 - 0.34, bridge_z2)
		_quad(bridge_st, deck_a, deck_b, deck_c, deck_d)
		for side: float in [-1.0, 1.0]:
			var rail_x := side * (ROAD_HALF + 0.28)
			var rail_a := Vector3(rail_x, by0 + 0.82, bridge_z)
			var rail_b := Vector3(rail_x, by0 + 1.28, bridge_z)
			var rail_c := Vector3(rail_x, by1 + 1.28, bridge_z2)
			var rail_d := Vector3(rail_x, by1 + 0.82, bridge_z2)
			_quad(bridge_st, rail_a, rail_b, rail_c, rail_d)
			var girder_x := side * (ROAD_HALF + 2.8)
			var girder_a := Vector3(girder_x, by0 - 6.0, bridge_z)
			var girder_b := Vector3(girder_x, by0 - 2.4, bridge_z)
			var girder_c := Vector3(girder_x, by1 - 2.4, bridge_z2)
			var girder_d := Vector3(girder_x, by1 - 6.0, bridge_z2)
			_quad(bridge_st, girder_a, girder_b, girder_c, girder_d)
		bridge_z += 20.0
	var bridge_mesh := bridge_st.commit()
	var bridge_mat := _road_mat(Color(0.38, 0.41, 0.45), 0.78)
	bridge_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	bridge_mesh.surface_set_material(0, bridge_mat)
	bridge.mesh = bridge_mesh

	var bridge_supports := _road.get_node_or_null("BridgeSupports") as MeshInstance3D
	if bridge_supports == null:
		bridge_supports = MeshInstance3D.new()
		bridge_supports.name = "BridgeSupports"
		_road.add_child(bridge_supports)
	var support_st := SurfaceTool.new()
	support_st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var support_z := bridge_start
	while support_z <= bridge_end:
		for side: float in [-1.0, 1.0]:
			var sx := side * (ROAD_HALF + 3.8)
			var support_a := Vector3(sx, _road_height(support_z) - 7.2, support_z)
			var support_b := Vector3(sx, _road_height(support_z) + 1.1, support_z)
			var support_c := Vector3(sx, _road_height(support_z) + 1.1, support_z + 18.0)
			var support_d := Vector3(sx, _road_height(support_z) - 7.2, support_z + 18.0)
			_quad(support_st, support_a, support_b, support_c, support_d)
		support_z += 80.0
	var support_mesh := support_st.commit()
	var support_mat := _road_mat(Color(0.42, 0.44, 0.47), 0.82)
	support_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	support_mesh.surface_set_material(0, support_mat)
	bridge_supports.mesh = support_mesh


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
	var smoothed := t * t * (3.0 - 2.0 * t)
	# Stay a thin far band early; rush in over the last third.
	var approach := pow(smoothed, 1.15)
	var dist_ahead := lerpf(310.0, 38.0, approach)
	var city_h := lerpf(34.0, 128.0, approach)
	var city_w := lerpf(620.0, 240.0, approach)

	(_skyline.mesh as QuadMesh).size = Vector2(city_w, city_h)

	var z := sim.distance + dist_ahead
	var x := RaceSim.road_center(z)
	# Quad faces +Z; rotate so the city faces the incoming camera.
	var face := _skyline_heading
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
		var tunnel_start := int(sim.finish_distance / 3.0) - 800
		var tunnel_end := int(sim.finish_distance / 3.0) + 800
		var in_tunnel := z >= tunnel_start and z <= tunnel_end
		if z % 32 == 0 and not in_tunnel:
			want["l%d" % z] = [z, 2.05, true]
		if z % 32 == 16 and not in_tunnel:
			want["r%d" % z] = [z, -2.05, true]
		if z >= SIGN_SPACING and z % SIGN_SPACING == 0 and not in_tunnel:
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
	var idx := int(z / float(SIGN_SPACING)) % SIGN_PLACES.size()
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
	var kmh := int(sim.speed * RaceSim.KMH_SCALE)
	_hud_speed.text = "%d KM/H" % kmh
	match sim.mode:
		RaceSim.Mode.ENFORCEMENT:
			_hud_place.text = "%d LEFT" % sim.rivals_left()
		RaceSim.Mode.CHASE:
			_hud_place.text = "CHASE" if sim.police_spawned else "CLEAR"
		_:
			_hud_place.text = "P%d / %d" % [sim.race_place(), sim.field_size()]
	var left := maxf(0.0, sim.finish_distance - sim.distance)
	_hud_dist.text = "%d m" % int(left)
	if sim.countdown_text != "":
		_hud_count.text = sim.countdown_text
		_hud_count.modulate = Color(0.2, 1.0, 0.4) if sim.lights_stage == 4 else Color(1.0, 0.25, 0.2)
	elif sim.busted:
		_hud_count.text = "BUSTED"
		_hud_count.modulate = Color(1.0, 0.2, 0.15)
	elif sim.cleared:
		_hud_count.text = "CLEARED"
		_hud_count.modulate = Color(0.3, 0.9, 1.0)
	elif sim.finished:
		_hud_count.text = "FINISH"
		_hud_count.modulate = Color(1.0, 0.85, 0.2)
	elif sim.mode == RaceSim.Mode.ENFORCEMENT and sim.crashed:
		_hud_count.text = "BUSTED"
		_hud_count.modulate = Color(0.4, 0.75, 1.0)
	elif sim.crashed:
		_hud_count.text = "CONTACT"
		_hud_count.modulate = Color(1.0, 0.4, 0.15)
	else:
		_hud_count.text = ""


func _highway_font() -> Font:
	var sys := SystemFont.new()
	sys.font_names = PackedStringArray(["Yu Gothic", "Yu Gothic UI", "Meiryo", "MS Gothic", "Noto Sans CJK JP"])
	return sys
