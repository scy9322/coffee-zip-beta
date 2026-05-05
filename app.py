import os
import json
import csv
from datetime import datetime
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

SIGNUPS_FILE = os.path.join(os.path.dirname(__file__), 'signups.csv')

# ── Google Sheets (optional) ──────────────────────────────────────────────────
_sheet_cache = None

def get_sheet():
    global _sheet_cache
    if _sheet_cache is not None:
        return _sheet_cache

    creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    sheet_id   = os.environ.get('GOOGLE_SHEET_ID')
    if not creds_json or not sheet_id:
        return None

    try:
        import gspread
        from google.oauth2.service_account import Credentials

        creds = Credentials.from_service_account_info(
            json.loads(creds_json),
            scopes=['https://www.googleapis.com/auth/spreadsheets'],
        )
        gc = gspread.authorize(creds)
        sheet = gc.open_by_key(sheet_id).sheet1

        # 헤더 초기화
        rows = sheet.get_all_values()
        if not rows or rows[0] != ['신청일시', '이메일']:
            sheet.insert_row(['신청일시', '이메일'], 1)

        _sheet_cache = sheet
        return sheet
    except Exception as e:
        print(f'[Google Sheets] 연결 실패: {e}')
        return None


# ── 로컬 CSV fallback ─────────────────────────────────────────────────────────
def init_csv():
    if not os.path.exists(SIGNUPS_FILE):
        with open(SIGNUPS_FILE, 'w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(['신청일시', '이메일'])


def csv_is_duplicate(email):
    if not os.path.exists(SIGNUPS_FILE):
        return False
    with open(SIGNUPS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if len(row) > 1 and row[1].lower() == email.lower():
                return True
    return False


# ── 공통 로직 ─────────────────────────────────────────────────────────────────
def is_duplicate(email):
    sheet = get_sheet()
    if sheet:
        existing = sheet.col_values(2)[1:]          # 헤더 제외
        return email.lower() in [e.lower() for e in existing]
    return csv_is_duplicate(email)


def save_signup(email):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sheet = get_sheet()
    if sheet:
        sheet.append_row([now, email])
        return
    init_csv()
    with open(SIGNUPS_FILE, 'a', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow([now, email])


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '잘못된 요청입니다.'}), 400

    email  = data.get('email', '').strip()
    agreed = data.get('agreed', False)

    if not email or '@' not in email or '.' not in email.split('@')[-1]:
        return jsonify({'success': False, 'message': '유효한 이메일 주소를 입력해주세요.'}), 400

    if not agreed:
        return jsonify({'success': False, 'message': '개인정보 처리방침에 동의해주세요.'}), 400

    if is_duplicate(email):
        return jsonify({'success': False, 'message': '이미 신청하신 이메일입니다.'}), 409

    save_signup(email)
    return jsonify({'success': True, 'message': '클로즈베타 신청이 완료되었습니다! 서비스 오픈 시 안내 이메일을 보내드릴게요.'})


@app.route('/admin/signups')
def view_signups():
    rows = []
    sheet = get_sheet()
    if sheet:
        rows = sheet.get_all_values()
    elif os.path.exists(SIGNUPS_FILE):
        with open(SIGNUPS_FILE, 'r', encoding='utf-8') as f:
            rows = list(csv.reader(f))

    count = max(0, len(rows) - 1)
    table = '<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;font-family:sans-serif">'
    for i, row in enumerate(rows):
        tag = 'th' if i == 0 else 'td'
        table += '<tr>' + ''.join(f'<{tag}>{cell}</{tag}>' for cell in row) + '</tr>'
    table += '</table>'
    return f'<h2>총 신청자: {count}명</h2>{table}'


if __name__ == '__main__':
    init_csv()
    port = int(os.environ.get('PORT', 4567))
    app.run(host='0.0.0.0', port=port, debug=False)
