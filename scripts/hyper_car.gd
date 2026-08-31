class_name HyperCar
extends Node3D

## Splash-matched hypercar. Rear sheet only until real Blender meshes exist.
## car_front.png and car_three_quarter.png stay on disk as placeholders.

@export var cyan := Color(0.3, 0.9, 1.0)
@export var orange := Color(1.0, 0.42, 0.08)
@export var body := Color(0.03, 0.035, 0.045)
@export var is_player := false
@export var number: int = 1

var _sprite: Sprite3D


func _ready() -> void:
	_sprite = Sprite3D.new()
	_sprite.texture = load("res://assets/sprites/car_rear.png")
	_sprite.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
	_sprite.pixel_size = 0.0027
	_sprite.centered = true
	_sprite.alpha_cut = SpriteBase3D.ALPHA_CUT_DISCARD
	_sprite.alpha_scissor_threshold = 0.08
	_sprite.shaded = false
	_sprite.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR
	_sprite.position = Vector3(0.0, 0.85, 0.0)
	add_child(_sprite)

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
