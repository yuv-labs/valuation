# Unified Shallow Dive Playbook (Buffett + Fisher)

한 기업(단건) 또는 3~5개 배치에 대해 **Deep Dive 진입 여부 + 트랙 배정(Buffett형 / Fisher형)** 을 1~2시간 내 판정한다.

**Shallow인 이유**: 훌륭함을 확신하려는 게 아니라 **(a) Deep Dive에 1~2주를 투자할 가치가 있는가** + **(b) 어느 트랙의 Deep이 적합한가**를 판정. 확신 형성(형용사 누적 · DCF 정밀화)은 해당 트랙의 Deep에서.

트랙별 Deep playbook은 분리 유지:

- **Buffett 트랙 Deep**: `playbook/buffett/DEEP_DIVE.md` (DCF 3시나리오 중심)
- **Fisher 트랙 Deep**: `playbook/fisher/DEEP_DIVE.md` (Stream A~F 구조)

---

## 설계 철학

1. **Phase 0~8은 트랙 무관 공통 재료.** 사업·재무·경영진·산업·질적 체크리스트·밸류에이션 위치·리스크·기회는 두 프레임 모두 출발점이 동일하다.
2. **Phase 9는 Track 판정.** `playbook/fisher/PHILOSOPHY.md:197-203`의 "해자 완성 vs 형성" 원칙을 4축 객관 지표로 구현. Valuation보다 **앞**에 배치 (판정이 valuation 방법론 분기).
3. **Phase 10은 Track 분기 Valuation (필수).** Buffett → 간이 3시나리오 DCF (EPS×PER) / Fisher → 간이 3시나리오 ROE×PBR 복리 CAGR. r = 10% 고정. Risk·Opp 강제 매핑으로 정성을 정량으로.
4. **Phase 11은 Deep 진입 판단.** 확신도 낮으면 Deep 진입 금지 (Fisher 계승). Phase 10 정량 결과가 보조 입력.
5. **Phase 12는 배치 모드 전용.** 3~5개 동시 Shallow 시 상대 비교. 트랙별 클러스터링 + 정량 축 포함.

---

## 실행 모드

| 모드 | 용도 | Phase 구성 |
| ------ | ------ | ---------- |
| **단건** (기본) | 한 기업만 판단 / 첫 실행 경험 쌓기 | Phase 0~11 (Phase 12 skip) |
| **배치** (3~5개 병렬) | Sensing 풀이 쌓여 월 1~2회 세션 | Phase 0~12 전부 |

입력 티커 수로 자연 분기. 호출 예시:

```text
단건:  "playbook/SHALLOW_DIVE.md를 읽고 {TICKER}에 대해 Shallow Dive를 실행해줘."
배치:  "playbook/SHALLOW_DIVE.md를 읽고 {T1}, {T2}, {T3}에 대해 Shallow Dive 배치를 실행해줘."
```

---

## 사전 조건

- `knowledge/` 디렉토리 프레임워크 파일 (아래 표)
- 데이터 파이프라인 실행 가능 (DART API key + pykrx / SEC User-Agent + Stooq)
- `../research/SENSING_LOG.md`에 대상 티커 기록 (또는 직접 Sensing 엔트리 추가 후 진입)

### 참조 knowledge 파일

| 파일 | 내용 | 사용 Phase |
| ------ | ------ | ----------- |
| `워런_버핏_경제적해자.md` | 프랜차이즈 3조건, See's 테스트, Owner Earnings | Phase 6-A |
| `성장주_투자.md` | Fisher 15 기준, N+1차항 | Phase 6-B |
| `가치평가_프리미엄.md` | 프리미엄 9요인, 터미널 스테이지 | Phase 6-C, Phase 7 |
| `피터_린치.md` | 2분 테스트, 6분류, PEG | Phase 2, Phase 6-D |
| `경영진_지배구조.md` | 1분 신뢰성 테스트 | Phase 4 |
| `할인율_기대수익률.md` | PBR 공식, 10년 기대수익률 | Phase 7 |
| `가치평가_본질.md` | value trap, 과신 체크 | Phase 11 |

---

## Phase 0: 데이터 수집

**입력**: 대상 티커 목록 (1개 또는 3~5개)
**산출**: Gold 패널에 대상 티커 적재

### 한국 주식 (KR)

```bash
python3.13 -m data.bronze.update_krx --tickers {TICKERS}
python3.13 -m data.silver.build --markets kr
python3.13 -m data.gold.build --panel valuation --markets kr
```

DART 재무제표는 `DARTProvider`로 수집 (API key 필요).

### 미국 주식 (US)

```bash
python3.13 -m data.bronze.update --tickers {TICKERS} --sec-user-agent "{이름} {이메일}"
python3.13 -m data.silver.build --markets us
python3.13 -m data.gold.build --panel valuation --markets us
```

### 검증

```python
panel = pd.read_parquet('data/gold/out/valuation_panel.parquet')
for t in TICKERS:
    ticker_data = panel[panel['ticker'] == t].sort_values('end')
```

티커별로 `revenue_ttm`, `ebit_ttm`, `cfo_ttm`, `capex_ttm`, `shares_q`, `total_equity_q`, `total_assets_q`, `price`, `market_cap` 존재 확인.

