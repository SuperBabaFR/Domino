extends Node


# Changer de scène
func changeScene(scene_name: String):
	print("change de scene vers : ",scene_name)
	get_tree().change_scene_to_file("res://Scenes/" + scene_name + ".tscn")

# Charger les images de profil
func load_profil_picture(base64_str, texture_rect: TextureRect):
	var image = Image.new()
	
	if base64_str == null:
		image = Image.load_from_file("res://Assets/images/default_profil.jpg")
		texture_rect.texture = ImageTexture.create_from_image(image)
		print("Image par défaut")
		return
	
	var img_data = Marshalls.base64_to_raw(base64_str)
	var err = image.load_jpg_from_buffer(img_data)

	if err != OK:
		print("❌ Erreur lors du chargement de l'image :", err)
		return null

	# Appel statique correct pour Godot 4.x
	texture_rect.texture = ImageTexture.create_from_image(image)
	texture_rect.visible = true
	texture_rect.queue_redraw()
