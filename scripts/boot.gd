extends Control

const RaceScene := preload("res://scenes/race.tscn")

var _mode: RaceSim.Mode = RaceSim.Mode.STANDARD
var _starting := false

@onready var _bg: TextureRect = $Background
@onready var _video: VideoStreamPlayer = $IntroVideo
@onready var _standard: Button = $Panel/Standard
@onready var _chase: Button = $Panel/Chase
@onready var _enforce: Button = $Panel/Enforcement
@onready var _start: Button = $Panel/Start
@onready var _mode_button: Button = $Panel/Mode
@onready var _options: Button = $Panel/Options
@onready var _hint: Label = $Hint
@onready var _flash: ColorRect = $Flash
@onready var _rain: ColorRect = $LensRain
var _options_overlay: Panel
var _options_stack: VBoxContainer
var _options_title: Label
var _options_page := 0
var _mode_overlay: Panel
var _mode_details_open := false
var _video_mode := 2
var _sound_on := true
var _music_on := true
var _fx_on := true
var _music_volume := 0.8
var _fx_volume := 0.8


func _ready() -> void:
	_bg.texture = load("res://assets/splash_still.jpg")
	var stream := load("res://assets/splash_intro.ogv")
	if stream:
		_video.stream = stream
	_video.volume_db = -80.0
	_video.expand = true
	_video.finished.connect(_on_video_finished)
	_standard.pressed.connect(func() -> void: _mode = RaceSim.Mode.STANDARD; _refresh())
	_chase.pressed.connect(func() -> void: _mode = RaceSim.Mode.CHASE; _refresh())
	_enforce.pressed.connect(func() -> void: _mode = RaceSim.Mode.ENFORCEMENT; _refresh())
	_start.pressed.connect(_begin)
	_mode_button.pressed.connect(_open_mode_menu)
	_options.pressed.connect(_open_options)
	_refresh()
	_mode_button.grab_focus()
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
	_standard.modulate = Color(1, 1, 1, 0.55 if _mode != RaceSim.Mode.STANDARD else 1.0)
	_chase.modulate = Color(1, 1, 1, 0.55 if _mode != RaceSim.Mode.CHASE else 1.0)
	_enforce.modulate = Color(1, 1, 1, 0.55 if _mode != RaceSim.Mode.ENFORCEMENT else 1.0)
	match _mode:
		RaceSim.Mode.CHASE:
			_hint.text = "Outrun the cop after 3 km    stay above 50 km/h"
		RaceSim.Mode.ENFORCEMENT:
			_hint.text = "Ram all 6    you don't slow on impact"
		_:
			_hint.text = "20 km race    5 rivals    ENTER to start"


func _unhandled_input(event: InputEvent) -> void:
	if _starting:
		return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.physical_keycode == KEY_ESCAPE and _mode_overlay != null:
			_close_mode_menu()
			get_viewport().set_input_as_handled()
			return
		if event.physical_keycode == KEY_ESCAPE and _options_overlay != null:
			if _options_page == 0:
				_close_options()
			else:
				_show_options_page(0)
			get_viewport().set_input_as_handled()
			return
		if (event.physical_keycode == KEY_ENTER or event.physical_keycode == KEY_KP_ENTER) and _mode_details_open:
			_begin()


func _open_mode_menu() -> void:
	if _mode_overlay != null:
		return
	_mode_overlay = Panel.new()
	_mode_overlay.name = "ModeOverlay"
	_mode_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	_mode_overlay.offset_left = 240.0
	_mode_overlay.offset_top = 120.0
	_mode_overlay.offset_right = -240.0
	_mode_overlay.offset_bottom = -120.0
	_mode_overlay.modulate = Color(0.82, 0.9, 1.0, 0.96)
	_mode_overlay.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(_mode_overlay)
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT, Control.PRESET_MODE_MINSIZE, 30)
	_mode_overlay.add_child(margin)
	var stack := VBoxContainer.new()
	stack.name = "ModeMenu"
	stack.add_theme_constant_override("separation", 14)
	margin.add_child(stack)
	var title := Label.new()
	title.text = "SELECT RACE MODE"
	title.add_theme_font_size_override("font_size", 34)
	stack.add_child(title)
	stack.add_child(_button("STANDARD", func() -> void: _show_mode_details(RaceSim.Mode.STANDARD)))
	stack.add_child(_button("CHASE", func() -> void: _show_mode_details(RaceSim.Mode.CHASE)))
	stack.add_child(_button("ENFORCEMENT", func() -> void: _show_mode_details(RaceSim.Mode.ENFORCEMENT)))
	stack.add_child(_button("BACK", _close_mode_menu))


