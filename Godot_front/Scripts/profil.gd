extends Control

@export var lab_pseudo: Label 
@export var texture_image: TextureRect 
@export var texture_courone: TextureRect
# Scores
@export var lab_wins : Label
@export var lab_pigs : Label
# Statut 
@export var lab_statut: Label 
@export var icon_statut: TextureRect 


var icon_ready
var icon_not_ready
var icon_hote

func _ready() -> void:
	icon_not_ready = preload("res://Assets/icons/light_not_ready_icon.png")
	icon_ready = preload("res://Assets/icons/light_ready_icon.png")
	icon_hote = preload("res://Assets/icons/light_crown_icon.svg")

func load_player_profile(pseudo, image):
	lab_pseudo.text = pseudo
	texture_image.texture = image
	texture_image.queue_redraw()

func toggle_hote(pseudo: String, state: bool):
	if lab_pseudo.text == pseudo:
		texture_courone.texture = icon_hote if state else null

func update_statut(statut):
	if statut == "":
		lab_statut.visible = false
		return
	
	var statut_text = "Prêt"
		
	if statut.contains("not"):
		statut_text = "Pas prêt"
	elif statut.contains("afk"):
		statut_text = "AFK"
	elif statut.contains("offline"):
		statut_text = "Hors ligne"

	icon_statut.texture = icon_ready if statut.contains("is_ready") else icon_not_ready
	
	lab_statut.text = statut_text
	$image_pseudo/name/statut_container.visible = true

func set_scores(wins, pigs):
	lab_wins.text = str(wins)
	lab_pigs.text = str(pigs)
