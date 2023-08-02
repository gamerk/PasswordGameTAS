from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.common.exceptions import TimeoutException
import time
import utils
from text_segments import BaseTextSegment
from info_tables import ROMAN_NUMERALS, YOUTUBE_LINKS
import re
import json
from multiprocessing.pool import ThreadPool

"""
return new Array(...document.querySelectorAll('ytd-thumbnail-overlay-time-status-renderer.ytd-thumbnail')).map(x => [x.innerText.trim(), x.parentElement.parentElement.href.match(/(?<=v=)[a-zA-Z0-9-_]{11}/)[0]]).filter(x => {
    let l = 60 * ~~x[0].split(':')[0] + ~~x[0].split(':')[1];
    let s = x[1].split('').filter(char => /\d/.test(char)).reduce((sum, digit) => sum + Number(digit), 0);
    return 180 <= l && l <= 2180 && !x[1].match(/[VXMLCD]|II|III/) && s <= 16;
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

already_used = {
    "Zeronium",
    "DisplacedGamers",
    "GDColon",
    "JacobGeller",
    "BigJoel",
    "IceCreamSandwich",
    "howitsmadeofficial1334",
    "OmaruPolka",
    "LaplusDarknesss",
    "SUSHIRAMEN-Riku",
    "bluearchive_Global",
    "bluearchive_kr",
    "bluearchive_tw",
    "bluearchive_jp",
    "GenshinImpact",
    "GenshinImpact_KR",
    "GenshinImpact_ZH",
    "Genshin_JP",
    "jacksfilms",
    "bluaca",
    "EricVanWilderman",
    "AeonAir",
    "Cobgd",
    "RealLifeLore",
    "PolyMatter",
    "hbomberguy",
    "Morphoduction",
    "Defunctland",
    "longplayarchive",
    "LEMMiNO",
    "AlarmTimer",
    "OnlineAlarmKurTV",
    "IHincognitoMode",
    "Gdconf",
    "LoopyLongplays",
    "ninbanyan",
    "CarlSagan42",
    "PandoraJourney",
    "LongnPlay",
    "worldoflongplays",
    "60minuteslongplay",
    "hackgameslongplaychannel",
    "supereyepatchwolf3007",
    "TheAnimeMan",
    "gigguk",
    "ludwig",
    "Alpharad",
    "Alpharad-Gold",
    "alpharadreplay",
    "SomeQueerDork",
}

tags = {
    "hawutski",
    "GDColon",
    "Animist_1",
    "BlueSechi",
    "Zeronium",
    "ramukukki",
    "alpharadreplay",
    "Alpharad",
    "Alpharad-Gold",
    "markiplier",
    "gigguk",
    "Smallant",
    "Onigiricat",
    "angle3206",
    "notalpharad",
    "supereyepatchwolf3007",
    "mirabeaustudios",
    "BigJoel",
    "unoriginalthings3303",
    "ARRW4",
    "coachb7373",
    "noodlefunny",
    "zachstar",
    "Teargelis",
    "tetsutobey",
    "happyaffey",
    "AsumSaus",
    "NerissaRavencroft",
    "answerinprogress",
    "user-jeenyburger",
    "ultravioletdelta",
    "DisplacedGamers",
    "Junferno",
    "HBMmaster",
    "SiIvaGunner",
    "ruiwang372",
    "bluearchive_Global",
    "ShondopilledIndividuals",
    "AdamNeely",
    "OverlySarcasticProductions",
    "bluaca",
    "tisubasah25",
    "Akatsuki-Records",
    "jacksfilms",
    "KUMORASE_CHANNEL",
    "RGMechEx",
    "shirokokawaiikv",
    "matoloid",
    "Keksi",
    "anssimirka",
    "SebastianLague",
    "JacobGeller",
    "InnuendoStudios",
    "LloydDunamis",
    "duncanclarke",
    "vgbootcamp",
    "ai-explained-",
    "MaxFosh",
    "silver279",
    "v1-v0",
    "hardahsnails",
    "regulareyepatchwolf6128",
    "TsukinoMito",
    "weebretronokias",
    "neoexplains",
    "InsideAMindInsideAMind",
    "megapussi",
    "ZubattoOkayu795",
    "partitionhlep2",
    "videogamedunkey",
    "TedNivison",
    "TheOperationsRoom",
    "Ytker",
    "yayataka3643",
    "Fireship",
    "master_samwise",
    "Deadzsh",
    "kennylauderdale_en",
    "silokhawk",
    "souma_game13",
    "Rapyo_Archive",
    "TheRightOpinion",
    "KazeN64",
    "2ManySnacks",
    "notamzu",
    "Foxsoccer",
    "SamONellaAcademy",
    "JediMasterGeoff",
    "rinnosama301",
    "ShuoshuoChinese",
    "frostu8",
    "mkbhd",
    "veritasium",
    "briandavidgilbert",
    "djskiskyskoski",
    "Wendoverproductions",
    "Otaku-kunClips",
    "MagicTheNoah",
    "BotanicSage",
    "Ididathing",
    "speedoru",
    "adultswim",
    "AccentedCinema",
    "Valiant_ID",
    "JonTronShow",
    "Max0r",
    "MeltySolid",
    "Drawfee",
    "CharlesCornellStudios",
    "NotJustBikes",
    "HelloFutureMe",
    "HintShot",
    "PatchQuest",
    "wizawhat",
    "PhoenixSC",
    "user-sm6og6tp8o",
    "BIG-SARU",
    "SsethTzeentach",
    "FoldingIdeas",
    "migiTF2",
    "kylehill",
    "JarToonyt",
    "JoaoPereiraCriacoes",
    "TrashTaste",
    "zumatk",
    "LegalEagle",
    "mattwith4ts",
    "NewFramePlus",
    "Stumblebee",
    "nekoshey",
    "DailyDoseOfInternet",
    "karljobst",
    "elaina8567",
    "3blue1brown",
    "noripro",
    "shar",
    "penguinz0",
    "Tantacrul",
    "IceCreamSandwich",
    "CircleToonsHD",
    "noisessv",
    "AsmonTV",
    "valteil",
    "Mordekaiser_Bot",
    "Haelian",
    "bluearchive_tw",
    "hololiveEnglish",
    "bluearchive-get",
    "ClementJ64",
    "tanamoxv2160",
    "proxyrin",
    "TheAnimeMan",
    "not_7OU",
    "DougDoug",
    "BlueArchive_JP",
    "ThatMumboJumbo",
    "FelioSmelio",
    "vclipnsubs4409",
    "ZullietheWitch",
    "LinusTechTips",
    "alph9321",
    "FUWAMOCOch",
    "LastWeekTonight",
    "mrnigelng",
    "NightMind",
    "Bitlytic",
    "atrioc",
    "hidechannel2",
    "cjthex",
    "Polritz",
    "RealCivilEngineerGaming",
    "thehellafreshg.o.s.7144",
    "domainofscience",
    "Jazza",
    "_pigden_223",
    "DailyDoseofHololiveEN",
    "InsiderBusiness",
    "TEDx",
    "EthanBecker70",
    "SolarSands",
    "flub9171",
    "tacobrayden7202",
    "Sophist",
    "vr6843",
    "PeterSantenello",
    "JoshuaWeissman",
    "Silvervale",
    "AniplexUSA",
    "SMN",
    "TechnologyConnections",
    "The8BitGuy",
    "InugamiKorone",
    "RhythmHeavenReanimated",
    "FoundFlix",
    "Jragostea",
    "FourStarBento",
    "WhatopiaHololiveClipper",
    "NBCNews",
    "bernadettebanner",
    "isaacwhyy",
    "amandametsnor4256",
    "tawnky",
    "cast7352",
    "FirstWeFeast",
    "YuYumonst",
    "LGR",
    "DanMan",
    "ChrissaBug",
    "user-mm1vc9fk9e",
    "kuroi0",
    "Burning-Flower",
    "Kenadian",
    "RRRcreators",
    "MistaGG",
    "fukkura_suzume_club",
    "destiny",
    "GawrGura",
    "ondoreyas",
    "TheInfographicsShow",
    "JamesLee",
    "1mincook",
    "NinomaeInanis",
    "porkyminch2231",
    "TEKITOH_Impact",
    "ShirakamiFubuki",
    "UMAMUSUME_official",
    "AudioUniversity",
    "KaelaKovalskia",
    "kuraburaman",
    "Ronnie300Fan",
    "Centr01d",
    "TakaneLui",
    "fuwafi",
    "packgod.",
    "nobuoJT",
    "CodeBullet",
    "CallMeKevin",
    "iiSayuri",
    "Mico_Sekishiro",
    "yoneyamai",
    "AuntieSaniyesRecipes",
    "YukinoshitaPeo",
    "BlackamoorFilms",
    "AsmongoldClips",
    "overwatchleague",
    "Lividy",
    "ScottTheWoz",
    "CGPGrey",
    "standup",
    "LavenderTowne",
    "ABCNews",
    "richenas",
    "Vsauce",
    "fgoxiaoyu0826",
    "Nth_rigze",
    "JimBrowning",
    "DoctorMike",
    "mothersbasement",
    "KateCavanaugh",
    "MogulMail",
    "kaya3rd",
    "ai-tools-search",
    "humanbug_univ.",
    "JYPEntertainment",
    "NewsNation",
    "KaiCenatLive"
}

tags -= already_used

dur_text = lambda secs: f"{secs // 60}:{secs % 60:02d}"

def missing_link_histogram():
    bin_size = 60
    f = open("ytlinks2.json", "r")
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
    
    f = open("ytlinks2.json", "w+")
    json.dump(links, f, indent=4, sort_keys=True)
    f.close()

if __name__ == "__main__":
    
    missing_link_histogram()
    
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    options.add_argument("--headless")
    options.add_argument("--log-level=3")
    
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(20000, 20000)
    
    f = open("ytlinks.json", "r")
    links: dict = json.load(f)
    f.close()
    
    try:
        for tag in tags:
            print(len(links), "/ 2000")
            print("Starting tag", tag)
            driver.get(f"https://www.youtube.com/@{tag}/videos")
            
            try:
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "ytd-thumbnail-overlay-time-status-renderer.ytd-thumbnail")))
            except TimeoutException:
                continue
            
            for _ in range(100):
                ActionChains(driver).scroll_by_amount(0, 1000000).perform()
                time.sleep(0.1)
            
            print("Writing...")
            els = driver.find_elements(By.CSS_SELECTOR, "ytd-thumbnail-overlay-time-status-renderer.ytd-thumbnail")
            
            def add_el(el):
                duration = el.text.strip()
                if not duration or duration in links:
                    return None
                
                link: str = el.find_element(By.XPATH, "../..").get_attribute("href")
                link = re.findall(r"(?<=watch\?v=)[a-zA-Z0-9_-]{11}", link)[0]
                if duration.count(":") > 1:
                    return None
                secs = int(duration.split(":")[0]) * 60 + int(duration.split(":")[1])
                if 180 <= secs <= 2180 and is_usable_link(link):
                    return {duration: link}
                return None
            
            with ThreadPool(8) as p:
                els = p.map(add_el, els)
            
            for el in els:
                if el:
                    links.update(el)
    except Exception:
        pass
    f = open("ytlinks.json", "w+")
    json.dump(links, f, indent=4, sort_keys=True)
    f.close()
    
    print(len(links), "/ 2000")
    
    interpolate_links()