extends Control

@export var slider_reflexion_time: Slider
@export var slider_nb_max_player: Slider
@export var btn_creer: Button
@export var lab_nb_max_player_value: Label
@export var lab_reflexion_time_value: Label
@export var ragequit_penality: CheckButton
@export var is_public_game: CheckButton
@export var session_name: LineEdit

var json_body

func _ready():
	session_name.text = "La session de " + Global.get_info("player", "pseudo")
	pass


func create_session():
	var body = {
		"session_name": session_name.placeholder_text,
		"reflexion_time": slider_reflexion_time.value, 
		"max_players_count": slider_nb_max_player.value, 
		"definitive_leave": ragequit_penality.toggle_mode, 
		"is_public": is_public_game.toggle_mode
	}
	
	if session_name.text != "":
		body["session_name"] = session_name
	
	json_body = JSON.stringify(body, "  ")
	print(json_body)
	Global.makeRequest("create", json_body)


func _on_session_created(result, response_code, headers, body):
	var json = JSON.new()
	json.parse(body.get_string_from_utf8())
	var response = json.get_data()
	
	if response_code == 201:
		Global.set_session_data(response.data, true)
		Global.changeScene("lobby")
	elif response_code == 401:
		Global.refreshToken()
		while not Global.is_token_fresh:
			pass
		# On relance la méthode quand le token est frais
		create_session()
	
	#get_tree().change_scene_to_file("res://Scenes/home_menu.tscn")


func _on_slider_nb_max_players_value_changed(value):
	lab_nb_max_player_value.text = str(slider_nb_max_player.value) + " Joueurs"

func _on_slider_reflexion_time_value_changed(value):
	lab_reflexion_time_value.text = str(slider_reflexion_time.value) + " Secondes"

func _on_btn_back_pressed():
	Global.changeScene("home_menu")

func _on_btn_creer_pressed():
	self.create_session()
