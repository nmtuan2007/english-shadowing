import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# PATHS
# =============================================================================
BASE_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = BASE_DIR / "scripts"
LESSONS_DIR = BASE_DIR / "lessons"
SOURCES_FILE = BASE_DIR / "sources.json"

# =============================================================================
# VIDEO FILTERS
# =============================================================================
MIN_DURATION = 30  # seconds (0.5 minutes)
MAX_DURATION = 900  # seconds (15 minutes)
VIDEOS_PER_CATEGORY = 30  # number of videos to fetch per category

# =============================================================================
# AI MODEL SETTINGS (Loaded from .env)
# =============================================================================
AI_API_KEY = os.getenv("AI_API_KEY")
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://api.groq.com/openai/v1")
AI_MODEL = os.getenv("AI_MODEL", "llama-3.3-70b-versatile")

if not AI_API_KEY:
    print("⚠️ WARNING: AI_API_KEY not found in .env file.")

# =============================================================================
# WHISPER ASR SETTINGS
# =============================================================================
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

# =============================================================================
# CATEGORIES & SOURCES
# =============================================================================
CATEGORIES = {
  "daily_life": {
    "level": "A2",
    "sources": [
      {
        "name": "Learn English with Bob the Canadian",
        "url": "https://www.youtube.com/@LearnEnglishwithBobtheCanadian"
      },
      {
        "name": "English Addict with Mr Duncan",
        "url": "https://www.youtube.com/@EnglishAddict"
      },
      {
        "name": "Easy English",
        "url": "https://www.youtube.com/@EasyEnglishVideos"
      },
      {
        "name": "Speak English With Vanessa",
        "url": "https://www.youtube.com/@SpeakEnglishWithVanessa"
      },
      {
        "name": "English with Lucy",
        "url": "https://www.youtube.com/@EnglishwithLucy"
      },
      {
        "name": "mmmEnglish",
        "url": "https://www.youtube.com/@mmmEnglish_Emma"
      },
      {
        "name": "English with Jennifer",
        "url": "https://www.youtube.com/@JenniferESL"
      }
    ]
  },
  "business": {
    "level": "B1",
    "sources": [
      {
        "name": "Harvard Business Review",
        "url": "https://www.youtube.com/@HarvardBusinessReview"
      },
      {
        "name": "Business English Pod",
        "url": "https://www.youtube.com/@BusinessEnglishPod"
      },
      {
        "name": "Learn English with TV Series",
        "url": "https://www.youtube.com/@LearnEnglishWithTVSeries"
      },
      {
        "name": "7ESL Learning English",
        "url": "https://www.youtube.com/@7ESLlearningEnglish"
      },
      {
        "name": "Anglo-Link",
        "url": "https://www.youtube.com/@Anglo-Link"
      },
      {
        "name": "Learn English | Let's Talk",
        "url": "https://www.youtube.com/@letstalk"
      },
      {
        "name": "Rebecca ESL - engVid",
        "url": "https://www.youtube.com/@engvidRebecca"
      },
      {
        "name": "ETJ English",
        "url": "https://www.youtube.com/@ETJEnglish"
      },
      {
        "name": "ToFluency",
        "url": "https://www.youtube.com/@ToFluency"
      }
    ]
  },
  "science": {
    "level": "B1",
    "sources": [
      {
        "name": "Kurzgesagt – In a Nutshell",
        "url": "https://www.youtube.com/@kurzgesagt"
      },
      {
        "name": "Crash Course",
        "url": "https://www.youtube.com/@CrashCourse"
      },
      {
        "name": "AsapSCIENCE",
        "url": "https://www.youtube.com/@AsapSCIENCE"
      },
      {
        "name": "SciShow",
        "url": "https://www.youtube.com/@SciShow"
      },
      {
        "name": "Veritasium",
        "url": "https://www.youtube.com/@veritasium"
      },
      {
        "name": "Vsauce",
        "url": "https://www.youtube.com/@Vsauce"
      },
      {
        "name": "MinutePhysics",
        "url": "https://www.youtube.com/@MinutePhysics"
      },
      {
        "name": "National Geographic",
        "url": "https://www.youtube.com/@NatGeo"
      }
    ]
  },
  "technology": {
    "level": "B2",
    "sources": [
      {
        "name": "TED Talk",
        "url": "https://www.youtube.com/@TED"
      },
      {
        "name": "Marques Brownlee (MKBHD)",
        "url": "https://www.youtube.com/@mkbhd"
      },
      {
        "name": "Linus Tech Tips",
        "url": "https://www.youtube.com/@LinusTechTips"
      },
      {
        "name": "The Verge",
        "url": "https://www.youtube.com/@TheVerge"
      },
      {
        "name": "WIRED",
        "url": "https://www.youtube.com/@WIRED"
      },
      {
        "name": "ColdFusion",
        "url": "https://www.youtube.com/@ColdFusion"
      },
      {
        "name": "Tech Quickie",
        "url": "https://www.youtube.com/@TechLinked"
      },
      {
        "name": "Computerphile",
        "url": "https://www.youtube.com/@Computerphile"
      }
    ]
  },
  "health": {
    "level": "B1",
    "sources": [
      {
        "name": "Osmosis",
        "url": "https://www.youtube.com/@osmosis"
      }
    ]
  },
  "education": {
    "level": "A2",
    "sources": [
      {
        "name": "TED-Ed",
        "url": "https://www.youtube.com/@TEDEd"
      },
      {
        "name": "BBC Learning English",
        "url": "https://www.youtube.com/@bbclearningenglish"
      },
      {
        "name": "Khan Academy",
        "url": "https://www.youtube.com/@khanacademy"
      },
      {
        "name": "English Singsing",
        "url": "https://www.youtube.com/@EnglishSingsing"
      },
      {
        "name": "British Council | LearnEnglish",
        "url": "https://www.youtube.com/@BritishCouncilLearnEnglish"
      },
      {
        "name": "Simple English Videos",
        "url": "https://www.youtube.com/@SimpleEnglishVideos"
      }
    ]
  },
  "pronunciation": {
    "level": "A2-B2",
    "sources": [
      {
        "name": "Rachel's English",
        "url": "https://www.youtube.com/@rachelsenglish"
      },
      {
        "name": "Pronunciation with Emma",
        "url": "https://www.youtube.com/@PronunciationwithEmma"
      },
      {
        "name": "Fluent American English",
        "url": "https://www.youtube.com/@fluentamericanshadowing"
      },
      {
        "name": "Sounds American",
        "url": "https://www.youtube.com/@SoundsAmerican"
      },
      {
        "name": "Accent's Way English with Hadar",
        "url": "https://www.youtube.com/@accentsway"
      }
    ]
  },
  "conversation": {
    "level": "A2-B1",
    "sources": [
      {
        "name": "Real English",
        "url": "https://www.youtube.com/@realenglish1"
      },
      {
        "name": "Learn English with Context",
        "url": "https://www.youtube.com/@LearnEnglishwithContext"
      },
      {
        "name": "Learn English with Papa Teach Me",
        "url": "https://www.youtube.com/@papateachme"
      },
      {
        "name": "RealLife English",
        "url": "https://www.youtube.com/@RealLifeEnglish1"
      }
    ]
  },
  "grammar": {
    "level": "A2-B2",
    "sources": [
      {
        "name": "engVid",
        "url": "https://www.youtube.com/@engvidenglish"
      },
      {
        "name": "Learn English with Gill (engVid)",
        "url": "https://www.youtube.com/@engvidGill"
      },
      {
        "name": "Benjamin's English (engVid)",
        "url": "https://www.youtube.com/@engvidBenjamin"
      }
    ]
  },
  "vocabulary": {
    "level": "A2-C1",
    "sources": [
      {
        "name": "Learn English Lab",
        "url": "https://www.youtube.com/@LearnEnglishLab"
      },
      {
        "name": "Daily Video Vocabulary",
        "url": "https://www.youtube.com/@DailyVideoVocabulary"
      }
    ]
  },
  "listening": {
    "level": "A2-C1",
    "sources": [
      {
        "name": "Luke's English Podcast",
        "url": "https://www.youtube.com/@LukesEnglishPodcast"
      },
      {
        "name": "Learn English with EnglishClass101.com",
        "url": "https://www.youtube.com/@EnglishClass101"
      },
      {
        "name": "VOA Learning English",
        "url": "https://www.youtube.com/@VOALearningEnglish"
      },
      {
        "name": "English Pod",
        "url": "https://www.youtube.com/@EnglishPod101"
      },
      {
        "name": "High Level Listening",
        "url": "https://www.youtube.com/@highlevellistening"
      }
    ]
  },
  "news": {
    "level": "B1-C1",
    "sources": [
      {
        "name": "CNN 10",
        "url": "https://www.youtube.com/@CNN10"
      },
      {
        "name": "BBC World News",
        "url": "https://www.youtube.com/@BBCNews"
      },
      {
        "name": "Al Jazeera English",
        "url": "https://www.youtube.com/@AlJazeeraEnglish"
      }
    ]
  },
  "test_preparation": {
    "level": "B1-C1",
    "sources": [
      {
        "name": "E2 IELTS",
        "url": "https://www.youtube.com/@E2IELTS"
      },
      {
        "name": "E2 TOEFL",
        "url": "https://www.youtube.com/@E2TOEFL"
      },
      {
        "name": "IELTS Liz",
        "url": "https://www.youtube.com/@ieltsliz"
      },
      {
        "name": "TOEFL with Juva",
        "url": "https://www.youtube.com/@TOEFLwithJuva"
      },
      {
        "name": "TST Prep TOEFL",
        "url": "https://www.youtube.com/@TSTPrep"
      }
    ]
  },
  "kids_beginners": {
    "level": "A1",
    "sources": [
      {
        "name": "Super Simple Songs",
        "url": "https://www.youtube.com/@SuperSimpleSongs"
      },
      {
        "name": "Little Fox",
        "url": "https://www.youtube.com/@LittleFox"
      },
      {
        "name": "British Council | LearnEnglish Kids",
        "url": "https://www.youtube.com/@LearnEnglishKids"
      },
      {
        "name": "Fun Kids English",
        "url": "https://www.youtube.com/@FunKidsEnglish"
      },
      {
        "name": "Cocomelon",
        "url": "https://www.youtube.com/@Cocomelon"
      }
    ]
  },
  "idioms_slang": {
    "level": "B2-C1",
    "sources": []
  },
  "travel_culture": {
    "level": "B1-B2",
    "sources": [
      {
        "name": "Mark Wiens",
        "url": "https://www.youtube.com/@MarkWiens"
      },
      {
        "name": "Drew Binsky",
        "url": "https://www.youtube.com/@drewbinsky"
      },
      {
        "name": "Rick Steves' Europe",
        "url": "https://www.youtube.com/@ricksteves"
      }
    ]
  },
  "entertainment": {
    "level": "B1-C1",
    "sources": [
      {
        "name": "Netflix",
        "url": "https://www.youtube.com/@netflix"
      },
      {
        "name": "The Tonight Show Starring Jimmy Fallon",
        "url": "https://www.youtube.com/@fallontonight"
      },
      {
        "name": "The Late Show with Stephen Colbert",
        "url": "https://www.youtube.com/@colbert"
      },
      {
        "name": "Saturday Night Live",
        "url": "https://www.youtube.com/@SaturdayNightLive"
      }
    ]
  },
  "motivation": {
    "level": "B2-C1",
    "sources": [
      {
        "name": "TEDx Talks",
        "url": "https://www.youtube.com/@TEDx"
      },
      {
        "name": "Jay Shetty",
        "url": "https://www.youtube.com/@JayShettyPodcast"
      },
      {
        "name": "Motivation Madness",
        "url": "https://www.youtube.com/@MotivationMadness"
      }
    ]
  },
  "advanced_learners": {
    "level": "C1-C2",
    "sources": [
      {
        "name": "The School of Life",
        "url": "https://www.youtube.com/@TheSchoolofLife"
      }
    ]
  }
}
