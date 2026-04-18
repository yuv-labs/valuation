# Shallow Dive Analysis Framework

> ⚠️ **DEPRECATED 2026-04-18**
>
> 신규 Shallow Dive는 통합 playbook **[../SHALLOW_DIVE.md](../SHALLOW_DIVE.md)** 를 사용하세요. 신규 통합 프로토콜은 Phase 10에 **Track Assignment Gate**를 두어 Buffett형/Fisher형을 객관 4축으로 배정합니다.
>
> 본 파일은 **legacy 참조용으로 보존** — 기존 `research/buffett/shallow-dive/*.md` 산출물(BBWI 등)의 해석과 Buffett 트랙 Deep Dive(`playbook/buffett/DEEP_DIVE.md`) 구조 이해에 활용.
>
> 신규 Shallow 산출물은 `research/shallow-dive/` 디렉토리에 작성.

---

주식 종목에 대해 정량(DCF) + 정성(투자 프레임워크 체크리스트) 분석을 체계적으로 수행하고 리포트를 생성하는 프롬프트 프레임워크.

**Shallow Dive인 이유:** 정성 분석은 투자 대가들의 프레임워크를 체크리스트로 적용하는 수준이다. 진정한 Deep Dive라면 산업 구조, 경쟁 역학, 공급망, 고객 인터뷰 등 현장 지식(scuttlebutt)에 기반한 깊은 이해가 필요하다. 이 프레임워크는 그 전 단계 — 정량 데이터와 공개 정보 기반의 구조화된 1차 스크리닝이다.

## 사용법

Claude Code에서 이 파일을 컨텍스트로 제공하고 분석 대상을 지정:

```text
"knowledge/ 디렉토리와 playbook/buffett/SHALLOW_DIVE.md를 읽고, {종목코드} {회사명}에 대해 분석을 수행해줘."
```

## 사전 조건

- `knowledge/` 디렉토리에 투자 프레임워크 파일 존재 (아래 목록 참조)
- 데이터 파이프라인 실행 가능
  - 한국 주식: DART API key + pykrx
  - 미국 주식: SEC User-Agent + Stooq

### knowledge 파일 목록

| 파일 | 내용 | 사용하는 Phase |
| ------ | ------ | --------------- |
| `워런_버핏_경제적해자.md` | 프랜차이즈 3조건, See's Candies 테스트, 해자 종류, Owner Earnings | Phase 3-1 |
| `성장주_투자.md` | Fisher 15 기준, N+1차항의 마법, GARP 비판, 사실 수집 | Phase 3-2 |
| `피터_린치.md` | 6분류, PEG, 10루타, 2분 테스트 | Phase 3-2, 7 |
| `가치평가_프리미엄.md` | 프리미엄 9요인 (반복구매, 확장성, 락인 등) | Phase 3-3 |
| `경영진_지배구조.md` | 1분 신뢰성 테스트, 사익편취 유형, 주주환원 | Phase 3-4 |
| `할인율_기대수익률.md` | PBR = ((1+ROE)/(1+r))^N 공식, CAPM 비판 | Phase 2-4 |
| `가치평가_본질.md` | 가치평가 7가지 함의, value trap, 가격 vs 가치 | Phase 7 |

---

## Phase 0: 데이터 수집

### Phase 0 목표

분석 대상 종목의 재무 데이터를 Bronze → Silver → Gold 파이프라인으로 적재.

### 절차 — 한국 주식 (KR)

1. **Bronze: DART 재무제표 수집**

   ```python
   from data.bronze.providers.dart import DARTProvider
   provider = DARTProvider(api_key=os.environ['DART_API_KEY'])
   provider.fetch(tickers=['{종목코드}'], out_dir=Path('data/bronze/out'), force=True)
   ```

   - 분기별 데이터(Q1~Q4) 확인. 연간(Q4)만 있으면 TTM 계산에 제약.
   - 최신 연도 데이터가 있는지 확인 (filed 날짜 기준).

2. **Bronze: KRX 주가 수집**

   ```bash
   python3.13 -m data.bronze.update_krx --tickers {종목코드}
   ```

3. **Silver + Gold 빌드**

   ```bash
   python3.13 -m data.silver.build --markets kr
   python3.13 -m data.gold.build --panel valuation --markets kr
   ```