---

## Phase 1: 유니버스 하한선 (게이트)

**입력**: 티커
**산출**: PASS / MARGINAL / FAIL — **FAIL이면 즉시 탈락**, Phase 2 이하 skip

**근거**: Fisher 프레임은 경영진 판단이 본체이므로 판단 가능한 규모·공시 수준이 전제 (`playbook/fisher/PHILOSOPHY.md` 섹션 6). Buffett 트랙에서도 동일 게이트 유효 — 공시가 얇으면 DCF 가정이 공중에 뜸.

| 항목 | 조건 | 판정 | 근거 |
| ------ | ------ | ------ | ------ |
| 상장 기간 | ≥ 5년 | | |
| 컨퍼런스콜 | 정기 운영 + Q&A 전사본 공개 | | |
| 현 경영진 재직 | ≥ 3년 | | |
| 임원 이직률 파악 | DART/EDGAR/링크드인으로 추적 가능 | | |
| 업계 평판 접근 | 최소 한 단계 거쳐 닿음 | | |

**FAIL 처리**: 하나라도 명백 FAIL → "판단 가능 범위 밖" → 탈락.
**MARGINAL 처리**: 상장 4.5년처럼 근접한 경우 조건부 PASS 가능 (근거 명시). Deep 진입 전까지 재확인.

---

## Phase 2: 2분 테스트 + 사업모델 한 페이지

**입력**: 기본 IR 자료·홈페이지
**산출**: 2분 요약 + 사업모델 표

### 2분 테스트 (Lynch)

> "10살짜리 아이에게 2분 이내에 주식을 보유한 이유를 설명할 수 없다면 그 주식을 소유해서는 안 된다."

한 문단: `{회사}는 {무엇을} {누구에게} {어떻게} 팔아서 돈을 번다. {왜 훌륭할 수 있는지} {한 문장}.`

설명 불가 → **탈락** (능력 범위 밖).

### 사업모델 한 페이지

| 항목 | 내용 |
| ------ | ------ |
| 제품/서비스 | |
| 주요 고객 | |
| 수익 모델 | |
| 고정비 vs 변동비 | |
| 규모의 경제 작동 여부 | |

---

## Phase 3: 정량 기초 5년

**입력**: Gold 패널
**산출**: 5년 추이 표 + 한 줄 코멘트 + 정량 시그널 추출 (Phase 9 Track Gate + Phase 10 Valuation 공통 입력)

정밀 DCF(Buffett)는 Phase 10-A 또는 Deep Section 6. 정밀 10년 CAGR(Fisher)은 Deep Stream C. 여기는 5년 일관성·추세만 확보.

| 지표 | 계산 | 해석 포인트 |
| ------ | ------ | ------------ |
| 매출 | `revenue_ttm` | 5년 CAGR, 추세 |
| 영업이익률 | `EBIT_ttm / Revenue_ttm` | 마진 유지/개선 |
| 순이익 | `net_income_ttm` | 회계 왜곡 체크용 |
| CFO | `cfo_ttm` | 현금창출력 일관성 |
| CAPEX | `capex_ttm` | 자본집약도 |
| **FCF** | `CFO − CAPEX` | 일관성 |
| **ROIC** | `EBIT × (1−0.22) / (총자산 − 유동부채 − 현금)` | 자본효율성 핵심 (Phase 10-B Fisher 입력) |
| **ROE** | `net_income / total_equity` | buyback 집약 기업은 왜곡 주의 (equity ≤ 0 가능) (Phase 10-B Fisher 입력) |
| R&D / 매출 | | 재투자 강도 (Phase 9 B축 입력) |
| Capex / 매출 | | 재투자 강도 (Phase 9 B축 입력) |
| 발행주식수 5년 변화 | | buyback/증자 패턴 (Phase 9 B축 + Phase 10-A 주식수 변화 입력) |

**5년 추세 한 줄 코멘트** 필수: "일관되게 성장·마진 확대" / "변동성 큼" / "최근 둔화" / "buyback으로 EPS 상향 분해" 등.

**Phase 9 Track Gate 입력 추출** (이 Phase 말미에 명시):

- 5년 매출 CAGR: `__%`
- 5년 ROIC 평균 및 추세: 안정 / 상승 / 하락
- 재투자율 = (Capex + R&D) / CFO: `__%`
- 5년 주식수 변화: `__%` (음수면 buyback 집약)

---

## Phase 4: 경영진 기본 프로필

**입력**: 사업보고서, 최근 컨콜 1건, DART/EDGAR Form 4/144
**산출**: 경영진 프로필 표 + 인상적 문장 1개 + 1분 신뢰성 테스트

정성 평가(Fisher 15 정성 10개)는 Fisher Deep Stream B, 경영진 심층 평가는 Buffett Deep Section 3. 여기는 1층위 자료 단편.

| 항목 | 내용 |
| ------ | ------ |
| CEO 이름 / 재직 기간 / 경력 배경 | |
| CFO 이름 / 재직 기간 / 경력 배경 | |
| CEO·CFO 자사주 보유율 | |
| 내부자 거래 최근 패턴 (매수/매도/중립) | |
| 과거 위기 대응 기록 1~2건 (2020 COVID, 금리 급등, 산업 충격 등) | |
| 주주서한·최근 컨콜 Q&A 인상적 문장 1개 | |

