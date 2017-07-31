from datetime import datetime
from .version import __version__
import tempfile
import os


class Logger:
    def __init__(self, log_path=tempfile.gettempdir(), debug=False):
        self.log_file = os.path.join(log_path, 'insta_browser_{}.log'.format(__version__))
        self.screen_shot_path = os.path.join(log_path, 'screenshot')
        self.debug = debug

    def log(self, text, force=False):
        if self.debug or force:
            print(text)
        self.log_to_file(text)

    def log_to_file(self, text):
        file = open(self.log_file, 'a')
        log_date = datetime.now()
        formatted_date = log_date.__format__("%d-%m-%Y %H:%M:%S")
        file.write("[{}] {}\n".format(formatted_date, text))

    def save_screen_shot(self, browser, screen_shot_name=None):
        """
        Save screen shot and log it
        :param browser:
        :param screen_shot_name:
        :return:
        """
        if screen_shot_name:
            try:
                screenshot_real_path = os.path.join(self.screen_shot_path, screen_shot_name)
                browser.save_screenshot(screenshot_real_path)
                self.log_to_file('Saving screen shot to {}'.format(screenshot_real_path))
                return True
            except:
                return False
