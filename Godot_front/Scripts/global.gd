extends Node
# API
var API_URL = "https://api--domino--y6qkmxzm7hxr.code.run/"
const headers = ["Content-Type: application/json"]
# Player
var player_data  # Stocke les infos utilisateur après connexion
var is_logged_in = false  # Statut de connexion
# Tokens
var token_access_fresh = false
var tokens
# Session
var session_data

var dominos_ref_list = []

func get_info(objet: String, key: String, default_value = null):
	if objet == "session":
		return session_data.get(key, default_value)
	elif objet == "player":
		return player_data.get(key, default_value)

func set_player_data(data: Dictionary):
	tokens = {"access_token": data.access_token, "refresh_token": data.refresh_token}
	token_access_fresh = true
	
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
	token_access_fresh = false
	print("Joueur déconnecté")


# DOMINOS
func pull_list_dominos():
	self.makeRequest("dominos", _on_list_dominos_pulled)
	pass


func _on_list_dominos_pulled(_result, response_code, _headers, body):
	var json = JSON.new()
	json.parse(body.get_string_from_utf8())
	var response = json.get_data()
	
	if response_code == HTTPClient.RESPONSE_OK:
		dominos_ref_list = response.data.domino_list
	elif response_code == HTTPClient.RESPONSE_UNAUTHORIZED:
		token_access_fresh = false
		refreshToken()
	else:
		push_error(response["message"])

# Session

func set_session_data(data: Dictionary):
	session_data = data
	
func add_player_info(data: Dictionary):
	pass


func makeRequest(action, method_signal, jsonBody=null, urlParams=null):
	print("--- Make request Début ---")
	print("Paramètres : action = " + str(action) + ", method_signal = " + str(method_signal) + ", urlParams = " + str(urlParams))
	var http_request = HTTPRequest.new()
	http_request.request_completed.connect(method_signal)
	http_request.request_completed.connect(http_request.queue_free.unbind(4))
	add_child(http_request)
	var error; var headers_auth = null
	if tokens != null:
		headers_auth = [
			"Content-Type: application/json",
			"Authorization: Bearer " + tokens.access_token
		]
	
	if action in ["login", "signup"]:
		error = http_request.request(API_URL + action, headers, HTTPClient.Method.METHOD_POST, jsonBody)
	
	if action in ["dominos", "sessions"]:
		error = http_request.request(API_URL + action, headers_auth, HTTPClient.Method.METHOD_GET)
	
	if action in ["create"]:
		error = http_request.request(API_URL + action, headers_auth, HTTPClient.Method.METHOD_POST, jsonBody)
	
	if error != OK:
		push_error("An error occurred in the HTTP request.")
	print("--- Make request Fin ---")


func refreshToken():
	# Create an HTTP request node and connect its completion signal.
	print('je me suis refresh')
	var action = "access"
	var json_body = JSON.stringify({"refresh_token": tokens.refresh_token})
	var http_request = HTTPRequest.new()
	http_request.request_completed.connect(self._when_token_refreshed)
	http_request.request_completed.connect(http_request.queue_free.unbind(4))
	add_child(http_request)
	var error = http_request.request(API_URL + action, headers, HTTPClient.Method.METHOD_POST, json_body)
	if error != OK:
		push_error("An error occurred in the HTTP request.")

func _when_token_refreshed(_result, response_code, _headers, body):
	var json = JSON.new()
	json.parse(body.get_string_from_utf8())
	var response = json.get_data()
	
	if response_code == HTTPClient.RESPONSE_CREATED:
		tokens.access_token = response.data.access_token
		token_access_fresh = true
	else:
		push_error(response["message"])
		get_tree().change_scene_to_file("res://Scenes/principal.tscn")
