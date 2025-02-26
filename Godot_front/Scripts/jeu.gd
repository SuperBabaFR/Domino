extends Control


func _ready():
	Websocket.game_someone_played.connect(someone_play)
	Websocket.game_someone_pass.connect(someone_pass)

func someone_play(data: Dictionary):	
	Global.update_game_data(data)
	print("domino joué : ", data.domino)
	print("joué à : ", data.side)
	
func someone_pass(data: Dictionary):
	Global.update_game_data(data)