### 절차 — 미국 주식 (US)

1. **Bronze: SEC 재무제표 + Stooq 주가 수집**

   ```bash
   python3.13 -m data.bronze.update --tickers {TICKER} --sec-user-agent "{이름} {이메일}"
   ```

2. **Silver + Gold 빌드**

   ```bash
   python3.13 -m data.silver.build --markets us
   python3.13 -m data.gold.build --panel valuation --markets us
   ```

### 데이터 검증 (공통)

```python
panel = pd.read_parquet('data/gold/out/valuation_panel.parquet')
ticker_data = panel[panel['ticker'] == '{종목코드}'].sort_values('end')
```

확인 항목:

- [ ] revenue_ttm, ebit_ttm, cfo_ttm, capex_ttm이 채워져 있는가
- [ ] shares_q, total_equity_q, total_assets_q가 있는가
- [ ] 최신 분기의 filed 날짜가 as_of_date 이전인가
- [ ] price, market_cap이 있는가 (NaN이면 주가 데이터 기간 확인)

---

## Phase 1: 회사 리서치

### Phase 1 목표

사업 모델, 부문별 실적, 성장 동력, 리스크 요인을 파악.

### 웹 리서치 체크리스트

- [ ] 사업 모델 (무엇을 만들어 누구에게 파는가)
- [ ] 핵심 브랜드/제품 라인업
- [ ] 부문별 매출 비중 및 추이 (부문이 다각화되어 있으면 부문별로)
- [ ] 최근 2년 매출/영업이익/순이익 추이
- [ ] 해외 매출 비중 및 주요 시장
- [ ] 최신 연간 가이던스 (매출, 영업이익률)
- [ ] 핵심 성장 동력 3가지
- [ ] 핵심 리스크 요인 3가지
- [ ] 최근 주요 뉴스/이벤트
- [ ] 현재 주가, 시가총액, 애널리스트 컨센서스

### 부문별 분석 (해당 시)

DART 파이프라인은 연결재무제표만 수집. 부문별 데이터는:

1. DART 사업보고서 본문 ("사업의 내용" 섹션)
2. 애널리스트 리포트
3. IR 자료

---

## Phase 2: 정량 분석

### Phase 2 목표

Gold 패널에서 핵심 지표를 추출하고 밸류에이션 기초 데이터를 산출.

### 2-1. 핵심 지표 추출 (연도별)

| 지표 | 계산 방법 | 용도 |
| ------ | ----------- | ------ |
| Owner Earnings | CFO_ttm - SBC_ttm - CAPEX_ttm | DCF 출발점. SBC 차감 근거는 valuation/RATIONALE.md 참조 |
| 영업이익률 | EBIT_ttm / Revenue_ttm | 마진 정상화 기준 |
| ROE | Net_Income_ttm / Total_Equity_q | PBR 공식 적용 |
| ROIC | EBIT_ttm × (1-0.22) / (Total_Assets - Current_Liab - Cash) | 자본효율성, 해자 |
| CAPEX/매출 | CAPEX_ttm / Revenue_ttm | 자본집약도 |
| OE/주 | Owner Earnings / Shares_q | 주당 가치 창출력 |

### 2-2. YoY 성장률 계산

매출, 영업이익, 순이익의 연도별 성장률 추이.

### 2-3. 밸류에이션 지표 (현재가 기준)

| 지표 | 계산 |
| ------ | ------ |
| 시가총액 | 현재가 × 총주식수 |
| PER | 시총 / Net_Income_ttm |
| PBR | 시총 / Total_Equity_q |
| EV/EBITDA | (시총 + 부채 - 현금) / (EBIT + D&A) |

### 2-4. PBR 공식 역산

`knowledge/할인율_기대수익률.md` 참조.

```text
PBR = ((1+ROE)/(1+r))^N
```

현재 PBR과 ROE를 대입하여 시장이 가정하는 N(ROE 유지기간)을 역산.
r = 10%, 12% 두 가지로 계산.

---

## Phase 3: 정성 분석 — 프레임워크 체크리스트

