import tqdm
import time


def like_posts(browser, logger, count):
    progress = tqdm.tqdm(range(count))
    browser.find_element_by_css_selector("article > div a").click()
    time.sleep(0.5)
    skipped = 0
    liked = 0
    already_liked = 0

    for i in progress:
        time.sleep(1)
        heart = is_liked_acc_post(browser)
        if heart:
            heart.find_element_by_xpath('..').click()
            logger.log_to_file("--> like post #{}".format(i))
            liked += 1
            already_liked = 0
            time.sleep(0.5)
        else:
            skipped += 1
            already_liked += 1

        link = has_next(browser)
        if not link:
            break
        if already_liked > 5:
            progress.close()
            break
        link.click()
        progress.update()

    return {'liked': liked, 'skipped': skipped}


def is_liked_acc_post(browser):
    try:
        heart = browser.find_element_by_css_selector(".coreSpriteHeartOpen")
        return heart
    except:
        return False


def has_next(browser):
    try:
        next_link = browser.find_element_by_css_selector(".coreSpriteRightPaginationArrow")
        return next_link
    except:
        return False
