extends Control

# Lines edit
@export var pseudo : LineEdit
@export var mdp : LineEdit

# Boutons
@export var btn_connect : Button 
@export var btn_inscription : Button 

func _ready():
	btn_inscription.connect("pressed", _on_Inscription_pressed)
	btn_connect.connect("pressed", _on_connexion_pressed) 

# Called every frame. 'delta' is the elapsed time since the previous frame.
func _on_connexion_pressed():
	if pseudo.text == "" and mdp.text == "":  
		print("Veuillez remplir tous les champs ") # Afficher le message à l'utilisateur a la place du print
		return
	
	var json = JSON.stringify({"pseudo": pseudo.text.strip_edges(), "password": mdp.text.strip_edges()})
	var response = await API.makeRequest("login", json)
	
	var response_code = response.response_code
	var body = response.body
	
	if response_code == 200:
		API.set_tokens(body.data)
		Global.set_player_data(body.data)
		Utile.changeScene("home_menu")
	else:
		print(body.message) #Afficher le message à l'utilisateur a la place du print


func _on_Inscription_pressed():
	Utile.changeScene("inscription")
