extends Control

@export var btn_leave: Button
@export var btn_pass: Button
var game_data: Dictionary = {}

@export var my_profil: Control
@export var players_profiles : BoxContainer

@export var dominoes: HBoxContainer
@export var table: HBoxContainer

const action_path = "game."
# Scènes composants
@export var domino_hand : PackedScene
@export var game_profil : PackedScene


func _ready():
	load_game()
	load_player()
	
	btn_leave.pressed.connect(_on_btn_leave_press)
	
	# Quelqu'un joue
	Websocket.game_someone_played.connect(someone_play)
	Websocket.game_someone_pass.connect(someone_pass)
	
	# C'est ton tour
	#Websocket.game_your_turn.connect(someone_play)
	#Websocket.game_your_turn_no_match.connect(someone_pass)
	
	# Changements de statuts
	Websocket.session_player_statut.connect(_update_statut)

func someone_play(data: Dictionary):	
	Global.update_game_data(data)
	print("domino joué : ", data.domino)
	print("joué à : ", data.side)
	
	if data.pseudo == Global.get_info("player", "pseudo"):
		return
	
	new_turn()
	
	var player_played = Global.get_player_info(data.pseudo)
	player_played.domino_count -= 1
	add_on_table(data.domino, data.side)


func add_on_table(domino: Dictionary, side: String):
	var my_domino = domino_hand.instantiate()
	my_domino.name = str(domino)
	my_domino.load_texture(domino, domino.orientation)
	table.add_child(my_domino)
	if side == "left":
		table.move_child(my_domino, 0)
	
	pass
	

func someone_pass(data: Dictionary):
	Global.update_game_data(data)
	if data.player_turn != Global.get_info("player", "pseudo"):
		new_turn()

func new_turn():
	game_data = Global.game_data
	var profil = players_profiles.get_node(game_data.player_turn)
	profil.activate_time_reflexion(game_data.player_time_end)


func load_game():
	var players = Global.get_all_players_infos()
	var my_pseudo = Global.get_info("player", "pseudo")
	
	for player in players:
		if my_pseudo == player.pseudo:
			continue
		
		add_player_node(player)


func add_player_node(data : Dictionary):
	if players_profiles.has_node(data.pseudo):
		return
	game_data = Global.game_data
	var image = Utile.load_profil_picture(data.image)
	var statut = "player.is_actif"
	# Crée le node pour le profil
	var profil_node = game_profil.instantiate()
	profil_node.name = data.pseudo

	# L'ajoute à l'écran
	players_profiles.add_child(profil_node)

	# Charge les informations
	profil_node.load_player_profile(data.pseudo, image)
	profil_node.update_statut(statut)
	profil_node.show_dominos_count(data.domino_count)
	if game_data.player_turn == data.pseudo:
		profil_node.activate_time_reflexion(game_data.player_time_end)


func _update_statut(data):
	if players_profiles.has_node(data.pseudo):
		var profil_node = players_profiles.get_node(data.pseudo)
		Global.update_player_statut(data)
		profil_node.update_statut(data.statut)


func _game_ended(data):
	Utile.changeScene("lobby")


func load_player():
	var player = Global.get_all_player_data()
	var pseudo = player.pseudo
	var image = Utile.load_profil_picture(player.image)

	my_profil.load_player_profile(pseudo, image)
	my_profil.update_statut("actif")
	my_profil.hide_pseudo(true)
	
	if Global.game_data.player_turn == pseudo:
		my_profil.activate_time_reflexion(game_data.player_time_end)
	
	load_my_dominoes()


func load_my_dominoes():
	var my_dominoes = str_to_var(game_data.dominoes)
	
	var children = dominoes.get_children()
	for child in children:
		child.free()
	
	for domino in my_dominoes:
		var my_domino = domino_hand.instantiate()
		my_domino.name = str(domino)
		my_domino.load_texture(domino)
		dominoes.add_child(my_domino)

func refresh_after_play(data: Dictionary):
	load_my_dominoes()
	pass


func no_match_turn(data: Dictionary):
	my_profil.activate_time_reflexion(game_data.player_time_end)
	btn_pass.visible = true


func _on_btn_leave_press():
	var body = {"session_id": Global.session_infos.session_id}
	var response = await API.makeRequest("kill", "", body)
	
	if response.response_code in [HTTPClient.RESPONSE_OK, HTTPClient.RESPONSE_NOT_FOUND]:
		Global.clear_session_data()
		Websocket.socket.close()
		Utile.changeScene("home_menu")
	else:
		print(response.body)
