from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

ua = 'Opera/9.80 (Windows NT 6.1; WOW64; U; en) Presto/2.10.229 Version/11.62'


def set_headers(driver):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.8',
        'Cache-Control': 'max-age=0'
    }
    caps = DesiredCapabilities.PHANTOMJS
    for key, value in headers.items():
        caps['phantomjs.page.customHeaders.{}'.format(key)] = value
    caps['phantomjs.page.settings.userAgent'] = ua
    browser = driver.PhantomJS(desired_capabilities=caps)
    browser.set_window_size(800, 600)
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
