extends Node

var API_URL = "https://api--domino--y6qkmxzm7hxr.code.run/"
var URL_test = "https://httpbin.org/get"
var player_data = {}  # Stocke les infos utilisateur après connexion
var is_logged_in = false  # Statut de connexion

func set_player_data(data: Dictionary):
	player_data = data
	is_logged_in = true
	print("Utilisateur connecté :", player_data.pseudo)

func get_player_info(key: String, default_value = null):
	return player_data.get(key, default_value)

func get_all_player_data():
	return player_data

func reset_user():
	player_data.clear()
	is_logged_in = false
	print("Utilisateur déconnecté")


func refreshToken():
	# Create an HTTP request node and connect its completion signal.
	var action = "/token/refresh"
	var json_body = JSON.stringify({"refresh_token": self.get_player_info("refresh_token")})
	var http_request = HTTPRequest.new()
	http_request.request_completed.connect(self._when_token_refreshed)
	http_request.request_completed.connect(http_request.queue_free.unbind(4))
	add_child(http_request)
	var error = http_request.request(API_URL + action, [], HTTPClient.Method.METHOD_POST, json_body)
	if error != OK:
		push_error("An error occurred in the HTTP request.")

func _when_token_refreshed(result, response_code, headers, body):
	var json = JSON.new()
	json.parse(body.get_string_from_utf8())
	var response = json.get_data()
	print(response)
	print(response.data)

func makeRequest(action, jsonBody, method_signal):
	# Create an HTTP request node and connect its completion signal.
	var http_request = HTTPRequest.new()
	http_request.request_completed.connect(method_signal)
	http_request.request_completed.connect(http_request.queue_free.unbind(4))
	add_child(http_request)
	var error
	
	if action == "login" or action == "signup" or action.contains("token"):
		error = http_request.request(API_URL + action, [], HTTPClient.Method.METHOD_POST, jsonBody)
	
	if error != OK:
		push_error("An error occurred in the HTTP request.")
