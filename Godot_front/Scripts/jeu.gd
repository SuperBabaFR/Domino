extends Control

@export var btn_leave: Button
var game_data: Dictionary = {}
@export var my_profil: Control
@export var dominoes: HBoxContainer
@export var players_profiles : BoxContainer

const action_path = "game."
var player_turn = ""
var domino_hand = preload("res://Scenes/Composants/hand_domino.tscn")

func _ready():
	load_game()
	load_player()
	Websocket.game_someone_played.connect(someone_play)
	Websocket.game_someone_pass.connect(someone_pass)

func someone_play(data: Dictionary):	
	Global.update_game_data(data)
	print("domino joué : ", data.domino)
	print("joué à : ", data.side)
	
func someone_pass(data: Dictionary):
	Global.update_game_data(data)

func load_game():
	game_data = Global.game_data
	
	var players = Global.get_all_players_infos()
	var my_pseudo = Global.get_info("player", "pseudo")
	
	var player_count = 1
	for player in players:
		var pseudo = player.pseudo
		
		if my_pseudo == pseudo:
			continue
		
		var image = Utile.load_profil_picture(player.image)
		var profil_node = get_node("player"+str(player_count))
		
		
		profil_node.load_player_profile(pseudo, image)		
		profil_node.show_dominos_count(player.domino_count)
		profil_node.update_statut("actif")

		player_count += 1
	

func _game_ended(data):
	Global.update_game_data(data)
	Utile.changeScene("lobby")


func load_player():
	var player = Global.get_all_player_data()
	var pseudo = player.pseudo
	var image = Utile.load_profil_picture(player.image)

	my_profil.load_player_profile(pseudo, image)		
	my_profil.update_statut("actif")
	
	var dominoes = game_data.dominoes
	
	for domino in dominoes:
		var my_domino = domino_hand.instantiate()
		my_domino.load_texture(domino.id)
		dominoes.add_child(my_domino)
