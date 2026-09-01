class_name HyperCar
extends Node3D

## GLB car wrapper. pose() yaws/leans on this root; chase cam stays on road heading.
## Models in assets/cars/ are auto-fitted to TARGET_LENGTH, grounded, +Z forward.

const TARGET_LENGTH := 4.2
const SLIDE_YAW := 0.55
const SLIDE_ROLL := 0.14
const LIGHTBAR_SCALE := 0.7
const BAR_ON := 18.0 * LIGHTBAR_SCALE
const BAR_OFF := 0.2 * LIGHTBAR_SCALE
const OMNI_ON := 14.0 * LIGHTBAR_SCALE
const WASH_GAIN := 4.2 * LIGHTBAR_SCALE

@export var cyan := Color(0.3, 0.9, 1.0)
@export var orange := Color(1.0, 0.42, 0.08)
@export var body := Color(0.03, 0.035, 0.045)
@export var is_player := false
@export var number: int = 1
@export var model_path: String = ""

var _slide := 0.0
var _model: Node3D
var _lightbar_on := false
var _red_mats: Array[StandardMaterial3D] = []
var _blue_mats: Array[StandardMaterial3D] = []
var _omni_red: OmniLight3D
var _omni_blue: OmniLight3D
var _wash_mats: Array[StandardMaterial3D] = []
var _wash_ready := false
var lightbar_color := Color(1.0, 0.12, 0.08)


func _ready() -> void:
	set_process(false)
	_build()


func pose(heading: float, slide: float, delta: float) -> void:
	_slide = lerpf(_slide, clampf(slide, -1.0, 1.0), 1.0 - exp(-delta * 12.0))
	rotation = Vector3(0.0, heading + _slide * SLIDE_YAW, -_slide * SLIDE_ROLL)


func _process(_delta: float) -> void:
	if _lightbar_on:
		_update_lightbar()


func enable_lightbar() -> void:
	if _lightbar_on:
		return
	_lightbar_on = true
	_collect_lightbar_mats()
	_spawn_lightbar_omnis()
	set_process(true)


func has_lightbar() -> bool:
	return _lightbar_on


func _build() -> void:
	if model_path != "":
		var packed := load(model_path) as PackedScene
		if packed != null:
			_build_model(packed)
			if is_player:
				_add_headlights()
			return
	_build_primitive()
	if is_player:
		_add_headlights()


func _build_model(packed: PackedScene) -> void:
	var model_root := Node3D.new()
	model_root.name = "Model"
	var inst := packed.instantiate() as Node
	_strip_extras(inst)
	model_root.add_child(inst)
	add_child(model_root)
	_fit(model_root)
	_model = model_root


func _is_import_junk(n: Node) -> bool:
	if n is Light3D or n is Camera3D:
		return true
	var key := n.name.to_lower()
	if key == "camera" or key == "light":
		return true
	# Blender ground cards, not Car_Plane meshes.
	if key == "plane" or key.begins_with("plane_") or key.begins_with("plane."):
		return true
	return false