func _show_mode_details(mode: RaceSim.Mode) -> void:
	_mode_details_open = true
	for child in _mode_overlay.get_children():
		child.queue_free()
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT, Control.PRESET_MODE_MINSIZE, 30)
	_mode_overlay.add_child(margin)
	var stack := VBoxContainer.new()
	stack.add_theme_constant_override("separation", 14)
	margin.add_child(stack)
	var title := Label.new()
	title.add_theme_font_size_override("font_size", 34)
	title.text = _mode_title(mode)
	stack.add_child(title)
	var image_placeholder := ColorRect.new()
	image_placeholder.custom_minimum_size = Vector2(0, 260)
	image_placeholder.color = Color(0.04, 0.08, 0.14, 0.85)
	image_placeholder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var image_label := Label.new()
	image_label.text = "IMAGE PLACEHOLDER"
	image_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	image_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	image_placeholder.add_child(image_label)
	stack.add_child(image_placeholder)
	var description := Label.new()
	description.text = _mode_description(mode)
	description.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	description.custom_minimum_size = Vector2(0, 92)
	description.add_theme_font_size_override("font_size", 20)
	stack.add_child(description)
	stack.add_child(_button("START RACE", func() -> void:
		_mode = mode
		_close_mode_menu()
		_begin()
	))
	stack.add_child(_button("BACK", func() -> void:
		_close_mode_menu()
		call_deferred("_open_mode_menu")
	))


func _mode_title(mode: RaceSim.Mode) -> String:
	match mode:
		RaceSim.Mode.CHASE:
			return "Police Chase"
		RaceSim.Mode.ENFORCEMENT:
			return "Law Enforcement"
		_:
			return "Standard Race"


func _mode_description(mode: RaceSim.Mode) -> String:
	match mode:
		RaceSim.Mode.CHASE:
			return "Outrun the pursuing police car after it merges onto the highway. Maintain at least 50 km/h to avoid being busted, while reaching the finish line."
		RaceSim.Mode.ENFORCEMENT:
			return "Drive as the police and clear the highway by ramming every rival vehicle. Impacts remove rivals without slowing your patrol car."
		_:
			return "A classic 20 km highway race against five rivals. Accelerate, steer through the course, avoid collisions, and finish in the best position."


func _close_mode_menu() -> void:
	if _mode_overlay == null:
		return
	_mode_overlay.queue_free()
	_mode_overlay = null
	_mode_details_open = false


func _open_options() -> void:
	if _options_overlay != null:
		return
	_options_overlay = Panel.new()
	_options_overlay.name = "OptionsOverlay"
	_options_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	_options_overlay.offset_left = 240.0
	_options_overlay.offset_top = 120.0
	_options_overlay.offset_right = -240.0
	_options_overlay.offset_bottom = -120.0
	_options_overlay.modulate = Color(0.82, 0.9, 1.0, 0.96)
	_options_overlay.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(_options_overlay)
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT, Control.PRESET_MODE_MINSIZE, 30)
	_options_overlay.add_child(margin)
	_options_stack = VBoxContainer.new()
	_options_stack.add_theme_constant_override("separation", 14)
	margin.add_child(_options_stack)
	_options_title = Label.new()
	_options_title.add_theme_font_size_override("font_size", 34)
	_options_stack.add_child(_options_title)
	_show_options_page(0)


func _clear_options_page() -> void:
	for child in _options_stack.get_children():
		if child != _options_title:
			child.queue_free()


