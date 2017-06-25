

def set_headers(driver):
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.8',
        'Cache-Control': 'max-age=0',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 6_0 like Mac OS X) AppleWebKit/536.26'
                      ' (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25'
    }
    for key, value in headers.items():
        driver.DesiredCapabilities.PHANTOMJS['phantomjs.page.customHeaders.{}'.format(key)] = value
    driver.DesiredCapabilities.PHANTOMJS['phantomjs.page.settings.userAgent'] = headers.get('User-Agent')
    browser = driver.PhantomJS()
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
