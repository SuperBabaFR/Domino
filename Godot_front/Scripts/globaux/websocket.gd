extends Node

# URL du websocket
const websocket_url = "wss://" + API.URL
# Crée le client websocket
var socket = WebSocketPeer.new()

func _ready():
	socket.connect_to_url("wss://ws.postman-echo.com/raw")

func _process(delta):
	socket.poll()
	var state = socket.get_ready_state()
	if state == WebSocketPeer.STATE_OPEN:
		while socket.get_available_packet_count():
			var new_packet = socket.get_packet()
			print("Packet: ", new_packet)
			print("message : ", new_packet.get_string_from_utf8())
	elif state == WebSocketPeer.STATE_CLOSING:
		# Keep polling to achieve proper close.
		pass
	elif state == WebSocketPeer.STATE_CLOSED:
		var code = socket.get_close_code()
		var reason = socket.get_close_reason()
		print("WebSocket closed with code: %d, reason %s. Clean: %s" % [code, reason, code != -1])
		set_process(false) # Stop processing.
