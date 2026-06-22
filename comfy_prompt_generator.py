#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ComfyUI Prompt Generator
========================
ComfyUI / Stable Diffusion 용 긍정문(positive) · 부정문(negative) 프롬프트 생성기.

- 추가 설치 필요 없음 (파이썬 표준 라이브러리만 사용, GUI 는 tkinter)
- GUI 모드:  python comfy_prompt_generator.py
- CLI 모드:  python comfy_prompt_generator.py --cli ...

스타일 : realistic(실사) / anime(애니) / fantasy(판타지/컨셉아트)
옵션   : 샷(shot) / 앵글(angle) / 표정(expression) / 포즈(pose) /
         인원수(count) / 주인공 지정(main) / 한글 자동 번역(--translate)

CLI 예시
--------
  # 실사, 전신, 로우앵글, 미소
  python comfy_prompt_generator.py --cli --style realistic \
      --shot full-body --angle low --expr smile --pose standing

  # 애니, 2명에서 주인공 강조 (한글 입력 자동 번역)
  python comfy_prompt_generator.py --cli --style anime --count 2 \
      --main "빨간머리 기사" --main-focus --translate

  # 옵션/태그 목록
  python comfy_prompt_generator.py --cli --list
"""

from __future__ import annotations

import argparse
import random
import re
import sys
import textwrap

# ---------------------------------------------------------------------------
# 1. 태그 라이브러리 (스타일별)
# ---------------------------------------------------------------------------
STYLES = {
    "realistic": {
        "label": "실사 / 포토리얼리즘",
        "quality": [
            "masterpiece", "best quality", "ultra detailed", "8k uhd",
            "photorealistic", "RAW photo", "high resolution",
        ],
        "subject": [
            "portrait of a woman", "portrait of a man",
            "elderly fisherman", "young athlete", "businesswoman",
            "street musician", "ballet dancer",
        ],
        "appearance": [
            "detailed skin texture", "freckles", "natural makeup",
            "wavy brown hair", "short black hair", "blue eyes",
            "athletic build", "elegant dress", "casual streetwear",
        ],
        "scene": [
            "in a cozy cafe", "on a city street at night", "in a sunlit forest",
            "on a beach at sunset", "in a modern studio", "in an old library",
        ],
        "lighting": [
            "soft natural lighting", "golden hour lighting", "rim lighting",
            "cinematic lighting", "studio softbox lighting", "dramatic shadows",
        ],
        "camera": [
            "shot on Canon EOS R5", "85mm f/1.4 lens", "shallow depth of field",
            "bokeh background", "sharp focus", "professional color grading",
        ],
    },
    "anime": {
        "label": "애니 / 일러스트",
        "quality": [
            "masterpiece", "best quality", "amazing quality", "very aesthetic",
            "highly detailed", "absurdres",
        ],
        "subject": [
            "magical girl", "samurai warrior", "school student",
            "idol singer", "swordsman", "witch", "knight",
        ],
        "appearance": [
            "long flowing hair", "twin tails", "cat ears", "heterochromia",
            "school uniform", "kimono", "fantasy armor", "hoodie",
            "detailed eyes", "blush",
        ],
        "scene": [
            "cherry blossom background", "futuristic city", "classroom",
            "starry night sky", "floating islands", "rainy street",
        ],
        "lighting": [
            "soft lighting", "vibrant colors", "glowing particles",
            "sunset glow", "neon lights", "god rays",
        ],
        "camera": [
            "dynamic angle", "depth of field", "detailed background",
            "lens flare", "vignette", "wide shot",
        ],
    },
    "fantasy": {
        "label": "판타지 / 컨셉아트",
        "quality": [
            "masterpiece", "best quality", "concept art", "highly detailed",
            "trending on artstation", "cinematic", "intricate details",
        ],
        "subject": [
            "ancient dragon", "elven ranger", "dwarven blacksmith",
            "floating sky castle", "enchanted forest", "cyberpunk mercenary",
            "celestial goddess",
        ],
        "appearance": [
            "ornate armor", "glowing runes", "flowing robes",
            "battle-worn cloak", "bioluminescent details", "crystal weapon",
            "intricate tattoos",
        ],
        "scene": [
            "epic mountain landscape", "ruined temple", "underground cavern",
            "alien planet", "stormy ocean", "neon-lit megacity",
        ],
        "lighting": [
            "volumetric lighting", "dramatic atmosphere", "ethereal glow",
            "moody fog", "backlit silhouette", "magical aura",
        ],
        "camera": [
            "epic wide shot", "matte painting", "8k",
            "unreal engine render", "octane render", "depth of field",
        ],
    },
    "creature": {
        "label": "크리쳐 / 몬스터 디자인",
        "quality": [
            "creature concept art", "masterpiece", "highly detailed",
            "intricate details", "trending on artstation", "sharp focus",
            "hyper detailed",
        ],
        "subject": [
            "fearsome dragon", "eldritch horror", "armored beast",
            "insectoid alien", "aquatic leviathan", "forest spirit creature",
            "undead abomination", "chimera monster", "demonic hound",
            "colossal kaiju", "mutated predator", "winged serpent",
        ],
        "appearance": [
            "scaled hide", "chitinous armor plates", "matted fur",
            "bioluminescent veins", "multiple glowing eyes", "razor-sharp claws",
            "bony protruding spikes", "writhing tentacles", "gaping maw with fangs",
            "leathery membrane wings", "rotting exposed flesh", "translucent skin",
            "horned crest", "barbed tail",
        ],
        "scene": [
            "dark cavern", "misty swamp", "alien planet surface",
            "volcanic wasteland", "ancient overgrown ruins",
            "deep ocean trench", "haunted forest", "barren frozen tundra",
        ],
        "lighting": [
            "dramatic rim lighting", "eerie glow", "volumetric fog",
            "moody backlight", "subsurface scattering", "harsh shadows",
            "ominous atmosphere",
        ],
        "camera": [
            "full body creature concept", "dynamic low angle", "cinematic",
            "8k", "octane render", "detailed texture", "creature turnaround",
        ],
    },
    "mature": {
        "label": "성인 무드 (우아·비노골적)",
        "quality": [
            "masterpiece", "best quality", "photorealistic", "elegant",
            "fashion editorial", "ultra detailed", "high resolution",
        ],
        "subject": [
            "elegant woman", "fashion model", "elegant man in a suit",
            "glamorous portrait", "graceful dancer", "stylish model",
        ],
        "appearance": [
            "elegant evening gown", "silk robe", "one-piece swimsuit",
            "off-shoulder dress", "lace detailing", "tasteful makeup",
            "flowing hair", "delicate jewelry", "confident expression",
            "graceful posture",
        ],
        "scene": [
            "luxurious boudoir interior", "elegant lounge", "poolside resort",
            "art studio", "softly lit bedroom", "marble bathroom",
            "sunlit balcony",
        ],
        "lighting": [
            "soft window light", "warm intimate lighting", "golden hour glow",
            "cinematic soft light", "rim lighting", "candlelight ambience",
        ],
        "camera": [
            "fashion editorial", "85mm portrait", "shallow depth of field",
            "professional photography", "elegant composition", "soft focus",
        ],
    },
}

# ---------------------------------------------------------------------------
# 2. 공통 옵션 — (한글 라벨, CLI 슬러그, 영어 태그)
#    GUI/CLI 가 같은 표를 공유한다 (중복 정의 제거).
#    슬러그가 "" 인 항목은 '지정 안 함' 이며 CLI 선택지에서 제외된다.
# ---------------------------------------------------------------------------
SHOT_SIZES = [
    ("지정 안 함", "", ""),
    ("익스트림 클로즈업", "extreme-closeup", "extreme close-up"),
    ("클로즈업(얼굴)", "closeup", "close-up, face focus"),
    ("포트레이트(얼굴~어깨)", "portrait", "portrait"),
    ("상반신", "upper-body", "upper body"),
    ("미디엄샷(허리 위)", "medium", "medium shot"),
    ("카우보이샷(허벅지 위)", "cowboy", "cowboy shot"),
    ("전신", "full-body", "full body shot"),
    ("와이드샷(멀리)", "wide", "wide shot"),
    ("롱샷(아주 멀리)", "long", "extreme long shot, scenery"),
    ("뒷모습 전신", "back-full", "from behind, full body, back view"),
    ("뒷모습 상반신", "back-upper", "from behind, upper body, back view"),
    ("뒷모습 클로즈업", "back-closeup", "from behind, close-up, back view"),
]

CAMERA_ANGLES = [
    ("지정 안 함", "", ""),
    ("정면", "front", "front view"),
    ("측면", "side", "side view"),
    ("로우앵글(아래에서)", "low", "from below, low angle"),
    ("하이앵글(위에서)", "high", "from above, high angle"),
    ("버드아이뷰", "birdseye", "bird's-eye view"),
    ("더치앵글(기울임)", "dutch", "dutch angle, tilted view"),
    ("어안(피시아이)", "fisheye", "fisheye lens, distorted perspective"),
    ("광각", "wide-angle", "wide-angle lens"),
    ("3/4 시점", "three-quarter", "three-quarter view"),
    ("정수리뷰(머리 위)", "overhead", "overhead shot, from directly above"),
    ("올려다봄", "looking-up", "looking up at subject"),
    ("POV(1인칭)", "pov", "pov"),
    ("뒤에서(뒷모습)", "behind", "from behind, back view"),
]

EXPRESSIONS = [
    ("지정 안 함", "", ""),
    ("미소", "smile", "smile"),
    ("활짝 웃음", "happy", "happy, open mouth, laughing"),
    ("무표정", "neutral", "expressionless"),
    ("진지함", "serious", "serious expression"),
    ("슬픔", "sad", "sad"),
    ("화남", "angry", "angry"),
    ("놀람", "surprised", "surprised"),
    ("부끄러움", "shy", "blush, shy"),
    ("윙크", "wink", "wink, one eye closed"),
    ("울음", "crying", "crying, tears"),
]

# 포즈: 다중 선택(체크) — (라벨, 슬러그, 태그)
POSES = [
    ("서 있음", "standing", "standing"),
    ("앉아 있음", "sitting", "sitting"),
    ("무릎 꿇기", "kneeling", "kneeling"),
    ("걷기", "walking", "walking"),
    ("달리기", "running", "running"),
    ("역동적 액션", "action", "dynamic action pose"),
    ("누워 있음", "lying", "lying down"),
    ("기대어 있음", "leaning", "leaning"),
    ("점프", "jumping", "jumping"),
    ("춤추기", "dancing", "dancing"),
    ("싸우는 자세", "fighting", "fighting stance"),
    ("팔짱", "arms-crossed", "crossed arms"),
    ("손 흔들기", "waving", "waving"),
    ("스트레칭", "stretching", "stretching"),
    ("정면 응시", "look-viewer", "looking at viewer"),
]

# 인원수: 단일 선택 — (라벨, key, 태그)
COUNTS = [
    ("1명 (solo)", "solo", "solo"),
    ("2명", "2", "2people, two characters"),
    ("3명", "3", "3people, group of three"),
    ("4명", "4", "4people, group"),
    ("여러 명/군중", "crowd", "crowd, multiple people"),
]

# --- 위 표에서 파생되는 조회용 딕셔너리 (단일 진실 공급원) ---
def _cli_map(rows: list[tuple[str, str, str]]) -> dict[str, str]:
    """(라벨, 슬러그, 태그) 표에서 슬러그→태그 딕셔너리 생성 (빈 슬러그 제외)."""
    return {slug: tag for _, slug, tag in rows if slug}


SHOT_CLI = _cli_map(SHOT_SIZES)
ANGLE_CLI = _cli_map(CAMERA_ANGLES)
EXPR_CLI = _cli_map(EXPRESSIONS)
POSE_CLI = _cli_map(POSES)
COUNT_TAG = {key: tag for _, key, tag in COUNTS}

# ---------------------------------------------------------------------------
# 3. 한글 → 영어 태그 사전 (오프라인 간이 번역)
# ---------------------------------------------------------------------------
# 자유 입력(주제/주인공)에 쓰인 한글 단어를 영어 태그로 치환한다.
# 긴 표현부터 먼저 치환하므로 '빨간머리' 가 '빨간'보다 우선한다.
KO_EN = {
    # 머리색
    "빨간머리": "red hair", "빨강머리": "red hair", "금발": "blonde hair",
    "흑발": "black hair", "검은머리": "black hair", "갈색머리": "brown hair",
    "은발": "silver hair", "백발": "white hair", "파란머리": "blue hair",
    "분홍머리": "pink hair", "보라머리": "purple hair", "초록머리": "green hair",
    # 머리모양
    "긴머리": "long hair", "단발": "short hair", "트윈테일": "twintails",
    "포니테일": "ponytail", "곱슬머리": "curly hair", "땋은머리": "braided hair",
    "머리": "hair",
    # 눈
    "파란눈": "blue eyes", "갈색눈": "brown eyes", "초록눈": "green eyes",
    "빨간눈": "red eyes", "금색눈": "golden eyes",
    # 인물
    "소녀": "1girl", "여자": "1girl", "여성": "woman", "소년": "1boy",
    "남자": "1boy", "남성": "man", "아이": "child", "할아버지": "old man",
    "할머니": "old woman",
    # 직업/종족
    "기사": "knight", "마법사": "mage", "전사": "warrior", "궁수": "archer",
    "닌자": "ninja", "사무라이": "samurai", "공주": "princess", "왕자": "prince",
    "왕": "king", "여왕": "queen", "메이드": "maid", "천사": "angel",
    "악마": "demon", "마녀": "witch", "흡혈귀": "vampire", "로봇": "robot",
    "기계": "mecha", "용": "dragon", "드래곤": "dragon", "엘프": "elf",
    "고양이귀": "cat ears", "여우귀": "fox ears", "해적": "pirate",
    # 의상
    "교복": "school uniform", "기모노": "kimono", "드레스": "dress",
    "갑옷": "armor", "정장": "suit", "후드티": "hoodie", "수영복": "swimsuit",
    "코트": "coat", "망토": "cloak", "로브": "robe", "치마": "skirt",
    "셔츠": "shirt", "바지": "pants",
    # 색
    "빨간": "red", "빨강": "red", "파란": "blue", "파랑": "blue",
    "초록": "green", "노란": "yellow", "노랑": "yellow", "검은": "black",
    "검정": "black", "하얀": "white", "흰": "white", "보라": "purple",
    "분홍": "pink", "주황": "orange", "금색": "gold", "은색": "silver",
    # 소품
    "안경": "glasses", "모자": "hat", "검": "sword", "칼": "sword",
    "활": "bow", "방패": "shield", "지팡이": "staff", "총": "gun",
    "날개": "wings", "꽃": "flowers", "왕관": "crown",
    # 배경/날씨
    "밤": "night", "낮": "daytime", "비": "rain", "눈내림": "snow",
    "눈오는": "snowing", "숲": "forest", "도시": "city", "바다": "ocean",
    "하늘": "sky", "성": "castle", "우주": "space", "사막": "desert",
    "산": "mountains", "벚꽃": "cherry blossoms",
    # 국적/인종
    "일본인": "japanese", "한국인": "korean", "중국인": "chinese",
    "서양인": "western", "동양인": "asian", "흑인": "dark skin",
    "백인": "pale skin",
    # 성격/분위기 (표정·인상으로 반영)
    "건방진": "arrogant", "도도한": "smug", "성격": "personality",
    "친절한": "friendly", "차가운": "cold expression", "활발한": "cheerful",
    "수줍은": "shy", "어두운": "gloomy", "당당한": "confident",
    "사나운": "fierce", "냉정한": "calm", "귀여운": "cute", "섹시한": "sexy",
    "우아한": "elegant", "강한": "strong", "신비로운": "mysterious",
    # 나이/체형
    "젊은": "young", "어린": "young", "늙은": "old", "중년": "middle-aged",
    "키큰": "tall", "마른": "slim", "근육질": "muscular", "통통한": "chubby",
    # 색 + '색' 형태
    "빨간색": "red", "빨강색": "red", "파란색": "blue", "파랑색": "blue",
    "노란색": "yellow", "노랑색": "yellow", "초록색": "green", "녹색": "green",
    "검은색": "black", "검정색": "black", "하얀색": "white", "흰색": "white",
    "보라색": "purple", "분홍색": "pink", "주황색": "orange", "회색": "gray",
    "갈색": "brown", "금색": "gold", "은색": "silver", "하늘색": "sky blue",
    "남색": "navy blue", "탁한": "muddy", "밝은": "bright", "어두운색": "dark",
    "파스텔": "pastel",
}


def _has_hangul(text: str) -> bool:
    return any("가" <= ch <= "힣" for ch in text)


_TOKEN_SPLIT = re.compile(r"([,\s]+)")


def translate_glossary(text: str | None) -> str | None:
    """내장 사전으로 단어 단위 치환(오프라인).

    공백/쉼표로 나뉜 '단어 단위'로만 치환한다. 사전에 없는 한글 단어는
    그대로 둔다(부분 치환으로 '용감한'→'dragon감한' 처럼 망가지는 것 방지).
    """
    if not text:
        return text
    return "".join(KO_EN.get(tok, tok) for tok in _TOKEN_SPLIT.split(text))


def translate_online(text: str, timeout: float = 6.0) -> str:
    """구글(비공식) 엔드포인트로 임의의 한글을 영어로 번역. 실패 시 예외."""
    import urllib.request
    import urllib.parse
    import json

    url = ("https://translate.googleapis.com/translate_a/single"
           "?client=gtx&sl=ko&tl=en&dt=t&q=" + urllib.parse.quote(text))
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    out = "".join(seg[0] for seg in data[0] if seg and seg[0])
    if not out.strip():
        raise ValueError("빈 번역 결과")
    return out


def translate_text(text: str | None, online: bool = True,
                   cache: dict | None = None) -> tuple[str | None, str]:
    """한글을 영어로 번역. (결과, 엔진) 반환.

    online=True 면 온라인 번역을 먼저 시도하고, 실패하면 내장 사전으로 폴백.
    엔진 값: 'online' / 'glossary' / 'none'(한글 없음/빈값).
    """
    if not text or not _has_hangul(text):
        return text, "none"
    if cache is not None and text in cache:
        return cache[text]
    result, engine = text, "glossary"
    if online:
        try:
            result, engine = translate_online(text), "online"
        except Exception:
            result, engine = translate_glossary(text), "glossary"
    else:
        result = translate_glossary(text)
    pair = (result, engine)
    if cache is not None:
        cache[text] = pair
    return pair


# ---------------------------------------------------------------------------
# 4. 부정문(negative) 프리셋
# ---------------------------------------------------------------------------
NEGATIVE_COMMON = [
    "lowres", "bad anatomy", "bad hands", "extra digits", "fewer digits",
    "cropped", "worst quality", "low quality", "jpeg artifacts",
    "signature", "watermark", "username", "blurry", "text", "error",
    "out of frame", "deformed", "mutated", "ugly", "duplicate",
]

NEGATIVE_BY_STYLE = {
    "realistic": [
        "cartoon", "anime", "illustration", "painting", "3d render",
        "plastic skin", "overexposed", "extra limbs", "disfigured face",
    ],
    "anime": [
        "extra fingers", "fused fingers", "long neck", "bad proportions",
        "poorly drawn face", "poorly drawn hands", "missing limb",
        "extra arms", "extra legs", "censored",
    ],
    "fantasy": [
        "flat lighting", "boring composition", "low detail",
        "amateur", "bad perspective", "oversaturated", "noise",
    ],
    "creature": [
        "cute", "human face", "humanoid", "cartoonish", "flat colors",
        "low detail", "boring design", "plain background", "poorly drawn",
        "amateur", "blurry", "duplicate",
    ],
    # 비노골적 유지를 위해 명시적/노출 태그를 강하게 차단
    "mature": [
        "nsfw", "nude", "nudity", "explicit", "sexual", "pornographic",
        "exposed", "topless", "see-through", "cleavage focus",
        "plastic skin", "overexposed", "extra limbs", "disfigured face",
    ],
}


# ---------------------------------------------------------------------------
# 5. 프롬프트 빌드 로직
# ---------------------------------------------------------------------------
def _dedupe(parts: list[str]) -> list[str]:
    seen: set[str] = set()
    return [p for p in parts if p and not (p in seen or seen.add(p))]


def build_positive(style: str, subject: str | None = None,
                   randomize: bool = True, seed: int | None = None,
                   shot: str = "", angle: str = "",
                   expression: str = "", poses: list[str] | None = None,
                   count: str = "solo", main_subject: str | None = None,
                   main_focus: bool = False, character: str | None = None,
                   background: str | None = None,
                   situation: str | None = None,
                   emphasis: bool = False, emphasis_weight: float = 1.4,
                   extra_tags: list[str] | None = None) -> str:
    """긍정문(positive) 프롬프트 생성.

    인물/배경/상황을 따로 받는다.
      character  : 인물 묘사 (예: "korean girl, long black hair").
      background : 배경/장소 (예: "rainy neon city"). 주면 랜덤 배경 대신 사용.
      situation  : 상황/행동/분위기 (예: "drinking coffee, relaxed").
      subject    : 옛 단일 입력 — character 의 별칭(하위호환).
    나머지 옵션은 shot/angle/expression/poses/count/main_* 참고.
    """
    if style not in STYLES:
        raise ValueError(f"알 수 없는 스타일: {style!r} (가능: {', '.join(STYLES)})")

    rng = random.Random(seed)
    data = STYLES[style]
    poses = poses or []
    multi = count not in ("solo", None, "")
    character = (character or subject or "").strip()
    background = (background or "").strip()
    situation = (situation or "").strip()
    has_main = bool(multi and main_subject)
    # 인물이 직접 지정됐는지(주인공 또는 인물칸). True 면 랜덤 인물/외형을 안 넣어
    # 사용자가 적은 인물과 충돌하지 않게 한다.
    person_specified = bool(character) or has_main

    def pick(category: str, k: int = 1) -> list[str]:
        pool = data[category]
        if randomize:
            return rng.sample(pool, min(k, len(pool)))
        return pool[:k]

    def pick_subject() -> str:
        # 인원수 태그가 숫자를 책임지므로, 자동 선택 풀에서는 '1girl/2girls'
        # 같이 숫자로 시작하는 주제를 제외해 'solo, 2girls' 모순을 막는다.
        pool = [s for s in data["subject"] if not s[:1].isdigit()] or data["subject"]
        return rng.choice(pool) if randomize else pool[0]

    parts: list[str] = []
    # (1) 품질
    parts += pick("quality", 3 if randomize else 2)
    # (2) 인원수
    parts.append(COUNT_TAG.get(count, ""))
    # (3) 인물 / 주인공
    if has_main:
        if main_focus:  # 가중치 + solo focus + 시선 유도
            parts += [f"({main_subject.strip()}:1.3)", "solo focus",
                      "looking at viewer"]
        else:
            parts.append(main_subject.strip())
    if character:
        parts.append(character)
    elif not person_specified:
        parts.append(pick_subject())
    # (4) 포즈 / 표정 / 상황
    parts += poses
    if expression:
        parts.append(expression)
    if situation:
        parts.append(situation)
    if extra_tags:
        parts += [t for t in extra_tags if t]
    # (5) 샷 / 앵글 — emphasis 면 가중치로 강하게 주입
    def emph(tag: str) -> str:
        return f"({tag}:{emphasis_weight:g})" if emphasis else tag

    if shot:
        parts.append(emph(shot))
    if angle:
        parts.append(emph(angle))
    # (6) 플레이버 — 인물을 직접 적었으면 랜덤 외형은 생략
    if not person_specified:
        parts += pick("appearance", 2)
    # 배경: 지정했으면 그대로, 아니면 랜덤
    parts.append(background if background else pick("scene", 1)[0])
    parts += pick("lighting", 1)
    if not shot and not angle:  # 프레이밍을 안 정했으면 카메라 태그 보강
        parts += pick("camera", 1)

    return ", ".join(_dedupe(parts))


def build_negative(style: str) -> str:
    tags = list(NEGATIVE_COMMON) + NEGATIVE_BY_STYLE.get(style, [])
    return ", ".join(_dedupe(tags))


def generate(style: str, **kwargs) -> dict:
    return {
        "style": style,
        "positive": build_positive(style, **kwargs),
        "negative": build_negative(style),
    }


MAIN_GUIDE = """\
[ 다수 인물에서 '주인공'을 정하는 방법 ]

