class_name AnimationComponent
extends Node

@export var from_center : bool = true
@export var hover_scale : Vector2 = Vector2(1,1)
@export var click_scale : Vector2 = Vector2(1,1)

@export var time : float = 0.1
@export var transition_type : Tween.TransitionType = Tween.TransitionType.TRANS_SINE

var target : Button
var default_scale : Vector2

func _ready():
	target = get_parent()
	connect_signals()
	
	call_deferred("setup")

func setup():
	if from_center:
		target.pivot_offset = target.size / 2
	default_scale = target.scale


func connect_signals():
	target.mouse_entered.connect(on_hover)
	target.mouse_exited.connect(off_hover)
	target.button_up.connect(off_press)
	target.button_down.connect(on_press)

func on_hover() -> void:
	add_tween("scale", hover_scale, time)

func off_hover() -> void:
	add_tween("scale", default_scale, time)

func on_press() -> void:
	add_tween("scale", click_scale, time)

func off_press() -> void:
	add_tween("scale", default_scale, time)

func add_tween(property: String, value, seconds: float) -> void:
	var tween = get_tree()
	
	if tween:
		tween = tween.create_tween()
		tween.tween_property(target, property, value, seconds).set_trans(transition_type)
