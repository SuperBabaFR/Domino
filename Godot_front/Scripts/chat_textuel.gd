extends Control


var channel = "global"
@export var input_msg : LineEdit
@export var list_msgs : RichTextLabel


func _ready():
	Websocket.chat_message.connect(_on_msg_received)

func _on_input_msg_text_submitted(new_text):
	if new_text == "":
		return
	
	var message = new_text
	print("message : ", message)
	
	var json = {
		"action": "chat_message",
		"data": {
			"channel": channel,
			"message": message
		}
	}
	
	if Websocket.send_json(json):
		input_msg.clear()
	

func _on_msg_received(data):
	var player = Global.get_player_info(data.sender)
	
	var image = "[img=20x20][/img]"
	var pseudo = "[b]" + player.pseudo + "[/b]"
	
	#list_msgs.append_text(image)
	list_msgs.append_text(pseudo + " : ")
	list_msgs.append_text(data.message + "\n")
