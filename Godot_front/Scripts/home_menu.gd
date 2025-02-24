extends Control

func _ready():
	if not Global.is_logged_in:
		return
	
	# Infos du joueur
	var player = Global.get_all_player_data()
	$Profil/pseudo.text = player.pseudo
	
	Utile.load_profil_picture(player.image, $Profil/image)
	
	API.pull_list_dominos()
	load_stats()

	$CreateBtn.connect("pressed", _on_start_pressed)
	$JoinBtn.connect("pressed", _on_join_pressed)
	$DisconnectBtn.connect("pressed", _on_disconnect_pressed)
	

func _on_start_pressed():
	Utile.changeScene("create_game")

func _on_join_pressed():
	Utile.changeScene("listeSessions")
	
func _on_disconnect_pressed():
	Global.reset_player()
	Utile.changeScene("principal")

func load_stats():
	var stats = await API.load_player_stats()
	$wins.text = "Parties gagnées : " + str(stats.wins)
	$games.text = "Parties disputées : " + str(stats.games)
	$pig_count.text = "Cochons : " + str(stats.pigs)
	var ratio = (stats.wins/stats.games) if stats.games > 0 else 0
	$ratio.text = "Ratio : " + str(ratio) + " (Victoires/Parties)"
