extends Control

@export var btn_start : Button

func _ready():
	# Connexion des signaux
	btn_start.pressed.connect(_on_StartButton_pressed)
	pass


func _on_StartButton_pressed():
	Utile.changeScene("connexion")
