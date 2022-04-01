import re
import random
from telegram\
	import 	Update,\
					InlineKeyboardButton,\
					InlineKeyboardMarkup
from telegram.ext\
	import Updater,\
				 MessageHandler,\
				 Filters,\
				 CallbackContext,\
				 CallbackQueryHandler

messages = {
	"hello": re.compile("[Hh]ello|[Hh]i"),
	"bullsandcows": re.compile("^\\d$"),
	"my word": re.compile("^\\d\\d\\d\\d$")
}

games = {}

class Patern:
	def __init__(self, word, bulls, cows):
		self.word = word
		self.bulls = bulls
		self.cows = cows

class Game:
	def __init__(self, len_num):
		self.len_num = len_num
		self.num_set = []
		for x in range(0, 10 ** len_num):
			word = format(x, "0>{}".format(len_num))
			flag = True
			for letter in word:
				if word.count(letter) > 1:
					flag = False
					break
			if flag:
				self.num_set.append(word)
		self.paterns = []
		# 0 - f step, 1 - s step, 2 - running, 3 - bot win, 4 - user win, 5 - error
		self.stage = 0
		self.state = None
		self.my_word = self.num_set[self.__get_random_index()]

	def check_patern(self, word, patern):
		bulls = self.find_bulls(word, patern.word)
		cows = self.find_cows(word, patern.word)
		return bulls == patern.bulls and cows == patern.cows

	def find_bulls(self, word, patern_word):
		count = 0
		for (index, letter) in enumerate(word):
			if letter == patern_word[index]:
				count += 1
		return count

	def find_cows(self, word, patern_word):
		count = 0
		for (index, letter) in enumerate(word):
			for (index_p, letter_p)in enumerate(patern_word):
				if letter_p == letter and index != index_p:
					count += 1
					continue
		return count

	def update_num_set(self):
		new_list = []
		for (index, num) in enumerate(self.num_set):
			flag = True
			for patern in self.paterns:
				if not self.check_patern(num, patern):
					flag = False
					break
			if flag:
				new_list.append(num)
		self.num_set = new_list

	def move(self, patern, word):
		if patern.bulls == 4:
			self.stage = 3 # END GAME
		result = ""
		if self.stage == 0:
			self.stage += 1
			result = "1234"
		elif self.stage == 1:
			self.stage += 1
			self.paterns.append(patern)			
			result = "5678"
		else:
			self.paterns.append(patern)
			self.update_num_set()
			index = self.__get_random_index()
			if len(self.num_set) < 1:
				self.stage = 5 # END GAME
			result = self.num_set[index]
		u_result = self.user_move(word)
		self.state = {
			"word": result,
			"user_out": u_result
		}
		return self.state

	def __get_random_index(self):
		return random.randint(0, len(self.num_set) - 1) if len(self.num_set) > 1\
			else 0

	def user_move(self, word):
		if word == self.my_word:
			self.stage = 4 # END GAME
		if self.stage != 2:
			return ""
		bulls = self.find_bulls(word, self.my_word)
		cows = self.find_cows(word, self.my_word)
		return "Bulls: {}, Cows: {}".format(bulls, cows)

def message(update: Update, context: CallbackContext):
	if messages["hello"].match(update.message.text):
		keyboard = [
			[
				InlineKeyboardButton("Done", callback_data="1"),
				InlineKeyboardButton("Exit", callback_data="2")
			]
		]
		update.message.reply_text(
			"Let the game begin!\r\nMake a number without repetition.",
			reply_markup=InlineKeyboardMarkup(keyboard)
			)
	elif messages["bullsandcows"].match(update.message.text)\
	and games.get(update.effective_user.id) != None\
	and games[update.effective_user.id].state != None:
		if games[update.effective_user.id].state.get("bulls") == None:
			games[update.effective_user.id].state["bulls"] = int(update.message.text)
		elif games[update.effective_user.id].state.get("cows") == None:
			games[update.effective_user.id].state["cows"] = int(update.message.text)
			context.bot.send_message(
				chat_id=update.effective_chat.id,
				text="My word?"
				)
	elif  messages["my word"].match(update.message.text)\
	and games.get(update.effective_user.id) != None\
	and games[update.effective_user.id].state != None:
		p = Patern(
			games[update.effective_user.id].state["word"],
			games[update.effective_user.id].state["bulls"],
			games[update.effective_user.id].state["cows"],				
			)

		games[update.effective_user.id].move(
			p,
			update.message.text
			)
		if games[update.effective_user.id].stage == 3:
			context.bot.send_message(
				chat_id=update.effective_chat.id,
				text="I WIN!\r\nMy number is {}"\
					.format(games[update.effective_user.id].my_word)
				)
			del games[update.effective_user.id]
			return
		elif games[update.effective_user.id].stage == 4:
			context.bot.send_message(
				chat_id=update.effective_chat.id,
				text="You WIN!"
				)
			del games[update.effective_user.id]
			return
		elif games[update.effective_user.id].stage == 5:
			context.bot.send_message(
				chat_id=update.effective_chat.id,
				text="Something went wrong\r\nMy number is {}"\
					.format(games[update.effective_user.id].my_word)
				)
			del games[update.effective_user.id]
			return
		context.bot.send_message(
			chat_id=update.effective_chat.id,
			text=games[update.effective_user.id].state["user_out"]
			)
		context.bot.send_message(
			chat_id=update.effective_chat.id,
			text="Your word: {}?".format(games[update.effective_user.id].state["word"])
			)
	else:
		context.bot.send_message(
			chat_id=update.effective_chat.id,
			text="I don't understand you\r\nDid you say hello?^^"
			)

def button(update: Update, context: CallbackContext):
	update.callback_query.answer()
	if update.callback_query.data == "1":
		g = Game(4)
		games[update.effective_user.id] = g
		w = games[update.effective_user.id].move(Patern("", 0, 0), "")
		context.bot.send_message(
				chat_id=update.effective_chat.id,
				text="Your word: {}?".format(w["word"])
				)
	else:
		context.bot.send_message(
			chat_id=update.effective_chat.id,
			text="Bie! Have a nice day:*"
			)

if __name__ == "__main__":
	updater = Updater(
		token="TG_TOKEN",
		use_context=True
		)
	dispatcher = updater.dispatcher
	echo_handler = MessageHandler(Filters.text & (~Filters.command), message)
	dispatcher.add_handler(echo_handler)
	dispatcher.add_handler(CallbackQueryHandler(button))
	updater.start_polling()
