extends Control

@export var btn_leave : Button
@export var btn_start : Button
@export var btn_ready : Button
@export var btn_update_session : Button

@export var players_profiles : HBoxContainer

@export var session_name : Label
@export var nb_joueurs : Label
@export var reflexion_time : Label
@export var code_session : Label

var is_ready: bool = false
const action_path = "session."

@export var profil_scene : PackedScene

func _ready():
	btn_leave.connect("pressed", _on_btn_leave_press)
	btn_start.connect("pressed", _on_start_game)
	btn_ready.connect("pressed", _set_ready_statut)
	btn_update_session.connect("pressed", _on_btn_update_press)
	# Session modifiée
	Websocket.session_update_infos.connect(session_updated)
	# Partie lancée
	Websocket.session_start_game.connect(_game_started)
	# Mouvement de joueurs
	Websocket.session_player_join.connect(_on_player_join)
	Websocket.session_player_leave.connect(_on_player_leave)
	Websocket.session_hote_leave.connect(func(): Utile.changeScene("home_menu"))
	# Changements de statuts
	Websocket.session_player_statut.connect(_update_statut)
	# Connexion au websocket
	Websocket.connect_to_websocket()

	load_players_info()
	load_session_info()


func load_players_info():
	var players = Global.get_all_players_infos()
	var hote_pseudo = Global.get_info("session", "session_hote")
	print("hote de la session : ",hote_pseudo)
	
	for player in players:
		add_player_node(player)
	
	var node_hote = players_profiles.get_node(hote_pseudo)
	if node_hote:
		node_hote.toggle_hote(hote_pseudo, true)


func load_session_info():
	var name_session = Global.get_info("session", "session_name")
	var joueurs_count = Global.get_all_players_infos().size()
	var max_nb_joueurs = Global.get_info("session", "max_players_count")
	var reflexion_time_value = Global.get_info("session", "reflexion_time")
	
	session_name.text = name_session
	nb_joueurs.text = "Nombre de joueurs : " + str(joueurs_count) + "/" + str(max_nb_joueurs)
	reflexion_time.text = "Temps par tours : " + str(reflexion_time_value) + "sec"
	code_session.text = "CODE : " + Global.get_info("session", "session_code")
	
	var my_pseudo = Global.get_info("player", "pseudo")
	var session_hote = Global.get_info("session", "session_hote")
	
	btn_start.visible = (my_pseudo == session_hote)
	btn_update_session.visible = (my_pseudo == session_hote)


func session_updated(data):
	Global.update_session_data(data)
	load_session_info()
	
	for player in Global.get_all_players_infos():
		var profil = players_profiles.get_node(player.pseudo)
		
		if data.session_hote == player.pseudo:
			profil.toggle_hote(player.pseudo, true)
		else:
			profil.toggle_hote(player.pseudo, false)	


func _on_btn_update_press():
	if Global.get_info("player", "pseudo") != Global.get_info("session", "session_hote"):
		print("Vous n'êtes pas l'hote")
		return
	get_node("UpdateSession").visible = true


func _on_btn_leave_press():
	var body = {"session_id": Global.session_infos.session_id}
	var response = await API.makeRequest("kill", "", body)
	
	if response.response_code in [HTTPClient.RESPONSE_OK, HTTPClient.RESPONSE_NOT_FOUND]:
		Global.clear_session_data()
		Websocket.socket.close()
		Utile.changeScene("home_menu")
	else:
		print(response.body)
	
func _on_start_game():
	var body = {"session_id": Global.session_infos.session_id}
	var response = await API.makeRequest("start", "", body)
	
	if response.response_code == HTTPClient.RESPONSE_CREATED:
		_game_started(response.body.data)
	else:
		print("Partie non créée : ", response.body)

func _set_ready_statut():
	is_ready = ! is_ready
	
	var statut_id = 7 if is_ready else 6
	
	var statut = {
		"action": action_path + "player_statut", 
		"data": {
			"statut" : str(statut_id)
		}}
	
	if ! Websocket.send_json(statut):
		is_ready = ! is_ready
		print("Le statut n'a pas pu être changé")
		return
	
	btn_ready.text = "Prêt" if is_ready else "Pas Prêt"

func _update_statut(data):
	if players_profiles.has_node(data.pseudo):
		var profil_node = players_profiles.get_node(data.pseudo)
		Global.update_player_statut(data)
		profil_node.update_statut(data.statut)

func _on_player_leave(data):
	if players_profiles.has_node(data.pseudo):
		var profil_node = players_profiles.get_node(data.pseudo)

		Global.remove_player_info(data.pseudo)
		profil_node.queue_free()
		get_node("ChatTextuel").load_channels()

func _on_player_join(data : Dictionary):
	if players_profiles.has_node(data.pseudo):
		return
	Global.add_player_info(data)
	var joueurs_count = Global.get_all_players_infos().size()
	var max_player_count = Global.get_info("session", "max_players_count")
	nb_joueurs.text = "Nombre de joueurs : " + str(joueurs_count) + "/" + str(max_player_count)
	add_player_node(data)
	get_node("ChatTextuel").load_channels()
	

func add_player_node(data : Dictionary):
	var hote_pseudo = Global.get_info("session", "session_hote")
	var pseudo = "VOUS" if data.pseudo == Global.get_info("player", "pseudo") else data.pseudo
	var image = Utile.load_profil_picture(data.image)
	var statut = "player.not_ready"
	# Crée le node pour le profil
	var profil_node = profil_scene.instantiate()
	profil_node.name = data.pseudo
	# L'ajoute à l'écran
	players_profiles.add_child(profil_node)
	
	# Charge les informations
	profil_node.load_player_profile(pseudo, image)
	if data.has("statut"):
		statut = data.statut if data.statut != "" else "player.not_ready"
	profil_node.update_statut(statut)
	# active la courone si c'est l'hote
	if hote_pseudo == data.pseudo:
		profil_node.toggle_hote(pseudo, true)
	
	profil_node.set_scores(data.games_win, data.pig_count)


func _game_started(data):
	Global.set_game_data(data)
	Utile.changeScene("jeu")
