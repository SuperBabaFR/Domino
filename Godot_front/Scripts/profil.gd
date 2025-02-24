extends Control


func _ready() -> void:
	Utile.load_profil_picture(null, $image)
	$pseudo.text = "pseudo"
