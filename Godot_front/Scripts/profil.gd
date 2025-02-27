extends Control

var is_hote = false
@export var lab_pseudo: Label 
@export var lab_statut: Label 
@export var texture_image: TextureRect 
@export var texture_courone: TextureRect 
@export var domino_count: VBoxContainer 

var parent_name: String

func _ready() -> void:
	visible = false
	parent_name = get_parent().name
	

func load_player_profile(pseudo, image):
	lab_pseudo.text = pseudo
	texture_image.texture = image
	texture_image.queue_redraw()
	visible = true

func toggle_hote(pseudo):
	if lab_pseudo.text == pseudo:
		is_hote = !is_hote
		texture_courone.visible = is_hote

func update_statut(statut):
	if statut == "":
		lab_statut.visible = false
		return
	var color = Color.GREEN
		
	if statut.contains("not"):
		color = Color.RED
		statut = "Pas prêt"
	elif statut.contains("afk"):
		color = Color.ORANGE		
		statut = "AFK"
	elif statut.contains("offline"):
		color = Color.BLACK
		statut = "Hors ligne"
	else:
		statut = "Prêt"
	
	lab_statut.text = statut
	lab_statut.add_theme_color_override("font_color", color)
	lab_statut.visible = true

func leave_player():
	visible = false

func show_dominos_count(count: int):
	var domino_hand = preload("res://Scenes/Composants/hand_domino.tscn")
	for i in range(1, count+1):
		domino_count.add_child(domino_hand.instantiate())
