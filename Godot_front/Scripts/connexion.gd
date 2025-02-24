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
	var response = await API.makeRequest("login", json)
	
	var response_code = response.response_code
	var body = response.body
	
	if response_code == 200:
		API.set_tokens(body.data)
		Global.set_player_data(body.data)
		Utile.changeScene("home_menu")
	else:
		print(body.message) #Afficher le message à l'utilisateur a la place du print


func _on_Inscription_pressed():
	Utile.changeScene("inscription")
