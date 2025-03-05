extends Node

func play_sound(audioStreamMP3):
	$AudioStreamPlayer.stream = audioStreamMP3
	$AudioStreamPlayer.play()
