shader_type canvas_item;

uniform sampler2D img_texture;

void fragment(){
	vec4 base_pixel = texture(TEXTURE, UV);
	vec4 texture_pixel = texture(img_texture, UV);
	base_pixel.a = texture_pixel.a;
	COLOR = base_pixel;
}