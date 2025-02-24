extends Node
# API
var API_URL = "https://api--domino--y6qkmxzm7hxr.code.run/"
# Valeur des dominos
var dominos_ref_list = []
# Player
var player_data: Dictionary  # Stocke les infos utilisateur après connexion
var is_logged_in = false  # Statut de connexion
# Tokens
var tokens
# Session
var session_infos: Dictionary
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
		"statut": data.statut,
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

# REJOINDRE UNE SESSION VIA SON CODE
func rejoindre_session(session_code):
	var body = {
		"code": session_code
	}
	var response = await makeRequest("join")
	
	var response_code = response.response_code
	var data: Dictionary = response.body.data
	var players_data = data.players
	data.erase("players")
	var session_data = {}
	
	if response_code == 200:
		print("Session rejointe avec succès")
		set_session_data(session_data, false)
		
		for player_info in players_data:
			add_player_info(player_info, false)
		
		changeScene("lobby")
	elif response_code == 401:
		return
	else:
		push_error("error? : ", response.body.message)


func makeRequest(action: String, jsonBody: String = "", urlParams = null):
	print("--- Make request début ---")
	print('\t action : ',action)
	var http_request = HTTPRequest.new()
	add_child(http_request)

	# Choisir l’URL et la méthode selon 'action'
	var full_url = API_URL + action
	var method = HTTPClient.Method.METHOD_GET

	match action:
		"login", "signup", "create":
			method = HTTPClient.Method.METHOD_POST
		"dominos", "sessions", "stats", "join":
			method = HTTPClient.Method.METHOD_GET
	# etc. Ajuste au besoin
	
	# Si on a des paramètres, on construit la query string
	if urlParams and method == HTTPClient.Method.METHOD_GET:
		var parts := []
		for key in urlParams.keys():
			var encoded_key = String(key).uri_encode()
			var encoded_value = String(urlParams[key]).uri_encode()
			parts.append("%s=%s" % [encoded_key, encoded_value])

		if parts.size() > 0:
			var packed_parts = PackedStringArray(parts)
			#var query_string = "?" + parts.join("&")
			#full_url += query_string
	
	var result = {"response_code" : 401}
	while result.response_code == 401:
		# Prépare les en-têtes selon qu’on a un token ou non
		var headers = ["Content-Type: application/json"]
		if tokens != null:
			headers.append("Authorization: Bearer " + tokens.access_token)
		
		# 1) Lancement de la requête
		var error = http_request.request(full_url, headers, method, jsonBody)
		
		if error != OK:
			push_error("Erreur durant l'init de la requête : %d" % error)
			http_request.queue_free()
			print("--- Make request fin (ERREUR DE LANCEMENT DE REQUETE) ---")
			return {"response_code" : 401}
		
		# 2) Attente asynchrone de la fin de la requête (signal request_completed)
		result = await http_request.request_completed

		result = { # On le transforme en dictionnaire
			"status" : result[0],
			"response_code" : result[1],
			"headers" : result[2],
			"body" : JSON.parse_string(result[3].get_string_from_utf8())
		}
		
		print("\tresponse_code : ", result.response_code)
		print("\tmessage : ", result.body.message)
		
		if result.response_code != HTTPClient.RESPONSE_UNAUTHORIZED:
			break
		# ON Refresh le token access comme il est plus frais
		var token_response_code = await refreshToken(http_request)
		
		if token_response_code == HTTPClient.RESPONSE_UNAUTHORIZED:
			http_request.queue_free()
			print("--- Make request fin (RECONNEXION NECESSAIRE) ---")
			return result
			
	# 3) On peut libérer le HTTPRequest maintenant
	http_request.queue_free()
	
	print("--- Make request fin ---")
	return result


# REFRESH TOKEN
func refreshToken(http_request: HTTPRequest):
	print("--- RefreshToken Début ---")
	var headers = ["Content-Type: application/json"]
	var json_body = JSON.stringify({"refresh_token": tokens.refresh_token})
	var error = http_request.request(API_URL + "access", headers, HTTPClient.Method.METHOD_POST, json_body)
	if error != OK:
		push_error("An error occurred in the HTTP request.")
		return null
	
	var result = await http_request.request_completed
	# result est un Array de la forme :
	#   [status, response_code, response_headers, body_bytes]
	# On le transforme en dictionnaire
	result = {
		"response_code" : result[1],
		"body" : JSON.parse_string(result[3].get_string_from_utf8())
	}
	var response_code = result.response_code
	print("\tresponse code : ", result.response_code)
	print("\tmessage : ", result.body.message)
	
	if response_code == HTTPClient.RESPONSE_CREATED:
		tokens.access_token = result.body.data.access_token
	elif response_code == HTTPClient.RESPONSE_UNAUTHORIZED:
		push_error(result.body.message)
		print("token refresh expiré -- Retour au menu principal")
		changeScene("principal")
	
	return response_code
	print("--- RefreshToken Fin ---")

# Changer de scène
func changeScene(scene_name: String):
	print("change de scene vers : ",scene_name)
	get_tree().change_scene_to_file("res://Scenes/" + scene_name + ".tscn")

# DOMINOS
func pull_list_dominos():
	print("--- pull_list_dominos Début ---")
	if not dominos_ref_list.is_empty():
		print("--- pull_list_dominos Fin (y'a déjà la liste de dominos) ---")
		return
	var response = await self.makeRequest("dominos")
	# Gestion de la réponse de l'API
	var response_code = response.response_code
	var body = response.body
	
	print("response_code", response_code)
	print("message", body.message)
	
	if response.response_code == HTTPClient.RESPONSE_OK:
		dominos_ref_list = body.data.domino_list
	else:
		print(body.message)
	print("--- pull_list_dominos Fin ---")
	return

# stats du joueur
func load_player_stats():
	print("--- load_player_stats Début ---")
	
	var response = await self.makeRequest("stats")
	# Gestion de la réponse de l'API
	var response_code = response.response_code
	var body = response.body
	
	print("response_code : ", response_code)
	print("message : ", body.message)
	
	
	if response.response_code == HTTPClient.RESPONSE_OK:
		player_data.merge(body.data, true)
		print(body.data)
	else:
		print(body.message)
	print("--- load_player_stats Fin ---")
	return body.data
	
