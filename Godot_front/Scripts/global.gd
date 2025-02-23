extends Node
# API
var API_URL = "https://api--domino--y6qkmxzm7hxr.code.run/"
# Valeur des dominos
var dominos_ref_list = []
# Player
var player_data  # Stocke les infos utilisateur après connexion
var is_logged_in = false  # Statut de connexion
# Tokens
var tokens
# Session
var session_infos = {}
# Liste des infos des joueurs dans la session
var player_list_data = []


func get_info(objet: String, key: String, default_value = null):
	if objet == "session":
		return session_infos.get(key, default_value)
	elif objet == "player":
		return player_data.get(key, default_value)

func set_player_data(data: Dictionary):
	tokens = {"access_token": data.access_token, "refresh_token": data.refresh_token}
	
	data.erase("access_token")
	data.erase("refresh_token")
	player_data = data
	is_logged_in = true
	print("Joueur connecté :", player_data.pseudo)

func get_all_player_data():
	return player_data

func reset_player():
	player_data.clear()
	is_logged_in = false
	tokens = null
	print("Joueur déconnecté")

# Session
func set_session_data(data: Dictionary, created: bool):
	session_infos = data
	if created:
		add_player_info(data, true)
	
func add_player_info(data: Dictionary, is_hote: bool):
	var info_player = {
		"pseudo": data.pseudo,
		"image": data.image,
		"rounds_win": 0,
		"games_win": data.games_win,
		"ping_count": data.ping_count,
		"hote": is_hote
	}
	player_list_data.append(info_player)

func remove_player_info(pseudo: String):
	for player_info in player_list_data:
		if player_info.pseudo == pseudo:
			player_list_data.erase(player_info)
			return true
	return false

func clear_session_data():
	session_infos.clear()
	player_list_data.clear()

# Request METHOD
#func makeRequest(action, method_signal, jsonBody=null, urlParams=null):
	#print("--- Make request Début ---")
	#print("Paramètres : action = " + str(action) + ", method_signal = " + str(method_signal) + ", urlParams = " + str(urlParams))
	#var http_request = HTTPRequest.new()
	#http_request.request_completed.connect(method_signal)
	#http_request.request_completed.connect(http_request.queue_free.unbind(4))
	#add_child(http_request)
	#var error; var headers_auth = null
	#if tokens != null:
		#headers_auth = [
			#"Content-Type: application/json",
			#"Authorization: Bearer " + tokens.access_token
		#]
	#
	#if action in ["login", "signup"]:
		#error = http_request.request(API_URL + action, headers, HTTPClient.Method.METHOD_POST, jsonBody)
	#
	#if action in ["dominos", "sessions"]:
		#error = http_request.request(API_URL + action, headers_auth, HTTPClient.Method.METHOD_GET)
	#
	#if action in ["create"]:
		#error = http_request.request(API_URL + action, headers_auth, HTTPClient.Method.METHOD_POST, jsonBody)
	#
	#if error != OK:
		#push_error("An error occurred in the HTTP request.")
	#print("--- Make request Fin ---")

func makeRequest(action: String, jsonBody: String = "", urlParams = null):
	print("--- Make request début ---")

	var http_request = HTTPRequest.new()
	add_child(http_request)

	# Prépare les en-têtes selon qu’on a un token ou non
	var headers = ["Content-Type: application/json"]
	if tokens != null:
		headers.append("Authorization: Bearer " + tokens.access_token)

	# Choisir l’URL et la méthode selon 'action'
	var full_url = API_URL + action
	var method = HTTPClient.Method.METHOD_GET

	match action:
		"login", "signup":
			method = HTTPClient.Method.METHOD_POST
		"dominos", "sessions":
			method = HTTPClient.Method.METHOD_GET
		"create":
			method = HTTPClient.Method.METHOD_POST
	# etc. Ajuste au besoin

	# 1) Lancement de la requête
	var error = http_request.request(full_url, headers, method, jsonBody)
	
	if error != OK:
		push_error("Erreur durant l'init de la requête : %d" % error)
		http_request.queue_free()
		return
	# 2) Attente asynchrone de la fin de la requête (signal request_completed)
	var result = await http_request.request_completed
	# result est un Array de la forme :
	#   [status, response_code, response_headers, body_bytes]
	# On le transforme en dictionnaire
	result = {
		"status" : result[0],
		"response_code" : result[1],
		"headers" : result[2],
		"body" : JSON.parse_string(result[3].get_string_from_utf8())
	}
	
	print("response_code : ", result.status)
	print("message : ", result.body.message)

	# 3) On peut libérer le HTTPRequest maintenant
	http_request.queue_free()
	
	

	print("--- Make request fin ---")
	return result


# REFRESH TOKEN
func oldrefreshToken():
	print("--- RefreshToken Début ---")
	var action = "access"
	var headers = ["Content-Type: application/json"]
	var json_body = JSON.stringify({"refresh_token": tokens.refresh_token})
	var http_request = HTTPRequest.new()
	http_request.request_completed.connect(self._when_token_refreshed)
	http_request.request_completed.connect(http_request.queue_free.unbind(4))
	add_child(http_request)
	var error = http_request.request(API_URL + action, headers, HTTPClient.Method.METHOD_POST, json_body)
	if error != OK:
		push_error("An error occurred in the HTTP request.")
	
	print("--- RefreshToken Fin ---")

func refreshToken():
	print("--- RefreshToken Début ---")
	
	
	
	print("--- RefreshToken Fin ---")
	
	


func _when_token_refreshed(_result, response_code, _headers, body):
	print("--- _when_token_refreshed Début ---")
	var json = JSON.new()
	json.parse(body.get_string_from_utf8())
	var response = json.get_data()
	
	print("response code : ", response_code)
	print("message : ", response.message)
	
	if response_code == HTTPClient.RESPONSE_CREATED:
		tokens.access_token = response.data.access_token
		# On émet le signal pour dire que c'est rafraîchi
		emit_signal("token_refreshed")
	elif response_code == HTTPClient.RESPONSE_UNAUTHORIZED:
		push_error(response.message)
		print("token refresh expiré -- Retour au menu principal")
		changeScene("principal")
	
	print("--- _when_token_refreshed Fin ---")

func _on_token_refreshed(action: String):
	# Le token est rafraîchi ici, on peut donc relancer la requête
	self.makeRequest(action, self._on_traiter_resultat)

	# On se déconnecte du signal pour éviter de relancer la requête en boucle
	if is_connected("token_refreshed", self._on_token_refreshed):
		disconnect("token_refreshed", self._on_token_refreshed)

func changeScene(scene_name: String):
	print("change de scene vers : ",scene_name)
	get_tree().change_scene_to_file("res://Scenes/" + scene_name + ".tscn")

# DOMINOS
func pull_list_dominos():
	#self.makeRequest("dominos", _on_list_dominos_pulled)
	pass


func _on_list_dominos_pulled(_result, response_code, _headers, body):
	var json = JSON.new()
	json.parse(body.get_string_from_utf8())
	var response = json.get_data()
	
	if response_code == HTTPClient.RESPONSE_OK:
		dominos_ref_list = response.data.domino_list
	elif response_code == HTTPClient.RESPONSE_UNAUTHORIZED:
		await refreshToken()
		
		pull_list_dominos()
	else:
		push_error(response.message)
