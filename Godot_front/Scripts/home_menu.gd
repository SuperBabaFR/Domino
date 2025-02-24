extends Control

# Boutons
@export var btn_disconnect : Button
@export var btn_create : Button
@export var btn_join : Button

# Labels
@export var label_wins : Label
@export var label_games : Label
@export var label_pigs : Label
@export var label_ratio : Label


func _ready():
	if not Global.is_logged_in:
		return
	
	# Infos du joueur
	var player = Global.get_all_player_data()
	$Profil/pseudo.text = player.pseudo
	
	Utile.load_profil_picture(player.image, $Profil/image)
	
	API.pull_list_dominos()
	load_stats()

	btn_create.connect("pressed", _on_start_pressed)
	btn_join.connect("pressed", _on_join_pressed)
	btn_disconnect.connect("pressed", _on_disconnect_pressed)
	

func _on_start_pressed():
	Utile.changeScene("create_game")

func _on_join_pressed():
	Utile.changeScene("liste_sessions")
	
func _on_disconnect_pressed():
	Global.reset_player()
	Utile.changeScene("principal")

func load_stats():
	var stats = await API.load_player_stats()
	label_wins.text = "Parties gagnées : " + str(stats.wins)
	label_games.text = "Parties disputées : " + str(stats.games)
	label_pigs.text = "Cochons : " + str(stats.pigs)
	var ratio = (stats.wins/stats.games) if stats.games > 0 else 0
	label_ratio.text = "Ratio : " + str(ratio) + " (Victoires/Parties)"
