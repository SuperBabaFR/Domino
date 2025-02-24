extends Control

@onready var file_dialog = $FileDialog
@onready var texture_rect = $TextureRect
@onready var button_import = $ButtonImport
@onready var button_inscrire = $ButtonInscrire
@onready var pseudo = $LineEditPseudo
@onready var mdp = $LineEditMdp
@onready var button_principal = $ButtonPrincipal  
@onready var button_connect = $ButtonConnect  

var selected_image_path = ""  # Stocke le chemin de l’image sélectionnée
var image_base64 = ""  # Stocke l’image convertie en Base64

const API_URL = "http://localhost:8000/signup"  

func _ready():
	# Connexion des boutons
	button_import.pressed.connect(_on_import_image_pressed)
	button_inscrire.pressed.connect(_on_inscription_pressed)
	
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
	
	# Convertir en Base64
	image_base64 = image_to_base64(image)
	print(image_base64)
	
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
	if pseudo.text == "" and mdp.text == "":
		print("remplir tous les champs")
		
	var body = {"pseudo": pseudo.text, "password": mdp.text}
	
	if image_base64 != "":
		body["image"] = image_base64
	
	var json_body = JSON.stringify(body)
	
	var response = await API.makeRequest("signup", json_body)
	# Gestion de la réponse de l'API
	var response_code = response.response_code
	body = response.body
	
	if response.response_code == 201:
		API.set_tokens(body.data)
		Global.set_player_data(body.data)
		Utile.changeScene("home_menu")
	else:
		print(body.message)

# Bouton qui renvoie vers le formulaire de connexion
func _on_ButtonConnect_pressed():
	Utile.changeScene("connexion")

# Bouton qui renvoie vers la page principale
func _on_ButtonPrincipal_pressed():
	Utile.changeScene("principal")
