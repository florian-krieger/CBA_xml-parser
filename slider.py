def slider_ids(item):
	if item == "Gartenarbeit":
		slider_buttons = {"$335515688149300": "slider1_minus",
						 "$335515688151100":  "slider1_plus",
						  "$335515688154100": "slider2_minus",
						  "$335515688152600": "slider2_plus",
						  "$335515688155600": "slider3_minus",
						  "$335515688157200": "slider3_plus"}


	elif item == "Handballtraining":
		slider_buttons = {"$284335454203000": "slider1_minus",
						  "$284335454204400": "slider1_plus",
						  "$284335454205200": "slider2_minus",
						  "$284335454205800":  "slider2_plus",
						  "$284335454206400":  "slider3_minus",
						  "$284335454207200":  "slider3_plus"}


	else:
		slider_buttons = dict()

	return slider_buttons


if __name__ == '__main__':
	a = slider_ids("Handballtraining")
	print(a)


	button =  "$284335454204400"
	if button in a:
		print(a.get(button))