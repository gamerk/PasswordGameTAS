from text_segments import CaptchaSolution, BaseTextSegment, UnsolvableException, FillerElements
from string import ascii_lowercase
from bs4 import BeautifulSoup
from dataclasses import dataclass
from info_tables import VOWELS, ROMAN_NUMERALS, FONT_SIZES

@dataclass
class Format:
    bold: bool = False
    italics: bool = False
    font_size: int = 28
    font_family: str = "Monospace"
    
    def apply(self, text: str):
        text = f'<span style="font-family: {self.font_family}; font-size: {self.font_size}px;">{text}</span>'
        if self.italics:
            text = f"<i>{text}</i>"
        if self.bold:
            text = f"<strong>{text}</strong>"
        return text

class Password:
    def __init__(self, segments: list[BaseTextSegment]):
        self.segments = segments
        self.sacrificed_letters = ""
        
        self.balance_digit_sum()
        self.balance_element_sum()
        
    def digit_sum(self):
        return sum(i.get_digit_sum() for i in self.segments)
    
    def element_sum(self):
        return sum(i.get_elm_sum() for i in self.segments)
    
    def sacrifice_candidates(self):
        unused = set(ascii_lowercase)
        for seg in self.segments:
            if not seg.modLetters:
                unused -= set(seg.text)
        return unused
    
    def balance_digit_sum(self):
        captcha_seg = None
        change_needed = 25 - self.digit_sum()
        for seg in self.segments:
            if change_needed == 0:
                break
            
            if seg.modDigits and type(seg) is not CaptchaSolution:
                print(seg, "Mod digits is", seg.modDigits)
                seg.modify_digits(change_needed)
            elif type(seg) is CaptchaSolution:
                captcha_seg = seg
            
            change_needed = 25 - self.digit_sum()
        
        if change_needed != 0 and captcha_seg and captcha_seg.get_digit_sum() > 0:
            captcha_seg.modify_digits(change_needed)
        
        if change_needed != 0:
            raise UnsolvableException("Unable to balance digit sum!")
        
    def has_2_letter_elm(self):
        for seg in self.segments:
            if seg.has_2_letter_elm():
                return True
        return False
    
    def balance_element_sum(self):
        change_needed = 200 - self.element_sum()
        for seg in self.segments:
            if change_needed == 0:
                break
            
            if type(seg) is FillerElements:
                seg.needs_2_letter = not self.has_2_letter_elm()
            
            if seg.modElm:
                print("Before:", seg.text)
                seg.modify_elm(change_needed, self.sacrificed_letters)
                print("After:", seg.text)
            
            change_needed = 200 - self.element_sum()
            print("Change still needed:", change_needed)
        
        if change_needed != 0:
            print(self.get_raw_text())
            raise UnsolvableException("Unable to balance element sum!")
        
    def contains_sacrificed(self, seg: BaseTextSegment):
        return any(i in seg.text.lower() for i in self.sacrificed_letters)
    
    def remove_sacrificed(self):
        for seg in self.segments:
            if not self.contains_sacrificed(seg):
                continue
            
            if not seg.modLetters:
                raise UnsolvableException(f"Impossible to remove sacrificed letters {repr(self.sacrificed_letters)} because of segment {seg.seg_type}:{repr(seg.text)}")
            
            seg.modify_letters(self.sacrificed_letters)
            if self.contains_sacrificed(seg):
                raise UnsolvableException(f"Impossible to remove sacrificed letters {repr(self.sacrificed_letters)} because of segment {seg.seg_type}:{repr(seg.text)} "
                                "(after attempting modification)")
        self.balance_digit_sum()
        self.balance_element_sum()
    
    def append(self, seg: BaseTextSegment):
        self.segments.append(seg)
        print("Appending", seg)
        
        # Balance digits
        if self.digit_sum() != 25 and seg.modDigits:
            seg.modify_digits(25 - self.digit_sum())
        if self.digit_sum() != 25:
            self.balance_digit_sum()
        
        # Balance elements
        if self.element_sum() != 200 and seg.modElm:
            seg.modify_elm(200 - self.element_sum())
        if self.element_sum() != 25:
            self.balance_element_sum()
            
        # Remove sacrificed
        if self.contains_sacrificed(seg):
            seg.modify_letters(self.sacrificed_letters)
    
    def get_raw_text(self):
        return ''.join(i.text for i in self.segments)
    
    def get_format(self):
        raw = self.get_raw_text()
        styles = [Format(italics=True) for i in raw]
        char_sizes = {i: 0 for i in ascii_lowercase}
        
        num_wingdings = 0
        
        for index, c in enumerate(raw):
            if c in VOWELS:
                styles[index].bold = True
                
            if c.isdigit():
                styles[index].font_size = int(c) ** 2
            elif c.lower() in ascii_lowercase:
                styles[index].font_size = FONT_SIZES[char_sizes[c.lower()]]
                char_sizes[c.lower()] += 1
            
            if c in ROMAN_NUMERALS:
                styles[index].font_family = "Times New Roman"
            elif num_wingdings <= 0.3 * len(raw):
                styles[index].font_family = "Wingdings"
                num_wingdings += 1
        
        return styles
    
    def to_html(self):
        raw = self.get_raw_text()
        print(f"Length ({len(raw)}): ", raw)
        styles = self.get_format()
        return ''.join(style.apply(char) for style, char in zip(styles, raw))