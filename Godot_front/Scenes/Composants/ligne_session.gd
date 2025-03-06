extends HBoxContainer

@export var s_name : Label
@export var hote : Label
@export var statut : Label
@export var joueurs : Label
@export var btn_rejoindre : Button

@onready var icon = preload("res://Assets/icons/light_lock_icon.svg")

func load_line(session_name, session_hote, p_statut, nb_j, public):
	s_name.text = session_name
	hote.text = "HÔTE : " + session_hote
	
	var color = Color.BLACK
	var statut_name = "No"
	
	match p_statut:
		"session.is_full":
			statut_name = "FULL"
			btn_rejoindre.disabled = true
			color = Color.RED
		"session.is_active":
			statut_name = "IN-GAME"
			btn_rejoindre.disabled = true
			color = Color.GRAY
		"session.is_open":
			statut_name = "OPEN"
			color = Color.GREEN
	
	statut.text = statut_name
	joueurs.text = nb_j
	
	statut.add_theme_color_override("font_color", color)
	joueurs.add_theme_color_override("font_color", color)
	
	if not public:
		btn_rejoindre.text = "PRIVATE"
		btn_rejoindre.disabled = true
		