> **한계:** 이 Phase는 투자 대가들의 프레임워크를 체크리스트로 대입하는 수준이다. 공개 정보 기반의 1차 스크리닝이지, 산업 전문가 수준의 분석이 아님을 유념할 것. 진정한 정성 분석은 현장 지식(Fisher의 scuttlebutt), 공급망/고객 인터뷰, 경쟁사 비교 실사 등을 통해 이루어진다. 여기서 "?" 또는 "검증 불가"로 남는 항목이 많을수록 추가 리서치가 필요하다는 신호.

### 3-1. 경제적 해자 평가

`knowledge/워런_버핏_경제적해자.md`를 읽고 적용.

**프랜차이즈 3조건:**

| 조건 | 판정 | 근거 |
| ------ | ------ | ------ |
| 1. 소비자가 필요로 하거나 욕망한다 | YES/NO/UNCERTAIN | |
| 2. 소비자 마음속에 대체재가 없다 | YES/NO/UNCERTAIN | |
| 3. 가격 규제가 없다 | YES/NO/UNCERTAIN | |

**See's Candies 테스트:**

- ROIC vs See's 세전 ROIC 60%
- CAPEX/매출 (낮을수록 좋음)
- OE > 순이익인가 (감가상각 > CAPEX = 기존 자산으로 현금 창출)

**해자 종류별 평가:**

| 해자 유형 | 등급 (NONE/LOW/MODERATE/HIGH) | 근거 |
| ----------- | ------ | ------ |
| 브랜드 | | |
| 네트워크 효과 | | |
| 전환비용 | | |
| 원가우위 | | |
| 수직통합 | | |

**슈퍼스타 CEO 리스크:**
> "슈퍼스타가 있어야만 훌륭한 성과를 낼 수 있는 사업이라면 훌륭한 사업이라고 평가할 수 없습니다."

특정 개인에 대한 의존도를 평가.

**가치 창출형 성장 확인:**
> "재투자가 많이 필요하지 않은 채로 성장하는 기업이 진정으로 가치 있는 기업"

매출 성장률 vs CAPEX/매출로 판단.

### 3-2. Fisher 15 기준 + Lynch 분류

`knowledge/성장주_투자.md`, `knowledge/피터_린치.md`를 읽고 적용.

**Lynch 6분류:** 저성장주 / 대형 우량주 / 고성장주 / 경기순환주 / 자산주 / 회생주

**PEG 비율:**

- PER / 예상 성장률
- Lynch 기준: "PER이 성장률의 절반이면 매우 유망, 두 배면 매우 불리"

**Fisher 15 기준 평가표:**

| # | 기준 | 판정 | 근거 |
| --- | ------ | ------ | ------ |
| 1 | 매출 성장 잠재력 | | |
| 2 | 신제품 개발 의지 | | |
| 3 | R&D 투입 대비 성과 | | |
| 4 | 평균 이상의 영업 역량 | | |
| 5 | 충분한 이익률 | | |
| 6 | 이익률 유지/개선 노력 | | |
| 7 | 노사관계 | | |
| 8 | 임원 간 관계 | | |
| 9 | 두터운 경영진(depth) | | |
| 10 | 원가/회계 관리 | | |
| 11 | 산업 특화 경쟁력 | | |
| 12 | 장기적 시각 | | |
| 13 | 대량 증자로 주주이익 훼손 | | |
| 14 | 나쁜 일에도 투자자와 소통 | | |
| 15 | 경영진 이해상충 | | |

### 3-3. 프리미엄 9요인 점수화

`knowledge/가치평가_프리미엄.md`를 읽고 적용.

> "사업 분석의 귀결점은 초과수익의 폭(ROE)과 지속가능기간(N)이다."

| # | 요인 | 점수 (1~5) | 근거 |
| --- | ------ | ----------- | ------ |
| 1 | 반복구매 | | |
| 2 | 확장성 | | |
| 3 | 생산성 향상 | | |
| 4 | 원가절감능력 | | |
| 5 | 락인 | | |
| 6 | 예측 가능성 | | |
| 7 | 사이클 (비순환일수록 높음) | | |
| 8 | 산업의 고성장 | | |
| 9 | 가격결정력 | | |

종합: /45 ( %)

### 3-4. 경영진 신뢰성

