extends Control

@export var btn_leave: Button
@export var btn_pass: Button

@export var btn_left: Button
@export var btn_right: Button

@export var my_profil: Control
@export var players_profiles : BoxContainer
@export var sides : BoxContainer

@export var dominoes: HBoxContainer
@export var table: HBoxContainer

const action_path = "game."

var id = 0

# Scènes composants
@export var domino_hand : PackedScene
@export var game_profil : PackedScene
@export var interaction_component : Script

@export var offset : Vector2

func _ready():
	load_game()
	load_player()
	
	btn_leave.pressed.connect(_on_btn_leave_press)
	btn_pass.pressed.connect(_i_pass)
	
	btn_left.pressed.connect(side_left)
	btn_right.pressed.connect(side_right)
	# Quelqu'un joue
	Websocket.game_someone_played.connect(someone_play)
	Websocket.game_someone_pass.connect(someone_pass)
	
	# C'est ton tour
	Websocket.game_your_turn.connect(your_match_turn)
	Websocket.game_your_turn_no_match.connect(no_match_turn)
	
	# Changements de statuts
	Websocket.session_player_statut.connect(_update_statut)

func someone_play(data: Dictionary):
	Global.update_player_turn(data)
	print("domino joué : ", data.domino)
	print("joué à : ", data.side)
	
	if data.pseudo == Global.get_info("player", "pseudo"):
		return
	
	new_turn()
	
	var player_played = Global.get_player_info(data.pseudo)
	player_played.domino_count -= 1
	players_profiles.get_node(data.pseudo).show_dominos_count(player_played.domino_count)
	add_on_table(data.domino, data.orientation, data.side)


func add_on_table(domino, orientation: String, side: String):
	var this_table = Global.game_data.table
	
	if typeof(Global.game_data.table) == TYPE_STRING:
		this_table = str_to_var(Global.game_data.table)
	
	
	if side == "left":
		this_table.push_front({"id": domino, "orientation": orientation})
	else:
		this_table.push_back({"id": domino, "orientation": orientation})
	
	
	var my_domino = domino_hand.instantiate()
	my_domino.name = str(domino)
	my_domino.load_texture(domino, orientation)
	table.add_child(my_domino)
	if side == "left":
		table.move_child(my_domino, 0)


func someone_pass(data: Dictionary):
	Global.update_player_turn(data)
	if data.player_turn != Global.get_info("player", "pseudo"):
		new_turn()

func new_turn():
	if not Global.game_data.player_turn:
		var profil = players_profiles.get_node(Global.game_data.player_turn)
		profil.activate_time_reflexion(Global.game_data.player_time_end)


func load_game():
	var players = Global.get_all_players_infos()
	var my_pseudo = Global.get_info("player", "pseudo")
	
	for player in players:
		if my_pseudo == player.pseudo:
			continue
		
		add_player_node(player)
	
	load_table(Global.game_data.table)


func add_player_node(data : Dictionary):
	if players_profiles.has_node(data.pseudo):
		return
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
	if Global.game_data.player_turn == data.pseudo:
		profil_node.activate_time_reflexion(Global.game_data.player_time_end)


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
		my_profil.activate_time_reflexion(Global.game_data.player_time_end)
	
	load_my_dominoes(Global.game_data.dominoes)


func load_table(dominoes_table):
	
	if typeof(dominoes_table) == TYPE_STRING:
		dominoes_table = str_to_var(dominoes_table)
	
	var children = table.get_children()
	for child in children:
		child.free()
	
	for domino in dominoes_table:
		if typeof(domino) == TYPE_STRING:
			domino = str_to_var(domino)
		var my_domino = domino_hand.instantiate()
		my_domino.load_texture(domino.id, domino.orientation)
		table.add_child(my_domino)
		my_domino.name = str(domino.id)


func load_my_dominoes(data : String):
	var my_dominoes = str_to_var(Global.game_data.dominoes)
	
	var children = dominoes.get_children()
	for child in children:
		child.free()
	
	for domino in my_dominoes:
		var my_domino = domino_hand.instantiate()
		my_domino.load_texture(domino)
		dominoes.add_child(my_domino)
		my_domino.name = str(domino)
		var interact_component = interaction_component.new()
		interact_component.connect("focus", func(): self.show_sides(my_domino))
		my_domino.add_child(interact_component)

func show_sides(domino: Node):
	if not Global.its_my_turn():
		return
	id = domino.id
	sides.visible = true
	
	sides.position = dominoes.position + domino.position - offset

func side_left():
	play_domino(id, "left")

func side_right():
	play_domino(id, "right")


func play_domino(id, side):
	if not Global.its_my_turn():
		return
	sides.visible = false
	
	var body = {
		"session_id": Global.session_infos.session_id,
		"round_id": Global.game_data.round_id,
		"domino_id": id,
		"side": side
		}
	
	var json_body = JSON.stringify(body, "  ")
	print(json_body)
	
	var response = await API.makeRequest("play", json_body)
	
	if response.response_code in [HTTPClient.RESPONSE_OK]:
		refresh_after_play(response.body.data)
	else:
		print(response.body)



func refresh_after_play(data: Dictionary):
	Global.update_player_game_data(data)
	load_my_dominoes(data.dominoes)
	load_table(data.table)
	new_turn()
	pass


func no_match_turn(data: Dictionary):
	my_profil.activate_time_reflexion(Global.game_data.player_time_end)
	btn_pass.visible = true

func your_match_turn(data: Dictionary):
	my_profil.activate_time_reflexion(Global.game_data.player_time_end)
	
	
func _i_pass():
	var json = {
		"action": action_path + "pass",
		"data": {
			"round_id": Global.game_data.round_id
		}
	}
	
	if Websocket.send_json(json):
		btn_pass.visible = false

func _on_btn_leave_press():
	var body = {"session_id": Global.session_infos.session_id}
	var response = await API.makeRequest("kill", "", body)
	
	if response.response_code in [HTTPClient.RESPONSE_OK, HTTPClient.RESPONSE_NOT_FOUND]:
		Global.clear_session_data()
		Websocket.socket.close()
		Utile.changeScene("home_menu")
	else:
		print(response.body)
