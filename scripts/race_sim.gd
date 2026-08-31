class_name RaceSim
extends RefCounted

## Port of PsyRacer V1.0 play_race / road_curve / AI / collision.
## Original sim ran at 20 FPS; FRAME_HZ converts those per-frame numbers to delta time.

const FRAME_HZ := 20.0
const DIST_PER_SPEED := 6.5

enum Difficulty { EASY, MEDIUM, HARD }

class Racer:
	var z: float
	var x: float
	var lane: float
	var hue: float
	var speed: float = 0.0
	var target_speed: float
	var number: int
	var car_name: String


static var difficulty_table := {
	Difficulty.EASY: {"max_speed": 1.35, "accel": 0.018, "finish": 10000.0, "ai_speed": 0.88},
	Difficulty.MEDIUM: {"max_speed": 1.65, "accel": 0.022, "finish": 20000.0, "ai_speed": 0.96},
	Difficulty.HARD: {"max_speed": 1.95, "accel": 0.026, "finish": 30000.0, "ai_speed": 1.05},
}

static var ai_field := [
	{"number": 2, "name": "Nova", "hue": 0.0, "x": -0.58, "z": 7.0, "pace": 0.92},
	{"number": 7, "name": "Volt", "hue": 210.0, "x": 0.58, "z": 7.0, "pace": 0.95},
	{"number": 11, "name": "Apex", "hue": 45.0, "x": -0.30, "z": 13.0, "pace": 1.00},
	{"number": 18, "name": "Blaze", "hue": 25.0, "x": 0.30, "z": 13.0, "pace": 0.97},
	{"number": 24, "name": "Ion", "hue": 180.0, "x": 0.0, "z": 19.0, "pace": 1.03},
]

var difficulty: Difficulty = Difficulty.MEDIUM
var finish_distance: float = 20000.0
var max_speed: float = 1.65
var accel: float = 0.022
var ai_speed_scale: float = 0.96

var distance: float = 0.0
var player_x: float = 0.0
var speed: float = 0.0
var cars: Array[Racer] = []
var crashed: bool = false
var crash_timer: float = 0.0
var overlapping: Dictionary = {}
var finished: bool = false
var racing: bool = false
var elapsed: float = 0.0
var lights_stage: int = 0
var countdown_text: String = "READY"


func setup(diff: Difficulty) -> void:
	difficulty = diff
	var cfg: Dictionary = difficulty_table[diff]
	max_speed = cfg["max_speed"]
	accel = cfg["accel"]
	finish_distance = cfg["finish"]
	ai_speed_scale = cfg["ai_speed"]
	distance = 0.0
	player_x = 0.0
	speed = 0.0
	crashed = false
	crash_timer = 0.0
	overlapping.clear()
	finished = false
	racing = false
	elapsed = 0.0
	cars.clear()
	for spec in ai_field:
		var r := Racer.new()
		r.z = spec["z"]
		r.x = spec["x"]
		r.lane = spec["x"]
		r.hue = spec["hue"]
		r.target_speed = max_speed * ai_speed_scale * spec["pace"]
		r.number = spec["number"]
		r.car_name = spec["name"]
		cars.append(r)


static func road_curve(z: float) -> float:
	return sin(z * 0.011) * 0.55 + sin(z * 0.027) * 0.28 + sin(z * 0.003) * 0.18


static func road_center(z: float) -> float:
	return road_curve(z) * 12.0


func tick(delta: float, steer: float, throttle: float, brake: float) -> void:
	var step: float = delta * FRAME_HZ
	elapsed += delta

	if elapsed < 0.9:
		lights_stage = 0
		countdown_text = "READY"
		racing = false
	elif elapsed < 1.8:
		lights_stage = 1
		countdown_text = "3"
		racing = false
	elif elapsed < 2.7:
		lights_stage = 2
		countdown_text = "2"
		racing = false
	elif elapsed < 3.6:
		lights_stage = 3
		countdown_text = "1"
		racing = false
	elif elapsed < 4.4:
		lights_stage = 4
		countdown_text = "GO!"
		racing = true
	else:
		lights_stage = 0
		countdown_text = ""
		racing = true

	if crash_timer > 0.0:
		crash_timer -= delta
		if crash_timer <= 0.0:
			crashed = false

	if racing and not finished:
		if throttle > 0.0:
			speed += accel * step * throttle
		if brake > 0.0:
			speed -= accel * 1.4 * step * brake
		speed -= 0.006 * step
		speed = clampf(speed, 0.0, max_speed)

		var curve := road_curve(distance + 8.0)
		player_x += steer * (0.045 + speed * 0.03) * step
		player_x += curve * speed * 0.018 * step
		if absf(player_x) > 0.92:
			speed *= pow(0.94, step)
			player_x = clampf(player_x, -1.15, 1.15)
		else:
			player_x = clampf(player_x, -1.08, 1.08)

		distance += speed * DIST_PER_SPEED * step
		_update_ai(step)
		_collide()
	else:
		speed = 0.0

	if distance >= finish_distance:
		finished = true
		speed *= pow(0.9, step)


func _update_ai(step: float) -> void:
	for car in cars:
		if car.speed < car.target_speed:
			car.speed += accel * randf_range(0.55, 1.05) * step
		else:
			car.speed -= 0.004 * step
		car.speed = clampf(car.speed, 0.0, car.target_speed)
		car.x += (car.lane - car.x) * 0.08 * step
		car.x += sin(car.z * 0.04 + car.number) * 0.004 * step
		car.x = clampf(car.x, -0.82, 0.82)
		car.z += car.speed * DIST_PER_SPEED * step


func _collide() -> void:
	var current: Dictionary = {}
	for car in cars:
		var rel: float = car.z - distance
		if rel > 2.0 and rel < 7.5 and absf(car.x - player_x) < 0.28:
			current[car.number] = true
			if not overlapping.has(car.number):
				speed = max_speed * 0.5
				car.speed = car.target_speed * 0.5
				crashed = true
				crash_timer = 8.0 / FRAME_HZ
	overlapping = current


func race_place() -> int:
	var ahead := 0
	for car in cars:
		if car.z > distance:
			ahead += 1
	return ahead + 1


func world_pos(z: float, x_lane: float) -> Vector3:
	var half := 7.0
	return Vector3(road_center(z) + x_lane * half, 0.0, z)