1) 순서 — 프롬프트 맨 앞에 둘수록 모델이 더 강하게 반영합니다.
   예) 2girls, (red-haired knight ...), background girl ...

2) 가중치 — 괄호와 숫자로 강조.  (대상:1.3) 처럼 1.1~1.4 권장.
   예) (red-haired knight:1.3)
   ※ 이 프로그램의 '주인공 강조' 체크가 자동으로 넣어줍니다.

3) solo focus 태그 — 여러 명이어도 한 명에 초점을 맞춥니다(부루/애니 모델).
   + 'looking at viewer' 로 주인공의 시선을 카메라로 유도.

4) BREAK 키워드 — 인물 묘사를 분리해 섞임(색 번짐)을 줄입니다.
   예) 2girls, BREAK, (red knight, red hair), BREAK, (blue mage, blue hair)

5) 가장 정확한 방법 = 리저널 프롬프트(영역 분리).
   ComfyUI 커스텀 노드를 쓰면 화면을 좌/우 등으로 나눠 인물별 프롬프트를
   따로 적용합니다. 색·의상 섞임이 거의 없어집니다.
   - 추천 노드: 'Attention Couple', 'Regional Prompter',
     기본 노드 'Conditioning (Set Area)' / 'Conditioning (Combine)'
   - 흐름: 인물별로 CLIP Text Encode → 각 영역(Set Area) 지정 → Combine
     → 하나의 conditioning 으로 KSampler 에 연결.

