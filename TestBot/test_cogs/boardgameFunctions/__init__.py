from PIL import ImageFont
from random import randint
import re

# Constants
font = ImageFont.truetype('C:/WINDOWS/Fonts/segoeui.ttf', 36)

# Functions
def roll_dice(dice_str):
	ret = []
	dice_rolls = parse_dice_str(dice_str)
	for amount, dice in dice_rolls:
		for i in range(amount):
			ret.append(randint(1, dice))
	return ret

def parse_dice_str(dice_str):
	rolls = re.findall('(\d+)?d(4|6|8|12|20|100)', die)
	ret = []
	for amt, dice in rolls:
		if not amt:
			amt = 1
		if not dice:
			continue
		ret.append((int(amt), int(dice)))
	return ret


# Classes
