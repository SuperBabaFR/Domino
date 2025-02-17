extends Control


# Called when the node enters the scene tree for the first time.
func _ready():
	$ConnexionButton.connect("pressed", _on_connexion_reussie) 
	$LoginRequest.request_completed.connect(self._on_traiter_resultat)

	#pass # Replace with function body.


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _on_connexion_reussie():
	if $Pseudo.text != "" and $Mdp.text != "":  
		var body = JSON.new().stringify({"pseudo": $Pseudo.text, "password": $Mdp.text})
		var headers = ["Content-Type: application/json"]
		$LoginRequest.request("http://localhost:8000/login", headers, HTTPClient.METHOD_POST, body)
		
func _on_traiter_resultat(result, response_code, headers, body):
	var json = JSON.new()
	json.parse(body.get_string_from_utf8())
	var response = json.get_data()
	print(response)
	
	
	
		
		
		
		#get_tree().change_scene_to_file("res://home_menu.tscn")
	
