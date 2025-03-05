extends Node
class_name sound_effect_component

@export var hover_fx: AudioStreamMP3 = preload("res://Assets/sfx/hover_sfx.mp3")
@export var click_fx: AudioStreamMP3 = preload("res://Assets/sfx/change_scene_sfx.mp3")

var target : Button
var audio_player : AudioStreamPlayer

signal finish

func _ready():
	target = get_parent()
	audio_player = AudioStreamPlayer.new()
	add_child(audio_player)
	connect_signals()

func connect_signals():
	target.mouse_entered.connect(on_hover)
	target.pressed.connect(off_press)


func on_hover() -> void:
	SFX.play_sound(hover_fx)


func off_press() -> void:
	SFX.play_sound(click_fx)
