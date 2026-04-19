# PYPL Tier 2 Verification -- Fisher Deep Dive Stream B 교차검증

기준일: 2026-04-19 | 소스: 웹 리서치 (Glassdoor, 앱 리뷰, 산업 리포트, 경쟁사 데이터, 뉴스)

이 문서는 Stream B "2층위 교차검증" 자료. 경영진 공언(1층위)을 제품/서비스 리뷰, 시장점유율, 직원 평가, 경쟁사 반응, 규제 자료로 방향 검증한다.

---

## 1. 제품/서비스 리뷰

### 1a. Fastlane Checkout

PayPal의 핵심 신제품. 게스트 checkout 가속으로 branded checkout 점유율 확대가 목표.

**PayPal 주장**:

- Fastlane 사용 게스트 -> 비사용 대비 전환율 +37% (2025-04~06 내부 데이터)
- 초기 테스트 가맹점에서 80%+ 전환율 (비사용 대비 +50%)
- 체크아웃 속도 +35% 개선

**독립 검증**:

- Black Forest Decor 사례: Fastlane 86% vs 일반 76% 완료율, 2분 vs 3.9분
- US only (해외 확장 2025 하반기 예정이었으나 현재 상태 미확인)
- BigCommerce, Adobe Commerce, Salesforce Commerce Cloud 통합 가능
- Fiserv 파트너십 통해 Clover POS 가맹점 접근

**불일치 지점**: Fastlane이 전환율을 크게 개선한다는 주장과, Q4 2025 branded checkout이 1% 성장에 그친 사실이 모순. 가능한 해석: (a) Fastlane 채택 규모가 아직 전체 branded checkout에 영향을 줄 만큼 크지 않음, (b) Fastlane 외 영역에서의 감소가 상쇄, (c) 주장된 전환율 개선이 선별적 데이터.

### 1b. Venmo

**사용자 메트릭**:

- MAU: 63M (2024), 72.9M 전망 (2025, +6.7%)
- 수익화 MAU: +24% (2024)
- Pay with Venmo: +50% (2025 초)
- 직불카드 TPV: +40%
- US P2P 시장 점유율: 81%

**Cash App 대비**:

- Venmo MAU 63-73M vs Cash App 57M
- Venmo 추정 수익 $1.7B vs Cash App $16.2B (Bitcoin 포함)
- Cash App은 Bitcoin 거래로 매출 팽창. 핵심 P2P/서비스 매출로 비교하면 격차 축소

**판정**: Venmo는 P2P에서 지배적이나, 수익화는 Cash App 대비 현저히 뒤처짐. PayPal이 Venmo 독립 수익률을 공시하지 않는 것은 수익성이 낮음을 시사.

### 1c. PYUSD (Stablecoin)

2023 출시. 공개 채택 데이터 제한적. DeFi 통합은 진행 중이나 USDC/USDT 대비 미미한 점유율. Chriss 해임 후 Lores 체제에서의 지속 여부 불확실.

---

## 2. 시장점유율 데이터

### 2a. 글로벌 온라인 결제

| 플레이어 | 글로벌 시장 점유율 | TPV (2025) |
|----------|------------------|-----------|
| PayPal | 43.4% | $1.92T |
| Stripe | 20.8-29% | $1.14T |
| 합산 | ~63.6% | |

### 2b. 결제관리 소프트웨어 (Payment Management Software)

| 플레이어 | 점유율 |
|----------|--------|
| Stripe | 34.8% |
| Braintree | 5.21% |

Stripe이 개발자 중심 결제 인프라에서 압도적. Braintree는 기존 대형 가맹점 기반이나 신규 채택에서 열세.

### 2c. Branded Checkout 추이

| 분기 | Branded Checkout 성장 |
|------|---------------------|
| Q2 2024 | 반등 시작 |
| Q3 2024 | Mid-single digits |
| Q4 2024 | ~6% |
| Q3 2025 | ~5% |
| **Q4 2025** | **1%** (급감) |

Q4 2025 급감 원인 (경영진 설명): US 리테일 약세, 해외(특히 독일) 역풍, 여행/티켓/크립토/게임 버티컬 둔화.

---

## 3. 직원/문화 검증

### 3a. Glassdoor 정량

| 지표 | 점수 | 해석 |
|------|------|------|
| 전체 평점 | 3.6/5.0 | 업계 평균 수준 (Stripe 추정 4.0+, Block 3.7) |
| Work-Life Balance | 3.7 | 양호 |
| Culture & Values | 3.5 | 보통 |
| Career Opportunities | **3.2** | **낮음** -- 가장 큰 불만 영역 |
| Compensation | ~3.5 | 보통 |
| 추천 의향 | 60% | 보통 |
| 12개월 추세 | **-3%** | 하락 중 |

