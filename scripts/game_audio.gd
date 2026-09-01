extends Node

## Loops the V1.0 music from launch and keeps playing across splash/race.
## M toggles mute (same idea as the old Music On/Off menu).

var _player: AudioStreamPlayer
var music_on := true
var sound_on := true
var music_volume := 0.8
var fx_on := true
var fx_volume := 0.8


func _ready() -> void:
	_player = AudioStreamPlayer.new()
	_player.name = "BGM"
	var stream := load("res://assets/Background Music.mp3")
	if stream == null:
		push_warning("PsyRacer: missing Background Music.mp3")
		return
	if stream is AudioStreamMP3:
		(stream as AudioStreamMP3).loop = true
	elif stream.has_method("set_loop"):
		stream.set("loop", true)
	_player.stream = stream
	_player.volume_db = linear_to_db(music_volume) - 4.0
	add_child(_player)
	_player.play()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.physical_keycode == KEY_M:
			toggle()
			get_viewport().set_input_as_handled()


func _exit_tree() -> void:
	if _player == null:
		return
	_player.stop()
	_player.stream = null
	_player.queue_free()
	_player = null


func toggle() -> void:
	music_on = not music_on
	if _player == null:
		return
	_player.stream_paused = not music_on
	if music_on and not _player.playing:
		_player.play()


func apply_settings(new_sound_on: bool, new_music_on: bool, new_music_volume: float, new_fx_on: bool, new_fx_volume: float) -> void:
	sound_on = new_sound_on
	music_on = new_music_on
	music_volume = clampf(new_music_volume, 0.0, 1.0)
	fx_on = new_fx_on
	fx_volume = clampf(new_fx_volume, 0.0, 1.0)
	if _player == null:
		return
	_player.stream_paused = not (sound_on and music_on)
	_player.volume_db = linear_to_db(maxf(music_volume, 0.001)) - 4.0
