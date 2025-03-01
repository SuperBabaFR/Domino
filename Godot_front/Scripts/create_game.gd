extends Control

@export var slider_reflexion_time: Slider
@export var slider_nb_max_player: Slider
@export var btn_creer: Button
@export var lab_nb_max_player_value: Label
@export var lab_reflexion_time_value: Label
@export var ragequit_penality: CheckButton
@export var is_public_game: CheckButton
@export var session_name: LineEdit

func _ready():
	session_name.text = "La session de " + Global.get_info("player", "pseudo")

func create_session():
	var body = {
		"session_name": "",
		"reflexion_time": slider_reflexion_time.value, 
		"max_players_count": slider_nb_max_player.value, 
		"definitive_leave": ragequit_penality.button_pressed, 
		"is_public": is_public_game.button_pressed
	}
	
	if session_name.text != "":
		body["session_name"] = session_name.text
	
	var json_body = JSON.stringify(body, "  ")
	print(json_body)
	
	var response = await API.makeRequest("create", json_body)
	
	if response.response_code == 201:
		Global.set_session_data(response.body.data, true)
		Utile.changeScene("lobby")
	else:
		print(response.body)


func _on_slider_nb_max_players_value_changed(value):
	lab_nb_max_player_value.text = str(slider_nb_max_player.value) + " Joueurs"

func _on_slider_reflexion_time_value_changed(value):
	lab_reflexion_time_value.text = str(slider_reflexion_time.value) + " Secondes"

func _on_btn_back_pressed():
	Utile.changeScene("home_menu")

func _on_btn_creer_pressed():
	self.create_session()
