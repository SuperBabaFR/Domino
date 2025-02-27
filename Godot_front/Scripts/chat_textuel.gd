extends Control


@export var input_msg : LineEdit
@export var list_msgs : RichTextLabel
@export var btn_send : Button
@export var btn_mute : Button
@export var channel_options : OptionButton

var channel : String
var mute: bool = false
var my_pseudo: String

var volume_on_icon
var volume_off_icon


func _ready():
	Websocket.chat_message.connect(_on_msg_received)
	
	volume_off_icon = preload("res://Assets/icons/dark_volume_off_icon.svg")
	volume_on_icon = preload("res://Assets/icons/dark_volume_on_icon.svg")
	
	input_msg.connect("text_submitted", _on_text_submitted)
	btn_mute.connect("toggled", _on_btn_mute_toggled)
	btn_send.connect("pressed", _on_btn_send_pressed)
	
	load_channels()

func load_channels():
	var players = Global.get_all_players_infos()
	my_pseudo = Global.get_info("player", "pseudo")
	for player in players:
		if player.pseudo == my_pseudo:
			continue
		channel_options.add_item(player.pseudo)
	
	channel_options.select(0)
	channel = channel_options.get_item_text(channel_options.get_selected_id())

func _on_text_submitted(new_text):
	if new_text == "":
		print("Aucun message")
		return
	send_msg(new_text)

func _on_btn_send_pressed():
	var message = input_msg.text
	print(message)
	if message == "":
		print("Aucun message")
		return
	send_msg(message)
	

func send_msg(message):
	channel = channel_options.get_item_text(channel_options.get_selected_id()).to_lower()
	print("channel selectionné : ", channel)
	print("message : ", message)
	
	var json = {
		"action": "chat_message",
		"data": {
			"channel": channel,
			"message": message
		}
	}
	
	if channel != "global":
		add_msg_to_list(my_pseudo, message, true)
	
	if Websocket.send_json(json):
		input_msg.clear()

func _on_msg_received(data):
	add_msg_to_list(data.sender, data.message, data.is_private)

	if not mute:
		pass # Jouer les notifs

func add_msg_to_list(pseudo, message, private: bool):
	var all_msg = "[b]" + pseudo + "[/b] : " + message + "\n"
	#var image = "[img=20x20][/img]"
	if private:
		all_msg = "[color=red]" + all_msg + "[/color]"
	
	list_msgs.append_text(all_msg)

func _on_btn_mute_toggled(toggled_on):
	mute = toggled_on
	btn_mute.icon = volume_off_icon if mute else volume_on_icon
