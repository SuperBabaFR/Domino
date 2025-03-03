extends TextureRect

var id = 0
var orientation = "double"

func _ready():
	#load_texture(5)
	pass
	

func load_texture(texture_id: int = 0, orientation_texture: String = "double"):
	self.id = texture_id
	self.orientation = orientation_texture
	
	var my_texture = load("res://Assets/images/Dominos/d" + str(id) + ".svg")
	var image = my_texture.get_image()
	custom_minimum_size = Vector2(45, 23)
	
	match orientation:
		"normal":
			pass
		"double":
			image.rotate_90(CLOCKWISE)
			custom_minimum_size = Vector2(23, 45)
		"inverse":
			image.flip_x()
	
	self.texture = ImageTexture.create_from_image(image)
