class_name HyperCar
extends Node3D

## Stylized neon hypercar matching PsyRacerSplash.jpg (black body, cyan/orange glow).
## Primitive boxes/cylinders until Blender meshes exist.

const SLIDE_YAW := 0.55
const SLIDE_ROLL := 0.14

@export var cyan := Color(0.3, 0.9, 1.0)
@export var orange := Color(1.0, 0.42, 0.08)
@export var body := Color(0.03, 0.035, 0.045)
@export var is_player := false
@export var number: int = 1

var _slide := 0.0


func _ready() -> void:
	_build()


func pose(heading: float, slide: float, delta: float) -> void:
	_slide = lerpf(_slide, clampf(slide, -1.0, 1.0), 1.0 - exp(-delta * 12.0))
	rotation = Vector3(0.0, heading + _slide * SLIDE_YAW, -_slide * SLIDE_ROLL)


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


func _build() -> void:
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

	if is_player:
		_add_headlights()


func _add_headlights() -> void:
	var light_l := SpotLight3D.new()
	light_l.position = Vector3(-0.5, 0.5, 2.2)
	light_l.rotation_degrees = Vector3(-8, 0, 0)
	light_l.light_color = cyan
	light_l.light_energy = 6.0
	light_l.spot_range = 55.0
	light_l.spot_angle = 28.0
	light_l.shadow_enabled = false
	light_l.light_volumetric_fog_energy = 0.0
	add_child(light_l)
	var light_r := light_l.duplicate() as SpotLight3D
	light_r.position.x = 0.5
	add_child(light_r)
