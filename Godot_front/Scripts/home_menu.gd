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

# Profil
@export var profil_picture : TextureRect
@export var lab_pseudo : Label


func _ready():
	if not Global.is_logged_in:
		return
	# Affiche le profil
	load_profil()
	# Charge les dominos si necessaire
	API.pull_list_dominos()
	# Charge les stats
	load_stats()
	# Nettoie les données de session
	Global.clear_session_data()

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
	label_wins.text = str(stats.wins)
	label_games.text = str(stats.games)
	label_pigs.text = str(stats.pigs)
	label_ratio.text = str(stats.games) + "/" + str(stats.wins)

func load_profil():
	# Infos du joueur
	var player = Global.get_all_player_data()
	var pseudo = player.pseudo
	var image = Utile.load_profil_picture(player.image)
	
	profil_picture.texture = image
	lab_pseudo.text = pseudo
	
