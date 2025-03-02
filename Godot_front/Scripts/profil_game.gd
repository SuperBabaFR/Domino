extends VBoxContainer

@export var lab_pseudo: Label 
@export var texture_image: TextureRect
@export var border_color: PanelContainer
@export var reflexion_time: ProgressBar
@export var player_time_end: Timer
@export var reflexion_container: BoxContainer
var panel: StyleBoxFlat

@export var domino_count: BoxContainer
var domino_hand = preload("res://Scenes/Composants/hand_domino.tscn")

func _ready():
	panel = preload("res://theme/panel/profil_game.tres")
	#show_dominos_count(7)
	#update_statut("actif")
	player_time_end.timeout.connect(reflexion_time_end)


func _process(delta):
	reflexion_time.value = player_time_end.time_left

func load_player_profile(pseudo, image):
	lab_pseudo.text = pseudo
	texture_image.texture = image
	texture_image.queue_redraw()

func update_statut(statut):
	if statut == "":
		return
	
	var color = Color.GREEN
		
	if statut.contains("not"):
		color = Color.RED
	elif statut.contains("afk"):
		color = Color.ORANGE		
	elif statut.contains("offline"):
		color = Color.BLACK

	panel.border_color = color
	border_color.add_theme_stylebox_override("panel", panel)

func show_dominos_count(count: int):
	for i in range(1, count+1):
		var domino = domino_hand.instantiate()
		domino.load_texture()
		domino_count.add_child(domino)

func activate_time_reflexion(time_end: String):
	var my_time = Time.get_datetime_dict_from_system(true)
	var reflexion_end_time = Time.get_datetime_dict_from_datetime_string(time_end, false)
	
	# Convertit les dictionnaires en timestamps (secondes depuis 1970)
	var my_timestamp = Time.get_unix_time_from_datetime_dict(my_time)
	var reflexion_end_timestamp = Time.get_unix_time_from_datetime_dict(reflexion_end_time)

	
	# Calcul de la différence en secondes
	var remaining_time = reflexion_end_timestamp - my_timestamp

	# Assurer que la durée est positive
	remaining_time = max(remaining_time, 0)
	
	
	reflexion_container.modulate = Color.WHITE
	reflexion_time.max_value = remaining_time
	player_time_end.wait_time = remaining_time
	set_process(true)
	player_time_end.start()


func reflexion_time_end():
	reflexion_container.modulate = Color.TRANSPARENT
	set_process(false)
	
