extends Control

@export var btn_leave: Button
var game_data: Dictionary = {}
@export var my_profil: Control
@export var dominoes: HBoxContainer

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
		
		
		profil_node.load_player_profile(
			pseudo, 
			image, 
			player.hote, 
			player.statut
		)
		
		profil_node.show_dominos_count(player.domino_count)

		player_count += 1
	

func _game_ended(data):
	Global.update_game_data(data)
	Utile.changeScene("lobby")


func load_player():
	var player = Global.get_all_player_data()
	var pseudo = player.pseudo
	var image = Utile.load_profil_picture(player.image)
	my_profil.load_player_profile(
		pseudo, 
		image, 
		player.hote, 
		player.statut
	)

	
	var dominoes = game_data.dominoes
	var domino_hand = preload("res://Scenes/Composants/hand_domino.tscn")
	
	for domino in dominoes:
		var domino_img = load("res://Assets/images/Dominos/d" + str(domino.id) + ".svg")
		domino_hand.texture = ImageTexture.create_from_image(domino_img)
		dominoes.add_child(domino_hand.instantiate())
