extends Control


# Called when the node enters the scene tree for the first time.
func _ready():
	$Valider.connect("pressed", _on_rejoindre_session) 
	$JoinRequest.request_completed.connect(self._on_traiter_resultat)

	#pass # Replace with function body.


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _on_rejoindre_session():
	if $CodeSession.text != "":   
		var body = JSON.stringify({"session_code": $CodeSession.text, "player_id": 5})
		#print(body)
		var headers = ["Content-Type: application/json"]
		$JoinRequest.request("http://localhost:8000/join", headers, HTTPClient.METHOD_POST, body)
	else:
		print("Veuillez remplir tous les champs ") #Afficher le message à l'utilisateur a la place du print
		
		
func _on_traiter_resultat(result, response_code, headers, body):
	var json = JSON.new()
	json.parse(body.get_string_from_utf8())
	var response = json.get_data()
	print(response)
	print(response_code)
	#if (response_code == 200):
		#get_tree().change_scene_to_file("res://home_menu.tscn")
	#else:
		##get_tree().change_scene_to_file("res://connexion.tscn")
		#print(response.message) #Afficher le message à l'utilisateur a la place du print
		#
		#
		
		
	
	
	
		
		
		
		#get_tree().change_scene_to_file("res://home_menu.tscn")
	