요약: 간단히는 (1)(2)(3), 확실히는 (5) 리저널 프롬프트를 쓰세요.
"""


# ---------------------------------------------------------------------------
# 6. CLI
# ---------------------------------------------------------------------------
def run_cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="comfy_prompt_generator --cli",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="ComfyUI 용 긍정/부정 프롬프트 생성 (CLI)",
    )
    parser.add_argument("--cli", action="store_true", help="CLI 모드로 실행")
    parser.add_argument("--style", choices=list(STYLES), default="realistic",
                        help="그림 스타일 (기본: realistic)")
    parser.add_argument("--subject", default=None,
                        help="(구) 단일 주제 — --character 의 별칭")
    parser.add_argument("--character", default=None,
                        help="인물 묘사 (예: 'korean girl, long black hair')")
    parser.add_argument("--background", default=None,
                        help="배경/장소 (예: 'rainy neon city')")
    parser.add_argument("--situation", default=None,
                        help="상황/행동/분위기 (예: 'drinking coffee, relaxed')")
    parser.add_argument("--no-random", dest="randomize", action="store_false",
                        default=True, help="무작위 대신 대표 태그 사용")
    parser.add_argument("--shot", choices=list(SHOT_CLI), default=None,
                        help="샷 크기: " + ", ".join(SHOT_CLI))
    parser.add_argument("--angle", choices=list(ANGLE_CLI), default=None,
                        help="카메라 앵글: " + ", ".join(ANGLE_CLI))
    parser.add_argument("--expr", choices=list(EXPR_CLI), default=None,
                        help="표정: " + ", ".join(EXPR_CLI))
    parser.add_argument("--pose", action="append", default=[],
                        choices=list(POSE_CLI),
                        help="포즈(여러 번 사용 가능): " + ", ".join(POSE_CLI))
    parser.add_argument("--count", choices=[k for _, k, _ in COUNTS],
                        default="solo", help="인원수 (기본 solo)")
    parser.add_argument("--main", dest="main_subject", default=None,
                        help="다수일 때 주인공 묘사")
    parser.add_argument("--main-focus", dest="main_focus", action="store_true",
                        help="주인공에 가중치+solo focus 로 강조")
    parser.add_argument("--no-emphasis", dest="emphasis", action="store_false",
                        default=True,
                        help="샷/앵글 가중치 강조를 끔 (기본은 강조 ON)")
    parser.add_argument("--emph-weight", dest="emph_weight", type=float,
                        default=1.4, help="샷/앵글 강조 가중치 (기본 1.4)")
    parser.add_argument("--translate", action="store_true",
                        help="주제/주인공의 한글을 영어로 자동 변환(온라인+사전 폴백)")
    parser.add_argument("--offline-translate", dest="offline_tr",
                        action="store_true",
                        help="번역 시 온라인을 끄고 내장 사전만 사용")
    parser.add_argument("-n", "--num", dest="num", type=int, default=1,
                        help="생성할 프롬프트 개수")
    parser.add_argument("--seed", type=int, default=None, help="랜덤 시드")
    parser.add_argument("--list", action="store_true", help="옵션/태그 목록")
    parser.add_argument("--help-main", action="store_true",
                        help="주인공 지정 방법 설명 출력")
    args = parser.parse_args(argv)

    if args.help_main:
        print(MAIN_GUIDE)
        return 0

    if args.list:
        for key, data in STYLES.items():
            print(f"\n■ {key}  ({data['label']})")
            for cat, tags in data.items():
                if cat == "label":
                    continue
                print(f"   - {cat:11s}: {', '.join(tags)}")
        print("\n■ 샷   (--shot) :  " + ", ".join(SHOT_CLI))
        print("■ 앵글  (--angle):  " + ", ".join(ANGLE_CLI))
        print("■ 표정  (--expr) :  " + ", ".join(EXPR_CLI))
        print("■ 포즈  (--pose) :  " + ", ".join(POSE_CLI))
        print("■ 인원수(--count):  " + ", ".join(k for _, k, _ in COUNTS))
        return 0

    # 주인공 지정했는데 인원수가 solo 면 자동으로 2명으로 올린다(버그 #2 수정).
    if args.main_subject and args.count == "solo":
        print("ℹ️  --main 이 지정되어 인원수를 자동으로 '2명'으로 설정합니다.")
        args.count = "2"

    fields = {
        "character": args.character or args.subject,
        "background": args.background,
        "situation": args.situation,
        "main_subject": args.main_subject,
    }
    if args.translate or args.offline_tr:
        use_online = not args.offline_tr
        labels = {"character": "인물", "background": "배경",
                  "situation": "상황", "main_subject": "주인공"}
        engines: set[str] = set()
        for key, val in list(fields.items()):
            fields[key], eng = translate_text(val, online=use_online)
            if eng != "none":
                engines.add(eng)
            if fields[key] and _has_hangul(fields[key]):
                print(f"⚠️  {labels[key]}에 번역 안 된 한글이 남아 있습니다: "
                      f"{fields[key]}")
        if engines:
            print(f"🌐 번역 엔진: {', '.join(sorted(engines))}")

    shot_tag = SHOT_CLI.get(args.shot, "") if args.shot else ""
    angle_tag = ANGLE_CLI.get(args.angle, "") if args.angle else ""
    expr_tag = EXPR_CLI.get(args.expr, "") if args.expr else ""
    pose_tags = [POSE_CLI[p] for p in args.pose]

    for i in range(max(1, args.num)):
        seed = args.seed if args.seed is None else args.seed + i
        result = generate(
            args.style, character=fields["character"],
            background=fields["background"], situation=fields["situation"],
            randomize=args.randomize, seed=seed, shot=shot_tag,
            angle=angle_tag, expression=expr_tag, poses=pose_tags,
            count=args.count, main_subject=fields["main_subject"],
            main_focus=args.main_focus, emphasis=args.emphasis,
            emphasis_weight=args.emph_weight,
        )
        header = f" 프롬프트 #{i + 1} [{args.style}] "
        print("\n" + header.center(60, "="))
        print("\n[ Positive ]")
        print(textwrap.fill(result["positive"], width=72, subsequent_indent="  "))
        print("\n[ Negative ]")
        print(textwrap.fill(result["negative"], width=72, subsequent_indent="  "))
    print()
    return 0


# ---------------------------------------------------------------------------
# 7. GUI (tkinter)
# ---------------------------------------------------------------------------
def run_gui() -> int:
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox, scrolledtext
    except Exception as exc:  # pragma: no cover
        print("tkinter 를 불러올 수 없습니다. CLI 모드를 사용하세요:")
        print("  python comfy_prompt_generator.py --cli --help")
        print(f"(원인: {exc})")
        return 1

    state = {"seed": None, "after": None, "tcache": {}}

    root = tk.Tk()
    root.title("ComfyUI 프롬프트 생성기")
    root.geometry("1040x720")
    root.minsize(900, 600)

    # 좌(옵션) | 우(결과) 2단 분할
    paned = ttk.PanedWindow(root, orient="horizontal")
    paned.pack(fill="both", expand=True)

    # ---- 왼쪽: 스크롤 가능한 옵션 패널 ----
    left_wrap = ttk.Frame(paned)
    paned.add(left_wrap, weight=0)
    canvas = tk.Canvas(left_wrap, width=380, highlightthickness=0)
    vsb = ttk.Scrollbar(left_wrap, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    left = ttk.Frame(canvas, padding=10)
    canvas.create_window((0, 0), window=left, anchor="nw")
    left.bind("<Configure>",
              lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind_all(
        "<MouseWheel>",
        lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"))

    # ---- 오른쪽: 결과 프리뷰 ----
    right = ttk.Frame(paned, padding=10)
    paned.add(right, weight=1)

    # === 왼쪽 컨트롤 ===
    ttk.Label(left, text="스타일:").pack(anchor="w")
    style_combo = ttk.Combobox(
        left, state="readonly", width=28,
        values=[f"{k} ({v['label']})" for k, v in STYLES.items()])
    style_combo.current(0)
    style_combo.pack(anchor="w", fill="x", pady=(0, 6))

    toggles = ttk.Frame(left)
    toggles.pack(anchor="w", fill="x", pady=(0, 6))
    randomize_var = tk.BooleanVar(value=True)
    translate_var = tk.BooleanVar(value=True)
    emphasis_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(toggles, text="무작위", variable=randomize_var,
                    command=lambda: do_generate()).pack(side="left")
    ttk.Checkbutton(toggles, text="한글번역", variable=translate_var,
                    command=lambda: do_generate()).pack(side="left", padx=6)
    ttk.Checkbutton(toggles, text="시점·샷 강조", variable=emphasis_var,
                    command=lambda: do_generate()).pack(side="left")

    def add_field(label):
        ttk.Label(left, text=label).pack(anchor="w")
        var = tk.StringVar()
        ent = ttk.Entry(left, textvariable=var)
        ent.pack(anchor="w", fill="x", pady=(0, 4))
        ent.bind("<KeyRelease>", lambda e: schedule_generate())
        return var

    character_var = add_field("인물:")
    background_var = add_field("배경:")
    situation_var = add_field("상황:")

    ttk.Separator(left, orient="horizontal").pack(fill="x", pady=6)

    def add_combo(label, rows):
        row = ttk.Frame(left)
        row.pack(anchor="w", fill="x", pady=1)
        ttk.Label(row, text=label, width=7).pack(side="left")
        cb = ttk.Combobox(row, state="readonly", width=24,
                          values=[r[0] for r in rows])
        cb.current(0)
        cb.pack(side="left", fill="x", expand=True)
        cb.bind("<<ComboboxSelected>>", lambda e: do_generate())
        return cb

    shot_combo = add_combo("샷:", SHOT_SIZES)
    angle_combo = add_combo("앵글:", CAMERA_ANGLES)
    expr_combo = add_combo("표정:", EXPRESSIONS)

    # 인원수 (라디오) — 줄바꿈 그리드로 (좁은 패널에서 잘리지 않게)
    ttk.Label(left, text="인원수:").pack(anchor="w", pady=(4, 0))
    count_box = ttk.Frame(left)
    count_box.pack(anchor="w", fill="x")
    count_var = tk.StringVar(value="solo")
    for idx, (label, key, _) in enumerate(COUNTS):
        ttk.Radiobutton(count_box, text=label, value=key, variable=count_var,
                        command=lambda: do_generate()).grid(
            row=idx // 3, column=idx % 3, sticky="w", padx=2)

    # 포즈 (체크, 다중)
    ttk.Label(left, text="포즈:").pack(anchor="w", pady=(6, 0))
    pose_box = ttk.Frame(left)
    pose_box.pack(anchor="w", fill="x")
    pose_vars: dict[str, tk.BooleanVar] = {}
    for idx, (label, _, tag) in enumerate(POSES):
        var = tk.BooleanVar(value=False)
        pose_vars[tag] = var
        ttk.Checkbutton(pose_box, text=label, variable=var,
                        command=lambda: do_generate()).grid(
            row=idx // 3, column=idx % 3, sticky="w", padx=2)

    ttk.Separator(left, orient="horizontal").pack(fill="x", pady=6)

    # 주인공 지정
    main_frame = ttk.LabelFrame(left, text="👑 주인공 (2명 이상일 때)", padding=6)
    main_frame.pack(anchor="w", fill="x")
    main_subject_var = tk.StringVar()
    main_entry = ttk.Entry(main_frame, textvariable=main_subject_var)
    main_entry.pack(anchor="w", fill="x")
    main_entry.bind("<KeyRelease>", lambda e: schedule_generate())
    main_focus_var = tk.BooleanVar(value=True)
    main_focus_chk = ttk.Checkbutton(
        main_frame, text="주인공 강조 (가중치+solo focus)",
        variable=main_focus_var, command=lambda: do_generate())
    main_focus_chk.pack(anchor="w", pady=(4, 0))
    ttk.Button(main_frame, text="❔ 주인공 지정 방법",
               command=lambda: messagebox.showinfo("주인공 지정 방법",
                                                   MAIN_GUIDE)).pack(
        anchor="w", pady=(4, 0))

    # === 오른쪽 결과 ===
    ttk.Label(right, text="Positive (긍정문)",
              font=("", 11, "bold")).pack(anchor="w")
    pos_text = scrolledtext.ScrolledText(right, height=8, wrap="word")
    pos_text.pack(fill="both", expand=True, pady=(2, 4))
    pos_btns = ttk.Frame(right)
    pos_btns.pack(anchor="e", pady=(0, 6))
    ttk.Button(pos_btns, text="Positive 복사",
               command=lambda: copy_to_clipboard(pos_text)).pack(side="right")

    ttk.Label(right, text="Negative (부정문)",
              font=("", 11, "bold")).pack(anchor="w")
    neg_text = scrolledtext.ScrolledText(right, height=8, wrap="word")
    neg_text.pack(fill="both", expand=True, pady=(2, 4))
    neg_btns = ttk.Frame(right)
    neg_btns.pack(anchor="e", pady=(0, 6))
    ttk.Button(neg_btns, text="Negative 복사",
               command=lambda: copy_to_clipboard(neg_text)).pack(side="right")

    status_var = tk.StringVar(value="")
    ttk.Label(right, textvariable=status_var, foreground="#0a7").pack(anchor="w")

    bottom = ttk.Frame(right)
    bottom.pack(fill="x", pady=(6, 0))
    ttk.Button(bottom, text="🎲 새로 생성(랜덤)",
               command=lambda: do_generate(new_seed=True)).pack(side="left")
    ttk.Button(bottom, text="닫기", command=root.destroy).pack(side="right")

    # === 동작 ===
    def style_key() -> str:
        idx = style_combo.current()
        return list(STYLES.keys())[idx if idx >= 0 else 0]

    def set_text(widget, value: str) -> None:
        widget.delete("1.0", "end")
        widget.insert("1.0", value)

    def update_main_state() -> None:
        # 입력칸/강조 체크만 토글하고, 도움말 버튼은 건드리지 않는다.
        st = "normal" if count_var.get() != "solo" else "disabled"
        main_entry.configure(state=st)
        main_focus_chk.configure(state=st)

    def do_generate(new_seed: bool = False) -> None:
        if new_seed or state["seed"] is None:
            state["seed"] = random.randrange(1_000_000_000)
        update_main_state()
        vals = {
            "character": character_var.get().strip() or None,
            "background": background_var.get().strip() or None,
            "situation": situation_var.get().strip() or None,
            "main_subject": main_subject_var.get().strip() or None,
        }
        if translate_var.get():
            engines: set[str] = set()
            for key, val in list(vals.items()):
                vals[key], eng = translate_text(val, online=True,
                                                cache=state["tcache"])
                if eng != "none":
                    engines.add(eng)
            leftover = any(v and _has_hangul(v) for v in vals.values())
            if not engines:
                status_var.set("")
            elif "online" in engines:
                status_var.set("🌐 온라인 번역 적용됨")
            elif leftover:
                status_var.set("⚠️ 오프라인 사전 사용 — 일부 단어 미번역")
            else:
                status_var.set("📖 오프라인 사전 번역 적용됨")
        else:
            status_var.set("")
        poses = [tag for tag, v in pose_vars.items() if v.get()]
        result = generate(
            style_key(), character=vals["character"],
            background=vals["background"], situation=vals["situation"],
            randomize=randomize_var.get(),
            seed=state["seed"], shot=SHOT_SIZES[shot_combo.current()][2],
            angle=CAMERA_ANGLES[angle_combo.current()][2],
            expression=EXPRESSIONS[expr_combo.current()][2], poses=poses,
            count=count_var.get(), main_subject=vals["main_subject"],
            main_focus=main_focus_var.get(), emphasis=emphasis_var.get(),
        )
        set_text(pos_text, result["positive"])
        set_text(neg_text, result["negative"])

    def schedule_generate(delay: int = 600) -> None:
        # 타이핑 중 매 키마다 온라인 번역을 호출하지 않도록 디바운스.
        if state["after"] is not None:
            root.after_cancel(state["after"])
        state["after"] = root.after(delay, do_generate)

    def copy_to_clipboard(widget) -> None:
        root.clipboard_clear()
        root.clipboard_append(widget.get("1.0", "end").strip())
        status_var.set("✅ 클립보드에 복사했습니다.")

    style_combo.bind("<<ComboboxSelected>>", lambda e: do_generate())

    do_generate(new_seed=True)
    root.mainloop()
    return 0


# ---------------------------------------------------------------------------
# 8. 엔트리 포인트
# ---------------------------------------------------------------------------
def main() -> int:
    argv = sys.argv[1:]
    if any(f in argv for f in ("--cli", "--list", "--help-main")) or argv:
        return run_cli(argv)
    return run_gui()


if __name__ == "__main__":
    raise SystemExit(main())
