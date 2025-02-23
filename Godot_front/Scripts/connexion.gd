extends Control


# Called when the node enters the scene tree for the first time.
func _ready():
	$Inscription.connect("pressed", _on_Inscription_pressed)
	$ConnexionButton.connect("pressed", _on_connexion_reussie) 
	$LoginRequest.request_completed.connect(self._on_traiter_resultat)

	#pass # Replace with function body.


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _on_connexion_reussie():
	if $Pseudo.text != "" and $Mdp.text != "":  
		var body = JSON.stringify({"pseudo": $Pseudo.text, "password": $Mdp.text})
		#print(body)
		var headers = ["Content-Type: application/json"]
		$LoginRequest.request("https://api--domino--y6qkmxzm7hxr.code.run/login", headers, HTTPClient.METHOD_POST, body)
	else:
		print("Veuillez remplir tous les champs ") #Afficher le message à l'utilisateur a la place du print
		
		
func _on_traiter_resultat(result, response_code, headers, body):
	var json = JSON.new()
	json.parse(body.get_string_from_utf8())
	var response = json.get_data()
	if (response_code == 200):
		print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", response.data)
		Global.set_player_data(response.data)
		get_tree().change_scene_to_file("res://Scenes/home_menu.tscn")
	else:
		#get_tree().change_scene_to_file("res://connexion.tscn")
		print(response.message) #Afficher le message à l'utilisateur a la place du print
func _on_Inscription_pressed():
	print("Bouton Connect pressé")
	get_tree().change_scene_to_file("res://Scenes/inscription.tscn")
		
		
		
		
	
	
	
		
		
		
		#get_tree().change_scene_to_file("res://home_menu.tscn")
	
