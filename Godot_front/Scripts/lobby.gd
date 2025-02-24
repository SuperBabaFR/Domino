extends Control


func _ready():
	$btn_leave.connect("pressed", _on_btn_leave_press)
	
	for i in range(1,5):
		get_node("P"+str(i)).visible = false
	load_players_info()


func load_players_info():
	var players = Global.get_all_players_infos()
	
	var player_count = 1	
	for player in players:
		var pseudo = get_node("P"+str(player_count)+"/pseudo")
		var image = get_node("P"+str(player_count)+"/image")
		
		pseudo.text = player.pseudo
		Utile.load_profil_picture(player.image, image)
		
		get_node("P"+str(player_count)).visible = true
		player_count += 1

func _on_btn_leave_press():
	var body = {"session_id": Global.session_infos.session_id}
	var response = await API.makeRequest("kill", "", body)
	
	if response.response_code == HTTPClient.RESPONSE_OK:
		Global.clear_session_data()
		Utile.changeScene("home_menu")
	else:
		print(body.message)
	
