extends Control

func _ready():
	var data = Global.get_all_player_data()

	print(data)
	#var token = data["access_token"]
#
	#print("montoken" , token)
	var headers = [
		"Content-Type: application/json" ,
		#"Authorization: Bearer" + access_token 
	]
	$SessionsRequest.request("https://api--domino--y6qkmxzm7hxr.code.run/sessions", headers, HTTPClient.METHOD_GET)
	$SessionsRequest.request_completed.connect(self._on_traiter_resultat)

# Fonction de traitement des données retournées par l'API
func _on_traiter_resultat(result, response_code, headers, body):
	print(response_code)
	if response_code == 200:
		var json = JSON.new()
		var parse_result = json.parse(body.get_string_from_utf8())  # On analyse le contenu JSON

	
		var response = json.get_data()
		print("Réponse  : ", response)
		afficher_sessions(response)
	
	

# Afficher toutes les sessions retournées par l'API
func afficher_sessions(response):
	var sessions = response["data"]["sessions"]
	for session in sessions:
		var session_name = session["session_name"]
		var session_label = Label.new()
		session_label.text = session_name  
		session_label.add_theme_color_override("font_color", Color(0, 0, 0))  
		session_label.add_theme_font_size_override("font_size", 45) 
		
		
		session_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		session_label.size_flags_vertical = Control.SIZE_EXPAND_FILL
		session_label.custom_minimum_size = Vector2(0, 30)  
		
	
		$VBoxContainer.add_child(session_label)