`knowledge/경영진_지배구조.md`를 읽고 적용.

**1분 신뢰성 테스트:**

| # | 항목 | 판정 | 근거 |
| --- | ------ | ------ | ------ |
| 1 | ROE 10%+ (30%+면 지속가능성 의심) | | |
| 2 | ROA 7%+ | | |
| 3 | 재무상태표 (현금, 매출채권, 무형자산, 자본잉여금) | | |
| 4 | 영업외/일회성 비용 패턴 | | |
| 5 | 배당 여부 | | |

---

## Phase 4: DCF 시나리오 밸류에이션

### Phase 4 목표

Bull/Base/Bear 3개 시나리오로 DCF 실행, 적정가치 범위 산출.

### 4-1. 시나리오 설계

`scenarios/POLICY_CATALOG.md` 참조하여 기업 유형에 맞는 정책 선택.

**기업 유형 판별:**

- 고성장 소비재 → normalized_margin + gordon + 10년
- 시클리컬 → normalized_margin + exit_multiple + 5년
- 자본집약형 → normalized_roic + exit_multiple + 5년
- 안정 배당주 → avg_3y + gordon + 5~10년

**시나리오 가정 설계:**

| 정책 | Bull | Base | Bear | 근거 |
| ------ | ------ | ------ | ------ | ------ |
| pre_maint_oe | | | | |
| maint_capex | | | | |
| growth | | | | |
| fade | linear | linear | linear | |
| shares | avg_5y | avg_5y | avg_5y | 바이백 반영 여부는 valuation/RATIONALE.md 참조 |
| terminal | | | | |
| discount | | | | |
| n_years | | | | |

각 시나리오의 가정 논리를 명확히 기술할 것.

### 4-2. 시나리오 파일 생성

`scenarios/stocks/{종목코드}/` 디렉토리에 `bull.json`, `base.json`, `bear.json` 생성.

### 4-3. DCF 실행

```python
from valuation.run import run_valuation
result = run_valuation(
    ticker='{종목코드}',
    as_of_date='{as_of_date}',  # 최신 데이터의 filed 날짜 이후
    loader=loader,
    config=config,
    market='kr',  # 미국 주식이면 'us'
)
```

**주의:** `as_of_date`는 최신 filed 날짜 이후여야 PIT 필터링에서 최신 데이터를 포함.

### 4-4. 결과 정리

| 시나리오 | IV/주 | 현재가/IV | 안전마진 |
| ---------- | ------- | ---------- | --------- |
| Bull | | | |
| Base | | | |
| Bear | | | |

### 4-5. 민감도 분석

할인율 (8%, 10%, 12%, 14%) × 초기성장률 (5%, 7%, 10%, 12%, 15%, 20%) 2D 테이블.
현재가와 가장 가까운 셀이 시장의 묵시적 가정.

---

## Phase 5: 교차검증

### 5-1. PBR 역산 (Phase 2-4에서 이미 계산)

시장이 ROE를 몇 년간 유지할 것으로 가정하는지 해석.

### 5-2. Reverse DCF

Base 마진 + 할인율 10% 가정에서, 현재가를 정당화하는 초기 성장률을 역산.
해당 성장률이 현실적인지 평가.

### 5-3. Comparable 분석

동종 업계 + 글로벌 유사 기업의 PER, PBR, 영업이익률 비교.
프리미엄/디스카운트의 근거를 성장률과 ROE 차이로 설명.

### 5-4. 터미널 스테이지 밸류에이션

`knowledge/가치평가_프리미엄.md`의 터미널 스테이지 방법 적용:

- 산업 포화 시 예상 점유율/이익률 추정
- 포화 시점의 적정 멀티플 부여
- 현재가로 할인하여 현재 시총과 비교

---

## Phase 6: 리스크 정량화

### 핵심 리스크 항목

각 리스크에 대해:

1. 발생 시나리오 기술
2. 영업이익/마진에 미치는 영향 추정
3. DCF Bear 시나리오에 이미 반영되었는지 확인

**주요 리스크 카테고리:**

- 사업 리스크 (경쟁, 기술 변화, 규제)
- 재무 리스크 (부채, 증자, 운전자본)
- 경영진 리스크 (핵심인물, 지배구조)
- 매크로 리스크 (환율, 관세, 경기)

