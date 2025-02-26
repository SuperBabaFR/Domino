extends Node

# URL du websocket
const websocket_url = "wss://" + API.URL + "/ws/session/"
# Crée le client websocket
var socket = WebSocketPeer.new()

# Signaux

# Session
signal session_player_join(data)
signal session_player_leave(data)
signal session_hote_leave(data)
signal session_player_statut(data)
signal session_update_infos(data)
# Début et fin de partie
signal session_start_game(data)
signal session_end_game(data)
# Partie
# Nouveau round
signal game_someone_mix_the_dominoes(data)
signal game_new_round(data)
# Le tour de quelqu'un
signal game_someone_played(data)
signal game_someone_pass(data)
# Ton tour
signal game_your_turn(data)
signal game_your_turn_no_match(data)
# Statuts de victoire
signal game_someone_win(data) 
signal game_blocked(data)
# Chat textuel
signal chat_message(data)

func _ready():
	set_process(false)

func connect_to_websocket():
	var session_id = Global.get_info("session", "session_id")
	var token = API.tokens.access_token
	
	print("token : ",token)
	print("session_id : ",session_id)
	
	var FULL_URL = websocket_url + "?session_id=" + str(session_id) + "&token=" + token
	
	print(FULL_URL)
	
	var err = 	socket.connect_to_url(FULL_URL)
	if err != OK:
		print("Unable to connect")
		set_process(false)
		return
	set_process(true)


func _process(delta):
	socket.poll()
	var state = socket.get_ready_state()
	if state == WebSocketPeer.STATE_OPEN:
		while socket.get_available_packet_count():
			var packet = socket.get_packet()
			var msg = packet.get_string_from_utf8()

			var json = JSON.parse_string(msg)
			if typeof(json) != TYPE_DICTIONARY:
				print("Message JSON invalide :", msg)
				continue

			var action: String = json.get("action", null)
			var data: Dictionary = json.get("data", {})
			if action == null:
				print("Pas de 'action' dans le message :", json)
				continue
			
			action = action.replace(".", "_")
			
			if self.has_signal(action):
				print("data : ", data)
				emit_signal(action, data)
			
			
	elif state == WebSocketPeer.STATE_CLOSING:
		# Keep polling to achieve proper close.
		pass
	elif state == WebSocketPeer.STATE_CLOSED:
		var code = socket.get_close_code()
		var reason = socket.get_close_reason()
		print("WebSocket closed with code: %d, reason %s. Clean: %s" % [code, reason, code != -1])
		Utile.changeScene("home_menu")
		set_process(false) # Stop processing.

func send_json(dict_data: Dictionary):
	var state = socket.get_ready_state()
	if state == WebSocketPeer.STATE_OPEN:
		var json_str = str(dict_data)
		socket.send_text(json_str)
		return true
	else:
		print("Impossible d'envoyer, WebSocket fermé :", dict_data)
		return false
