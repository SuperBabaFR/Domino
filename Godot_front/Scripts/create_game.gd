extends Control

@export var session_name: LineEdit
@export var slider_reflexion_time: Slider
@export var lab_reflexion_time_value: Label
@export var ragequit_penality: CheckButton

@export var btn_creer: Button
@export var btn_reset: Button


@export var btn_2: Button
@export var btn_3: Button
@export var btn_4: Button

@export var btn_public: Button
@export var btn_privee: Button


var is_public = false
var nombre_joueurs = 4

func _ready():
	session_name.text = "La session de " + Global.get_info("player", "pseudo")
	
	btn_2.pressed.connect(btn_2_presssed)
	btn_3.pressed.connect(btn_3_presssed)
	btn_4.pressed.connect(btn_4_presssed)
	
	btn_public.pressed.connect(btn_pb_presssed)
	btn_privee.pressed.connect(btn_pv_presssed)
	
	btn_reset.pressed.connect(_on_pressed_btn_reset)
	
	btn_4.button_pressed = true
	btn_privee.button_pressed = true
	
	
	

func create_session():
	var body = {
		"session_name": "",
		"reflexion_time": slider_reflexion_time.value, 
		"max_players_count": nombre_joueurs, 
		"definitive_leave": ragequit_penality.button_pressed, 
		"is_public": is_public
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


func btn_2_presssed():
	btn_3.button_pressed = false
	btn_4.button_pressed = false
	nombre_joueurs = 2
	
func btn_3_presssed():
	btn_2.button_pressed = false
	btn_4.button_pressed = false
	nombre_joueurs = 3
	
func btn_4_presssed():
	btn_2.button_pressed = false
	btn_3.button_pressed = false
	nombre_joueurs = 4

func btn_pb_presssed():
	btn_privee.button_pressed = false
	is_public = true
	
func btn_pv_presssed():
	btn_public.button_pressed = false
	is_public = false

func _on_pressed_btn_reset():
	session_name.text = "La session de " + Global.get_info("player", "pseudo")
	
	btn_2.button_pressed = false
	btn_3.button_pressed = false
	btn_4.button_pressed = true
	nombre_joueurs = 4
	
	btn_privee.button_pressed = true
	btn_public.button_pressed = false
	
	slider_reflexion_time.value = 20
	
	ragequit_penality.button_pressed = false
	
	is_public = false


func _on_slider_reflexion_time_value_changed(value):
	lab_reflexion_time_value.text = str(slider_reflexion_time.value) + "s"

func _on_btn_back_pressed():
	Utile.changeScene("home_menu")

func _on_btn_creer_pressed():
	self.create_session()
