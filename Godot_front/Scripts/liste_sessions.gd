extends Control

var label_settings
@export var btn_join : Button
@export var btn_actualiser : Button
@export var input_code_session: LineEdit

@onready var session_line: PackedScene = preload("res://Scenes/Composants/ligne_session.tscn")

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
		print(session)
		
		# Nom de la session
		var line = session_line.instantiate()
		
		var nb = str(session.player_count) + "/" + str(session.max_players_count)
		
		line.load_line(session.session_name, session.session_hote, session.statut, nb, session.is_public)

		# Ajoute l'élément entier
		$ScrollContainer/VBoxContainer.add_child(line)


func _on_btn_retour_pressed():
	Utile.changeScene("home_menu")

func _on_rejoindre_pressed():
	if input_code_session.text == "":
		print("Veuillez remplir tous les champs ") #Afficher le message à l'utilisateur a la place du print
	API.rejoindre_session(input_code_session.text)
