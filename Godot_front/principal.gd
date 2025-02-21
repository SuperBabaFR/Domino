extends Control

func _ready():
	#  Boutons connexion et inscription masquer au lancement
	$ButtonConnexion.hide()
	$ButtonInscription.hide()
	
	# Connexion des signaux
	$ButtonConnexion.pressed.connect(_on_ButtonConnexion_pressed)
	$ButtonInscription.pressed.connect(_on_ButtonInscription_pressed)
	$StartButton.pressed.connect(_on_StartButton_pressed)

func _on_ButtonConnexion_pressed():
	get_tree().change_scene_to_file("res://Scenes/connexion.tscn")

func _on_ButtonInscription_pressed():
	get_tree().change_scene_to_file("res://Scenes/inscription.tscn")

func _on_StartButton_pressed():
	#Bouton "start" masuqer et affichage des boutons connexion et inscription
	$StartButton.hide()
	$ButtonConnexion.show()
	$ButtonInscription.show()
