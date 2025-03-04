extends VBoxContainer

@export var lab_pseudo: Label 
@export var pts_restants: Label 
@export var texture_image: TextureRect
@export var border_color: PanelContainer
@export var reflexion_time: ProgressBar
@export var player_time_end: Timer
@export var reflexion_container: BoxContainer
var panel: StyleBoxFlat

@export var pseudo_container: VBoxContainer

@export var dominoes: BoxContainer
var domino_hand = preload("res://Scenes/Composants/hand_domino.tscn")

func _ready():
	panel = preload("res://theme/panel/profil_game.tres")
	player_time_end.timeout.connect(reflexion_time_end)


func _process(_delta):
	reflexion_time.value = player_time_end.time_left

func load_player_profile(pseudo, image):
	lab_pseudo.text = "VOUS" if pseudo == Global.get_info("player", "pseudo") else pseudo
	texture_image.texture = image
	texture_image.queue_redraw()

func update_statut(statut):
	if statut == "":
		return
	
	var color = Color.GREEN
	
	if statut.contains("afk"):
		color = Color.ORANGE		
	elif statut.contains("offline"):
		color = Color.RED

	panel.border_color = color
	border_color.add_theme_stylebox_override("panel", panel)

func show_dominos_count(count: int):
	
	var children = dominoes.get_children()
	for child in children:
		child.free()
	
	for i in range(0, count):
		var domino = domino_hand.instantiate()
		domino.load_texture()
		dominoes.add_child(domino)

func show_list_dominos(list):
		
	var children = dominoes.get_children()
	for child in children:
		child.free()
	
	for id in list:
		var domino = domino_hand.instantiate()
		domino.load_texture(str(id))
		dominoes.add_child(domino)


func activate_time_reflexion(time_end: String):
	var my_time = Time.get_datetime_dict_from_system(true)
	var reflexion_end_time = Time.get_datetime_dict_from_datetime_string(time_end, false)
	
	# Convertit les dictionnaires en timestamps (secondes depuis 1970)
	var my_timestamp = Time.get_unix_time_from_datetime_dict(my_time)
	var reflexion_end_timestamp = Time.get_unix_time_from_datetime_dict(reflexion_end_time)
	
	# Calcul de la différence en secondes
	var remaining_time = reflexion_end_timestamp - my_timestamp

	# Assurer que la durée est positive
	remaining_time = max(remaining_time, 1)
	
	reflexion_container.modulate = Color.WHITE
	reflexion_time.max_value = remaining_time
	player_time_end.wait_time = remaining_time
	set_process(true)
	player_time_end.start()

func hide_pseudo(value):
	pseudo_container.visible = value

func reflexion_time_end():
	reflexion_container.modulate = Color.TRANSPARENT
	set_process(false)

func force_end_reflexion_time():
	reflexion_container.modulate = Color.TRANSPARENT
	player_time_end.stop()
	set_process(false)
