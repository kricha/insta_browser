def set_headers(driver):
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.8',
        'Cache-Control': 'max-age=0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                      ' (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    for key, value in headers.items():
        driver.DesiredCapabilities.PHANTOMJS['phantomjs.page.customHeaders.{}'.format(key)] = value
    browser = driver.PhantomJS()
    driver.DesiredCapabilities.PHANTOMJS['phantomjs.page.settings.userAgent'] = headers.get('User-Agent')
    browser.set_window_size(800, 1000)
    return browser


def clear_driver_cache(browser):
    browser.execute('executePhantomScript', {'script': '''
        var page = this;
        page.clearMemoryCache();
    ''', 'args': []})


def resource_requested_logic(browser):
    browser.execute('executePhantomScript', {'script': '''
        var page = this;
        page.onResourceRequested = function(request, networkRequest) {
            if (/\.(jpg|jpeg|png|mp3|css|mp4)/i.test(request.url))
            {
                //console.log('Final with css! Suppressing image: ' + request.url);
                networkRequest.abort();
                return;
            }
        }
    ''', 'args': []})
