'''
The kivy app that runs schedule creator 4
'''

from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager

class SM(ScreenManager):
	pass

class MainScreen(Screen):
	pass





class schedule_creatorApp(App):
	def build(self):
		return SM()

def main():
	schedule_creatorApp().run()


if __name__ == '__main__':
	main()