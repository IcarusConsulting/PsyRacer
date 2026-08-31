extends Node

## Loops the V1.0 music from launch and keeps playing across splash/race.
## M toggles mute (same idea as the old Music On/Off menu).

var _player: AudioStreamPlayer
var music_on := true


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
	_player.volume_db = -4.0
	add_child(_player)
	_player.play()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.physical_keycode == KEY_M:
			toggle()
			get_viewport().set_input_as_handled()


func toggle() -> void:
	music_on = not music_on
	if _player == null:
		return
	_player.stream_paused = not music_on
	if music_on and not _player.playing:
		_player.play()
