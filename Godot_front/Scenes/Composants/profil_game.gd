extends VBoxContainer

@export var lab_pseudo: Label 
@export var texture_image: TextureRect
@export var border_color: PanelContainer
var panel: StyleBoxFlat

@export var domino_count: BoxContainer


func _ready():
	panel = preload("res://theme/panel/profil_game.tres")


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
	var domino_hand = preload("res://Scenes/Composants/hand_domino.tscn")
	for i in range(1, count+1):
		domino_count.add_child(domino_hand.instantiate())
