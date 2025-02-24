extends Control

func _ready():
	$Valider.connect("pressed", _on_rejoindre_pressed) 

func _on_rejoindre_pressed():
	if $CodeSession.text == "":
		print("Veuillez remplir tous les champs ") #Afficher le message à l'utilisateur a la place du print
	Global.rejoindre_session($CodeSession.text)
