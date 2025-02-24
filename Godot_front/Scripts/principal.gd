extends Control

func _ready():
	#  Boutons connexion et inscription masquer au lancement
	$ButtonConnexion.hide()
	$ButtonInscription.hide()
	
	# Connexion des signaux
	$StartButton.pressed.connect(_on_StartButton_pressed)
	$ButtonConnexion.pressed.connect(_on_ButtonConnexion_pressed)
	$ButtonInscription.pressed.connect(_on_ButtonInscription_pressed)

func _on_ButtonConnexion_pressed():
	Utile.changeScene("connexion")


func _on_ButtonInscription_pressed():
	Utile.changeScene("inscription")
	

func _on_StartButton_pressed():
	#Bouton "start" masuqer et affichage des boutons connexion et inscription
	$StartButton.hide()
	$ButtonConnexion.show()
	$ButtonInscription.show()
