extends Control

func _ready():
	$CreateBtn.connect("pressed", _on_start_pressed)
	$JoinBtn.connect("pressed", _on_join_pressed)
	$DisconnectBtn.connect("pressed", _on_disconnect_pressed)
func _on_start_pressed():
	get_tree().change_scene_to_file("res://scenes/GameScene.tscn")

func _on_join_pressed():
	get_tree().change_scene_to_file("res://Rejoindre.tscn")
	
func _on_disconnect_pressed():
	get_tree().change_scene_to_file("res://scenes/GameScene.tscn")
	
