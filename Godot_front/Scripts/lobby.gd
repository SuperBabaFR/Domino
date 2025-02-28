extends Control

@export var btn_leave : Button
@export var btn_start : Button
@export var btn_ready : Button

@export var players_profiles : HBoxContainer

var is_ready: bool = false
const action_path = "session."
var hote_pseudo

@export var profil_scene : PackedScene

func _ready():
	btn_leave.connect("pressed", _on_btn_leave_press)
	btn_start.connect("pressed", _on_start_game)
	btn_ready.connect("pressed", _set_ready_statut)
	
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


func load_players_info():
	var players = Global.get_all_players_infos()
	hote_pseudo = Global.get_info("session", "session_hote")
	print("hote de la session : ",hote_pseudo)
	
	for player in players:
		_on_player_join(player)
	
	var node_hote = players_profiles.get_node(hote_pseudo)
	if node_hote:
		node_hote.toggle_hote(hote_pseudo, true)


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
		var data = response.body.data
		Global.set_game_data(data)
		Utile.changeScene("jeu")
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
	
	btn_ready.text = "Retirer Prêt" if is_ready else "Mettre Prêt"

func _update_statut(data):
	var profil_node = players_profiles.get_node(data.pseudo)
	if profil_node:
		profil_node.update_statut(data.statut)

func _on_player_leave(data):
	var profil_node = players_profiles.get_node(data.pseudo)
	if profil_node:
		profil_node.queue_free()

func _on_player_join(data : Dictionary):
	if players_profiles.get_node(data.pseudo):
		return
	
	var pseudo = data.pseudo
	var image = Utile.load_profil_picture(data.image)
	var statut = "player.not_ready"
	# Crée le node pour le profil
	var profil_node = profil_scene.instantiate()
	profil_node.name = pseudo
	# L'ajoute à l'écran
	players_profiles.add_child(profil_node)
	
	# Charge les informations
	profil_node.load_player_profile(pseudo, image)
	if data.has("statut"):
		statut = data.statut if data.statut != "" else "player.not_ready"
	profil_node.update_statut(statut)
	# active la courone si c'est l'hote
	if hote_pseudo == pseudo:
		profil_node.toggle_hote(pseudo, true)
	
	profil_node.set_scores(data.games_win, data.pig_count)
	profil_node.visible = true
	


func _game_started(data):
	Global.set_game_data(data)
	Utile.changeScene("jeu")
