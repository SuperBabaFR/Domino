extends Control

func _ready():
	Global.makeRequest("sessions", self._on_traiter_resultat)

func _on_traiter_resultat(result, response_code, headers, body):
	if response_code == 200:
		var json = JSON.new()
		var parse_result = json.parse(body.get_string_from_utf8())
		var response = json.get_data()
		afficher_sessions(response)
	elif response_code == 401:
		Global.refreshToken()
		while not Global.is_token_fresh:
			pass
		# On relance la méthode quand le token est frais
		Global.makeRequest("sessions", self._on_traiter_resultat)

func afficher_sessions(response):
	var sessions = response["data"]["sessions"]
	for session in sessions:
		var session_name = session["session_name"]
		var session_status = session["statut"]
		var is_public = session["is_public"]
		print(is_public)
		var session_code = session["code"]
		if session_status == "session.is_open" and is_public:

			var session_container = HBoxContainer.new()
			var session_label = Label.new()
			session_label.text = session_name

			#session_label.add_theme_color_ooverride("font_color", Color(0, 1, 0))
			var join_button = Button.new()
			join_button.text = "Rejoindre"
			join_button.pressed.connect(func(): rejoindre_session(session_code))
			session_container.add_child(join_button)

			session_label.add_theme_font_size_override("font_size", 45)
			session_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			session_label.size_flags_vertical = Control.SIZE_EXPAND_FILL
			session_label.custom_minimum_size = Vector2(0, 30)

			session_container.add_child(session_label)
			$VBoxContainer.add_child(session_container)

func rejoindre_session(session_code):
	var token = Global.get_player_info("access_token")
	var headers = [
		"Content-Type: application/json",
		"Authorization: Bearer " + token
	]
	var url = "https://api--domino--y6qkmxzm7hxr.code.run/join"
	var body = {
		"code": session_code
	}
	var json_body = JSON.stringify(body)
	$JoinRequest.request(url, headers, HTTPClient.METHOD_POST, json_body)
	$JoinRequest.request_completed.connect(self._on_join_result)

func _on_join_result(result, response_code, headers, body):
	if response_code == 200:
		print("Session rejointe avec succès")
