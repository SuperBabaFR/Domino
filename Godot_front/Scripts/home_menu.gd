extends Control

func _ready():
	if not Global.is_logged_in:
		return
	
	# Infos du joueur
	var player = Global.get_all_player_data()
	$Profil/pseudo.text = player.pseudo
	
	load_player_picture(player.image)
	
	Global.pull_list_dominos()
	load_stats()

	$CreateBtn.connect("pressed", _on_start_pressed)
	$JoinBtn.connect("pressed", _on_join_pressed)
	$DisconnectBtn.connect("pressed", _on_disconnect_pressed)
	

func _on_start_pressed():
	Global.changeScene("create_game")

func _on_join_pressed():
	Global.changeScene("listeSessions")
	
func _on_disconnect_pressed():
	Global.reset_player()
	Global.changeScene("principal")
	
func load_player_picture(base64_str: String):
	if base64_str == null:
		print("Pas d'image")
		return
	# Supprime le "b'" au début et "'" à la fin si présent
	base64_str = base64_str.strip_edges()  # Supprime les espaces et apostrophes

	# Vérifie s'il commence par "b'" et enlève ce préfixe
	if base64_str.begins_with("b'") or base64_str.begins_with('b"'):
		base64_str = base64_str.substr(2, base64_str.length() - 3)  # Supprime les b' et '	
	
	var image = Image.new()
	var img_data = Marshalls.base64_to_raw(base64_str)

	var err = ERR_PARSE_ERROR
	if base64_str.begins_with("/9j/"):  # JPEG
		err = image.load_jpg_from_buffer(img_data)
	else:  # PNG
		err = image.load_png_from_buffer(img_data)

	if err != OK:
		print("❌ Erreur lors du chargement de l'image :", err)
		return null

	# Appel statique correct pour Godot 4.x
	$Profil/image.texture = ImageTexture.create_from_image(image)
	$Profil/image.visible = true
	$Profil/image.queue_redraw()

func load_stats():
	var stats = await Global.load_player_stats()
	$wins.text = "Parties gagnées : " + str(stats.wins)
	$games.text = "Parties disputées : " + str(stats.games)
	$pig_count.text = "Cochons : " + str(stats.pigs)
	var ratio = (stats.wins/stats.games) if stats.games > 0 else 0
	$ratio.text = "Ratio : " + str(ratio) + " (Victoires/Parties)"