func _button(text: String, callback: Callable) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size.y = 44
	button.pressed.connect(callback)
	return button


func _show_options_page(page: int) -> void:
	_options_page = page
	_clear_options_page()
	if page == 0:
		_options_title.text = "OPTIONS"
		_options_stack.add_child(_button("1. Controls", func() -> void: _show_options_page(1)))
		_options_stack.add_child(_button("2. Video", func() -> void: _show_options_page(2)))
		_options_stack.add_child(_button("3. Audio", func() -> void: _show_options_page(3)))
		_options_stack.add_child(_button("4. Back", _close_options))
	elif page == 1:
		_options_title.text = "1. CONTROLS"
		_options_stack.add_child(_button("Keyboard (Keybinding): WASD / Arrow Keys", func() -> void: pass))
		_options_stack.add_child(_button("Joystick: Windows controller detected automatically", func() -> void: pass))
		_options_stack.add_child(_button("Apply Settings", func() -> void: _show_options_page(0)))
		_options_stack.add_child(_button("Back", func() -> void: _show_options_page(0)))
	elif page == 2:
		_options_title.text = "2. VIDEO"
		var display := OptionButton.new()
		display.add_item("Windowed Mode (Resizable)", 0)
		display.add_item("Fullscreen Windowed", 1)
		display.add_item("Fullscreen @ Monitor Resolution", 2)
		display.selected = _video_mode
		display.custom_minimum_size.y = 44
		_options_stack.add_child(display)
		_options_stack.add_child(_button("Apply Settings", func() -> void:
			_video_mode = display.selected
			_apply_video_settings()
			_show_options_page(0)
		))
		_options_stack.add_child(_button("Back", func() -> void: _show_options_page(0)))
	elif page == 3:
		_options_title.text = "3. AUDIO"
		var sound := CheckButton.new()
		sound.text = "Sound on/off"
		sound.button_pressed = _sound_on
		_options_stack.add_child(sound)
		var music := CheckButton.new()
		music.text = "Music on/off"
		music.button_pressed = _music_on
		_options_stack.add_child(music)
		var music_slider := HSlider.new()
		music_slider.min_value = 0.0
		music_slider.max_value = 1.0
		music_slider.value = _music_volume
		_options_stack.add_child(_labeled_control("Music volume", music_slider))
		var fx := CheckButton.new()
		fx.text = "FX on/off"
		fx.button_pressed = _fx_on
		_options_stack.add_child(fx)
		var fx_slider := HSlider.new()
		fx_slider.min_value = 0.0
		fx_slider.max_value = 1.0
		fx_slider.value = _fx_volume
		_options_stack.add_child(_labeled_control("FX volume", fx_slider))
		_options_stack.add_child(_button("Apply Settings", func() -> void:
			_sound_on = sound.button_pressed
			_music_on = music.button_pressed
			_music_volume = music_slider.value
			_fx_on = fx.button_pressed
			_fx_volume = fx_slider.value
			GameAudio.apply_settings(_sound_on, _music_on, _music_volume, _fx_on, _fx_volume)
			_show_options_page(0)
		))
		_options_stack.add_child(_button("Back", func() -> void: _show_options_page(0)))


func _labeled_control(label_text: String, control: Control) -> Control:
	var row := VBoxContainer.new()
	var label := Label.new()
	label.text = label_text
	row.add_child(label)
	row.add_child(control)
	return row


func _apply_video_settings() -> void:
	if _video_mode == 0:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
		DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_RESIZE_DISABLED, false)
	elif _video_mode == 1:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
	else:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_EXCLUSIVE_FULLSCREEN)


func _close_options() -> void:
	if _options_overlay == null:
		return
	_options_overlay.queue_free()
	_options_overlay = null
	_options_page = 0


func _begin() -> void:
	if _starting:
		return
	_starting = true
	_standard.disabled = true
	_chase.disabled = true
	_enforce.disabled = true
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
	RaceWorld.start_mode = _mode
	get_tree().change_scene_to_packed(RaceScene)
