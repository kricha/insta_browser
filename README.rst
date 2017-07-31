Instabrowser
============

|Build Status| |PyPI| |Code Climate|

👍 ♥️ 🏆 Library for instagram.com automation. Like instagram feed (whole
or by count), like username profile (whole or by count), like posts from
location.

You need to have PhantomJS or Chrome web driver for work.

Download and place binary from archive to bin folder: -
`PhantomJS <http://phantomjs.org/download.html>`__ -
`Chrome <https://sites.google.com/a/chromium.org/chromedriver/downloads>`__

Example of using package for liking specific user:

.. code:: python

    import os
    from insta_browser import browser

    br = browser.Browser(
        debug=True,
        chrome=False,
        cookie_path=os.path.join('var', 'cookies'),
        log_path=os.path.join('var', 'logs'),
        db_path=os.path.join('var', 'db'),
        exclude=os.path.join('var', 'exclude.txt')
    )

    try:
        br.auth('YOUR_INSTA_LOGIN', 'YOUR_INSTA_PASSWORD')
        br.process_user('al_kricha')
        print(br.get_summary())
    finally:
        br.close_all()

Other examples can be seen in my repository:
`insta\_bot <https://github.com/aLkRicha/insta_bot>`__

.. |Build Status| image:: https://travis-ci.org/aLkRicha/insta_browser.svg?branch=master
   :target: https://travis-ci.org/aLkRicha/insta_browser
.. |PyPI| image:: https://img.shields.io/pypi/v/insta_browser.svg
   :target: https://pypi.python.org/pypi/insta_browser
.. |Code Climate| image:: https://img.shields.io/codeclimate/github/aLkRicha/insta_browser.svg
   :target: https://codeclimate.com/github/aLkRicha/insta_browser