### 1분 신뢰성 테스트 (`knowledge/경영진_지배구조.md`)

| # | 항목 | 판정 | 근거 |
| --- | ------ | ------ | ------ |
| 1 | ROE 10%+ (30%+면 지속 의심) | | |
| 2 | ROA 7%+ | | |
| 3 | 재무상태표 의심 항목 (매출채권·무형자산·자본잉여금 등) | | |
| 4 | 영업외/일회성 비용 패턴 | | |
| 5 | 주주환원 (배당·buyback 정책) | | |

**경영진 가이던스 성격 관찰** (Phase 9 D축 입력):

- 최근 2분기 컨콜의 경영진 강조 지점이 **현금 환원·마진 안정** 중심인가, **재투자·파이프라인·시장 확대** 중심인가?

---

## Phase 5: 산업 지도

**입력**: 산업 리포트·IR 자료
**산출**: 산업 지형 표

| 항목 | 내용 |
| ------ | ------ |
| 주요 경쟁사 3~5 | |
| 시장 집중도 (상위 N사 점유율) | |
| 산업 성장률 (최근 3년 + 향후 전망 CAGR) | |
| 이 기업의 산업 내 위치 | 1등 / 2등 / 틈새 / 도전자 |
| 해자 유형 후보 (Phase 6에서 판정) | 브랜드 / 네트워크 / 전환비용 / 원가우위 / 수직통합 |

**산업 성숙도 관찰** (Phase 9 C축 입력):

- 산업 CAGR 대비 이 기업 매출 CAGR이 상회 / 근접 / 미달?
- 산업 자체가 확장 중 / 성숙 / 축소?

---

## Phase 6: 질적 체크리스트 (혼합)

**입력**: Phase 1~5 + 공시·IR·언론
**산출**: 4개 프레임 각 요약 판정

한 번의 Shallow로 Buffett·Fisher·Lynch·Premium 4개 프레임 모두에 재료를 확보. 각 서브섹션은 **깊은 해석이 아닌 관찰 스냅샷**. 정식 판정은 해당 트랙의 Deep에서.

### 6-A. 버핏 해자 (프랜차이즈 3조건)

`knowledge/워런_버핏_경제적해자.md` 참조.

| 조건 | 판정 | 근거 |
| ------ | ------ | ------ |
| 1. 소비자가 필요로 하거나 욕망한다 | YES/NO/UNCERTAIN | |
| 2. 소비자 마음속에 대체재가 없다 | YES/NO/UNCERTAIN | |
| 3. 가격 규제가 없다 | YES/NO/UNCERTAIN | |

**See's 테스트**: ROIC vs See's 세전 ROIC 60% / CAPEX/매출 수준 / OE > NI인가.

**해자 유형별 등급** (NONE/LOW/MODERATE/HIGH): 브랜드 / 네트워크 / 전환비용 / 원가우위 / 수직통합.

### 6-B. Fisher 15 정량 5개

`knowledge/성장주_투자.md` 참조. 공개 숫자로 답할 수 있는 5개. 정성 10개는 Fisher Deep Stream B.

| # | 기준 | 지표 | 판정 | 근거 |
| --- | ------ | ------ | ------ | ------ |
| 1 | 매출 성장 잠재력 | 5년 매출 CAGR + 경영진 가이던스 | PASS/MIXED/FAIL | |
| 3 | R&D 투입 대비 성과 | R&D/매출 추이 + 매출 성장 연동 | | |
| 5 | 충분한 이익률 | 영업이익률 vs 업계 평균 | | |
| 6 | 이익률 유지/개선 노력 | 5년 마진 추세 | | |
| 10 | 원가/회계 관리 | CFO/NI, 운전자본 추이, 회계 이슈 유무 | | |

정량 5/5 PASS = Deep 진입 우선순위 상승. FAIL 2+ = 우선순위 하향 (단정 금지).

### 6-C. 프리미엄 9요인

`knowledge/가치평가_프리미엄.md` 참조. 각 요인 1~5점.

| # | 요인 | 점수 | 근거 |
| --- | ------ | ----- | ------ |
| 1 | 반복구매 | | |
| 2 | 확장성 | | |
| 3 | 생산성 향상 | | |
| 4 | 원가절감능력 | | |
| 5 | 락인 | | |
| 6 | 예측 가능성 | | |
| 7 | 사이클 (비순환일수록 높음) | | |
| 8 | 산업의 고성장 | | |
| 9 | 가격결정력 | | |

종합: __/45

### 6-D. Lynch 6분류

`knowledge/피터_린치.md` 참조. 라벨만 (정밀 해석은 해당 Deep에서):

| 분류 | 해당? | 근거 |
| ------ | ------ | ------ |
| 저성장주 / 대형 우량주 / 고성장주 / 경기순환주 / 자산주 / 회생주 | 1개 선택 | |

**PEG 간이**: PER / 예상 성장률. Lynch 기준 (PER이 성장률 절반이면 매우 유망, 두 배면 매우 불리).

---

## Phase 7: 밸류에이션 현재 위치

