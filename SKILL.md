---
name: canva-assignment-pdf-merge
description: |
  사용자가 "역사 과제 완료본 병합해줘", "완료본 합쳐줘", "PDF로 모아줘"처럼 요청하면
  Canva에서 완료본 디자인을 검색하고, 제목 규칙에 맞는 항목만 필터링한 뒤,
  각 디자인을 PDF로 export하여 학생 번호 순으로 하나의 PDF로 병합해 반환한다.
  로컬 프로젝트 스크립트에 의존하지 말고, 이 채팅 환경에서 사용 가능한 도구만 사용한다.
---

# Canva Assignment PDF Merge

## 목적

Canva 과제 완료본을 디자인 제목 규칙으로 식별하여,
완료된 학생들만 자동 수집하고 하나의 병합 PDF를 만들어 사용자에게 전달한다.

## 트리거

다음과 같은 요청이 오면 이 스킬을 사용한다.

- "과제 병합"
- "완료본 합쳐줘"
- "PDF로 모아줘"
- "{과제명} 병합해줘"
- "{과제명} 완료본 병합해줘"

사용자 발화에서 `assignmentName`을 추출한다.
앞뒤 공백은 제거(trim)하되, **비교는 exact match**로 한다.

---

## 제목 규칙 (source of truth)

디자인 제목은 아래 형식을 따른다.

```text
완료{sep}{assignmentName}{sep}{studentNumber}{sep}{studentName}
```

허용 규칙:

- `sep`은 `-` 또는 ` - `
- 공백 유무 차이는 허용
- `studentNumber`는 숫자만 허용
- `assignmentName`은 사용자 요청에서 추출한 과제명과 trim 후 exact match
- `studentName`은 비어 있지 않아야 함

유효 예시:

- `완료 - 역사 - 15 - 김민수`
- `완료-역사-15-김민수`

무효 예시:

- `완료 - 역사 - abc - 김민수` ← `studentNumber` 비숫자
- `완료-여행지-15-김민수` ← `assignmentName` 불일치
- `완료 - 역사 - 15` ← `studentName` 누락

## 전체 동작 원칙

- 제목 규칙에 맞는 디자인만 사용한다.
- 규칙에 맞지 않는 항목은 조용히 제외하되, 최종 리포트에는 기록한다.
- 일부 export가 실패해도 전체 작업은 중단하지 말고 계속 진행한다.
- 같은 학생 번호가 여러 개면 `updatedAt` 기준 최신본만 사용한다.
- 최종 병합 순서는 `studentNumber` 오름차순이다.

## 워크플로우

### 1) 디자인 검색

먼저 아래 쿼리로 검색한다.

```text
완료 - {assignmentName}
```

결과가 0건이면 아래로 한 번 더 검색한다.

```text
완료-{assignmentName}
```

가능하다면 검색 결과는 충분히 넉넉하게 가져온다.
검색 결과가 많더라도 후속 파싱으로 걸러낸다.

### 2) 제목 파싱 및 필터링

검색 결과의 각 디자인 제목을 로컬에서 파싱한다.

파싱 규칙 예시:

- 제목을 `-` 기준으로 분리하되,
- 양쪽 공백을 trim 하고,
- 정확히 4개 토큰이 나와야 한다.

예상 토큰:

- `완료`
- `assignmentName`
- `studentNumber`
- `studentName`

검증 조건:

- 첫 토큰이 정확히 `완료`
- 두 번째 토큰이 사용자 과제명과 exact match
- 세 번째 토큰이 숫자만으로 구성
- 네 번째 토큰이 비어 있지 않음

실패한 항목은 파싱 실패 목록에 기록한다.

### 3) 중복 제거

유효 항목들을 `studentNumber` 기준으로 그룹화한다.

동일한 `studentNumber`가 여러 개면:

- `updatedAt` 최신본 1개만 유지
- 나머지는 제외
- 제외된 항목은 중복 제외 목록에 기록한다.

