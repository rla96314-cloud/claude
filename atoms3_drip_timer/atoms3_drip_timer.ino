/*
 * M5Stack AtomS3 - 드립커피 추출 타이머
 * ------------------------------------------------------------
 * 기능 요약
 *  - 측면(외부) 버튼: 레시피 선택 (누를 때마다 다음 레시피, 화면에 이름 표시)
 *  - 액정(전면 화면 버튼, G41) 누름: 레시피 결정 화면 → 두 번 깜빡임
 *  - 한 번 더 누름: 해당 레시피 시작
 *  - 각 단계의 정해진 초를 카운트다운, 5초 남으면 비프음
 *  - 카운트다운이 끝나면 자동으로 다음 단계로 진행
 *  - 레시피 편집은 WiFi 웹페이지(http://atoms3-drip.local 또는 IP)에서
 *
 * 보드 / 라이브러리 (Arduino IDE 보드매니저 / 라이브러리매니저)
 *  - 보드: "M5Stack" 보드 패키지의 "M5AtomS3"
 *  - M5Unified
 *  - ArduinoJson (v7 권장)
 *
 * 배선 (AtomS3 하단 헤더 핀 사용, 아래 상수에서 변경 가능)
 *  - 외부 버튼: PIN_SIDE_BUTTON(G39) <-> GND  (내부 풀업 사용)
 *  - 부저:      PIN_BUZZER(G38) <-> 부저 +, 부저 - <-> GND
 *               (패시브 피에조 부저 기본. 액티브 부저면 BUZZER_ACTIVE 1)
 */

#include <M5Unified.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <Preferences.h>
#include <ArduinoJson.h>
#include <vector>

// ===================== 사용자 설정 =====================
// 집 WiFi 정보 (STA 모드). 접속 실패 시 자동으로 AP 모드로 전환됩니다.
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASS = "YOUR_WIFI_PASSWORD";

// STA 접속 실패 시 폴백 AP 정보
const char* AP_SSID = "AtomS3-Drip";
const char* AP_PASS = "dripcoffee";   // 8자 이상

// mDNS 호스트네임 -> http://atoms3-drip.local
const char* MDNS_HOST = "atoms3-drip";

// 핀 배치 (필요 시 변경)
constexpr int PIN_SIDE_BUTTON = 39;   // 외부 레시피 선택 버튼 (GND로 연결)
constexpr int PIN_BUZZER      = 38;   // 외부 부저

#define BUZZER_ACTIVE 0   // 0=패시브 피에조(주파수 구동), 1=액티브 부저(ON/OFF)

// 마지막 5초 카운트다운 경고 비프 시작 시점(초)
constexpr int WARN_SECONDS = 5;
// ======================================================

// ----- 데이터 모델 -----
struct Step {
  String label;
  uint16_t seconds;
};
struct Recipe {
  String name;
  std::vector<Step> steps;
};

std::vector<Recipe> recipes;
Preferences prefs;
WebServer server(80);

constexpr size_t MAX_RECIPES = 12;
constexpr size_t MAX_STEPS   = 16;

// ----- 화면 상태 -----
enum AppState {
  STATE_SELECT,   // 레시피 선택
  STATE_CONFIRM,  // 결정(두 번 깜빡임) 후 시작 대기
  STATE_RUNNING,  // 추출 진행
  STATE_DONE      // 완료
};
AppState state = STATE_SELECT;

int   selectedRecipe = 0;
int   currentStep    = 0;
unsigned long stepStartMs   = 0;
int   lastShownSecond = -1;     // 표시 갱신용
bool  warnBeeped      = false;  // 단계별 5초 경고 비프 1회 처리
int   lastTickSecond  = -1;     // 마지막 5초 틱 비프용

unsigned long confirmStartMs = 0;
bool  confirmReady    = false;  // 깜빡임 끝나고 시작 입력 받을 준비
int   confirmLastPhase = -1;    // 깜빡임 단계 표시 갱신용

String netInfo = "";            // 화면 하단에 표시할 접속 주소

// ----- 비프(부저) 비차단 제어 -----
unsigned long buzzerOffAt = 0;