**입력**: 현재가·Gold 패널
**산출**: 대략치 지표 표 + PBR 역산

피셔식 10년 기대수익률 정밀은 Fisher Deep Stream C. 정밀 DCF는 Phase 10-A 또는 Buffett Deep Section 6. 여기 Phase 7은 **감 잡기 + 트랙 배정 시그널**만.

| 지표 | 값 | 5년 평균 | 5년 레인지 | 해석 |
| ------ | ----- | --------- | ----------- | ------ |
| PER | | | | 과열/소외 구간 |
| PBR | | | | |
| EV/EBIT | | | | |
| FCF Yield | FCF_ttm / 시총 | | | 수익률 하한선 감 |
| 주가 5년 추이 | (고점/저점/현재) | | | 절대 수준 감각 |

### PBR 공식 역산 (`knowledge/할인율_기대수익률.md`)

```text
PBR = ((1+ROE)/(1+r))^N
```

현재 PBR과 **경제적 ROE** (buyback 왜곡 제거 — ROE 대신 **ROIC 또는 ROA×레버리지** 대입)를 이용, 시장이 가정하는 N(초과수익 지속기간)을 역산. r = 10%, 12% 두 가지.

**주의**: buyback 집약 기업(예: 자기자본 ≤ 0)은 원본 ROE 공식 적용 불가. ROIC 기반 대체: `r = (1+ROIC)/(EV/IC)^(1/N) − 1`.

**Fisher 트랙 배정 시 매수 금지 판정에는 이 단계 사용하지 않음** (N+1차항 논리). 본격 판정은 Fisher Deep Stream C.

---

## Phase 8: 1차 가설 + 리스크·기회 톱3

**입력**: Phase 2~7 전체
**산출**: 한 문단 가설 + 리스크 3개 + 기회 3개

Phase 10 Track 분기 Valuation에서 이 6항목을 시나리오 변수(CAGR·마진·ROE·PBR)에 매핑하므로, 관찰 지표는 **정량 지표**로 기술할 것.

### 1차 가설

`{회사}는 {산업 맥락}에서 {독특한 포지션}으로 {해자 또는 성장 드라이버}. 앞으로 {기간} 동안 {성장 경로}가 가능해 보이며, {경영진 또는 조직 특징}이 이 경로를 뒷받침한다.`

확신 표현 금지. "~할 수 있다", "~해 보인다" 톤.

### 리스크 톱3

| 순위 | 리스크 | 발생 시 영향 | 관찰 지표 |
| ------ | -------- | -------------- | ----------- |
| 1 | | | |
| 2 | | | |
| 3 | | | |

꼬리 리스크(확률 낮지만 치명적)부터.

### 기회 톱3

| 순위 | 기회 | 실현 시 영향 | 관찰 지표 |
| ------ | -------- | -------------- | ----------- |
| 1 | | | |
| 2 | | | |
| 3 | | | |

현재 가격에 반영되지 않은 상방 요인(신제품·지역 확장·재무 개선·규제 완화 등)부터.

---

## Phase 9 ⭐ Track Assignment Gate

**입력**: Phase 3~7 산출물
**산출**: 트랙 배정 (버핏형 / 피셔형 / 미정) + 확신도 + 4축 판정

> **중요 — 순서 원칙**: Valuation(Phase 10)은 Track 판정(Phase 9) **후**에만 수행. Track 판정이 valuation 방법론을 분기하므로 이 순서 역전 금지. (2026-04-18 v1에서 v2 개정 이유: Phase 9 조건부 DCF가 Track Gate 앞에 있을 때 agent가 스킵 유혹 → Buffett 배정된 PM·RMD도 DCF 결측 발생)

### 배정 질문

`playbook/fisher/PHILOSOPHY.md:200` 계승: **"해자가 이미 완성되어 현금 회수 중인가? / 아직 형성·확장 중인가?"**

### 4축 판정 기준

| 축 | 지표 출처 | Buffett형 신호 | Fisher형 신호 |
| --- | --- | --- | --- |
| **A. ROIC 추세** (5년) | Phase 3 | 안정·성숙 (레인지 박스) 또는 소폭 하락 | 상승 중 또는 확장 여지 명확 |
| **B. 재투자율** | Phase 3 | **낮음 <30%** (Capex+R&D)/CFO + buyback/배당 많음 | **높음 >50%** + buyback/배당 적거나 없음 |
| **C. 매출 CAGR** (5년) | Phase 3 + Phase 5 | **산업 CAGR 근처 또는 완만** | **산업 CAGR 명백히 상회** |
| **D. 경영진 가이던스 성격** | Phase 4 | 현금 환원·마진 안정·비용 규율 중심 | 재투자·N+1차항·파이프라인·시장 확대 중심 |

### 판정 테이블 (Shallow 출력에 포함)

```markdown
| 축 | 관측값 | 판정 |
| --- | --- | --- |
| A. ROIC 추세 | 5년 평균 __%, 추세 _____ | → 버핏형 / 피셔형 |
| B. 재투자율 | (Capex+R&D)/CFO = __%, buyback __%/yr | → 버핏형 / 피셔형 |
| C. 매출 CAGR | 기업 __% vs 산업 __% | → 버핏형 / 피셔형 |
| D. 가이던스 성격 | _____ | → 버핏형 / 피셔형 |
```

