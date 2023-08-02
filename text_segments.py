from info_tables import ELEMENTS, ROMAN_NUMERALS, PRIMES, WEIGHT_LIFTER
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
import utils
import datetime

class UnsolvableException(BaseException):
    pass

class BaseTextSegment:
    def __init__(self, text: str, *, modDigits: bool=False, modElm: bool=False, modRoman: bool=False, modLetters: bool=False, seg_type: str="Basic Text Segment"):
        self.text = text
        self.modDigits = modDigits
        self.modElm = modElm
        self.modRoman = modRoman
        self.modLetters = modLetters
        self.seg_type = seg_type
    
    def modify_digits(self, change_needed: int):
        """Changes the sum of the digits in the text segment

        Args:
            change_needed (int): Amount to add or subtract from digit sum

        Raises:
            NotImplementedError: Modification is possible but not implemented
            TypeError: Modification is not possible
        """
        raise NotImplementedError() if self.modDigits else TypeError(f"{self.seg_type} does not support modifying its digit value")
    
    def modify_elm(self, change_needed: int, avoid_letters: str):
        """Changes the sum of the elements in the text segment

        Args:
            change_needed (int): Amount to add or subtract from element sum
            avoid_letters (str): Letters to not use in text segment

        Raises:
            NotImplementedError: Modification is possible but not implemented
            TypeError: Modification is not possible
        """
        raise NotImplementedError() if self.modElm else TypeError(f"{self.seg_type} does not support modifying its element symbol value")
    
    def modify_letters(self, avoid: str):
        """Changes text to remove letters

        Args:
            avoid (str): Letters to remove

        Raises:
            NotImplementedError: Modification is possible but not implemented
            TypeError: Modification is not possible
        """
        # TODO: string of letters to remove must contain both the upper and lower case versions
        raise NotImplementedError() if self.modElm else TypeError(f"{self.seg_type} does not support modifying its letters")
    
    def remove_roman(self):
        """Removes the roman numerals in the text segment

        Raises:
            NotImplementedError: Modification is possible but not implemented
            TypeError: Modification is not possible
        """
        raise NotImplementedError() if self.modRoman else TypeError(f"{self.seg_type} does not support modifying its roman numeral value")
    
    def get_digit_sum(self):
        return sum(int(i) for i in self.text if i.isdigit())
    
    def get_elm_sum(self):
        total = 0
        txt = self.text
        # 2 letter
        for num, elm in enumerate(ELEMENTS):
            if elm and len(elm) == 2:
                total += num * txt.count(elm)
                txt = txt.replace(elm, "")
        
        # 1 letter
        for num, elm in enumerate(ELEMENTS):
            if elm and len(elm) == 1:
                total += num * txt.count(elm)
                txt = txt.replace(elm, "")
        return total
    
    def has_2_letter_elm(self):
        total = 0
        txt = self.text
        # 2 letter
        for num, elm in enumerate(ELEMENTS):
            if elm and len(elm) == 2:
                return True
        return False
    
    def has_roman(self):
        return any([numeral in self.text for numeral in ROMAN_NUMERALS])
    
    def __str__(self):
        return self.text
    
    def __repr__(self):
        return repr(self.text)

