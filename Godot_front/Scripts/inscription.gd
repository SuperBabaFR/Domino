extends Control

@onready var file_dialog = $FileDialog
@onready var texture_rect = $TextureRect
@onready var button_import = $ButtonImport
@onready var button_inscrire = $ButtonInscrire
@onready var line_edit_pseudo = $LineEditPseudo
@onready var line_edit_mdp = $LineEditMdp
@onready var button_principal = $ButtonPrincipal  
@onready var button_connect = $ButtonConnect  

var selected_image_path = ""  # Stocke le chemin de l’image sélectionnée
var image_base64 = ""  # Stocke l’image convertie en Base64

const API_URL = "http://localhost:8000/signup"  

func _ready():
	print("🔍 Vérification des nœuds...")
	file_dialog.hide()

	# Vérification des nœuds
	if not file_dialog or not texture_rect:
		print("❌ ERREUR : 'Window' ou ses enfants sont introuvables !")
		return
	if not button_import or not button_inscrire:
		print("❌ ERREUR : Un des boutons est introuvable !")
		return
	if not line_edit_pseudo or not line_edit_mdp:
		print("❌ ERREUR : Un champ de saisie est introuvable !")
		return

	# Configuration du FileDialog
	file_dialog.visible = false
	file_dialog.file_mode = FileDialog.FILE_MODE_OPEN_FILE
	file_dialog.access = FileDialog.ACCESS_FILESYSTEM
	file_dialog.filters = PackedStringArray(["*.png", "*.jpg", "*.jpeg"])
	file_dialog.title = "Sélectionner une image"
	file_dialog.size = Vector2(600, 400)
	file_dialog.always_on_top = true

	# Connexion des boutons
	button_import.pressed.connect(_on_import_image_pressed)
	button_inscrire.pressed.connect(_on_inscription_pressed)
	file_dialog.file_selected.connect(_on_file_dialog_file_selected)
	
	# Connexion des boutons de navigation
	button_connect.pressed.connect(_on_ButtonConnect_pressed)
	button_principal.pressed.connect(_on_ButtonPrincipal_pressed)

# Ouvre la boîte de dialogue pour sélectionner une image
func _on_import_image_pressed():
	if file_dialog:
		print("📂 Sélection de l’image...")
		file_dialog.popup_centered()

# Charge et affiche l’image sélectionnée + Convertit en Base64
func _on_file_dialog_file_selected(path):
	var image = Image.new()
	var err = image.load(path)

	if err != OK:
		print("❌ ERREUR : Impossible de charger l’image !")
		return

	# Redimensionne à 300x300 px pour optimiser la taille
	image.resize(300, 300)
	
	# Convertir en Base64
	image_base64 = image_to_base64(image)
	
	# Appliquer l’image sur TextureRect
	var texture = ImageTexture.new()
	texture.set_image(image)
	texture_rect.texture = texture
	selected_image_path = path

# Convertir l’image en Base64
func image_to_base64(img: Image) -> String:
	var buffer = img.save_jpg_to_buffer(0.8)  # Compression JPEG 80%
	return Marshalls.raw_to_base64(buffer)

# Fonction d'inscription
func _on_inscription_pressed():
	#if $LineEditPseudo.text != ""  and $LineEditMdp.text != "":
		#print(" mdp ou pseudo requis")
	#var pseudo = line_edit_pseudo.text.strip_edges()
	#var mdp = line_edit_mdp.text.strip_edges()
#
	## Vérifications des champs
	#if pseudo == "" or mdp == "":
		#print("❌ ERREUR : Pseudo et mot de passe sont requis !")
		#return
	#if mdp.length() < 8 or mdp.length() > 20:
		#print("❌ ERREUR : Le mot de passe doit contenir entre 8 et 20 caractères.")
		#return
		
	if $LineEditPseudo.text != "" and $LineEditMdp.text != "":
		
		var body = {"pseudo": $LineEditPseudo.text, "password": $LineEditMdp.text}
		if image_base64 != "":
			body["image"] = image_base64
		var json_body = JSON.stringify(body)
		
		Global.makeRequest("signup", self._on_request_completed, json_body)
	else:
		print("remplir tous les champs")
		# Création du JSON pour l'API
	#var json_data = {
		#"pseudo": pseudo,
		#"mdp": mdp,
		#"image": image_base64
	#}
	#
	#var body = JSON.stringify(json_data)
	#print("🔍 Données envoyées :", body)

	# Envoi de la requête HTTP
	#var http_request = HTTPRequest.new()
	#add_child(http_request)
	#http_request.request_completed.connect(_on_request_completed)
#
	#var headers = ["Content-Type: application/json; charset=utf-8"]
	#var err = http_request.request(API_URL, headers, HTTPClient.METHOD_POST, body)

	#if err != OK:
		#print("❌ ERREUR : Impossible d'envoyer la requête !")

# Gestion de la réponse de l'API
func _on_request_completed(result, response_code, headers, body):
	var json = JSON.new()
	json.parse(body.get_string_from_utf8())
	var response = json.get_data()

		#get_tree().change_scene_to_file("res://connexion.tscn")
	print(response.message)
	print(response_code) #Afficher le message à l'utilisateur a la place du print
	
	# Bouton qui renvoie vers le formulaire de connexion
func _on_ButtonConnect_pressed():
	print("Bouton Connect pressé")
	get_tree().change_scene_to_file("res://Scenes/connexion.tscn")

# Bouton qui renvoie vers la page principale
func _on_ButtonPrincipal_pressed():
	print("Bouton Principal pressé")
	get_tree().change_scene_to_file("res://Scenes/principal.tscn")
		
	#print("🔄 Code réponse :", response_code)
	#print("🔄 Réponse brute :", body.get_string_from_utf8())
#
	#var response = JSON.parse_string(body.get_string_from_utf8())
#
	#if response_code == 201:
		#print("✅ Inscription réussie :")
		#
	#elif response_code == 400:
		#if response and "message" in response:
			#print("❌ ERREUR : ", response["message"])
		#else:
			#print("❌ ERREUR 400 : Mauvaise requête -", body.get_string_from_utf8())
	#else:
		#print("❌ ERREUR Serveur :", response_code, body.get_string_from_utf8())
