extends Control

const RaceScene := preload("res://scenes/race.tscn")

var _diff: RaceSim.Difficulty = RaceSim.Difficulty.MEDIUM
var _starting := false

@onready var _bg: TextureRect = $Background
@onready var _video: VideoStreamPlayer = $IntroVideo
@onready var _title_border: Label = $TitleBorder
@onready var _title: Label = $Title
@onready var _byline: Label = $Byline
@onready var _dim: ColorRect = $Dim
@onready var _panel: HBoxContainer = $Panel
@onready var _easy: Button = $Panel/Easy
@onready var _med: Button = $Panel/Medium
@onready var _hard: Button = $Panel/Hard
@onready var _start: Button = $Panel/Start
@onready var _hint: Label = $Hint
@onready var _flash: ColorRect = $Flash
@onready var _rain: ColorRect = $LensRain


func _ready() -> void:
	_bg.texture = load("res://assets/splash_still.jpg")
	var stream := load("res://assets/splash_intro.ogv")
	if stream:
		_video.stream = stream
	_video.volume_db = -80.0
	_video.expand = true
	_video.finished.connect(_on_video_finished)
	_easy.pressed.connect(func() -> void: _diff = RaceSim.Difficulty.EASY; _refresh())
	_med.pressed.connect(func() -> void: _diff = RaceSim.Difficulty.MEDIUM; _refresh())
	_hard.pressed.connect(func() -> void: _diff = RaceSim.Difficulty.HARD; _refresh())
	_start.pressed.connect(_begin)
	_refresh()
	_start.grab_focus()
	call_deferred("_hold_first_frame")


func _hold_first_frame() -> void:
	if _video.stream == null:
		return
	_video.visible = true
	_video.play()
	await get_tree().process_frame
	await get_tree().process_frame
	_video.paused = true
	_video.stream_position = 0.0
	_bg.visible = false


func _refresh() -> void:
	if _starting:
		return
	_easy.modulate = Color(1, 1, 1, 0.55 if _diff != RaceSim.Difficulty.EASY else 1.0)
	_med.modulate = Color(1, 1, 1, 0.55 if _diff != RaceSim.Difficulty.MEDIUM else 1.0)
	_hard.modulate = Color(1, 1, 1, 0.55 if _diff != RaceSim.Difficulty.HARD else 1.0)


func _unhandled_input(event: InputEvent) -> void:
	if _starting:
		return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.physical_keycode == KEY_ENTER or event.physical_keycode == KEY_KP_ENTER:
			_begin()


func _begin() -> void:
	if _starting:
		return
	_starting = true
	_easy.disabled = true
	_med.disabled = true
	_hard.disabled = true
	_start.disabled = true

	var rain_mat := _rain.material as ShaderMaterial
	if rain_mat:
		rain_mat.set_shader_parameter("drip_dir", -1.0)

	if _video.stream:
		_video.visible = true
		_video.paused = false
		if not _video.is_playing():
			_video.play()
	else:
		_go_race()


func _on_video_finished() -> void:
	_flash.color = Color(1, 1, 1, 0)
	_flash.visible = true
	var tw := create_tween()
	tw.tween_property(_flash, "color:a", 1.0, 0.12)
	tw.tween_interval(0.08)
	tw.tween_callback(_go_race)


func _go_race() -> void:
	RaceWorld.start_difficulty = _diff
	get_tree().change_scene_to_packed(RaceScene)
