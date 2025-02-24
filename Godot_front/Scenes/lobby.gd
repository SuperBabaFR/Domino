extends Control


func _ready():
	
	
	
	for i in range(1, 5):
		var pseudo = get_node("P"+str(i)+"/pseudo")
		var image = get_node("P"+str(i)+"/image")
		pseudo.text = "Player " + str(i)