func _strip_extras(n: Node) -> void:
	var kill: Array[Node] = []
	for c in n.get_children():
		_strip_extras(c)
		if _is_import_junk(c):
			kill.append(c)
	for c in kill:
		c.free()
	if n is MeshInstance3D:
		(n as MeshInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


func _collect_meshes(n: Node) -> Array[MeshInstance3D]:
	var out: Array[MeshInstance3D] = []
	if n is MeshInstance3D:
		out.append(n as MeshInstance3D)
	for c in n.get_children():
		out.append_array(_collect_meshes(c))
	return out


func _aabb_local(from: Node) -> AABB:
	var started := false
	var result := AABB()
	var inv := global_transform.affine_inverse()
	for mi: MeshInstance3D in _collect_meshes(from):
		if mi.mesh == null:
			continue
		var la := mi.get_aabb()
		for i in 8:
			var lp: Vector3 = inv * (mi.global_transform * la.get_endpoint(i))
			if not started:
				result = AABB(lp, Vector3.ZERO)
				started = true
			else:
				result = result.expand(lp)
	return result


func _recenter(model_root: Node3D) -> AABB:
	var aabb := _aabb_local(model_root)
	if aabb.size == Vector3.ZERO:
		return aabb
	var c := aabb.get_center()
	model_root.position += Vector3(-c.x, -aabb.position.y, -c.z)
	return _aabb_local(model_root)


func _fit(model_root: Node3D) -> void:
	var aabb := _recenter(model_root)
	if aabb.size == Vector3.ZERO:
		return
	if aabb.size.x > aabb.size.z + 0.05:
		model_root.rotate_y(PI * 0.5)
		aabb = _recenter(model_root)
	aabb = _face_plus_z(model_root, aabb)
	var length: float = aabb.size.z
	if length > 0.001:
		var s: float = TARGET_LENGTH / length
		model_root.scale *= s
		aabb = _recenter(model_root)


func _face_plus_z(model_root: Node3D, aabb: AABB) -> AABB:
	var front_sum := 0.0
	var rear_sum := 0.0
	var front_n := 0
	var rear_n := 0
	var inv := global_transform.affine_inverse()
	for mi: MeshInstance3D in _collect_meshes(model_root):
		var key := mi.name.to_lower()
		var parent_key := mi.get_parent().name.to_lower() if mi.get_parent() else ""
		var blob := "%s %s" % [key, parent_key]
		var la := mi.get_aabb()
		var c: Vector3 = inv * (mi.global_transform * la.get_center())
		if _name_is_front(blob):
			front_sum += c.z
			front_n += 1
		elif _name_is_rear(blob):
			rear_sum += c.z
			rear_n += 1
	if front_n > 0 and rear_n > 0:
		if (front_sum / float(front_n)) < (rear_sum / float(rear_n)):
			model_root.rotate_y(PI)
			return _recenter(model_root)
	return aabb


func _name_is_front(blob: String) -> bool:
	return (
		blob.contains("front")
		or blob.contains("_fl")
		or blob.contains("_fr")
		or blob.contains("wheel_f")
	)


func _name_is_rear(blob: String) -> bool:
	return (
		blob.contains("rear")
		or blob.contains("back")
		or blob.contains("_rl")
		or blob.contains("_rr")
		or blob.contains("wheel_r")
	)


func _mat(color: Color, emission: Color = Color.BLACK, energy: float = 0.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.metallic = 0.85
	m.roughness = 0.28
	if energy > 0.0:
		m.emission_enabled = true
		m.emission = emission
		m.emission_energy_multiplier = energy
	return m


func _box(size: Vector3, pos: Vector3, mat: Material, rot := Vector3.ZERO) -> void:
	var mi := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = size
	mi.mesh = mesh
	mi.position = pos
	mi.rotation_degrees = rot
	mi.material_override = mat
	add_child(mi)


func _cyl(radius: float, height: float, pos: Vector3, mat: Material, rot := Vector3(0, 0, 90)) -> void:
	var mi := MeshInstance3D.new()
	var mesh := CylinderMesh.new()
	mesh.top_radius = radius
	mesh.bottom_radius = radius
	mesh.height = height
	mesh.radial_segments = 12
	mi.mesh = mesh
	mi.position = pos
	mi.rotation_degrees = rot
	mi.material_override = mat
	add_child(mi)


func _build_primitive() -> void:
	var body_mat := _mat(body)
	var cyan_mat := _mat(cyan, cyan, 4.2)
	var orange_mat := _mat(orange, orange, 3.4)
	var glass := _mat(Color(0.02, 0.04, 0.08, 0.85), cyan * 0.3, 0.6)
	glass.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA

	_box(Vector3(1.85, 0.42, 4.1), Vector3(0, 0.38, 0), body_mat)
	_box(Vector3(1.55, 0.28, 2.2), Vector3(0, 0.68, -0.15), body_mat)
	_box(Vector3(1.05, 0.38, 1.15), Vector3(0, 0.95, 0.15), glass)
	_box(Vector3(1.15, 0.28, 1.35), Vector3(0, 0.34, 1.55), body_mat)
	_box(Vector3(1.95, 0.06, 0.42), Vector3(0, 1.12, -1.85), body_mat)
	_box(Vector3(0.08, 0.55, 0.18), Vector3(-0.72, 0.82, -1.78), body_mat)
	_box(Vector3(0.08, 0.55, 0.18), Vector3(0.72, 0.82, -1.78), body_mat)
	_box(Vector3(0.12, 0.22, 3.4), Vector3(-0.98, 0.28, 0.05), body_mat)
	_box(Vector3(0.12, 0.22, 3.4), Vector3(0.98, 0.28, 0.05), body_mat)

	_box(Vector3(0.06, 0.05, 3.6), Vector3(-0.55, 0.62, 0.1), cyan_mat)
	_box(Vector3(0.06, 0.05, 3.6), Vector3(0.55, 0.62, 0.1), cyan_mat)
	_box(Vector3(0.05, 0.04, 2.8), Vector3(-0.72, 0.48, 0.2), orange_mat)
	_box(Vector3(0.05, 0.04, 2.8), Vector3(0.72, 0.48, 0.2), orange_mat)
	_box(Vector3(1.4, 0.04, 0.05), Vector3(0, 0.62, 1.9), cyan_mat)

	_box(Vector3(0.42, 0.08, 0.12), Vector3(-0.52, 0.42, 2.18), cyan_mat)
	_box(Vector3(0.42, 0.08, 0.12), Vector3(0.52, 0.42, 2.18), cyan_mat)
	_box(Vector3(0.55, 0.08, 0.08), Vector3(-0.5, 0.52, -2.08), orange_mat)
	_box(Vector3(0.55, 0.08, 0.08), Vector3(0.5, 0.52, -2.08), orange_mat)

	var rubber := _mat(Color(0.04, 0.04, 0.045))
	var rim := _mat(Color(0.12, 0.12, 0.14), orange, 0.8)
	for xz: Vector2 in [Vector2(-0.82, 1.25), Vector2(0.82, 1.25), Vector2(-0.82, -1.35), Vector2(0.82, -1.35)]:
		_cyl(0.38, 0.28, Vector3(xz.x, 0.38, xz.y), rubber)
		_cyl(0.22, 0.3, Vector3(xz.x, 0.38, xz.y), rim)


func _add_headlights() -> void:
	var nose_z := 2.2
	var hx := 0.5
	var hy := 0.5
	if _model != null:
		var aabb := _aabb_local(_model)
		if aabb.size != Vector3.ZERO:
			nose_z = aabb.position.z + aabb.size.z - 0.05
			hx = aabb.size.x * 0.22
			hy = clampf(aabb.size.y * 0.38, 0.35, 0.7)
	var light_l := SpotLight3D.new()
	light_l.position = Vector3(-hx, hy, nose_z)
	light_l.rotation_degrees = Vector3(-8, 0, 0)
	light_l.light_color = cyan
	light_l.light_energy = 6.0
	light_l.spot_range = 55.0
	light_l.spot_angle = 28.0
	light_l.shadow_enabled = false
	light_l.light_volumetric_fog_energy = 0.0
	add_child(light_l)
	var light_r := light_l.duplicate() as SpotLight3D
	light_r.position.x = hx
	add_child(light_r)


func _mat_name(src: Material) -> String:
	if src == null:
		return ""
	var n := src.resource_name.to_lower()
	if n == "" and src.get("name") != null:
		n = str(src.get("name")).to_lower()
	return n.replace(" ", "")


func _collect_lightbar_mats() -> void:
	if _model == null:
		return
	for mi: MeshInstance3D in _collect_meshes(_model):
		if mi.mesh == null:
			continue
		for i in mi.mesh.get_surface_count():
			var src := mi.get_active_material(i)
			var key := _mat_name(src)
			var albedo := Color.BLACK
			if src is BaseMaterial3D:
				albedo = (src as BaseMaterial3D).albedo_color
			var is_blue := key.contains("blue") or (albedo.b > 0.45 and albedo.b > albedo.r + 0.2)
			var is_white_bar := key.contains("whitelight")
			if not is_blue and not is_white_bar:
				continue
			var m := StandardMaterial3D.new()
			m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			m.emission_enabled = true
			if is_blue:
				m.albedo_color = Color(0.08, 0.2, 1.0)
				m.emission = Color(0.2, 0.45, 1.0)
				_blue_mats.append(m)
			else:
				m.albedo_color = Color(1.0, 0.08, 0.05)
				m.emission = Color(1.0, 0.12, 0.06)
				_red_mats.append(m)
			mi.set_surface_override_material(i, m)


func _spawn_lightbar_omnis() -> void:
	var bar_y := 1.35
	var bar_z := -0.35
	if _model != null:
		var aabb := _aabb_local(_model)
		if aabb.size != Vector3.ZERO:
			bar_y = aabb.position.y + aabb.size.y * 0.95
			bar_z = aabb.get_center().z - aabb.size.z * 0.06
	_omni_red = _make_bar_omni(Color(1.0, 0.1, 0.06), Vector3(0.22, bar_y, bar_z))
	_omni_blue = _make_bar_omni(Color(0.15, 0.35, 1.0), Vector3(-0.22, bar_y, bar_z))


func _make_bar_omni(color: Color, pos: Vector3) -> OmniLight3D:
	var o := OmniLight3D.new()
	o.position = pos
	o.light_color = color
	o.light_energy = 0.0
	o.light_specular = 1.2
	o.light_size = 0.45
	o.omni_range = 16.0
	o.omni_attenuation = 1.35
	o.shadow_enabled = false
	o.light_volumetric_fog_energy = 1.4 * LIGHTBAR_SCALE
	add_child(o)
	return o


func _update_lightbar() -> void:
	var beat := int(Time.get_ticks_msec() / 100.0) % 4
	var red_on := beat < 2
	var blue_on := not red_on
	_set_bar_energy(_red_mats, BAR_ON if red_on else BAR_OFF)
	_set_bar_energy(_blue_mats, BAR_ON if blue_on else BAR_OFF)
	if _omni_red:
		_omni_red.light_energy = OMNI_ON if red_on else 0.0
	if _omni_blue:
		_omni_blue.light_energy = OMNI_ON if blue_on else 0.0
	lightbar_color = Color(1.0, 0.12, 0.08) if red_on else Color(0.18, 0.4, 1.0)


func _set_bar_energy(mats: Array[StandardMaterial3D], energy: float) -> void:
	for m in mats:
		m.emission_energy_multiplier = energy


func set_proximity_wash(color: Color, amount: float) -> void:
	if not _wash_ready:
		_prep_wash()
	var e: float = amount * WASH_GAIN
	for m in _wash_mats:
		m.emission_enabled = e > 0.04
		m.emission = color
		m.emission_energy_multiplier = e


func _prep_wash() -> void:
	_wash_ready = true
	if _model == null:
		return
	for mi: MeshInstance3D in _collect_meshes(_model):
		if mi.mesh == null:
			continue
		for i in mi.mesh.get_surface_count():
			var src := mi.get_active_material(i)
			var key := _mat_name(src)
			if key.contains("tire") or key.contains("rubber"):
				continue
			var m: StandardMaterial3D
			if src is StandardMaterial3D:
				m = (src as StandardMaterial3D).duplicate() as StandardMaterial3D
			else:
				m = StandardMaterial3D.new()
				if src is BaseMaterial3D:
					m.albedo_color = (src as BaseMaterial3D).albedo_color
			m.metallic = maxf(m.metallic, 0.55)
			m.roughness = minf(m.roughness, 0.32)
			mi.set_surface_override_material(i, m)
			_wash_mats.append(m)
