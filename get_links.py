from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.common.exceptions import TimeoutException
import time
import utils
from text_segments import BaseTextSegment
from info_tables import ROMAN_NUMERALS, ELEMENTS
import re
import json
from multiprocessing.pool import ThreadPool

scrape_links = """\
return new Array(...document.querySelectorAll('ytd-thumbnail-overlay-time-status-renderer.ytd-thumbnail')).map(x => [x.innerText.trim(), x.parentElement.parentElement.href.match(/(?<=v=)[a-zA-Z0-9-_]{11}/)[0]]).filter(x => {
    let l = 60 * ~~x[0].split(':')[0] + ~~x[0].split(':')[1];
    let s = x[1].split('').filter(char => /\d/.test(char)).reduce((sum, digit) => sum + Number(digit), 0);
    return !x[0].match(/\d+:\d+:\d+/) && 180 <= l && l <= 2180 && !x[1].match(/[VXMLCD]|II|III/) && s <= 16;
});
"""

def is_usable_link(link: str):
    if any(i in link for i in ROMAN_NUMERALS[1:]):
        return False
    if "II" in link or "III" in link:
        return False
    seg = BaseTextSegment(link)
    if seg.get_digit_sum() > 25 or seg.get_elm_sum() > 169:
        return False
    return True

f = open("checked_tags.txt", "r")
checked_tags = set(map(str.strip, f))
f.close()

f = open("channel_tags.txt", "r")
tags = list(set(map(str.strip, f)) - checked_tags)
f.close()

dur_text = lambda secs: f"{secs // 60}:{secs % 60:02d}"

def missing_link_histogram(file_path: str):
    bin_size = 60
    f = open(file_path, "r")
    links: dict = json.load(f)
    f.close()
    
    num_missing = 0
    for secs in range(180, 2181):
        if dur_text(secs) not in links:
            num_missing += 1
        
        if secs % bin_size == 0:
            print(f"{dur_text((secs - 1) // bin_size * bin_size + 1)}-{dur_text(secs)}: {num_missing}")
            num_missing = 0

def interpolate_links():
    f = open("ytlinks.json", "r")
    links: dict = json.load(f)
    f.close()
    new = {}
    
    for secs in range(180, 2181):
        dur = dur_text(secs)
        low = dur_text(secs - 1)
        high = dur_text(secs + 1)
        
        if dur not in links:
            if low in links:
                new[dur] = links[low]
            elif high in links:
                new[dur] = links[high]
    
    links.update(new)
    
    f = open("ytlinks_interp.json", "w+")
    json.dump(links, f, indent=4, sort_keys=True)
    f.close()

def check_link(dur_link: list[str, str]):
        link = dur_link[1]
        
        total_sum = 0
        
        # 2 letter elements
        for num, sym in enumerate(ELEMENTS):
            if sym and len(sym) == 2:
                total_sum += num * link.count(sym)
        
        # 1 letter elements
        for num, sym in enumerate(ELEMENTS):
            if sym and len(sym) == 1:
                total_sum += num * link.count(sym)
        
        if total_sum <= (200 - 23 - 113):
            digit_sum = sum(map(int, filter(str.isdigit, link)))
            return (total_sum + digit_sum * 8, {dur_link[0]: link})
        return None

if __name__ == "__main__":
            
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    options.add_argument("--headless")
    options.add_argument("--log-level=3")
    
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(20000, 20000)
    
    f = open("ytlinks.json", "r")
    links: dict = json.load(f)
    f.close()
    
    # All duration-link pairs
    possible_links = [[i, links[i]] for i in links]
    
    tag_index = 0
    
    try:
        for tag in tags:
            print("Found links:", len(possible_links))
            tag_index = tags.index(tag)
            print(f"Starting tag #{tag_index}: {tag}")
            driver.get(f"https://www.youtube.com/@{tag}/videos")
            
            print("Waiting to load...")
            try:
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "ytd-thumbnail-overlay-time-status-renderer.ytd-thumbnail")))
            except TimeoutException:
                continue
            
            print("Scrolling page...")
            # Scroll page to load all links
            last_height = 0
            for _ in range(300):
                driver.execute_script("return document.documentElement.scrollBy(0, 1000000000000)")
                time.sleep(0.5)
                new_height = driver.execute_script("return document.documentElement.scrollHeight")
                if new_height == last_height:
                    print("Ended because hit end of page")
                    break
                last_height = new_height
            else:
                print("Ended because of iteration cap")
            
            
            print("Getting links...")
            possible_links += driver.execute_script(scrape_links)
    except KeyboardInterrupt:
        print("Skipping...")
    except Exception as ex:
        print(ex)
    # driver.close()
    
    print("Writing...")
    
    # Score each link and remove invalid ones
    with ThreadPool(8) as p:
        scored_dicts = p.map(check_link, possible_links)
    scored_dicts = list(filter(None, scored_dicts))
    
    # Replace links with ones with lower scores
    scored_dicts.sort(reverse=True, key=lambda x: x[0])
    print(scored_dicts)
    for score, dur_link in scored_dicts:
        links.update(**dur_link)
    
    f = open("ytlinks.json", "w+")
    json.dump(links, f, indent=4, sort_keys=True)
    f.close()
    
    f = open("checked_tags.txt", "w+")
    f.write('\n'.join(tags[:tag_index]))
    f.close()
    
    print(len(links), "/ 2000")
    
    interpolate_links()