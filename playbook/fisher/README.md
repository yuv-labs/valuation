# 피셔 트랙 Playbook

성장주(피셔 프레임) 투자 프로세스. **철학·파이프라인·실행 playbook**이 이 디렉토리에 모여 있다.

## 읽는 순서

| # | 파일 | 역할 | 언제 읽는가 |
|---|------|------|-----------|
| 1 | `README.md` (이 파일) | 디렉토리 지도 | 첫 진입 |
| 2 | `PHILOSOPHY.md` | 성장주 철학·합의 (왜 이렇게 설계했는가) | 프레임 흔들릴 때, 새 기업 판단 직전 |
| 3 | `PIPELINE.md` | Sensing→Shallow→Deep→숙성기→편입→유지보수 뼈대 | 전체 프로세스 파악, 단계 연결 확인 |
| 4 | `../SHALLOW_DIVE.md` ⭐ | **통합 Shallow Dive playbook** (Buffett+Fisher 공통) | Shallow 실행할 때 |
| ~~4'~~ | ~~`SHALLOW_DIVE.md`~~ | ~~Fisher 전용 Shallow~~ — **2026-04-18 DEPRECATED**, legacy 참조용 | 기존 ONON/IDXX shallow 해석 시만 |
| 5 | `DEEP_DIVE.md` | Deep 단계 실행 playbook (Stream A~F) | Fisher형 배정 종목 Deep 실행할 때 |

## AI 세션 진입점

- **전체 맥락 필요**: `README.md` → `PHILOSOPHY.md` → `PIPELINE.md` 순 로드
- **Shallow 실행**: `../SHALLOW_DIVE.md` (통합) + `PHILOSOPHY.md`(필요시) + 해당 기업 Sensing 엔트리. Phase 10 Track Gate에서 Fisher형 배정 시만 본 디렉토리의 Deep playbook 진입
- **Deep 실행 (Fisher형 배정 종목)**: `PHILOSOPHY.md` + `DEEP_DIVE.md` + 해당 기업 Shallow 리포트
- **Deep의 특정 Stream만**: `DEEP_DIVE.md` 해당 Stream 섹션 + 선행 Stream 출력물

## 전체 파이프라인 한눈에

```text
Sensing  →  Shallow Dive  →  Track 배정  →  Deep Dive  →  숙성기  →  편입  →  유지보수
(평생)      1~2h·단건/배치    Phase 10      1~2주 집중    2~4주     분할매수   분기
 ↓             ↓                ↓             ↓             ↓         ↓          ↓
SENSING_LOG   research/       Buffett형     research/    Deep 내     가격아닌  research/
 (공통)        shallow-dive/  vs Fisher형   fisher/       Stream E    해자체크  fisher/
               (통합 NEW)                    deep-dive/                          deep-dive/
                                             (피셔 배정시)                       {ticker}_
                                                                                  monitoring.md
```

- **Sensing 로그 + Shallow는 버핏·피셔 공통** (`../../research/SENSING_LOG.md`, `../../research/shallow-dive/`)
- **Deep 이후는 트랙별 분리 경로** (`research/{buffett|fisher}/deep-dive/`)
- **프레임 배정은 통합 Shallow Phase 10에서 4축 판정** (`../SHALLOW_DIVE.md` Phase 10), Deep은 한 프레임으로만

## 핵심 원칙 요약

- 피셔 트랙은 **정량 스크리닝으로 시작하지 않는다**
- 경영진·조직 검증이 Deep의 본체이되, **제품·산업·기술 이해**(Stream A)가 독립 축으로 함께 있어야 반쪽 아님
- 자료는 **1층위(주주서한·컨콜) → 2층위(제품 리뷰·NPS 등)** 역방향 교차검증
- 확신은 **형용사의 누적** — 한 번의 조사가 아님
- 매수 금지 기준은 엄격 (10년 CAGR < 무위험이자율 → 금지), **매수 적기는 없음** — 즉시 소액 + 하락 시 추가
- 매도는 **가격이 아닌 해자 건강도**
- **숙성기 2~4주**로 AI 속도의 과신 편향 제동

## 살아있는 문서

모든 playbook은 실운영 사이클로 개정된다. 회고는 각 실행 산출물(shallow/deep/monitoring) 안에 기록, 개정 이력은 `git log`로 추적.
