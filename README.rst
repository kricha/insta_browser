Instabrowser
============

`Build Status <https://travis-ci.org/kricha/insta_browser>`__
`PyPI <https://pypi.org/pypi/insta_browser>`__

| 💻 Library for instagram.com automation.
| ♥️ Like instagram feed, username profile, location, tag.
| 🤝 Auto-follow unknown users, during liking, from locations or tags.
| 📊 Get statistic of any public account.

Requirements
~~~~~~~~~~~~

-  Python 3
-  `ChromeDriver <https://sites.google.com/a/chromium.org/chromedriver/downloads>`__
   for headless web-surfing

Examples
~~~~~~~~

-  Example of using package for liking specific user:

   .. code:: python

      import os
      from insta_browser import browser

      br = browser.Browser(
          debug=True,cookie_path=os.path.join('var', 'cookies'),
          log_path=os.path.join('var', 'logs'),
          db_path=os.path.join('var', 'db'),
          exclude=os.path.join('var', 'exclude.txt'),
          auto_follow=True
      )

      try:
          br.auth('YOUR_INSTA_LOGIN', 'YOUR_INSTA_PASSWORD')
          br.process_user('al_kricha')
          print(br.get_summary())
      finally:
          br.close_all()

Other examples can be seen in my repository:
`insta_bot <https://github.com/kricha/insta_bot>`__