void buzzerStart(int freq) {
#if BUZZER_ACTIVE
  (void)freq;
  digitalWrite(PIN_BUZZER, HIGH);
#else
  tone(PIN_BUZZER, freq);
#endif
}
void buzzerStop() {
#if BUZZER_ACTIVE
  digitalWrite(PIN_BUZZER, LOW);
#else
  noTone(PIN_BUZZER);
#endif
}
// freq Hz 음을 ms 동안 (비차단)
void beep(int freq, int ms) {
  buzzerStart(freq);
  buzzerOffAt = millis() + ms;
}
void updateBuzzer() {
  if (buzzerOffAt && millis() >= buzzerOffAt) {
    buzzerStop();
    buzzerOffAt = 0;
  }
}

// =====================================================================
//  레시피 저장/로드 (NVS Preferences에 JSON 문자열로 보관)
// =====================================================================
String recipesToJson() {
  JsonDocument doc;
  JsonArray arr = doc["recipes"].to<JsonArray>();
  for (auto& r : recipes) {
    JsonObject ro = arr.add<JsonObject>();
    ro["name"] = r.name;
    JsonArray sarr = ro["steps"].to<JsonArray>();
    for (auto& s : r.steps) {
      JsonObject so = sarr.add<JsonObject>();
      so["label"]   = s.label;
      so["seconds"] = s.seconds;
    }
  }
  String out;
  serializeJson(doc, out);
  return out;
}

// JSON 문자열을 파싱해 recipes 벡터에 적용. 성공 시 true.
bool loadRecipesFromJson(const String& json) {
  JsonDocument doc;
  DeserializationError err = deserializeJson(doc, json);
  if (err) return false;
  JsonArray arr = doc["recipes"].as<JsonArray>();
  if (arr.isNull()) return false;

  std::vector<Recipe> parsed;
  for (JsonObject ro : arr) {
    if (parsed.size() >= MAX_RECIPES) break;
    Recipe r;
    r.name = (const char*)(ro["name"] | "이름없음");
    for (JsonObject so : ro["steps"].as<JsonArray>()) {
      if (r.steps.size() >= MAX_STEPS) break;
      Step s;
      s.label   = (const char*)(so["label"] | "단계");
      long sec  = so["seconds"] | 30;
      if (sec < 1)    sec = 1;
      if (sec > 3600) sec = 3600;
      s.seconds = (uint16_t)sec;
      r.steps.push_back(s);
    }
    if (!r.steps.empty()) parsed.push_back(r);
  }
  if (parsed.empty()) return false;
  recipes = parsed;
  if (selectedRecipe >= (int)recipes.size()) selectedRecipe = 0;
  return true;
}

void saveRecipes() {
  prefs.putString("recipes", recipesToJson());
}

void loadDefaultRecipes() {
  recipes.clear();
  // 기본 예시: 하리오 V60 4:6 스타일 (총 6단계)
  Recipe a;
  a.name = "V60 4:6";
  a.steps = {
    {"1차 (50g)", 45},
    {"2차 (70g)", 45},
    {"3차 (60g)", 45},
    {"4차 (60g)", 45},
    {"5차 (60g)", 45},
    {"드립 완료 대기", 30},
  };
  Recipe b;
  b.name = "기본 핸드드립";
  b.steps = {
    {"뜸들이기", 30},
    {"1차 추출", 40},
    {"2차 추출", 40},
    {"마무리", 30},
  };
  recipes.push_back(a);
  recipes.push_back(b);
}

void loadRecipes() {
  String json = prefs.getString("recipes", "");
  if (json.isEmpty() || !loadRecipesFromJson(json)) {
    loadDefaultRecipes();
    saveRecipes();
  }
}

