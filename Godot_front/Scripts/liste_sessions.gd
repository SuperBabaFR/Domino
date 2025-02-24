extends Control

func _ready():
	load_sessions()

func load_sessions():
	var response = await Global.makeRequest("sessions")
	
	var response_code = response.response_code
	
	if response_code == 200:
		afficher_sessions(response.body.data.sessions)
	elif response_code == 401:
		return
	else:
		push_error("error? : ", response.body.message)


func afficher_sessions(sessions):
	for session in sessions:
		print(session)
		# Pour chaque session que l'on peut vraiment rejoindre
		if session.statut == "session.is_open" and session.is_public:
			var session_container = HBoxContainer.new()
			var session_label = Label.new()
			session_label.text = session.session_name

			#session_label.add_theme_color_ooverride("font_color", Color(0, 1, 0))
			var join_button = Button.new()
			join_button.text = "Rejoindre"
			join_button.pressed.connect(func(): Global.rejoindre_session(session.code))

			session_label.add_theme_font_size_override("font_size", 30)
			session_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			session_label.size_flags_vertical = Control.SIZE_EXPAND_FILL
			session_label.custom_minimum_size = Vector2(0, 30)

			session_container.add_child(session_label)
			session_container.add_child(join_button)
			$VBoxContainer.add_child(session_container)


func _on_btn_retour_pressed():
	Global.changeScene("home_menu")
