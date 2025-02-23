extends Control

func _ready():
	var data = Global.get_all_player_data()
	if not Global.is_logged_in:
		return
	#if data:
		#print(data)
	if data.image != null:
		var base64_string = data.image
		base64_string = clean_base64(base64_string)  # Nettoie la chaîne base64
		var image_texture = load_image_from_base64(base64_string)
		#print("🔍 Base64 reçu (50 premiers caractères) :", image_texture.substr(0, 50))
  
		$ProfileImage.texture = image_texture
		$ProfileImage.visible = true
		$ProfileImage.queue_redraw()

	$ProfileImage/Pseudo.text = data.pseudo

	$CreateBtn.connect("pressed", _on_start_pressed)
	$JoinBtn.connect("pressed", _on_join_pressed)
	$DisconnectBtn.connect("pressed", _on_disconnect_pressed)
	
	Global.pull_list_dominos()
	

func _on_start_pressed():
	get_tree().change_scene_to_file("res://Scenes/create_game.tscn")

func _on_join_pressed():
	get_tree().change_scene_to_file("res://Scenes/listeSessions.tscn")
	
func _on_disconnect_pressed():
	Global.reset_player()
	get_tree().change_scene_to_file("res://Scenes/principal.tscn")
	
func load_image_from_base64(base64_str: String) -> ImageTexture:
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
	var texture = ImageTexture.create_from_image(image)
	return texture



func clean_base64(base64_str: String) -> String:
	# Supprime le "b'" au début et "'" à la fin si présent
	base64_str = base64_str.strip_edges()  # Supprime les espaces et apostrophes

	# Vérifie s'il commence par "b'" et enlève ce préfixe
	if base64_str.begins_with("b'") or base64_str.begins_with('b"'):
		base64_str = base64_str.substr(2, base64_str.length() - 3)  # Supprime les b' et '

	# Vérifie s'il commence par "data:image"
	if base64_str.begins_with("data:image"):
		base64_str = base64_str.split(",")[1]  # Enlève "data:image/png;base64,"

	return base64_str
#func load_image_from_base64(base64_str: String) -> ImageTexture:
	#var image = Image.new()
	#var img_data = Marshalls.base64_to_raw(base64_str)  # Convertir le Base64 en données binaires
	#var err = image.load_png_from_buffer(img_data)  # Charger les données binaires en image
#
	#if err != OK or not image.is_valid():
		#print("❌ Erreur de décodage de l’image :", err)
		#return null
#
	#var texture = ImageTexture.new()
	#texture.create_from_image(image)
	#return texture