// =====================================================================
//  웹페이지 (레시피 편집 SPA)
// =====================================================================
const char INDEX_HTML[] PROGMEM = R"HTMLPAGE(
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>드립 레시피 설정</title>
<style>
  :root { color-scheme: light dark; }
  * { box-sizing: border-box; }
  body { font-family: -apple-system, system-ui, "Noto Sans KR", sans-serif;
         margin: 0; padding: 16px; background:#111; color:#eee; }
  h1 { font-size: 20px; margin: 0 0 12px; }
  .recipe { background:#1d1d22; border:1px solid #333; border-radius:12px;
            padding:12px; margin-bottom:14px; }
  .recipe-head { display:flex; gap:8px; align-items:center; margin-bottom:8px; }
  .recipe-head input { flex:1; font-size:16px; font-weight:600; }
  input { background:#2a2a30; color:#eee; border:1px solid #444;
          border-radius:8px; padding:8px; font-size:15px; }
  input[type=number]{ width:84px; text-align:center; }
  table { width:100%; border-collapse:collapse; }
  td { padding:4px 2px; }
  td.sec { text-align:right; white-space:nowrap; }
  button { border:none; border-radius:8px; padding:9px 12px; font-size:14px;
           cursor:pointer; background:#3a3a44; color:#eee; }
  button.primary { background:#c97b34; color:#fff; font-weight:700; }
  button.danger  { background:#5a2a2a; color:#f3b4b4; }
  button.small   { padding:6px 9px; font-size:13px; }
  .row-actions { display:flex; gap:8px; margin-top:8px; }
  .bottom { position:sticky; bottom:0; padding:12px 0;
            background:linear-gradient(transparent,#111 30%); display:flex; gap:10px; }
  #status { font-size:14px; min-height:20px; padding-top:6px; }
  .hint { color:#999; font-size:12px; margin-bottom:14px; }
</style>
</head>
<body>
  <h1>☕ 드립 레시피 설정</h1>
  <div class="hint">단계마다 라벨과 시간(초)을 정합니다. 장치에서 측면 버튼으로 레시피를 고르고, 액정을 눌러 시작합니다.</div>
  <div id="recipes"></div>
  <button class="small" onclick="addRecipe()">+ 레시피 추가</button>
  <div class="bottom">
    <button class="primary" style="flex:1" onclick="save()">장치에 저장</button>
    <button class="small" onclick="load()">새로고침</button>
  </div>
  <div id="status"></div>

<script>
let data = { recipes: [] };

async function load() {
  setStatus("불러오는 중...");
  try {
    const r = await fetch('/api/recipes');
    data = await r.json();
    if (!data.recipes) data.recipes = [];
    render();
    setStatus("");
  } catch (e) { setStatus("불러오기 실패: " + e); }
}

function setStatus(t) { document.getElementById('status').textContent = t; }

function render() {
  const root = document.getElementById('recipes');
  root.innerHTML = '';
  data.recipes.forEach((rec, i) => {
    const box = document.createElement('div');
    box.className = 'recipe';

    const head = document.createElement('div');
    head.className = 'recipe-head';
    const name = document.createElement('input');
    name.value = rec.name || '';
    name.placeholder = '레시피 이름';
    name.oninput = () => rec.name = name.value;
    const del = document.createElement('button');
    del.className = 'danger small';
    del.textContent = '삭제';
    del.onclick = () => { data.recipes.splice(i,1); render(); };
    head.appendChild(name);
    head.appendChild(del);
    box.appendChild(head);

    const tbl = document.createElement('table');
    (rec.steps || []).forEach((st, j) => {
      const tr = document.createElement('tr');

      const tdL = document.createElement('td');
      const lab = document.createElement('input');
      lab.style.width = '100%';
      lab.value = st.label || '';
      lab.placeholder = (j+1) + '단계';
      lab.oninput = () => st.label = lab.value;
      tdL.appendChild(lab);

      const tdS = document.createElement('td');
      tdS.className = 'sec';
      const sec = document.createElement('input');
      sec.type = 'number'; sec.min = '1'; sec.max = '3600';
      sec.value = st.seconds;
      sec.oninput = () => st.seconds = parseInt(sec.value || '0', 10);
      tdS.appendChild(sec);
      tdS.appendChild(document.createTextNode(' 초'));

      const tdD = document.createElement('td');
      tdD.className = 'sec';
      const rm = document.createElement('button');
      rm.className = 'danger small';
      rm.textContent = '×';
      rm.onclick = () => { rec.steps.splice(j,1); render(); };
      tdD.appendChild(rm);

      tr.appendChild(tdL); tr.appendChild(tdS); tr.appendChild(tdD);
      tbl.appendChild(tr);
    });
    box.appendChild(tbl);

    const actions = document.createElement('div');
    actions.className = 'row-actions';
    const addStep = document.createElement('button');
    addStep.className = 'small';
    addStep.textContent = '+ 단계 추가';
    addStep.onclick = () => {
      rec.steps = rec.steps || [];
      rec.steps.push({ label: '', seconds: 30 });
      render();
    };
    actions.appendChild(addStep);
    box.appendChild(actions);

    root.appendChild(box);
  });
}

function addRecipe() {
  data.recipes.push({ name: '새 레시피', steps: [{ label: '뜸들이기', seconds: 30 }] });
  render();
}

async function save() {
  // 간단 검증
  for (const r of data.recipes) {
    if (!r.steps || r.steps.length === 0) {
      setStatus("'" + (r.name||'무제') + "' 레시피에 단계가 없습니다."); return;
    }
    for (const s of r.steps) {
      if (!s.seconds || s.seconds < 1) { setStatus("초는 1 이상이어야 합니다."); return; }
    }
  }
  setStatus("저장 중...");
  try {
    const res = await fetch('/api/recipes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (res.ok) setStatus("저장 완료 ✓ 장치에 반영되었습니다.");
    else setStatus("저장 실패: " + res.status + " " + (await res.text()));
  } catch (e) { setStatus("저장 실패: " + e); }
}

load();
</script>
</body>
</html>
)HTMLPAGE";

void handleRoot() {
  server.send_P(200, "text/html; charset=utf-8", INDEX_HTML);
}

void handleGetRecipes() {
  server.send(200, "application/json; charset=utf-8", recipesToJson());
}

void handlePostRecipes() {
  if (!server.hasArg("plain")) {
    server.send(400, "text/plain; charset=utf-8", "본문이 없습니다");
    return;
  }
  String body = server.arg("plain");
  std::vector<Recipe> backup = recipes;  // 실패 시 롤백
  if (loadRecipesFromJson(body)) {
    saveRecipes();
    // 진행 중이 아니면 선택 인덱스 정리
    if (state == STATE_SELECT && selectedRecipe >= (int)recipes.size())
      selectedRecipe = 0;
    server.send(200, "application/json; charset=utf-8", "{\"ok\":true}");
  } else {
    recipes = backup;
    server.send(400, "text/plain; charset=utf-8", "레시피 형식 오류");
  }
}

// =====================================================================
//  WiFi 연결 (STA, 실패 시 AP 폴백)
// =====================================================================
void setupWifi() {
  M5.Display.fillScreen(TFT_BLACK);
  M5.Display.setTextDatum(middle_center);
  M5.Display.setTextColor(TFT_WHITE);
  M5.Display.setTextSize(1);
  M5.Display.drawString("WiFi 연결중...", M5.Display.width()/2, M5.Display.height()/2);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  unsigned long t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < 12000) {
    delay(250);
  }

  if (WiFi.status() == WL_CONNECTED) {
    netInfo = WiFi.localIP().toString();
  } else {
    // 폴백: AP 모드
    WiFi.mode(WIFI_AP);
    WiFi.softAP(AP_SSID, AP_PASS);
    netInfo = "AP:" + WiFi.softAPIP().toString();
  }

  if (MDNS.begin(MDNS_HOST)) {
    MDNS.addService("http", "tcp", 80);
  }

  server.on("/", HTTP_GET, handleRoot);
  server.on("/api/recipes", HTTP_GET, handleGetRecipes);
  server.on("/api/recipes", HTTP_POST, handlePostRecipes);
  server.begin();
}

// =====================================================================
//  버튼 입력
// =====================================================================
// 측면(외부) 버튼: 눌림 이벤트를 1회 반환 (디바운스)
bool sideRawPrev = HIGH;
unsigned long sideChangeMs = 0;
bool sideWasPressed() {
  bool raw = digitalRead(PIN_SIDE_BUTTON);
  bool event = false;
  if (raw != sideRawPrev && millis() - sideChangeMs > 30) {
    sideChangeMs = millis();
    if (raw == LOW) event = true;   // HIGH(풀업) -> LOW(눌림)
    sideRawPrev = raw;
  } else if (raw == sideRawPrev) {
    sideChangeMs = millis();
  }
  return event;
}

// 액정(전면 화면) 버튼 G41
bool lcdWasPressed() {
  return M5.BtnA.wasPressed();
}

// =====================================================================
//  화면 표시
// =====================================================================
void drawNetFooter() {
  M5.Display.setTextDatum(bottom_center);
  M5.Display.setTextColor(TFT_DARKGREY, TFT_BLACK);
  M5.Display.setTextSize(1);
  M5.Display.drawString(netInfo, M5.Display.width()/2, M5.Display.height() - 2);
}

void drawSelect() {
  M5.Display.fillScreen(TFT_BLACK);
  int w = M5.Display.width(), h = M5.Display.height();

  M5.Display.setTextDatum(top_center);
  M5.Display.setTextColor(TFT_ORANGE);
  M5.Display.setTextSize(1);
  M5.Display.drawString("레시피 선택", w/2, 6);

  // 레시피 이름 (크게, 길면 자동 축소)
  M5.Display.setTextColor(TFT_WHITE);
  M5.Display.setTextDatum(middle_center);
  const String& name = recipes[selectedRecipe].name;
  int size = name.length() <= 6 ? 3 : (name.length() <= 10 ? 2 : 1);
  M5.Display.setTextSize(size);
  M5.Display.drawString(name, w/2, h/2 - 6);

  // 단계/순번 정보
  M5.Display.setTextSize(1);
  M5.Display.setTextColor(TFT_LIGHTGREY);
  char buf[40];
  snprintf(buf, sizeof(buf), "%d/%d  단계 %d개",
           selectedRecipe + 1, (int)recipes.size(),
           (int)recipes[selectedRecipe].steps.size());
  M5.Display.drawString(buf, w/2, h/2 + 22);

  M5.Display.setTextColor(TFT_DARKGREY);
  M5.Display.drawString("측면:다음  액정:선택", w/2, h - 16);
  drawNetFooter();
}

void drawConfirm(bool visible) {
  M5.Display.fillScreen(TFT_BLACK);
  int w = M5.Display.width(), h = M5.Display.height();
  if (visible) {
    M5.Display.setTextDatum(middle_center);
    M5.Display.setTextColor(TFT_GREENYELLOW);
    const String& name = recipes[selectedRecipe].name;
    int size = name.length() <= 6 ? 3 : (name.length() <= 10 ? 2 : 1);
    M5.Display.setTextSize(size);
    M5.Display.drawString(name, w/2, h/2 - 8);
    M5.Display.setTextSize(1);
    M5.Display.setTextColor(TFT_WHITE);
    if (confirmReady)
      M5.Display.drawString("한 번 더 눌러 시작", w/2, h/2 + 24);
  }
}

void drawRunning(int remaining) {
  Recipe& r = recipes[selectedRecipe];
  Step& s = r.steps[currentStep];
  int w = M5.Display.width(), h = M5.Display.height();
  bool warn = remaining <= WARN_SECONDS;

  M5.Display.fillScreen(warn ? TFT_MAROON : TFT_BLACK);

  // 상단: 단계 순번
  M5.Display.setTextDatum(top_center);
  M5.Display.setTextColor(TFT_ORANGE, warn ? TFT_MAROON : TFT_BLACK);
  M5.Display.setTextSize(1);
  char head[24];
  snprintf(head, sizeof(head), "단계 %d/%d", currentStep + 1, (int)r.steps.size());
  M5.Display.drawString(head, w/2, 4);

  // 단계 라벨
  M5.Display.setTextColor(TFT_WHITE, warn ? TFT_MAROON : TFT_BLACK);
  {
    const String& lab = s.label;
    int size = lab.length() <= 8 ? 2 : 1;
    M5.Display.setTextSize(size);
    M5.Display.drawString(lab, w/2, 22);
  }

  // 큰 카운트다운 숫자
  M5.Display.setTextDatum(middle_center);
  M5.Display.setTextColor(warn ? TFT_YELLOW : TFT_CYAN, warn ? TFT_MAROON : TFT_BLACK);
  M5.Display.setFont(&fonts::Font7);
  M5.Display.setTextSize(1);
  char num[8];
  snprintf(num, sizeof(num), "%d", remaining);
  M5.Display.drawString(num, w/2, h/2 + 8);
  M5.Display.setFont(&fonts::efontKR_16);   // 한글 폰트로 복귀

  // 진행 바
  int barW = w - 16;
  int total = s.seconds;
  int done = total - remaining;
  int fill = total > 0 ? (barW * done) / total : 0;
  M5.Display.drawRect(8, h - 14, barW, 8, TFT_DARKGREY);
  M5.Display.fillRect(8, h - 14, fill, 8, warn ? TFT_YELLOW : TFT_ORANGE);
}

void drawDone() {
  M5.Display.fillScreen(TFT_DARKGREEN);
  int w = M5.Display.width(), h = M5.Display.height();
  M5.Display.setTextDatum(middle_center);
  M5.Display.setTextColor(TFT_WHITE, TFT_DARKGREEN);
  M5.Display.setTextSize(3);
  M5.Display.drawString("완료", w/2, h/2 - 10);
  M5.Display.setTextSize(1);
  M5.Display.drawString("액정 눌러 돌아가기", w/2, h/2 + 26);
}

// =====================================================================
//  상태 전환
// =====================================================================
void enterSelect() {
  state = STATE_SELECT;
  drawSelect();
}

void enterConfirm() {
  state = STATE_CONFIRM;
  confirmStartMs = millis();
  confirmReady = false;
  confirmLastPhase = 0;
  beep(1200, 50);
  drawConfirm(true);   // 첫 깜빡임 "켜짐" 프레임
}

void startRecipe() {
  state = STATE_RUNNING;
  currentStep = 0;
  stepStartMs = millis();
  lastShownSecond = -1;
  warnBeeped = false;
  lastTickSecond = -1;
  beep(1500, 120);   // 시작 비프
}

void enterDone() {
  state = STATE_DONE;
  beep(880, 150);
  drawDone();
}

void nextStepOrFinish() {
  beep(2000, 200);   // 단계 전환 비프
  currentStep++;
  if (currentStep >= (int)recipes[selectedRecipe].steps.size()) {
    enterDone();
  } else {
    stepStartMs = millis();
    lastShownSecond = -1;
    warnBeeped = false;
    lastTickSecond = -1;
  }
}

// =====================================================================
//  setup / loop
// =====================================================================
void setup() {
  auto cfg = M5.config();
  M5.begin(cfg);
  M5.Display.setRotation(0);
  M5.Display.setBrightness(120);
  M5.Display.setFont(&fonts::efontKR_16);   // 한글 표시용 폰트

  pinMode(PIN_SIDE_BUTTON, INPUT_PULLUP);
#if BUZZER_ACTIVE
  pinMode(PIN_BUZZER, OUTPUT);
  digitalWrite(PIN_BUZZER, LOW);
#endif
  sideRawPrev = digitalRead(PIN_SIDE_BUTTON);

  prefs.begin("drip", false);
  loadRecipes();

  setupWifi();
  enterSelect();
}

void loop() {
  M5.update();
  server.handleClient();
  updateBuzzer();

  bool sidePressed = sideWasPressed();
  bool lcdPressed  = lcdWasPressed();

  switch (state) {

    case STATE_SELECT:
      if (sidePressed) {
        selectedRecipe = (selectedRecipe + 1) % recipes.size();
        beep(1200, 40);
        drawSelect();
      }
      if (lcdPressed) {
        enterConfirm();
      }
      break;

    case STATE_CONFIRM: {
      // 진입 후 두 번 깜빡임 (300ms 주기로 켜고 끄기 x2 = 약 1200ms)
      unsigned long el = millis() - confirmStartMs;
      const unsigned long BLINK = 300;
      int phase = el / BLINK;          // 0:on 1:off 2:on 3:off
      bool visible = (phase % 2) == 0;
      if (phase >= 4) {                // 깜빡임 종료
        if (!confirmReady) {
          confirmReady = true;
          drawConfirm(true);           // 이름 + "한 번 더 눌러 시작"
        }
      } else if (phase != confirmLastPhase) {
        confirmLastPhase = phase;
        drawConfirm(visible);
      }

      if (confirmReady && lcdPressed) {
        startRecipe();
      }
      // 깜빡임 도중/대기 중 측면 버튼은 취소(선택으로 복귀)
      if (sidePressed) {
        beep(600, 60);
        enterSelect();
      }
      break;
    }

    case STATE_RUNNING: {
      Step& s = recipes[selectedRecipe].steps[currentStep];
      unsigned long el = millis() - stepStartMs;
      int remaining = (int)s.seconds - (int)(el / 1000);
      if (remaining < 0) remaining = 0;

      // 5초 남는 순간 경고 비프 (1회)
      if (!warnBeeped && remaining <= WARN_SECONDS && remaining > 0) {
        warnBeeped = true;
        beep(1800, 150);
      }
      // 5초 경고 이후 매초(4,3,2,1) 짧은 틱
      if (remaining < WARN_SECONDS && remaining > 0 && remaining != lastTickSecond) {
        lastTickSecond = remaining;
        beep(1800, 60);
      }

      if (remaining != lastShownSecond) {
        lastShownSecond = remaining;
        drawRunning(remaining);
      }

      if (el >= (unsigned long)s.seconds * 1000UL) {
        nextStepOrFinish();
      }

      // 측면 버튼 = 추출 취소
      if (sidePressed) {
        buzzerStop();
        beep(400, 100);
        enterSelect();
      }
      break;
    }

    case STATE_DONE:
      if (lcdPressed || sidePressed) {
        enterSelect();
      }
      break;
  }

  delay(5);
}