가능하면 어떤 항목이 남고 어떤 항목이 제외됐는지 제목 기준으로 남긴다.

예:

```text
15번 중복: 최신본 유지 = "완료 - 역사 - 15 - 김민수", 제외 = [...]
```

### 4) PDF export

중복 제거 후 남은 디자인 각각에 대해 PDF export를 수행한다.

개념적으로:

```text
export-design(design_id, format={type: "pdf"})
```

주의:

- export URL은 만료될 수 있으므로 export 후 즉시 다운로드/병합 단계로 넘긴다.
- export 실패 시 해당 항목만 건너뛰고 계속 진행한다.
- 실패 항목은 export 실패 목록에 기록한다.

### 5) PDF 다운로드 및 병합

병합 대상은 `(studentNumber, pdf_url)` 목록이다.

- `studentNumber` 오름차순으로 정렬
- 각 PDF를 다운로드
- 하나의 PDF로 병합

예시 구현 로직:

```python
import io
import os
import tempfile
import requests
from pypdf import PdfWriter

def merge_pdfs(url_list: list[tuple[int, str]]) -> bytes:
    writer = PdfWriter()

    for student_num, url in sorted(url_list, key=lambda x: x[0]):
        r = requests.get(url, timeout=30)
        r.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(r.content)
            tmp_path = f.name

        try:
            writer.append(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()
```

병합 결과 파일명:

```text
{assignmentName}_완료본_병합.pdf
```

예:

```text
역사_완료본_병합.pdf
```

## 반환 형식

사용자에게 병합 PDF 파일을 전달하고, 아래 리포트를 함께 보여준다.

```text
병합 완료: {N}명
제외 (파싱 실패): [목록]
제외 (중복): [목록]
제외 (export 실패): [목록]
```

목록이 비어 있으면 `없음`으로 표기한다.

예:

```text
병합 완료: 24명
제외 (파싱 실패): ["완료 - 역사 - abc - 김민수"]
제외 (중복): ["완료 - 역사 - 07 - 박서준 (구버전)"]
제외 (export 실패): 없음
```

## 실패 처리

검색 결과 없음

두 가지 검색 모두 0건이면 아래처럼 반환한다.

```text
완료본을 찾지 못했습니다.
검색한 과제명: {assignmentName}
확인한 검색어:
- 완료 - {assignmentName}
- 완료-{assignmentName}
유효 항목 0개
```

검색 결과는 있었지만 제목 규칙에 맞는 항목이 하나도 없으면 아래처럼 반환한다.

```text
검색 결과는 있었지만 제목 규칙과 일치하는 완료본이 없습니다.
제목 형식:
완료 - {assignmentName} - 학번 - 이름
```

병합 대상 1개

1개만 유효하면 병합 없이 단일 PDF를 그대로 반환해도 된다.
단, 리포트에는 `병합 완료: 1명`으로 표시한다.

## 구현 지침

- 로컬 프로젝트의 기존 `scripts/` 코드를 호출하지 말 것
- 이 채팅 환경에서 사용 가능한 Canva 도구 + 파일 처리 수단만 사용할 것
- 파일 저장은 임시 처리 후 최종 결과물만 사용자에게 전달할 것
- 제목 규칙 검증을 최우선 source of truth로 사용할 것

## 의존성

필요 시:

```bash
pip install pypdf requests
```

## 제약

- Canva export URL은 일정 시간 후 만료될 수 있으므로 export 직후 바로 다운로드/병합해야 함
- export 실패는 전체 실패가 아니라 부분 실패로 처리
- `assignmentName` 비교는 trim 후 exact match
- `studentNumber`는 숫자 정렬 기준으로 처리

## 중요

검색 결과의 제목이 규칙과 거의 비슷해 보여도 추측해서 포함하지 말고, 규칙에 정확히 맞는 것만 포함하라.