### 배정 규칙

- **3~4축 동일 방향** → 해당 트랙 배정 (확신도: 높음)
- **2:2 혼재** → **미정** (확신도: 낮음) — Deep 진입 보류 또는 양쪽 Deep 고려
- **경계 (3:1)** → 배정하되 확신도: 중간. Deep 중 재배정 여지 명시

### 오배정 허용

배정 확정 후 Deep 중 오배정 징후 관찰 시 **재배정 허용** (`PHILOSOPHY.md:201` 원칙 계승). 단 "한 세션 한 프레임" — 재배정은 세션 종료 후.

### 산출물 포맷

```markdown
## Phase 9. Track Assignment

**배정**: {버핏형 | 피셔형 | 미정}
**확신도**: {높음 | 중간 | 낮음}
**4축 판정**:
- A. ROIC 추세: ... → 버핏/피셔
- B. 재투자율: ... → 버핏/피셔
- C. 매출 CAGR: ... → 버핏/피셔
- D. 가이던스 성격: ... → 버핏/피셔
**Deep 프로토콜**: `playbook/{buffett|fisher}/DEEP_DIVE.md`
**재배정 플래그**: (Deep 중 관찰할 역신호 명시)
```

---

## Phase 10: 간이 3시나리오 Valuation (필수, Track 분기)

**입력**: Phase 3 정량 기초, Phase 5 산업 지도, Phase 8 Risk·Opportunity, **Phase 9 Track 배정**
**산출**: Bull/Base/Bear 시나리오 + 확률가중 기대치 + Trigger 신호

**공통 가정**:

- 할인율 `r = 10% 고정` (개인 요구수익률 표준화, `knowledge/할인율_기대수익률.md`)
- 기간 10년
- 세율 22% (법정 + state mix 정상화)

**분기 규칙**:

- **버핏형 배정** → **10-A만** (DCF: EPS × PER × 할인)
- **피셔형 배정** → **10-B만** (ROE × PBR 복리 CAGR)
- **미정** → **10-A + 10-B 둘 다** 수행, 값 비교가 재분류 힌트

**프레임 근거**:

- Buffett 해자 완성·현금 회수형 → 현금흐름 할인이 자연 (DCF)
- Fisher 해자 형성·복리 재투자형 → book 복리가 자연 (ROE × PBR)
- `playbook/fisher/PHILOSOPHY.md:197-203`의 "해자 완성 vs 형성" 구분이 valuation 방법론 분기로 확장

---

### 10-A. 버핏 분기 — 간이 3시나리오 DCF (EPS × PER)

**참조 원형**: `research/fisher/deep-dive/IDXX_idexx-laboratories.md:820-955` (Stream C)

#### 10-A-1. 시나리오 가정 매트릭스

| 변수 | Bull | Base | Bear |
| --- | :-: | :-: | :-: |
| 매출 CAGR (10년) | __% | __% | __% |
| 터미널 EBIT 마진 | __% | __% | __% |
| 주식수 연간 변화 (buyback 음수) | __% | __% | __% |
| 터미널 PER | __x | __x | __x |

#### 10-A-2. Risk / Opportunity 매핑 (Phase 8 연계)

| 항목 | Bull 전제 | Base 전제 | Bear 전제 |
| --- | --- | --- | --- |
| Risk #1 | 해소 | 완만 | 실현 |
| Risk #2 | 해소 | 완만 | 실현 |
| Risk #3 | 해소 | 완만 | 실현 |
| Opp #1 | 실현 | 부분 | 미실현 |
| Opp #2 | 실현 | 부분 | 미실현 |
| Opp #3 | 실현 | 부분 | 미실현 |

#### 10-A-3. 계산

```text
10년 후 매출 = 현재 매출 × (1 + CAGR)^10
10년 후 NI = 매출 × EBIT 마진 × (1 − 세율)
10년 후 주식수 = 현재 × (1 + Δshares)^10
10년 후 EPS = NI / 주식수
10년 후 가격 = EPS × 터미널 PER + 누적 배당 (배당 있으면)
PV = 10년 후 가격 / 1.10^10
```

#### 10-A-4. 결과

| 시나리오 | PV | 현재가 대비 | 실현 CAGR |
| --- | --- | --- | --- |
| Bull | | | |
| Base | | | |
| Bear | | | |

**확률가중 PV**: `P_Bull × PV_Bull + P_Base × PV_Base + P_Bear × PV_Bear` (확률 추정 근거 1줄 명시)
**현재가 대비**: __%

---

### 10-B. 피셔 분기 — 간이 3시나리오 기대 CAGR (ROE × PBR)

**공식**: `knowledge/할인율_기대수익률.md`

- 기본: `r = (1+ROE) / PBR^(1/N) − 1`
- **buyback 집약 (equity ≤ 0)**: `r = (1+ROIC) / (EV/IC)^(1/N) − 1`
- **배당 있는 경우** (단순화): `r ≈ (1+ROE×(1−payout)) / PBR^(1/N) − 1 + 배당수익률`

#### 10-B-1. 시나리오 가정 매트릭스

