extends Control

func _ready():
	$StartButton.connect("pressed", _on_start_pressed)
func _on_start_pressed():
	get_tree().change_scene_to_file("res://scenes/GameScene.tscn")
