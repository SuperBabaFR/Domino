extends Control

@export var slider_reflexion_time: Slider
@export var slider_nb_max_player: Slider
@export var btn_update: Button
@export var btn_cancel: Button
@export var lab_nb_max_player_value: Label
@export var lab_reflexion_time_value: Label
@export var ragequit_penality: CheckButton
@export var is_public_game: CheckButton
@export var session_name: LineEdit
@export var list_players: OptionButton

func _ready():
	slider_reflexion_time.value_changed.connect(_on_slider_reflexion_time_value_changed)
	slider_nb_max_player.value_changed.connect(_on_slider_nb_max_players_value_changed)
	btn_cancel.pressed.connect(_on_btn_cancel_pressed)
	btn_update.pressed.connect(update_session)
	
	visibility_changed.connect(load_data)
	
func load_data():
	var my_pseudo = Global.get_info("player", "pseudo")
	
	session_name.text = Global.get_info("session", "session_name")
	
	slider_nb_max_player.value = Global.get_info("session", "max_players_count")
	lab_nb_max_player_value.text = str(slider_nb_max_player.value)
	
	slider_reflexion_time.value = Global.get_info("session", "reflexion_time")
	lab_reflexion_time_value.text = str(slider_reflexion_time.value) + "s"
	
	is_public_game.button_pressed = type_convert(Global.get_info("session", "is_public"), TYPE_BOOL)
	ragequit_penality.button_pressed = type_convert(Global.get_info("session", "definitive_leave"), TYPE_BOOL)
	
	var players = Global.get_all_players_infos()
	var i = 0
	
	list_players.clear()
	
	for player in players:
		list_players.add_item(player.pseudo)
		if my_pseudo == player.pseudo:
			list_players.select(i)
		i += 1
	
	

func update_session():
	var json = {
		"session_id": Global.get_info("session", "session_id"),
		"session_name": session_name.text,
		"hote_pseudo": list_players.get_item_text(list_players.get_selected_id()),
		"reflexion_time": slider_reflexion_time.value, 
		"max_players_count": slider_nb_max_player.value, 
		"definitive_leave": ragequit_penality.button_pressed, 
		"is_public": is_public_game.button_pressed
	}
	
	json = JSON.stringify(json, "  ")
	print("data_send : ",json)
	
	var response = await API.makeRequest("update", json)
	
	print(response.body)
	_on_btn_cancel_pressed()


func _on_slider_nb_max_players_value_changed(value):
	lab_nb_max_player_value.text = str(slider_nb_max_player.value)

func _on_slider_reflexion_time_value_changed(value):
	lab_reflexion_time_value.text = str(slider_reflexion_time.value) + "s"

func _on_btn_cancel_pressed():
	visible = false
