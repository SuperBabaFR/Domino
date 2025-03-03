class_name InteractionDominoComponent
extends Node

const from_center : bool = true
const hover_scale : Vector2 = Vector2(1.05, 1.05)

const time : float = 0.1
const transition_type : Tween.TransitionType = Tween.TransitionType.TRANS_SINE

signal focus

var target : TextureRect
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
	target.gui_input.connect(_gui_input)

func on_hover() -> void:
	if not Global.its_my_turn:
		return
	add_tween("scale", hover_scale, time)

func off_hover() -> void:
	if not Global.its_my_turn:
		return
	add_tween("scale", default_scale, time)

func _gui_input(event):
	if not Global.its_my_turn:
		return
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		print("Left mouse button was pressed!")
		
		focus.emit()
		

func add_tween(property: String, value, seconds: float) -> void:
	var tween = get_tree()
	
	if tween:
		tween = tween.create_tween()
		tween.tween_property(target, property, value, seconds).set_trans(transition_type)
