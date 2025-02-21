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
	pass

func _on_slider_nb_max_players_value_changed(value):
	lab_nb_max_player_value.text = str(slider_nb_max_player.value) + " Joueurs"

func _on_slider_reflexion_time_value_changed(value):
	lab_reflexion_time_value.text = str(slider_reflexion_time.value) + " Secondes"

func _on_btn_back_pressed():
	get_tree().change_scene_to_file("res://Scenes/home_menu.tscn")


func _on_btn_creer_pressed():
	var session_name = session_name.text
	var reflexion_time = slider_reflexion_time.value
	var max_players_count = slider_nb_max_player.value
	var definitive_leave = ragequit_penality.toggle_mode
	var is_public = is_public_game.toggle_mode
	
	var body = {
		"reflexion_time": reflexion_time, 
		"max_players_count": max_players_count, 
		"definitive_leave":definitive_leave, 
		"is_public":is_public
	}
	
	if session_name != "":
		body["session_name"] = session_name
	
	var json_body = JSON.stringify(body, "  ")
	
	print(json_body)
	
	Global.makeRequest("", json_body, self._on_session_created, )
	

func _on_session_created(result, response_code, headers, body):
	var json = JSON.new()
	json.parse(body.get_string_from_utf8())
	var response = json.get_data()

	print(response)
	#get_tree().change_scene_to_file("res://Scenes/home_menu.tscn")