### ROE 평균회귀 모델링

`knowledge/경영진_지배구조.md`: "ROE 30% 이상: 지속 불가 의심"

자본 축적에 따른 ROE 하락 경로:

- 순이익 유보 시 1년 후 자본 = 현재 자본 + 순이익
- ROE = 순이익 / (현재 자본 + 순이익) → 자연 하락
- 몇 년 내에 30% 이하로 수렴하는지 추정

---

## Phase 7: 종합 판정

### 판정 기준

`knowledge/가치평가_본질.md` 참조.

| 조건 | 판정 |
| ------ | ------ |
| Bear IV > 현재가 | 보수적 기준에서도 싸 보이는 구간. 단, "확실히 싸다"가 아닌 "싸 보인다"로 표현 |
| Base IV > 현재가 > Bear IV | 적정~약간 저평가 가능성 |
| Bull IV > 현재가 > Base IV | 낙관 시나리오에서만 정당화되는 가격 |
| 현재가 > Bull IV | 합리적 낙관론마저 초과하는 가격 |

### 과신 점검 (Overconfidence Check)

결론을 내리기 전에 아래 질문을 반드시 자문할 것.

#### "왜 싼가?" / "왜 비싼가?"

시장에는 수많은 참여자가 있고, 현재 가격은 그들의 집합적 판단이다. 이 shallow dive가 공개 정보만으로 수행한 1차 분석에서 "시장이 틀렸다"는 결론이 쉽게 나온다면, 내가 모르는 것이 있을 가능성이 높다.

**과신 경고 신호:**

- Bear IV > 현재가 × 2 → "극도의 저평가"보다 "내가 핵심 리스크를 놓치고 있다"가 더 유력
- 현재가 > Bull IV × 2 → "극도의 고평가"보다 "내가 성장 동력을 과소평가하고 있다"가 더 유력
- PBR < 1인 수익성 기업 → 시장이 할인하는 구체적 이유를 설명할 수 없다면 판정 보류
- PBR > 20 → 시장이 프리미엄을 주는 구체적 이유를 설명할 수 없다면 판정 보류

**확신도 (반드시 명시):**

- **높음**: DCF와 시장가격의 괴리 원인을 구체적으로 설명할 수 있음
- **중간**: 괴리 원인의 방향은 알지만 규모를 추정하기 어려움
- **낮음**: 왜 이 가격인지 충분히 설명할 수 없음 → **Deep dive 필요** 명시

> 이 프레임워크는 shallow dive다. "이 가격이 적정한지"에 대한 최종 답이 아니라, "추가 분석이 필요한 종목인지"를 판별하는 1차 필터 역할이다.

### 프레임워크별 요약표

| 프레임워크 | 판정 |
| ----------- | ------ |
| 버핏 (해자) | |
| 피셔 (성장) | |
| 린치 (PEG) | |
| 프리미엄 | /45 |
| DCF | |
| PBR 역산 | |
| Comparable | |

### 최종 등급

| 항목 | 등급 (5점) |
| ------ | ----------- |
| 사업의 질 | |
| 가격의 매력 | |
| 정보의 확신 | |

### 2분 테스트 (Lynch)

> "10살짜리 아이에게 2분 이내에 주식을 보유한 이유를 설명할 수 없다면 그 주식을 소유해서는 안 된다."

한 문단으로 종합 판단을 기술:
"{회사}는 {사업 설명}. {핵심 강점}. {가격 판단}. {결론}."

---

## 출력 포맷

리포트를 `research/buffett/shallow-dive/{종목코드}_{회사명}.md`에 저장.

```markdown
# {회사명}({종목코드}) Shallow Dive — {날짜}

기준일: {날짜} | 데이터: {데이터 출처} | 주가: {현재가} ({날짜} KRX)

---

## 1. 회사 개요
## 2. 핵심 재무 지표
## 3. 경제적 해자 평가
## 4. Fisher 15 기준 + Lynch 분류
## 5. 프리미엄 9요인
## 6. DCF 밸류에이션
## 7. 민감도 분석
## 8. 교차검증
## 9. 리스크
## 10. 종합 판정
```
