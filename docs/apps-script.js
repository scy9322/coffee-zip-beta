// =====================================================
// Google Apps Script 코드
// 사용법:
//   1. Google Sheets 새 시트 만들기
//   2. 상단 메뉴 → 확장 프로그램 → Apps Script
//   3. 아래 코드 전체 붙여넣기 (기존 코드 교체)
//   4. 저장 후 → 배포 → 새 배포
//      - 유형: 웹 앱
//      - 다음 사용자로 실행: 나
//      - 액세스 권한: 모든 사용자
//   5. 배포 URL 복사 → docs/index.html의 APPS_SCRIPT_URL_HERE 에 붙여넣기
// =====================================================

function doPost(e) {
  try {
    const data  = JSON.parse(e.postData.contents);
    const email = (data.email || '').trim().toLowerCase();
    const agreed = data.agreed;

    if (!email || !email.includes('@') || !email.includes('.')) {
      return response({ success: false, message: '유효한 이메일 주소를 입력해주세요.' });
    }
    if (!agreed) {
      return response({ success: false, message: '개인정보 처리방침에 동의해주세요.' });
    }

    const sheet   = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    const lastRow = sheet.getLastRow();

    // 헤더 초기화
    if (lastRow === 0) {
      sheet.appendRow(['신청일시', '이메일']);
    }

    // 중복 체크
    if (lastRow > 1) {
      const existing = sheet.getRange(2, 2, lastRow - 1, 1).getValues().flat()
        .map(v => String(v).toLowerCase());
      if (existing.includes(email)) {
        return response({ success: false, message: '이미 신청하신 이메일입니다.' });
      }
    }

    // 저장
    const now = Utilities.formatDate(new Date(), 'Asia/Seoul', 'yyyy-MM-dd HH:mm:ss');
    sheet.appendRow([now, email]);

    return response({ success: true, message: '클로즈베타 신청이 완료되었습니다! 서비스 오픈 시 안내 이메일을 보내드릴게요.' });

  } catch (err) {
    return response({ success: false, message: '오류가 발생했습니다. 다시 시도해주세요.' });
  }
}

function doGet() {
  return ContentService.createTextOutput('OK');
}

function response(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
