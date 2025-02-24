extends Node
# API
const API_URL = "https://api--domino--y6qkmxzm7hxr.code.run/"
# Tokens
var tokens


# Set tokens
func set_tokens(data: Dictionary):
	tokens = {"access_token": data.access_token, "refresh_token": data.refresh_token}


# REJOINDRE UNE SESSION VIA SON CODE
func rejoindre_session(session_code):
	print("--- rejoindre_session début ---")
	print("\tsession_code : ", session_code)
	var body = {
		"session_code": session_code
	}
	var response = await self.makeRequest("join", "", body)
	var response_code = response.response_code
	
	if response_code == 200:
		print("Session rejointe avec succès")
		
		var data: Dictionary = response.body.data
		var players_data = data.players
		data.erase("players")
		Global.set_session_data(data, false)
		
		for player_info in players_data:
			Global.add_player_info(player_info, false)
		
		Utile.changeScene("lobby")
	elif response_code == 401:
		print("--- rejoindre_session fin (retour menu principal) ---")
		return
	else:
		push_error("error? : ", response.body.message)
	print("--- rejoindre_session fin ---")

# METHODE GLOBALE FAIRE DES REQUETES PROPRES AVEC GESTION DU TOKEN
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
		"dominos", "sessions", "stats", "join", "kill":
			method = HTTPClient.Method.METHOD_GET
	# etc. Ajuste au besoin
	
	# Si on a des paramètres, on construit la query string
	if urlParams and method == HTTPClient.Method.METHOD_GET:
		var parts := []
		for key in urlParams.keys():
			var encoded_key = str(key).uri_encode()
			var encoded_value = str(urlParams[key]).uri_encode()
			parts.append("%s=%s" % [encoded_key, encoded_value])

		if parts.size() > 0:
			var query_string = "?"
			# j'ajoute chaque arg 
			for part in parts:
				query_string += part + "&"
			# Je construit l'url
			full_url += query_string.substr(0, query_string.length() - 1)
	
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
		Utile.changeScene("principal")
	
	print("--- RefreshToken Fin ---")
	return response_code



# DOMINOS
func pull_list_dominos():
	print("--- pull_list_dominos Début ---")
	if not Global.dominos_ref_list.is_empty():
		print("--- pull_list_dominos Fin (y'a déjà la liste de dominos) ---")
		return
	var response = await self.makeRequest("dominos")
	# Gestion de la réponse de l'API
	var response_code = response.response_code
	var body = response.body
	
	print("response_code", response_code)
	print("message", body.message)
	
	if response.response_code == HTTPClient.RESPONSE_OK:
		Global.dominos_ref_list = body.data.domino_list
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
		Global.player_data.merge(body.data, true)
		print(body.data)
	else:
		print(body.message)
	print("--- load_player_stats Fin ---")
	return body.data