### 3b. Glassdoor 정성 -- 핵심 테마

**부정**:

- "New leaders from McKinsey, Goldman have ruined the culture" -- Chriss의 외부 영입진에 대한 반발
- "Constant fear of job loss, poor morale, cut throat coworkers" -- 연속 감원의 심리적 영향
- "Alex Chriss is in way over his head" -- CEO 역량에 대한 직접적 불신 (해임 전 리뷰)
- "Only solution to growth is massive layoffs at least once annually"
- "Worst Company, Hire and Fire" -- 채용-해고 반복 패턴
- RTO 3+일/주 강제에 대한 불만

**긍정**:

- "Great brand to have on a resume"
- "Benefits are good and work atmosphere was wonderful" (과거형 사용 주목)
- "Great place to work since Alex's taken over" -- 일부 Chriss 지지자 존재

**양극화**: Chriss 지지자와 반대자가 극명히 나뉨. "No confidence in leadership" vs "Great place since Alex" -- 조직 내부가 분열.

### 3c. 인력 변화

| 시점 | 인원 | 이벤트 |
|------|------|--------|
| FY2022 | 29,900 | |
| 2023-01 | ~27,900 | Schulman: 2,000명 감원 (~7%) |
| FY2023 | ~26,800 | 자연 감소 |
| 2024-01 | ~24,400 | Chriss: 2,500명 감원 (~9%) |
| 2025 | ~23,000 (추정) | "Re-engineer technology infrastructure, optimize workforce" |

3년간 총 인력 감소: ~7,000명 (-23%). 연속 감원은 조직 내 심리적 안전감을 파괴.

### 3d. 경영진 이동 패턴

Chriss 취임 후:

- Intuit 출신 외부 영입 다수 (구체적 VP+ 이름 확인 필요)
- "Outsiders treated as threats" 패턴 -- Glassdoor 다수 리뷰에서 반복
- Chriss 해임으로 그의 영입진도 퇴진 가능성 -> 추가 조직 불안정

---

## 4. 경쟁사 시각

### 4a. Stripe

비상장이나 간접 지표:

- 2025 밸류에이션 $91.5B (2024 $50B에서 회복)
- TPV 2024에 40% 성장 (PayPal 전체 TPV 성장 ~5-7% 대비 압도적)
- 개발자 커뮤니티에서 PayPal/Braintree 대비 강한 선호

### 4b. Adyen

H2 2024/H1 2025 실적 콜에서 Braintree 직접 언급 확인 필요 (웹 접근 제한으로 미완).

### 4c. Block (Square/Cash App)

- Cash App MAU 57M vs Venmo 63-73M
- Cash App 매출 $16.2B >> Venmo $1.7B (Bitcoin 수익 포함)
- P2P에서는 Venmo 우세, 수익화에서는 Cash App 우세

### 4d. Apple Pay

- 모바일 결제 채택 가속
- PayPal branded checkout 1% 성장 급감의 주요 원인 중 하나로 추정
- 구체적 Apple Pay checkout 점유율 데이터 미확보

---

## 5. Elliott Management 타임라인

| 시점 | 이벤트 |
|------|--------|
| 2022-07 | Elliott, PayPal 지분 $2B 공시 |
| 2022-08 | PayPal: $15B 자사주 매입 승인, Elliott과 정보 공유 합의. Schulman: "substantially aligned" |
| 2022-08 ~ 2023-02 | "건설적 대화" 진행 |
| 2023-02 | Schulman "은퇴" 발표 + Jesse Cohn(Elliott) 이사회 옵저버 |
| 2023-06 | Jesse Cohn 정식 이사 선임 |
| 2023-08 | **Elliott, PayPal 지분 완전 퇴출** (SEC 공시) |
| 2023-09 | Alex Chriss CEO 취임 |

**핵심 관찰**: Elliott은 목적(CEO 교체) 달성 후 6개월 만에 완전 퇴출. 장기 가치 창출이 아닌 전형적 activist 단기 개입. 그러나 결과적으로 거버넌스 기능을 활성화시킨 긍정적 효과도 있음.

---

## 소싱 한계

- SEC Form 4 개별 거래 내역: 웹페이지 접근 제한으로 미완. openinsider.com/PYPL, fintel.io/sn/us/pypl에서 확인 필요
- Adyen 실적 콜 PayPal/Braintree 언급: 미확인
- Glassdoor CEO 승인율(Schulman vs Chriss 비교): 구체적 수치 미확보
- Blind 포스트: 직접 접근 불가
- LinkedIn VP+ 이동 패턴: 직접 검색 불가