| 변수 | Bull | Base | Bear |
| --- | :-: | :-: | :-: |
| 유지 ROE (또는 ROIC) | __% | __% | __% |
| 예상 지속 년수 N | 10 | 10 | 10 |
| 터미널 PBR (또는 EV/IC) | __x | __x | __x |

**터미널 PBR 가정 가이드**:

- 해자 소실·경쟁균형 수렴 시나리오 → PBR → **1.0x** (ROE = r로 수렴)
- 해자 유지 시나리오 → **2~3x** (지속 프리미엄)
- 해자 확장 지속 시나리오 → **현재 PBR 유지** 또는 완만한 축소

#### 10-B-2. Risk / Opportunity 매핑 (Phase 8 연계)

| 항목 | Bull 전제 | Base 전제 | Bear 전제 |
| --- | --- | --- | --- |
| Risk #1~3 | 해소 (ROE 유지 · PBR 프리미엄) | 완만 (ROE 점감 · PBR 하락) | 실현 (ROE 훼손 · PBR 리레이팅) |
| Opp #1~3 | 실현 (ROE 상향 · PBR 유지) | 부분 | 미실현 |

#### 10-B-3. 계산 + 결과

| 시나리오 | 기대 CAGR | 판정 (아래 10-C 참조) |
| --- | :-: | :-: |
| Bull | __% | |
| Base | __% | |
| Bear | __% | |

---

### 10-C. 판정 기준 · Trigger 신호

본 Phase 결과는 **Deep 우선순위 감지용**. 매수/매도 판정은 Deep에서.

**10-A (Buffett DCF) 트리거**:

- **Bear PV > 현재가** → 극단 저가 신호 (단, "내가 핵심 리스크를 놓침" 자문 동반)
- **현재가 > Bull PV** → 과신 경고 (단, "내가 성장 동력을 과소평가" 자문 동반)
- **Base PV 근처** → 합리적 구간, Deep에서 정밀화

**10-B (Fisher ROE×PBR) 판정** — `playbook/fisher/PHILOSOPHY.md:178-195` 계승:

- **Bull CAGR ≥ 10%** → 매수 가능 후보 (Deep 필수)
- **Bull CAGR < 4%** → **매수 금지 trigger** (가장 낙관 가정으로도 리스크프리 이하)
- **Base CAGR > 10%** → 극단 저가 신호
- 중간 → 회색 구간, Deep Stream C에서 정밀 판정

**10-A, 10-B 값이 크게 다르면 재분류 힌트**:

- 미정 트랙에서 특히 유용
- DCF가 PV > 현재가인데 ROE×PBR CAGR < 4%라면 "터미널 PER 낙관 vs PBR 수렴 가정"의 이견 → Phase 9 재검토

---

### 10-D. 원칙

1. **판정 vs 감지 구분**: 본 Phase 결과는 Phase 11 "Deep 진입 결정"의 **보조 입력만**. Shallow 수준 자료(Gold + 웹 리서치)에서 도출된 숫자이므로 정밀 매수/매도 판정 금지.
2. **Fisher 원칙 보존**: 10-B의 **Bull CAGR < 4% 매수 금지 trigger**가 Shallow에서 유일한 강한 판정. 피셔식 "가장 낙관도 리스크프리 이하면 비싸다" 원칙.
3. **Deep과의 중복 최소화**:
   - 10-A (EPS×PER 4변수 간이) ≠ Buffett Deep Section 6 (policy catalog 기반 정밀 DCF + 민감도 + Reverse DCF)
   - 10-B (ROE×PBR 3변수 간이) ≠ Fisher Deep Stream C (EPS×PER 4시나리오 + 피어 터미널 PER + Reverse 역산)
4. **Risk/Opp 강제 매핑**: Phase 8의 6개 항목이 Bull/Base/Bear 시나리오 변수에 전부 tag. 정성 가정을 숫자로 강제.

---

## Phase 11: Deep 진입 결정 + 확신도

**입력**: Phase 1~10 전체
**산출**: 4갈래 결정 + 확신도

| 결과 | 조건 | 다음 행동 |
| ------ | ------ | ---------- |
| **Deep Dive 진입** | 유니버스 PASS + 2분 테스트 명료 + 정량 5개 PASS ≥ 3 + Track Gate 확신도 ≥ 중간 + **Phase 10 가격 축 장애 없음** (10-B Bull CAGR ≥ 4% or 10-A Bull PV 현재가 근처 이상) + (배치면 상대 우위 명확) | 배정된 트랙 Deep 착수 (동시 Deep 2~4개 한도) |
| **Keep** (배치 모드 한정) | 매력적이나 Deep 우선순위 아직 — 다음 배치에서 신규 후보와 상대 비교하면 판단 날카로움. Phase 10 결과가 Base ≈ 현재가 회색 구간인 경우 포함 | 다음 Shallow Batch 자동 포함 |
| **Parking Lot** | 분기 재방문이 맞음 — 외부 이벤트 대기(신제품·규제·사이클 저점) | 분기 리뷰 세션 |
| **탈락** | 유니버스 FAIL / 2분 테스트 실패 / Phase 9 "미정" + 확신도 낮음 / **Phase 10-B Bull CAGR < 4% 매수 금지 trigger** / 명확한 결격 | Sensing 로그에서 제거 고려 |

