from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from info_tables import ELEMENTS, ROMAN_NUMERALS, LOCATIONS, CHESS_SOLUTIONS, YOUTUBE_LINKS
import requests
from datetime import datetime
from json.decoder import JSONDecoder
from password import Password
import re
from itertools import combinations
from text_segments import UnsolvableException
import win32api
import time

def set_password(driver: webdriver.Chrome, html: str):
    driver.execute_script(f'document.getElementsByClassName("ProseMirror")[0].innerHTML = \'{html}\'')
    
def get_captcha(driver: webdriver.Chrome):
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'captcha-img')))
    return driver.execute_script('return document.getElementsByClassName("captcha-img")[0].src.match(/(?<=https\:\/\/neal\.fun\/password\-game\/captchas\/)[0-9a-z]+(?=\.png)/)[0]')

def refresh_captcha(driver: webdriver.Chrome):
    # WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'captcha-img')))
    driver.execute_script('return document.getElementsByClassName("captcha-refresh")[0].click()')

def get_wordle_answer():
    response = requests.get("https://neal.fun/api/password-game/wordle?date=" + datetime.now().strftime("%Y-%m-%d"))
    decoded = JSONDecoder().decode(response.content.decode())["answer"]
    response.close()
    return decoded

def get_geo_location(driver: webdriver.Chrome):
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'iframe.geo')))
    src = driver.find_element(By.CSS_SELECTOR, "iframe.geo").get_attribute("src")
    return LOCATIONS[src].lower()

def get_chess_solution(driver: webdriver.Chrome):
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'chess-img')))
    src = driver.find_element(By.CLASS_NAME, 'chess-img').get_attribute("src")
    puzzle_num = int(re.findall(r"(?<=puzzle)\d+(?=\.svg)", src)[0])
    return CHESS_SOLUTIONS[puzzle_num]

def get_youtube_link(driver: webdriver.Chrome):
    text = driver.find_element(By.CSS_SELECTOR, "div.rule.rule-error.youtube > div > div > div").text
    matches = re.findall("(\d+) minute (\d+) second", text)
    if len(matches) == 0:
        matches = re.findall("(\d+) minute", text)
        return "youtu.be/" + YOUTUBE_LINKS[f"{matches[0]}:00"]
    return "youtu.be/" + YOUTUBE_LINKS[f"{matches[0][0]}:{int(matches[0][1]):02d}"]

def sacrifice_letters(driver: webdriver.Chrome, word: Password):
    
    # Find and remove 2 letters
    candidates = list(word.sacrifice_candidates())
    print(candidates)
    if len(candidates) < 2:
        raise UnsolvableException("Unable to remove any letters!")
    
    for comb in combinations(candidates, 2):
        word.sacrificed_letters = comb[0] + comb[0].upper() + comb[1] + comb[1].upper()
        try:
            word.remove_sacrificed()
        except UnsolvableException:
            continue
        else:
            break
    else:
        raise UnsolvableException("Unable to remove any letters!")
    
    print("Sacrificing", word.sacrificed_letters)
    
    ac = ActionChains(driver)
    # Enter sacrificed letters into UI
    buttons = driver.find_elements(By.CSS_SELECTOR, ".letters > .letter")
    for button in buttons:
        if button.text.strip() in word.sacrificed_letters:
            ac.click(button)
    sb = driver.find_element(By.CLASS_NAME, "sacrafice-btn")
    ac.click(sb)
    ac.perform()

def get_hex_color(driver: webdriver.Chrome):
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'rand-color')))
    color = driver.find_element(By.CLASS_NAME, 'rand-color').get_attribute("style")
    rgb = list(map(int, re.findall("\((\d+), (\d+), (\d+)\)", color)[0]))
    print(color, rgb, hex((rgb[0] << 16) | (rgb[1] << 8) | (rgb[2]))[2:])
    return "#" + hex((rgb[0] << 16) | (rgb[1] << 8) | (rgb[2]))[2:].zfill(6)

def refresh_hex_color(driver: webdriver.Chrome):
    driver.execute_script('return document.querySelector(".rand-color > .refresh").click()')

def enter_final_password(driver: webdriver.Chrome, html: str):
    driver.execute_script('document.querySelector(".final-password > button:first-child").click()')
    WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".password-box-inner.complete")))
    driver.execute_script(f"document.querySelector('.password-box-inner.complete > div > .ProseMirror > p').innerHTML = \'{html}\'")
    
def win_set_time():
    NEW_TIME = (2023,   # Year
                8,      # Month
                1,      # Day
                1 + time.timezone // 3600 - time.daylight,      # Hour
                0 + time.timezone % 3600 // 60,      # Minute
                0 + time.timezone % 60,      # Second
                0)      # Millisecond
    
    dayOfWeek = datetime(*NEW_TIME).isocalendar()[2]
    t = NEW_TIME[:2] + (dayOfWeek,) + NEW_TIME[2:]
    win32api.SetSystemTime(*t)

if __name__ == "__main__":
    win_set_time()
