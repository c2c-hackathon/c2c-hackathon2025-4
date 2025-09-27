import logging
import queue
import threading
import time
import random
import typing
import random
from dataclasses import dataclass

import library
from matrix_button_led_controller import MatrixButtonLEDController

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
USE_LED_HAT = True

# #correct = [[0,0,0,0],[0,0,0,0], [0,0,0,0],[0,0,0,0]]
# COLORS = ["red", "blue", "gold", "green", "plum", "orchid", "cyan", "gray"]
# SOUNDS = [
#             "thunder2",
#             "fart_z",
#             "baby_x",
#             "slide_whistle_x",
#             "arrow2",
#             "phone_pay",
#             "bloop_x",
#             "car_horn_x",
#         ]#
# used = []

@dataclass
class ButtonInfo:
    color: str
    sound: str
    matched: bool


class Game:
    def __init__(self, button_pad: MatrixButtonLEDController):
        self.button_pad = button_pad
        self.button_pad.assign_button_events(self.when_pressed, self.when_held, self.when_released)
        self.buttons: typing.List[ButtonInfo] = []
        self.sounds: typing.List[str] = []
        self.colors: typing.List[str] = []
        self.speaker = library.speaker.Speaker()
        self.initialize_button_pad()
        self.started = False
        self.play_game = True
        self.queue = queue.Queue()
        self.last_pressed_index = None

    @property
    def correct_sound(self):
        """The sound that is played when player gets a pair"""
        # OPTIONAL: change this to a different sound if you want
        return "correct_answer"

    @property
    def incorrect_sound(self):
        """The sound that is played when player makes an incorrect guess"""
        # OPTIONAL: change this to a different sound if you want
        return "incorrect"

    @property
    def end_of_game_sound(self):
        """The sound that is played when the game ends."""
        # OPTIONAL: change this to a different sound if you want
        return "end_of_game"
    

    def reveal_board(self):
        for i in range(self.button_pad.button_count):
            button = self.buttons[i]
            self.button_pad.set_button_led_color(self.button_pad.get_button(i+1), button.color)

    def _background_logic_checker(self):
        while self.play_game:
            time.sleep(0.005)  # Prevents busy-waiting
            if self.queue.empty():
                continue
            button_number = self.queue.get()
            print(f"Handling button {button_number}")
            # TODO: check your game state, and update things

    def when_pressed(self, button):
        # TODO: this is called when a button is pressed. Add what you need to here
        _logger.info(f"Button {button.pin.info.number} pressed")
        self.queue.put(button.pin.info.number)

        buttonInfo = self.buttons[button.pin.info.number-1]
        self.button_pad.set_button_led_color(self.button_pad.get_button(button.pin.info.number), buttonInfo.color)
        self.speaker.play_preloaded_wav(buttonInfo.sound, wait_until_done=self.last_pressed_index  is not None)


    def when_held(self, button):
        if button.pin.info.number == 1:
            print(f'button {button.pin.info.number} held')
            self.initialize_button_pad()
            self._start_game()
        if button.pin.info.number == 2:
            print(f'button {button.pin.info.number} held')
            self.reveal_board()
            self.speaker.play_preloaded_wav("boing_x", wait_until_done=False)
            

        # TODO: this is called when a button is held. Add what you need to here
        pass

    def when_released(self, button):
        # TODO: this is called when a button is released. Add what you need to here
        buttonInfo = self.buttons[button.pin.info.number-1]
        if(self.last_pressed_index is not None):
            if(button.pin.info.number-1 != self.last_pressed_index): 
                last_pressed_info = self.buttons[self.last_pressed_index]
                if(buttonInfo.matched is not False and last_pressed_info.matched is not False):
                    pass
                elif(buttonInfo.matched is not False):
                    self.button_pad.set_button_led_color(self.button_pad.get_button(self.last_pressed_index+1), "black")
                elif(last_pressed_info.matched is not False):
                    self.button_pad.set_button_led_color(self.button_pad.get_button(button.pin.info.number), "black")
                else:
                    if(buttonInfo.color == last_pressed_info.color): 
                        self.speaker.play_preloaded_wav("correct_answer", wait_until_done=True)
                        buttonInfo.matched = True
                        last_pressed_info.matched = True
                    else:
                        self.speaker.play_preloaded_wav("incorrect", wait_until_done=True)
                        self.button_pad.set_button_led_color(self.button_pad.get_button(button.pin.info.number), "black") 
                        self.button_pad.set_button_led_color(self.button_pad.get_button(self.last_pressed_index+1), "black")
                
                self.last_pressed_index = None
        
        else:
            self.last_pressed_index = button.pin.info.number-1
        self.handle_end_game()
    def initialize_button_pad(self):
        self.button_pad.clear_button_pad()
        # TODO: Set all buttons to a color, List of colors to choose from: https://github.com/waveform80/colorzero/blob/master/colorzero/tables.py#L315
        # sounds are available in the sounds directory
        self.colors = ["red", "green", "blue", "#ff00ff", "#00ffff", "gold", "teal", "white"]
        self.sounds = [
            "thunder2",
            "fart_z",
            "baby_x",
            "slide_whistle_x",
            "arrow2",
            "phone_pay",
            "bloop_x",
            "car_horn_x",
        ]
        # TODO: assign to buttons
        random.shuffle(self.colors)
        random.shuffle(self.sounds)
        self.buttons=[]
        for i in range(8):    
            self.buttons.append(ButtonInfo(self.colors[i], self.sounds[i], False))

        self.buttons= self.buttons + self.buttons
        random.shuffle(self.buttons)
        
    def _start_game(self):
        self.thread = threading.Thread(target=self._background_logic_checker)
        self.thread.start()
        # TODO: play a sound to start the game
        self.speaker.play_preloaded_wav("drum_roll2", wait_until_done=True)
        self.started = True

    def play(self):
        self._start_game()
        try:
            input("Press Enter to exit the game...")
        except KeyboardInterrupt:
            print("Exiting game...")
        finally:
            self.play_game = False
            self.thread.join()
            self.button_pad.cleanup()
    #gets called when game ends
    def handle_end_game(self):
        print("x", all(buttonInfo.matched for buttonInfo in self.buttons))
        if (all(buttonInfo.matched for buttonInfo in self.buttons)):
            self.speaker.play_preloaded_wav("end_of_game", wait_until_done=False)
            self.initialize_button_pad()
            self._start_game()


def _main():
    button_pad = MatrixButtonLEDController(
        scan_delay=0.020, pwm_freq=10000, display_pause=0.001, use_led_hat=USE_LED_HAT
    )
    game = Game(button_pad)
    game.play()


if __name__ == "__main__":
    _main()