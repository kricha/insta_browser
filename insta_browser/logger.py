from datetime import datetime


class Logger:
    def __init__(self, log_file='/tmp/insta_browser.txt', screen_shot_path='/tmp', debug=False):
        self.log_file = log_file
        self.screen_shot_path = screen_shot_path
        self.debug = debug

    def log(self, text, force=False):
        if self.debug or force:
            print(text)
        self.log_to_file(text)

    def log_to_file(self, text):
        file = open(self.log_file, 'a')
        log_date = datetime.now()
        log_date.__format__("%d-%m-%Y %H:%M")
        file.write("[{}] {}\n".format(log_date, text))

    def save_screen_shot(self, browser, screen_shot_name=None):
        """
        Save screen shot and log it
        :param browser:
        :param screen_shot_name:
        :return:
        """
        if screen_shot_name:
            try:
                browser.save_screenshot('{}/{}'.format(self.screen_shot_path, screen_shot_name))
                self.log_to_file('Saving screen shot to {}/{}'.format(self.screen_shot_path, screen_shot_name))
                return True
            except:
                return False
