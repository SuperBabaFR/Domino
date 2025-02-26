extends Control

@export var btn_leave : Button
@export var btn_start : Button
@export var btn_ready : Button

var is_ready: bool = false
const action_path = "session."
var my_profil: Node
var player_count = 0

func _ready():
	btn_leave.connect("pressed", _on_btn_leave_press)
	btn_start.connect("pressed", _on_start_game)
	btn_ready.connect("pressed", _set_ready_statut)
	
	Websocket.session_player_statut.connect(_update_statut)
	Websocket.session_player_leave.connect(_update_statut)
	
	Websocket.connect_to_websocket()
	
	for i in range(1,5):
		get_node("P"+str(i)).visible = false
	load_players_info()


func load_players_info():
	var players = Global.get_all_players_infos()
	var my_pseudo = Global.get_info("player", "pseudo")
	
	player_count = 1	
	for player in players:
		var pseudo = player.pseudo
		var image = Utile.load_profil_picture(player.image)
		var profil_node = get_node("P"+str(player_count))
		
		profil_node.load_player_profile(
			pseudo, 
			image, 
			player.hote, 
			player.statut
		)
		
		if my_pseudo == pseudo:
			my_profil = profil_node
		
		player_count += 1

func _on_btn_leave_press():
	var body = {"session_id": Global.session_infos.session_id}
	var response = await API.makeRequest("kill", "", body)
	
	if response.response_code == HTTPClient.RESPONSE_OK:
		Global.clear_session_data()
		Websocket.socket.close()
		Utile.changeScene("home_menu")
	else:
		print(body.message)
	
func _on_start_game():
	var body = {"session_id": Global.session_infos.session_id}
	var response = await API.makeRequest("start", "", body)
	
	if response.response_code == HTTPClient.RESPONSE_CREATED:
		var data = response.body.data
		Global.set_game_data(data)
	else:
		print("Partie non créée : ", response.body)

func _set_ready_statut():
	is_ready = ! is_ready
	
	var statut_id = 7 if is_ready else 6
	
	var statut = {
		"action": action_path + "player_statut", 
		"data": {
			"statut" : str(statut_id)
		}}
	
	if ! Websocket.send_json(statut):
		is_ready = ! is_ready
		print("Le statut n'a pas pu être changé")
		return
	
	btn_ready.text = "Retirer Prêt" if is_ready else "Mettre Prêt"

func _update_statut(data):
	for i in range(1,5):
		var profil_node = get_node("P"+str(i))
		
		if profil_node.lab_pseudo.text != data.player:
			continue
		
		profil_node.update_statut(data.statut)

func _on_player_leave(data):
	for i in range(1,5):
		var profil_node = get_node("P"+str(i))
		
		if profil_node.lab_pseudo.text != data.player:
			continue
		
	player_count -= 1
		