### 확신도 명시

| 확신도 | 의미 |
| -------- | ------ |
| 높음 | 판정 근거를 한 문단으로 설명 가능 + Track Gate 3~4축 일치 |
| 중간 | 방향은 있으나 일부 축 불확실 — Deep 중 재확인 필요 |
| 낮음 | 왜 이 가격·왜 이 트랙인지 충분히 설명 불가 → **Deep 진입 금지** |

**단건 모드의 Keep 주의**: 단건은 비교 대상 없으므로 Keep의 원래 효용(상대 비교)이 없음. 단건에서 Keep은 **"다음 배치 예약"** 예약 개념. 권고: 단건은 3갈래(Deep / Parking / 탈락).

### 과신 점검 (Overconfidence Check)

`knowledge/가치평가_본질.md` 참조. 결론 전 자문:

> "왜 싸가?" / "왜 비싼가?" / "왜 이 트랙인가?"

- Bear IV > 현재가 × 2 → "내가 핵심 리스크를 놓치고 있다"가 더 유력
- 현재가 > Bull IV × 2 → "내가 성장 동력을 과소평가"가 더 유력
- PBR < 1인 수익성 기업에서 시장 할인 이유를 설명 못 하면 판정 보류
- Track Gate 4축이 2:2인데 "이 트랙일 것 같다" 직감으로 배정하면 **미정 플래그 유지**

---

## Phase 12: 배치 비교 테이블 (배치 모드 전용)

**실행 조건**: 티커 2개 이상. 단건 모드 skip.

**입력**: 배치 내 모든 기업의 Phase 1~11 산출물
**산출**: 트랙별 비교 테이블 2개 (Buffett 그룹 / Fisher 그룹)

### 공통 축

| 기업 | 사업모델 1줄 | 경영진 재직 | ROIC 5년 | 해자/성장 가설 | **트랙 배정** | 정량 5개 PASS | Deep 진입 추천 | 확신도 |
| ------ | ------------- | ------------- | ---------- | --------------- | :---: | :---: | :---: | :---: |
| | | | | | 버핏/피셔/미정 | /5 | | |

### Buffett 그룹 — 정량 축 (Phase 10-A 결과)

| 기업 | 확률가중 PV | 현재가 | 현재가/PV | Bear/현재가 | Bull/현재가 | 가격 매력 순위 |
| --- | --- | --- | --- | --- | --- | :---: |

- **현재가/PV**: 낮을수록 저평가 (100% 미만 = PV > 현재가)
- **Bear/현재가 > 100%**: 극단 저가 신호
- **Bull/현재가 < 100%**: 과신 경고

### Fisher 그룹 — 정량 축 (Phase 10-B 결과)

| 기업 | Bull CAGR | Base CAGR | Bear CAGR | 확률가중 CAGR | 매수 금지 trigger? | 가격 매력 순위 |
| --- | --- | --- | --- | --- | :-: | :---: |

- **Bull CAGR ≥ 10%**: 매수 가능 후보 (Deep 필수)
- **Bull CAGR < 4%**: 매수 금지 trigger (피셔 원칙)
- 확률가중 CAGR이 r=10% 상회 여부가 상대 순위 핵심

### 미정 트랙 (Phase 10-A + 10-B 둘 다 수행한 기업)

| 기업 | 10-A 확률가중 PV / 현재가 | 10-B 확률가중 CAGR | 프레임 간 이견 | 재분류 힌트 |
| --- | --- | --- | --- | --- |

두 방식 값이 크게 다르면 "터미널 PER 가정 vs PBR 수렴 가정"의 이견 → Phase 9 재검토.

비교 테이블이 단독 리포트보다 정보 많음 — 상대 우위가 드러남. 특히 **같은 트랙 내 Deep 우선순위**가 정량으로 명료화.

---

## 출력 포맷

### 파일 위치

**신규 통합 Shallow**: `../research/shallow-dive/{TICKER}_{name}.md`

(기존 `research/{buffett|fisher}/shallow-dive/*`는 legacy 보존, 신규 Shallow는 모두 통합 디렉토리에 작성)

### 파일 템플릿

```markdown
---
ticker: XXXX
shallow_date: YYYY-MM-DD
track_verdict: fisher       # buffett | fisher | undecided
confidence: high            # high | medium | low
deep_eligible: true
# Phase 10 정량 결과 (optional, Track에 따라 택1)
scenario_pv_weighted: 123.45    # Buffett 배정 시 (10-A 확률가중 PV)
scenario_cagr_bull: 0.12        # Fisher 배정 시 (10-B Bull CAGR)
scenario_cagr_weighted: 0.07    # Fisher 배정 시 (확률가중 CAGR)
---

# {회사명}({TICKER}) Shallow Dive — {날짜}

기준일: {날짜} | 데이터: {출처} | 주가: {현재가} ({날짜})
실행 모드: {단건 / 배치 세션 YYYY-MM-DD}

## 1. 유니버스 하한선 (Phase 1)
## 2. 2분 테스트 + 사업모델 (Phase 2)
## 3. 정량 기초 5년 (Phase 3)
## 4. 경영진 기본 프로필 (Phase 4)
## 5. 산업 지도 (Phase 5)
## 6. 질적 체크리스트 (Phase 6)
  ### 6-A. 버핏 해자
  ### 6-B. Fisher 15 정량 5개
  ### 6-C. 프리미엄 9요인
  ### 6-D. Lynch 6분류
## 7. 밸류에이션 현재 위치 (Phase 7)
## 8. 1차 가설 + 리스크·기회 톱3 (Phase 8)
## 9. Track Assignment (Phase 9) ⭐
## 10. 간이 3시나리오 Valuation (Phase 10) — Track 분기 필수
  ### 10-A. Buffett DCF (EPS×PER) — 버핏 배정 시
  ### 10-B. Fisher 기대 CAGR (ROE×PBR) — 피셔 배정 시
  ### 10-C. Trigger 신호
## 11. Deep 진입 결정 + 확신도 (Phase 11)
## 12. (배치 모드) 배치 비교 코멘트 (Phase 12)
```

