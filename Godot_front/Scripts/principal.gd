extends Control

@export var btn_connexion : Button
@export var btn_inscription : Button
@export var btn_start : Button

func _ready():
	#  Boutons connexion et inscription masquer au lancement
	btn_connexion.hide()
	btn_inscription.hide()
	
	# Connexion des signaux
	btn_start.pressed.connect(_on_StartButton_pressed)
	btn_connexion.pressed.connect(_on_ButtonConnexion_pressed)
	btn_inscription.pressed.connect(_on_ButtonInscription_pressed)
	
	get_node("maco").connect("pressed", func(): Websocket.socket.send_text("maco"))

	
func _on_ButtonConnexion_pressed():
	Utile.changeScene("connexion")


func _on_ButtonInscription_pressed():
	Utile.changeScene("inscription")
	

func _on_StartButton_pressed():
	#Bouton "start" masuqer et affichage des boutons connexion et inscription
	btn_start.hide()
	btn_connexion.show()	
	btn_inscription.show()
