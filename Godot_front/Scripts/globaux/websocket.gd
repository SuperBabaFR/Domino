extends Node

# URL du websocket
const websocket_url = "wss://" + API.URL
# Crée le client websocket
var ws = WebSocketPeer.new()

func _ready():
	pass
	
	#set_process(false)
	#
	## 2) Connecte les signaux au script courant (ou un autre Node, au besoin)
	#ws.connect("connection_established", _on_connection_established)
	#ws.connect("connection_error", _on_connection_error)
	#ws.connect("connection_closed", _on_connection_closed)
	#ws.connect("data_received", _on_data_received)


func _on_connection_established():
	pass

func _on_connection_error():
	pass
