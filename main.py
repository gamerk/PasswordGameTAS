from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from time import sleep
import utils
from password import Password
from text_segments import *


if __name__ == "__main__":
    
    solved = False
    
    while not solved:
        try:
            word = Password([
                BaseTextSegment("iamloved", seg_type="Affirmation"),
                FillerNumbers(25),
                BaseTextSegment("XXXV", seg_type="Roman Numerals"),
                BaseTextSegment("`", seg_type="Special Character"),
                BaseTextSegment("may", seg_type="Month"),
                BaseTextSegment("shell", seg_type="Sponsor"),
                FillerElements(200),
                BaseTextSegment(utils.get_wordle_answer(), seg_type="Wordle Answer"),
                BaseTextSegment("🌕🌖🌗🌘🌑🌒🌓", seg_type="Moon Phase"),
                BaseTextSegment("0", seg_type="Leap Year"),
                BaseTextSegment("🥚🐛🐛🐛🐛🐛🐛", seg_type="Dave and Food"),
                BaseTextSegment(WEIGHT_LIFTER * 3, seg_type="Strength"),
                CurrentTime(),
            ])            
            driver = webdriver.Chrome()

            driver.get("https://neal.fun/password-game/")
            
            try:
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'ProseMirror')))
                utils.set_password(driver, word.to_html())
                
                word.append(CaptchaSolution(driver))
                utils.set_password(driver, word.to_html())
                
                word.append(BaseTextSegment(utils.get_geo_location(driver), seg_type="GMaps Location"))
                utils.set_password(driver, word.to_html())
                
                word.append(BaseTextSegment(utils.get_chess_solution(driver), seg_type="Chess Solution"))
                utils.set_password(driver, word.to_html())
                
                WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.rule.rule-error.fire")))
                utils.set_password(driver, "<p>🥚</p>")
                WebDriverWait(driver, 3).until_not(EC.presence_of_element_located((By.CSS_SELECTOR, "div.rule.rule-error.fire")))
                utils.set_password(driver, word.to_html())
                
                WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.rule.rule-error.youtube > div > div > :not(#youtube-player-wrapper)")))
                WebDriverWait(driver, 3).until(lambda x: x.find_element(By.CSS_SELECTOR, "div.rule.rule-error.youtube > div > div > :not(#youtube-player-wrapper)").text)
                word.append(BaseTextSegment(utils.get_youtube_link(driver), seg_type="Youtube Link"))
                utils.set_password(driver, word.to_html())
                
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'letters')))
                utils.sacrifice_letters(driver, word)
                utils.set_password(driver, word.to_html())
                
                word.append(HexColor(driver))
                utils.set_password(driver, word.to_html())
                
                utils.set_password(driver, word.to_html())
                word.append(PasswordLength(word))
                utils.set_password(driver, word.to_html())
                
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'final-password')))
                utils.enter_final_password(driver, word.to_html())
                
            except TimeoutException:
                print("Timed out!")
                continue
                
            
        except UnsolvableException as ue:
            solved = False
            print(ue)
            driver.close()
        else:
            solved = True
    
    while True:
        sleep(60)
        utils.set_password(driver, word.to_html())