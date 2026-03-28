---
name: canva-assignment-pdf-merge
description: |
  사용자가 "역사 과제 완료본 병합해줘" 같이 말하면,
  Canva에서 완료본 디자인을 검색·필터·export하고 하나의 PDF로 병합해 반환한다.
  Python CLI나 로컬 파일 없이 이 채팅 환경의 MCP 툴만으로 동작한다.
---

# Canva Assignment PDF Merge

## 트리거

다음 표현이 포함되면 이 스킬을 사용한다.
- "과제 병합", "완료본 합쳐줘", "PDF로 모아줘"
- "{과제명} 병합해줘"

## 제목 규칙 (source of truth)

```text
완료{sep}{assignmentName}{sep}{studentNumber}{sep}{studentName}
```

- `sep`은 `-` 또는 ` - ` (공백 유무 무관)
- `studentNumber`는 숫자만
- `assignmentName`은 사용자가 말한 과제명과 trim 후 exact match

유효 예시:
- `완료 - 역사 - 15 - 김민수`  ✅
- `완료-역사-15-김민수`         ✅

무효 예시:
- `완료 - 역사 - abc - 김민수` ❌ (studentNumber 비숫자)
- `완료-여행지-15-김민수`       ❌ (assignmentName 불일치)

## 워크플로우

### 1. 검색

```text
search-designs 쿼리: "완료 - {assignmentName}"
```

결과가 0건이면 `"완료-{assignmentName}"` 으로 재검색.

### 2. 파싱 & 필터

반환된 모든 디자인 제목을 위 제목 규칙으로 로컬 파싱.
규칙에 맞지 않는 항목은 조용히 제외 (리포트에 기록).

### 3. 중복 제거

같은 `studentNumber`가 여러 개면 `updatedAt` 최신본만 유지.
충돌 목록은 최종 리포트에 포함.

### 4. PDF export

유효 디자인 각각에 대해:

```text
export-design(design_id, format={type: "pdf"})
```

반환된 URL로 PDF bytes 다운로드.
export 실패 시 해당 항목만 건너뛰고 리포트에 기록 (계속 진행).

### 5. 병합

`studentNumber` 오름차순으로 PDF를 병합.

```python
import pypdf, requests, tempfile, os

def merge_pdfs(url_list: list[tuple[int, str]]) -> bytes:
    writer = pypdf.PdfWriter()
    for student_num, url in sorted(url_list):
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(r.content)
            tmp = f.name
        writer.append(tmp)
        os.unlink(tmp)
    import io
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()
```

### 6. 반환

병합 PDF를 파일로 저장 후 사용자에게 전달.
파일명: `{assignmentName}_완료본_병합.pdf`

최종 리포트 (텍스트로 출력):

```text
병합 완료: {N}명
제외 (파싱 실패): [목록]
제외 (중복): [목록]
제외 (export 실패): [목록]
```

## 의존성

```bash
pip install pypdf requests
```

## 제약

- Canva MCP export URL은 수 시간 후 만료됨 → 병합은 export 직후 즉시 수행
- export-design은 이 채팅(claude.ai) 환경의 Canva MCP 연결이 필요
- Python CLI(`scripts/`) 코드는 레거시 참고용이며 이 스킬에서는 사용하지 않음