class FillerNumbers(BaseTextSegment):
    def __init__(self, amount: int):
        self.text = "9" * (amount // 9) + str(amount % 9)
        super().__init__(self.text, modDigits=True, seg_type="Filler Numbers")
        
    def modify_digits(self, change_needed: int):
        amount = self.get_digit_sum() + change_needed
        self.text = "9" * (amount // 9) + (str(amount % 9) if amount % 9 != 0 else "")
        
class FillerElements(BaseTextSegment):
    def __init__(self, amount: int, needs_2_letter: bool = True):
        super().__init__(FillerElements.solve_elements(amount, ""), modElm=True, modLetters=True, seg_type="Filler Elements")
        self.needs_2_letter = needs_2_letter
        
    def modify_elm(self, change_needed: int, avoid_letters: str):
        print("Modifying elements to sum:", self.get_elm_sum() + change_needed)
        self.text = FillerElements.solve_elements(self.get_elm_sum() + change_needed, avoid_letters, need_2_letter=self.needs_2_letter)
        
    def modify_letters(self, avoid: str):
        self.text = FillerElements.solve_elements(self.get_elm_sum(), avoid, need_2_letter=self.needs_2_letter)
    
    def solve_elements(amount: int, avoid: str, need_2_letter: bool = True):
        avoid += ROMAN_NUMERALS
        result = []
        has_2_letter = not need_2_letter
        for num, sym in list(enumerate(ELEMENTS))[:0:-1]:
            if amount >= num and not any(i in sym for i in avoid) and (has_2_letter or len(sym) == 2):
                has_2_letter = True
                result += [sym] * (amount // num)
                amount %= num
            
            if amount == 0:
                break
        
        # if amount != 0:
        #     print(result)
        #     raise UnsolvableException(f"Could not solve for elements with conditions ({amount=} {avoid=} {need_2_letter=})")
        
        return ''.join(result)

class CaptchaSolution(BaseTextSegment):
    REFRESH_ATTEMPTS = 100
    
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        # Letters will never be upper case
        super().__init__(utils.get_captcha(driver), modDigits=True, modLetters=True, seg_type="Captcha")
    
    def modify_digits(self, change_needed: int):
        target = change_needed + self.get_digit_sum()
        for _ in range(CaptchaSolution.REFRESH_ATTEMPTS):
            utils.refresh_captcha(self.driver)
            try:
                # WebDriverWait(self.driver, 1).until(lambda x: self.text != x.find_element(By.CLASS_NAME, "captcha-img").get_attribute("src"))
                WebDriverWait(self.driver, 1).until_not(EC.text_to_be_present_in_element_attribute((By.CLASS_NAME, "captcha-img"), "src", self.text))
            except TimeoutException:
                continue
            self.text = utils.get_captcha(self.driver)
            
            if self.get_digit_sum() <= target:
                break
        else:
            raise UnsolvableException("Failed to modify digits in captcha!")
    
    def modify_letters(self, avoid: str):
        print("Mod letters in captcha")
        for _ in range(CaptchaSolution.REFRESH_ATTEMPTS):
            utils.refresh_captcha(self.driver)
            try:
                WebDriverWait(self.driver, 1).until_not(EC.text_to_be_present_in_element_attribute((By.CLASS_NAME, "captcha-img"), "src", self.text))
            except TimeoutException:
                continue
            self.text = utils.get_captcha(self.driver)
            
            if any(i in self.text for i in avoid):
                break
        else:
            raise UnsolvableException("Failed to modify letters in captcha!")

class HexColor(BaseTextSegment):
    REFRESH_ATTEMPS = 100
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        super().__init__(utils.get_hex_color(driver), modDigits=True, modLetters=True, seg_type="Hex Color")
    
    def modify_letters(self, avoid: str):
        for _ in range(HexColor.REFRESH_ATTEMPS):
            old = self.driver.find_element(By.CLASS_NAME, "rand-color").get_attribute("background")
            utils.refresh_hex_color(self.driver)
            try:
                WebDriverWait(self.driver, 1).until_not(EC.text_to_be_present_in_element_attribute((By.CLASS_NAME, "rand-color"), "background", old))
            except TimeoutException:
                continue
            self.text = utils.get_hex_color(self.driver)
            
            if not any(i in self.text for i in avoid):
                break
        else:
            raise UnsolvableException("Failed to modify letters in hex color!")
    
    def modify_digits(self, change_needed: int):
        target = change_needed + self.get_digit_sum()
        for _ in range(HexColor.REFRESH_ATTEMPS):
            old = self.driver.find_element(By.CLASS_NAME, "rand-color").get_attribute("background")
            utils.refresh_hex_color(self.driver)
            try:
                WebDriverWait(self.driver, 1).until_not(EC.text_to_be_present_in_element_attribute((By.CLASS_NAME, "rand-color"), "background", old))
            except TimeoutException:
                continue
            self.text = utils.get_hex_color(self.driver)
            
            if self.get_digit_sum() <= target:
                break
        else:
            raise UnsolvableException("Failed to modify letters in hex color!")

class PasswordLength (BaseTextSegment):
    def __init__(self, password):
        self.password = password
        self.seg_type = "Password Length"
        self.modDigits = False
        self.modElm = False
        self.modLetters = False
        self.modRoman = False
        self._length = 0
        self._last_text = ""
    
    @property
    def text(self):
        lngth = 0
        segments: list[BaseTextSegment] = self.password.segments
        for seg in segments:
            if seg is not self:
                # Combined emojis should only count as 1 each
                lngth += len(seg.text.replace(WEIGHT_LIFTER, "W"))
        lngth += len(str(self._length))
        print("Length is", lngth)
        
        if lngth != self._length:
            lngth -= len(str(self._length))
            # self._length = lngth + len(str(self._length))
            self._length = min(filter(lambda x: x >= lngth + len(str(x)), PRIMES),
                                key=lambda x: sum(int(i) for i in str(x) if i.isdigit()))
        
        self._last_text = str(self._length) + "." * (self._length - len(str(self._length)) - lngth)
        print("Final length is", len(self._last_text.replace(WEIGHT_LIFTER, "W")))
        return self._last_text
            
    def modify_digits(self, change_needed: int):
        self._length = min(filter(lambda x: x > self._length - len(str(self._length)) + len(str(x)), PRIMES),
                            key=lambda x: sum(int(i) for i in str(x) if i.isdigit()))

class CurrentTime(BaseTextSegment):
    def __init__(self):
        self.seg_type = "Current Time"
        self.modDigits = False
        self.modElm = False
        self.modLetters = False
        self.modRoman = False
    
    @property
    def text(self):
        if datetime.datetime.now().strftime("%I:%M") != "01:00":
            utils.win_set_time()
        return datetime.datetime.now().strftime("%I:%M")
# TODO: Maybe add sponsors text segment