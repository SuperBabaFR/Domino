extends Control


# Called when the node enters the scene tree for the first time.
func _ready():
	$Inscription.connect("pressed", _on_Inscription_pressed)
	$ConnexionButton.connect("pressed", _on_connexion_pressed) 

# Called every frame. 'delta' is the elapsed time since the previous frame.
func _on_connexion_pressed():
	if $Pseudo.text == "" and $Mdp.text == "":  
		print("Veuillez remplir tous les champs ") # Afficher le message à l'utilisateur a la place du print
		return
	
	var json = JSON.stringify({"pseudo": $Pseudo.text, "password": $Mdp.text})
	var response = await Global.makeRequest("login", json)
	
	var response_code = response.response_code
	var body = response.body
	
	if response_code == 200:
		Global.set_player_data(body.data)
		get_tree().change_scene_to_file("res://Scenes/home_menu.tscn")
	else:
		print(body.message) #Afficher le message à l'utilisateur a la place du print


func _on_Inscription_pressed():
	Global.changeScene("inscription")
