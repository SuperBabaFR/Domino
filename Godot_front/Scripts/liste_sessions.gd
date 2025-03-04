extends Control

var label_settings
@export var btn_join : Button
@export var btn_actualiser : Button
@export var input_code_session: LineEdit

func _ready():
	load_sessions()
	label_settings = preload("res://theme/label_settings.tres")
	btn_join.connect("pressed", _on_rejoindre_pressed)
	btn_actualiser.connect("pressed", load_sessions)
	

func load_sessions():
	var response = await API.makeRequest("sessions")
	
	var response_code = response.response_code
	
	if response_code == 200:
		afficher_sessions(response.body.data.sessions)
	elif response_code == 401:
		return
	else:
		push_error("error? : ", response.body.message)


func afficher_sessions(sessions):
	
	var children = $ScrollContainer/VBoxContainer.get_children()
	for child in children:
		child.free()
	
	
	for session in sessions:
		session["can_join"] = true
		if session.statut in ["session.is_active", "session.is_full"] or not session.is_public:
			session["can_join"] = false
		print(session)
		
		# Pour chaque session que l'on peut vraiment rejoindre
		var session_container = HBoxContainer.new()
		# Nom de la session
		var session_label = Label.new()
		session_label.text = session.session_name
		session_label.set_label_settings(label_settings)
		session_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		session_label.size_flags_vertical = Control.SIZE_EXPAND_FILL
		session_label.custom_minimum_size = Vector2(0, 30)
		
		session_container.add_child(session_label)
		# Bouton rejoindre
		if session.can_join:
			var join_button = Button.new()
			join_button.text = "Rejoindre"
			join_button.pressed.connect(func(): API.rejoindre_session(session.code))
			
			session_container.add_child(join_button)
		# Ajoute l'élément entier
		$ScrollContainer/VBoxContainer.add_child(session_container)


func _on_btn_retour_pressed():
	Utile.changeScene("home_menu")

func _on_rejoindre_pressed():
	if input_code_session.text == "":
		print("Veuillez remplir tous les champs ") #Afficher le message à l'utilisateur a la place du print
	API.rejoindre_session(input_code_session.text)
