extends Node

var API_URL = "https://api--domino--y6qkmxzm7hxr.code.run/"
const headers = ["Content-Type: application/json"]
var player_data = {}  # Stocke les infos utilisateur après connexion
var is_logged_in = false  # Statut de connexion
var token_access_fresh = false
var tokens = null

var dominos_ref_list = []

func set_player_data(data: Dictionary):
	tokens = {"access_token": data.access_token, "refresh_token": data.refresh_token}
	
	data.erase("access_token")
	data.erase("refresh_token")
	player_data = data
	#print(data)
	is_logged_in = true
	#token_access_fresh = true
	#print("Joueur connecté :", player_data)

func get_player_info(key: String, default_value = null):
	return player_data.get(key, default_value)

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
	
	print(response)

	if response_code == HTTPClient.RESPONSE_OK:
		dominos_ref_list = response.data.domino_list
	elif response_code == HTTPClient.RESPONSE_UNAUTHORIZED:
		token_access_fresh = false
		refreshToken()
	else:
		push_error(response["message"])


func makeRequest(action, method_signal, jsonBody=null, urlParams=null):
	# Create an HTTP request node and connect its completion signal.
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
	
	if action == "login" or action == "signup" or action.contains("token"):
		error = http_request.request(API_URL + action, headers, HTTPClient.Method.METHOD_POST, jsonBody)
	
	if action == "dominos" or action == "sessions":
		error = http_request.request(API_URL + action, headers_auth, HTTPClient.Method.METHOD_GET)
	
	if error != OK:
		push_error("An error occurred in the HTTP request.")


func refreshToken():
	# Create an HTTP request node and connect its completion signal.
	print('je me suis refresh')
	var action = "access"
	var refresh_token = get_player_info("refresh_token", null)
	var json_body = JSON.stringify({"refresh_token": refresh_token})
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
		player_data["access_token"] = response["data"]["access_token"]
		token_access_fresh = true
	else:
		push_error(response["message"])
		get_tree().change_scene_to_file("res://Scenes/principal.tscn")