---

## 원칙

1. **Shallow에서 확신 만들려 하지 말 것** — Deep 진입 여부 + 트랙 배정 + 정량 감지만
2. **유니버스 하한선은 게이트** — 미통과 = 판단 불가 = 탈락. "어떻게든 해보자" 금지
3. **Phase 6 네 프레임은 스냅샷** — 정식 판정은 배정된 트랙의 Deep에서
4. **Phase 9 Track 판정 → Phase 10 Valuation 순서 엄격 준수** — 판정이 valuation 방법론 분기. 순서 역전 시 skip 유혹.
5. **Phase 10은 Track 분기 필수** — Buffett 10-A (DCF) / Fisher 10-B (ROE×PBR) / 미정 둘 다. r=10% 고정.
6. **Phase 10은 판정 아닌 감지** — 단 10-B Bull CAGR < 4% **매수 금지 trigger**만 예외 (피셔 원칙).
7. **Phase 9는 객관 4축** — 직감이 아닌 지표. 2:2 혼재면 "미정" 유지
8. **배치 > 단건** — 비교의 이점은 Deep 우선순위 판단에 날카로움. 단건에서 Keep은 실질 Parking-like
9. **확신도 낮음 = Deep 진입 금지** — Parking 또는 탈락
10. **buyback 집약 기업의 ROE 왜곡 주의** — Phase 3·7·10-B에서 ROIC + EV/IC 변형 사용
11. **Sensing 오염 금지** — Shallow 결과가 Sensing 로그의 기록 방식을 바꾸지 않도록
12. **AI 협업의 1~2시간 compression을 확신 형성으로 착각하지 말 것** — 본격 확신은 Deep + 숙성기

---

## 트랙 배정 후 Deep 진입

배정된 트랙의 Deep playbook 호출:

- **Buffett형 → `playbook/buffett/DEEP_DIVE.md`** (DCF 3시나리오 중심, 해자 건강도·경영진·위기 대응 심화)
- **Fisher형 → `playbook/fisher/DEEP_DIVE.md`** (Stream A~F, 경영진 형용사 누적·10년 CAGR·숙성기)
- **미정** → Deep 보류. 추가 Shallow 라운드에서 축 재평가 or Parking

산출물 위치:

- Deep 본문: `../research/{buffett|fisher}/deep-dive/{TICKER}_{name}.md`
- Monitoring (Fisher Stream F): `../research/fisher/deep-dive/{TICKER}_monitoring.md`

---

## 살아있는 문서

실운영 경험이 쌓이면 Phase·판정 기준·출력 포맷이 개정된다. 개정 이력은 `git log`. 각 Shallow 산출물에서 "뼈대에 부족했던 것"을 짧게 회고하면 다음 개정의 입력.

**특히 Phase 9 Track Gate 4축은 실전 시험이 많이 필요한 초기 설계** — 2~3건 이상 사례 누적 후 가중치·tie-breaker 재검토.

### 변경 이력

- **2026-04-18 v1**: 신규 작성. 기존 `playbook/{buffett,fisher}/SHALLOW_DIVE.md`의 두 트랙을 통합 + Phase 10 Track Assignment Gate 신설. 기존 두 파일은 DEPRECATED로 마킹하고 legacy 참조용으로 보존.
- **2026-04-18 v2**: Phase 순서 역전 + Track 분기 Valuation 필수화.
  - **Phase 9·10 번호 교체**: Track Gate가 Phase 9(앞), 간이 Valuation이 Phase 10(뒤). v1에서 조건부 Valuation이 Track Gate 앞에 있을 때 agent skip 유혹 → Buffett 배정된 PM·RMD도 DCF 결측된 문제 구조적 해결.
  - **Phase 10 Track 분기**: 버핏 → 10-A (EPS×PER DCF) / 피셔 → 10-B (ROE×PBR 복리 CAGR) / 미정 → 둘 다. r = 10% 고정. 프레임 일치 (해자 완성 → 현금흐름 / 해자 형성 → book 복리).
  - **Phase 8 확장**: 기회 톱3 테이블 신설. Phase 10 시나리오 변수 강제 매핑 재료.
  - **Phase 12 확장**: 트랙별 정량 축 컬럼 2종 (Buffett: 확률가중 PV/현재가 / Fisher: Bull·Base CAGR).
