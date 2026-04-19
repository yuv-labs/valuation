# PayPal Holdings (PYPL) Deep Dive — Section 1-2

기준일: 2026-04-19 | 주가: $49.52 (2026-04-15) | Shallow Dive 기준가: $41.70 (2026-02-03)

> 이 문서는 [shallow dive](../../shallow-dive/PYPL_paypal.md)의 후속 심층 분석이다.
> Shallow dive에서 도출한 "버핏형 저평가 후보" 결론의 전제를 검증하고, 사업 구조를 상세히 분석한다.

---

## 용어 사전

| 약어 | 정의 |
| --- | --- |
| TPV | Total Payment Volume — 플랫폼을 통해 처리된 총 결제 금액 |
| TMD | Transaction Margin Dollars — 거래수익에서 거래비용(interchange 등)을 차감한 거래마진 금액 |
| Branded | 소비자가 PayPal/Venmo 버튼을 직접 클릭하여 결제하는 방식. 높은 take rate |
| Unbranded | Braintree 등을 통해 PayPal 로고 없이 백엔드 결제처리. 낮은 take rate |
| Braintree | PayPal의 unbranded 결제처리 플랫폼. 대형 가맹점 대상 |
| PPCP | PayPal Complete Payments — SMB(Small and Medium-sized Business, 중소기업)향 통합결제 솔루션 |
| BNPL | Buy Now Pay Later — 후불결제/분할결제 |
| P2P | Person-to-Person — 개인간 송금 (주로 Venmo) |
| Fastlane | PayPal의 게스트 체크아웃 가속 서비스. 비회원도 저장된 카드로 원클릭 결제 |
| Take rate | 수수료율 — 거래수익 / TPV. Gross = 총수수료, Net = 마진(TMD/TPV) |
| OVAS | Other Value-Added Services — 거래수수료 외 부가서비스 매출 (이자, FX, 구독료 등) |
| PSP | Payment Service Provider — 결제대행사 (Braintree의 산업 분류) |
| OE | Owner Earnings — 주주 귀속 현금이익 (CFO − SBC − CAPEX) |
| SBC | Stock-Based Compensation — 주식 기반 보상 |
| IC | Invested Capital — 투하자본 (총자산 − 유동부채 − 현금) |

> Flag key: [D] 공시, [E] 추정, [N/D] 미공시

---

## 1. 사업 분석

### 1-1. PayPal은 어떻게 돈을 버는가

PayPal의 매출을 두 가지 축으로 분해한다. 축1(제품 기준)이 사업 이해에 가장 직관적이고, 축2(공시 기준)가 SEC filing에서 확인 가능한 수치다.

#### 축1: 제품 기준 (비공식 — 사업 이해용)

```text
PayPal 총매출 ~$33.2B (FY2025)
│
├── Branded Checkout ·························· ~$13.2B [E¹]
│   소비자가 "Pay with PayPal" 버튼 클릭 → 가맹점이 수수료 지불
│   Gross take rate ~2.65%. 해자의 핵심, 최고 마진 제품
│   → 온라인 체크아웃 시장 점유율 44% [E]
│
├── Braintree (Unbranded PSP) ················· ~$10.9B [E²]
│   대형 가맹점 백엔드 결제처리 (소비자에게 PayPal 로고 안 보임)
│   Gross take rate ~1.75%. 볼륨 드라이버, 마진 희석 요인
│   → Stripe, Adyen과 직접 경쟁
│
├── Venmo ···································· ~$1.7B [D³]
│   P2P 송금(무료) + Pay with Venmo(가맹점 수수료)
│   + 직불카드(interchange) + Venmo Credit Card
│   → FY2025 +20% YoY. 2027년 $2B 목표 [D]
│
├── BNPL (Pay Later) ························· ~$1.5B [E⁴]
│   소비자 후불/분할결제. 가맹점 수수료 + 소비자 이자수익
│   TPV ~$40B+, +20% YoY [D]
│
├── PPCP (SMB 통합결제) ······················ 포함 [E]
│   Branded + Unbranded + BNPL + Venmo를 하나로 묶은 SMB 솔루션
│   → 단독 매출 미공시. 위 카테고리에 분산 포함
│
└── OVAS (부가서비스) ························ ~$3.4B [D⁵]
    고객 예치금 이자수익, FX 수수료, Instant Transfer 수수료,
    Working Capital 대출 이자, 구독/게이트웨이 수수료
    → FY2025 +14% YoY. 금리 환경에 민감
```

> **수치 소스:**
> ¹ 추정. FY2024 analyst model 기준 branded TPV ~$471B(Bob Hammel/Substack)에 FY2025 branded TPV +6% 성장(어닝콜 [D]) 적용 → ~$499B × gross take rate ~2.65% ≈ $13.2B. Take rate은 FY2024 ~2.68%에서 소폭 하락 가정.
> ² 추정. FY2024 Braintree TPV ~$572B에 ~2.5% 성장 적용 → ~$622B × ~1.75% ≈ $10.9B. Braintree 재가격책정(margin 개선, volume 둔화)으로 take rate 하락.
> ³ 공시. Q4 2025 어닝콜에서 Venmo revenue ~$1.7B, +20% YoY 확인.
> ⁴ 추정. BNPL TPV $40B+(공시) × ~3.5-4% take rate(merchant fee + consumer interest).
> ⁵ 공시. 10-K FY2025: Other value-added services revenue $3.37B.
>
> **검산**: $13.2 + $10.9 + $1.7 + $1.5 + $3.4 = $30.7B. 실제 총매출 $33.2B와의 차이 ~$2.5B는 (1) P2P 수수료(Instant Transfer 등), (2) Working Capital 대출수익, (3) 기타 가맹점 서비스에 분산. PayPal은 제품별 매출을 공시하지 않아 정확한 분리 불가.
>
> **핵심 인사이트**: Branded Checkout(~40% 매출)이 수익의 핵심이나, Braintree(~33%)가 볼륨으로는 최대. Braintree의 gross take rate(~1.75%)은 branded(~2.65%)의 66% 수준이지만, **net take rate** 기준으로는 branded ~2.25% vs Braintree ~0.30%(Mizuho 추정 [E])으로 **7.5배 차이**. 이 격차가 PayPal 밸류에이션의 핵심 변수.

#### 축2: 공시 기준 (SEC Filing)

PayPal은 **단일 운영 세그먼트**로 보고하며 [D], 매출을 2개 라인으로만 분해한다.

| 매출 라인 | FY2020 | FY2021 | FY2022 | FY2023 | FY2024 | FY2025 | 소스 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Transaction revenues | $17.5B | $21.8B | $24.3B | $26.9B | $28.8B | $29.8B | 10-K [D] |
| Other VAS | $3.9B | $3.6B | $3.2B | $2.9B | $3.0B | $3.4B | 10-K [D] |
| **Total** | **$21.5B** | **$25.4B** | **$27.5B** | **$29.8B** | **$31.8B** | **$33.2B** | 10-K [D] |
| Transaction Rev % | 81.7% | 85.7% | 88.4% | 90.2% | 90.7% | 89.8% | |
| Total YoY | — | +18.1% | +8.5% | +8.2% | +6.8% | +4.3% | |

> 수치 소스: FY2023-2025는 10-K FY2025 (filed 2026-02-03) [D]. FY2020-2022는 각 연도 10-K [D]. OVAS 감소(FY2020-2023)는 저금리기 이자수익 감소, FY2024-2025 반등은 금리 상승 + 신용상품 확대.

#### TPV 및 운영 지표 (공시)

| 지표 | FY2020 | FY2021 | FY2022 | FY2023 | FY2024 | FY2025 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Total TPV ($T) | $0.94 | $1.25 | $1.36 | $1.53 | $1.68 | $1.79 |
| TPV YoY | — | +33% | +9% | +13% | +10% | +7% |
| 결제 건수 (B) | 15.4 | 19.3 | 22.3 | 25.0 | 26.3 | 25.4 |
| 활성 계정 (M) | 377 | 426 | 435 | 426 | 434 | 439 |
| 계정당 결제 건수 | 40.9 | 45.4 | 51.4 | 58.7 | 60.6 | 57.7 |
| Gross take rate (bps) | 229 | 203 | 202 | 195 | 188 | 186 |

> 수치 소스: 10-K 각 연도 [D]. Gross take rate = Transaction revenue / TPV.
>
> 주: FY2025 결제 건수 감소(-4%)는 저마진 unbranded PSP 건수를 의도적으로 축소한 결과. Unbranded 제외 시 +6% 성장(16.1B건) [D]. 활성 계정은 Chriss 체제에서 deemphasize — 대신 Monthly Active Accounts(MAA, 231M Q4 2025 [D])를 강조.

#### 지역별 매출 (FY2025)

| 지역 | 매출 | 비중 |
| --- | ---: | ---: |
| 미국 | ~$18.9B | ~57% [E] |
| 해외 | ~$14.3B | ~43% [E] |

> 수치 소스: 10-K [D] 기반 비중 추정. 정확한 금액은 10-K Note에서 확인 필요.

---

### 1-2. 분기별 추적 가능 지표

| 지표 | 공시 여부 | 시작 | 추적 방법 |
| --- | --- | --- | --- |
| **Transaction revenue** | 공시 | 수년 | 10-Q |
| **OVAS revenue** | 공시 | 수년 | 10-Q |
| **Total TPV** | 공시 | 수년 | 10-Q / earnings release |
| **TMD (Transaction Margin Dollars)** | 공시 | FY2024~ | Earnings release (Chriss 핵심 KPI) |
| **Operating margin** | 공시 | 수년 | 10-Q |
| **Active accounts** | 공시 | 수년 | 10-Q (de-emphasized) |
| **Payment transactions** | 공시 | 수년 | 10-Q |
| **Share count** | 공시 | 수년 | 10-Q |
| Branded checkout TPV | **미공시** | — | 어닝콜에서 성장률만 언급. 총 TPV와 take rate로 역산 |
| Braintree revenue | **미공시** | — | 추정만 가능 |
| Venmo revenue | **일부 공시** | FY2024~ | 어닝콜에서 연간 수치 + 성장률 코멘트 |
| Fastlane 채택 지표 | **미공시** | — | 어닝콜 정성 코멘트만 |
| Net take rate by product | **미공시** | — | Sell-side 추정치 참조 |

> **축1 제품별 추적 방법:**
>
> - Branded checkout: 어닝콜에서 "branded checkout TPV +X%" 코멘트 [D] + 총 TPV / blended take rate로 역산 [E]
> - Braintree: 어닝콜에서 성장률 정성 코멘트 [D] (예: "roughly flat", "mid-single-digit growth"). 정확한 매출 미공시
> - Venmo: FY2024부터 연 revenue 수준과 성장률을 어닝콜에서 공시 [D]
> - TMD: FY2024부터 Chriss가 핵심 KPI로 제시. 분기별 금액 + YoY 공시 [D]. Branded/unbranded 분리는 미공시

---

### 1-3. 분기별 실적 추이

#### 축2 기준: 공시 (10-Q / Earnings Release)

| 분기 | Net Revenue (YoY) | Txn Revenue [D] | OVAS [D] | TPV ($B, YoY) | TMD (YoY) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Q1 FY2024 | $7.70B (+9%) | — | — | $403.9B (+14%) | $3.55B (+4%) |
| Q2 FY2024 | $7.89B (+8%) | — | — | $416.8B (+11%) | $3.61B (+8%) |
| Q3 FY2024 | $7.85B (+6%) | — | — | $422.6B (+9%) | $3.65B (+6%) |
| Q4 FY2024 | $8.37B (+4%) | — | — | $437.8B (+7%) | $3.94B (+9%) |
| Q1 FY2025 | $7.79B (+1%) | ~$7.0B [E] | ~$0.79B [E] | $417.2B (+3%) | $3.72B (+7%) |
| Q2 FY2025 | $8.30B (+5%) | ~$7.5B [E] | ~$0.80B [E] | $443.5B (+6%) | ~$3.5B ex-int (+8%) |
| Q3 FY2025 | $8.42B (+7%) | $7.52B [D] | ~$0.90B [E] | $458.1B (+8%) | ~$3.8B [E] (+7%) |
| Q4 FY2025 | $8.68B (+4%) | ~$7.8B [E] | $0.86B [D] | $475.1B (+9%) | $4.0B (+3%) |

> 수치 소스: Revenue, TPV는 earnings release [D]. TMD는 earnings release [D]. 분기별 Txn/OVAS 분리는 일부 분기만 공시, 나머지 추정 [E].
> Q1 FY2025 매출 YoY +1%는 역대 최저 — Braintree 재가격책정 + 저마진 볼륨 축소 영향. 이후 회복 추세.

#### 핵심 운영 지표 (공시)

| 분기 | Active Accts (M) | Payment Txns (B) | Txns/Acct (TTM) | Gross Take Rate (bps) |
| --- | ---: | ---: | ---: | ---: |
| Q1 FY2024 | 427 | 6.5 | 59.1 | 191 |
| Q2 FY2024 | 429 | 6.6 | 60.4 | 189 |
| Q3 FY2024 | 432 | 6.6 | 60.9 | 186 |
| Q4 FY2024 | 434 | 6.6 | 60.6 | 191 |
| Q1 FY2025 | 436 | 6.0 | 57.7 | 187 |
| Q2 FY2025 | 438 | 6.2 | — | 187 |
| Q3 FY2025 | 438 | 6.3 | — | 184 |
| Q4 FY2025 | 439 | 6.8 | 57.7 | 183 |

> 수치 소스: 10-Q / earnings release [D]. Gross take rate = Transaction revenue / TPV. FY2025 Txns 감소는 PSP 볼륨 축소 때문 — ex-PSP 기준 +6% 성장 [D].

#### 축1 기준: 제품별 분기 (추정)

축1 추정치는 정확도가 낮다. PayPal이 제품별 매출을 공시하지 않으므로, 아래는 어닝콜 코멘트 + take rate 역산으로 구성한 방향성 참고용 추정이다.

| 분기 | Branded Rev [E] | Braintree Rev [E] | Venmo Rev [E] | OVAS [D/E] |
| --- | ---: | ---: | ---: | ---: |
| Q1 FY2025 | ~$3.1B | ~$2.7B | ~$0.4B | ~$0.79B |
| Q2 FY2025 | ~$3.3B | ~$2.7B | ~$0.4B | ~$0.80B |
| Q3 FY2025 | ~$3.4B | ~$2.8B | ~$0.44B | ~$0.90B |
| Q4 FY2025 | ~$3.4B | ~$2.7B | ~$0.46B | ~$0.86B |

> 추정 근거: 어닝콜 성장률 코멘트(branded +6%, Braintree flat→mid-single, Venmo +20%) + FY2024 analyst baseline(Bob Hammel model). 분기 합계와 실제 매출의 차이는 BNPL, P2P 수수료, Working Capital 등 미배분 항목.

---

## 2. 경쟁우위 + 산업구조

### 2-1. 스크리닝 시그널 → 해자 원인 매핑

Gold 패널 기준(screening panel.py: ROIC = EBIT × 0.75 / IC, IC = 총자산 − 유동부채 − 현금):

| 시그널 | PYPL 수치 | 기준 | 해자 종류 추정 |
| --- | --- | --- | --- |
| ROIC 17.7% > 7% | ✓ (FY2025) | 해자 존재 | 네트워크 효과 + 규모의 경제 |
| ROIC 3y avg 16.0% > 7% | ✓ | 해자 공고 | 3년간 자본비용의 2배+ |
| ROIC trend: rising | ✓ (9.1% → 17.7%, 5yr) | 해자 강화 (또는 구조조정) | 마진 중심 전환 효과 |
| FCF/NI 1.06 > 0.8 | ✓ (FY2025) | 이익의 질 | NI보다 현금이 더 나옴 |
| CAPEX/Revenue 2.6% | ✓ (FY2025) | 자본경량 | 디지털 플랫폼 특성 |
| 주식수 5yr -18.4% | ✓ | 현금환원 | 공격적 buyback 가속 |

> 수치 소스: data/gold/out/valuation_panel.parquet 직접 계산. screening panel.py의 ROIC 공식 적용.

**외부 소스 교차검증:**

| 지표 | 내부 값 | 외부 소스 | 일치 여부 |
| --- | --- | --- | --- |
| Revenue FY2025 | $33.17B | MacroTrends $33.17B | ✓ 일치 |
| ROIC FY2025 | 17.7% | 정의 차이 예상 | ⚠️ IC 정의에 따라 변동 |
| FCF FY2025 | $5.56B | Earnings release "Adjusted FCF $6.4B" [D] | ⚠️ PayPal의 adjusted FCF는 SBC 제외 정의 |
| Shares FY2025 | 968M | 10-K [D] 968M | ✓ 일치 |

> ROIC 차이 원인: 외부 소스마다 IC 정의가 다름 (자기자본+장기부채 vs 총자산−CL−현금 등). 방향(10%+ 초과수익)은 동일. PayPal의 adjusted FCF($6.4B)와 내부 FCF($5.56B)의 차이($0.84B)는 SBC를 원가에서 제외하는 PayPal의 adjusted 정의 때문.

**GP margin이 ~47%인 이유 — 구조적 차이:**

PayPal의 transaction margin(TMD/Revenue ≈ 47%)은 SaaS 기업(80-90%)보다 훨씬 낮다. 이는 해자 약점이 아니라 **사업 모델의 구조적 특성**:

- PayPal의 "매출원가" = Transaction expense(카드 네트워크 interchange 수수료, 은행 수수료, fraud 손실 등)
- 전체 매출의 ~53%가 Visa/Mastercard/은행에 지급하는 통과 비용
- 이 구조는 결제 프로세서 전체에 공통 — Stripe, Adyen도 동일

따라서 PayPal의 해자 강도는 GP margin이 아닌 **(1) take rate 안정성, (2) TMD 성장률, (3) branded/unbranded 마진 격차 유지**로 판단해야 한다.

---

### 2-2. 해자 분석

#### 해자 1: 양면 네트워크 효과 (Two-Sided Network)

PayPal의 가장 중요한 해자. ROIC 17.7%의 근본 원인.

**메커니즘:**

- **4.39억 소비자 계정** + **3,600만+ 가맹점** → 양면 네트워크
- Cross-side: 소비자가 많을수록 가맹점이 PayPal을 채택할 인센티브 ↑ → 더 많은 결제 옵션 → 소비자 유틸리티 ↑
- Same-side (Venmo): P2P에서 사용자가 많을수록 송금 유틸리티 ↑ (Venmo MAA 67M [D])
- 글로벌 200+ 시장, 100+ 통화 지원 → cross-border 결제에서 특히 강력

**정량 증거:**

- TPV $1.79T — 규모 자체가 진입장벽. 이 볼륨을 처리하는 fraud 모델, 리스크 데이터, 가맹점 관계를 새로 구축하는 비용이 막대
- 활성 계정 439M — 감소 추세 아님(+1.1% YoY FY2025). Monthly Active 231M [D]
- 온라인 체크아웃 시장 점유율 ~44% [E] (Capital One Shopping, 2025 기준)
- Branded checkout에서 guest checkout 대비 conversion rate +50% 프리미엄 (Fastlane 데이터 [D])

**취약점:**

- **네트워크가 비배타적** — 소비자는 PayPal, Apple Pay, 카드를 동시에 사용. 결제수단 복수 보유가 기본
- **가맹점 leverage** — 대형 가맹점은 Braintree vs Stripe vs Adyen을 경쟁 입찰시킬 수 있음
- 활성 계정 성장 정체 (+1.1% FY2025) — 성숙 시장 신호

#### 해자 2: 전환비용 (가맹점 측)

**메커니즘:**

- API 통합: 가맹점 체크아웃 플로우에 PayPal/Braintree API가 깊이 연동. 교체 시 개발 비용 + 테스트 + 다운타임 리스크
- Fraud 데이터: 가맹점별 거래 이력으로 학습된 리스크 모델. 새 프로세서로 전환 시 fraud 학습 기간 필요
- 멀티 프로덕트 통합: checkout + BNPL + Venmo + fraud tools + Working Capital을 하나의 가맹점 관계에서 제공
- PPCP(SMB 통합): 결제 게이트웨이 + 처리 + 다양한 결제수단을 원스톱 제공 → SMB의 전환비용 높음

**정량 증거:**

- 가맹점 이탈률 낮음 (어닝콜 정성 코멘트 [D], 정확한 수치 미공시 [N/D])
- 가맹점당 활용 제품 수 증가 추세 (PPCP 채택 확대 [D])
- ex-PSP payment transactions +6% 성장 [D] — 기존 가맹점의 거래 증가

**취약점:**

- **소비자 측 전환비용은 낮음** — 월렛 추가/삭제가 매우 쉬움. PayPal 계정 삭제 = 클릭 몇 번
- **대형 가맹점은 멀티 프로세서** — Braintree + Adyen을 동시에 사용하는 대형 가맹점 다수. 전환이 아니라 분산

#### 해자 3: 브랜드 신뢰 (소비자 측)

**메커니즘:**

- "PayPal" = 온라인 결제 신뢰의 대명사. 25년 역사(2000~)
- **구매자 보호(Buyer Protection)**: 제품 미수령, 불일치 시 환불 보장 → 소비자가 낯선 사이트에서도 안심하고 결제
- Cross-border 거래에서 특히 강력: 해외 판매자를 신뢰할 수 없을 때 PayPal이 중개자 역할

**정량 증거:**

- Branded checkout이 unbranded 대비 7.5배 높은 net take rate 유지 가능한 이유 = 브랜드 프리미엄
- 미국 소비자 42%가 PayPal 사용(U.S. 1위 디지털 월렛 [E])
- PayPal 버튼이 있으면 checkout conversion rate 상승 (가맹점 입장에서 브랜드 가치)

**취약점:**

- 결제는 "아무거나 되면 OK" 특성 — 크리에이티브 도구와 달리 결제수단에 대한 감정적 로열티가 낮음
- 젊은 세대: Venmo는 사용하지만 "PayPal"은 부모 세대 브랜드로 인식하는 경향
- DOJ 합의($150M, 2024) — "해지 어렵게 만들었다"는 이미지 → 브랜드 신뢰 일부 훼손

---

### 2-3. 산업 구조: 세그먼트별 경쟁 지형

#### Online Branded Checkout (~$13.2B, 추정)

| 영역 | PayPal | 경쟁자 | 위협 |
| --- | --- | --- | --- |
| 체크아웃 버튼 | PayPal (1위, ~44% share [E]) | Apple Pay (~14%), Google Pay, Shop Pay (Shopify) | **높음** |
| Cross-border 결제 | PayPal (1위) | Wise, 현지 월렛 | 중간 |
| 게스트 checkout 가속 | Fastlane (~2,600 가맹점, U.S.) | Shop Pay, Amazon Pay | 중간 (초기) |
| Buyer protection | PayPal (차별화) | 카드사 chargeback | 낮음 |

> Apple Pay: 글로벌 ~8.18억 사용자, 온라인 체크아웃 14%, 인스토어 모바일월렛 54% [E]. 기기 레벨 우위(iPhone에 사전 탑재)가 구조적 강점. 다만 가맹점 채택률은 PayPal보다 낮음.

#### Unbranded Payment Processing — Braintree (~$10.9B, 추정)

| 영역 | Braintree | 경쟁자 | 위협 |
| --- | --- | --- | --- |
| Enterprise 결제처리 | Top 3 | **Stripe** (1위, 개발자 경험), **Adyen** (옴니채널) | **높음** |
| Developer experience | 보통 | Stripe (best-in-class 문서·API) | 높음 |
| 옴니채널 (온+오프라인) | 제한적 | Adyen (best-in-class) | 중간 |
| 가격경쟁력 | Braintree 재가격책정 중 | Stripe/Adyen도 enterprise 할인 | 높음 |

> Braintree 전략 전환: FY2024 이후 저마진 대형 고객 계약을 재가격책정. 볼륨 성장률은 double-digit → roughly flat으로 급감했으나, transaction margin은 +120bps 개선 [D]. "Value over volume" 전략.

#### P2P / Consumer Finance — Venmo (~$1.7B, 공시)

| 영역 | Venmo | 경쟁자 | 위협 |
| --- | --- | --- | --- |
| P2P 송금 | Venmo (밀레니얼/Z세대 1위) | **Zelle** (bank-embedded, 볼륨 1위), Cash App | 중간 |
| P2P → Commerce | Pay with Venmo (+45% YoY [D]) | Cash App, Apple Pay | 중간 |
| 직불카드 | Venmo Debit (MAU +40% QoQ [D]) | Cash App Card | 중간 |
| BNPL | PayPal Pay Later ($40B+ TPV) | Affirm, Klarna, Apple Pay Later (중단) | 중간 |

> Venmo 핵심: P2P 송금 자체는 무료(수익 0)이나, Pay with Venmo(가맹점 수수료), Venmo Debit Card(interchange), Venmo Credit Card(이자)를 통해 수익화. FY2025 revenue ~$1.7B [D], 2027 $2B 목표 [D]. Zelle는 볼륨에서 Venmo를 초과하지만 은행이 운영하므로 별도 수익화 모델 없음.

#### SMB 통합결제 — PPCP

| 영역 | PPCP | 경쟁자 | 위협 |
| --- | --- | --- | --- |
| SMB 올인원 결제 | PPCP (초기) | **Square** (POS 1위), Stripe, Shopify Payments | **높음** |

> PPCP는 Branded + Unbranded + BNPL + Venmo를 하나로 묶어 SMB에 제공하는 솔루션. Chriss의 Intuit(SMB) 경험이 반영된 전략 제품이나, 아직 단독 실적이 공시되지 않아 규모 파악 불가.

#### 경쟁자 규모 비교

| 기업 | 매출/Net Rev | TPV/Processed Vol | 성장률 | 시총/밸류에이션 | PayPal과의 관계 |
| --- | ---: | ---: | ---: | ---: | --- |
| **PayPal** | $33.2B gross | $1.79T | +4% rev | $48B | — |
| **Stripe** | $6.9B net [D] | $1.9T [D] | +36% net rev | $159B [D] | Braintree 직접 경쟁 |
| **Adyen** | EUR 2.4B net [D] | EUR 1.4T [D] | +18% net rev | ~EUR 50B | Braintree enterprise 경쟁 |
| **Block** | ~$24B gross | $210B Square GPV | +17% GP | ~$30B | Venmo + SMB 경쟁 |
| **Visa** | ~$36B | $15T+ volume | +10% | ~$650B | 네트워크 레이어 (파트너 + 잠재 위협) |

> 수치 소스: Stripe 2025 Annual Letter [D], Adyen H2 2025 Results [D], Block Q3-Q4 2025 Earnings [D].
>
> **Take rate 비교** (net 기준): PayPal blended ~0.87% (TMD/TPV), Stripe ~0.36%, Adyen ~0.17%. PayPal이 가장 높은 이유 = branded checkout(고마진) 비중. Stripe/Adyen은 unbranded만 처리.
>
> **밸류에이션 역설**: PayPal($33.2B 매출, $48B 시총) vs Stripe($6.9B net rev, $159B 밸류에이션). Stripe의 +36% 성장률이 3.3배 시총 프리미엄을 정당화하는가는 Deep Section 6(밸류에이션)에서 검토.

---

### 2-4. 해자 Proxy 지표 — 실측

| Proxy 지표 | FY2023 | FY2024 | FY2025 | 3년 추이 | 의미 |
| --- | ---: | ---: | ---: | --- | --- |
| **ROIC** | 15.3% | 15.0% | 17.7% | → ↑ | 자본비용(~10%) 초과. FY2022 11.1%에서 회복+상승 |
| **FCF/NI** | 0.99 | 1.63 | 1.06 | 변동 | FY2024 이상치(CFO 급증). 평균 ~1.2. 이익보다 현금이 더 나옴 |
| **CAPEX/Revenue** | 2.1% | 2.1% | 2.6% | 안정 | 매출의 2-3% 재투자. 디지털 플랫폼 특성 |
| **Transaction margin rate** | 46.3% | 46.1% | 46.7% | 안정 | TMD/Revenue. 교차확인: $15.5B/$33.2B ≈ 46.7% |
| **Op margin** | 16.9% | 16.7% | 18.3% | → ↑ | Chriss 체제 마진 확대. FY2022 저점(13.9%)에서 +440bps |
| **주식수** | 1,107M | 1,039M | 968M | ↓↓ | 3년 -12.6%. YoY -6.8%(FY2025). Buyback 가속 |
| **Gross take rate (bps)** | 195 | 188 | 186 | ↓ | Braintree 볼륨 믹스 변화. Branded 자체는 안정 |
| **Net take rate (TMD/TPV)** | — | 87.5 bps | 86.6 bps | ~안정 | 마진 기준 take rate. Gross보다 의미 있는 지표 |
| **TMD growth** | — | +7% | +6% | — | 핵심 수익성 지표. 매출(+4%) 대비 빠른 성장 |

> 수치 소스: valuation_panel.parquet 직접 계산 + earnings release [D].
>
> **ROIC 상승이 구조적인가?** FY2020 9.1% → FY2025 17.7% 상승의 주요 원인:
> (1) EBIT margin 확대: 15.3% → 18.3% (+300bps) — 비용 구조조정(2023 감원 2,500명) + Braintree 재가격책정
> (2) IC 효율화: IC가 $27.1B(FY2020) → $25.7B(FY2025)로 오히려 감소 — 자산 효율 개선
> 구조조정 일회성 효과(FY2023-24)와 지속적 효율화(Braintree 재가격책정, 비용 규율)가 섞여 있어, ROIC가 17-18% 수준에서 안정화될지 추가 상승할지는 Section 6에서 시나리오별 검토 필요.

---

### 2-5. 해자 위협 vs 방어

**위협:**

| 위협 | 영향받는 해자 | 심각도 | 시간축 |
| --- | --- | :---: | --- |
| Apple Pay/Google Pay의 checkout 대체 | 브랜드 + 네트워크 (소비자 측) | ★★★★☆ | 진행 중 |
| Stripe/Adyen의 enterprise 경쟁 | 전환비용 (가맹점 측) | ★★★☆☆ | 진행 중 |
| 결제처리 상품화 (commoditization) | 전환비용 전반 | ★★★☆☆ | 점진적 |
| Zelle/FedNow의 P2P 대체 | 네트워크 (Venmo) | ★★☆☆☆ | 느림 |
| 규제 (CFPB on BNPL, interchange 규제) | 가격결정력 | ★★☆☆☆ | 불확실 |

**방어:**

| 방어 | 보호하는 해자 | 강도 |
| --- | --- | :---: |
| 4.39억 계정 + 3,600만 가맹점 installed base | 네트워크 효과 | ★★★★★ |
| Branded checkout conversion premium (+50%) | 브랜드 신뢰 | ★★★★☆ |
| Buyer Protection 보증 | 브랜드 신뢰 | ★★★★☆ |
| Cross-border 네트워크 (200+ 시장, 100+ 통화) | 네트워크 효과 | ★★★★☆ |
| 멀티 프로덕트 통합 (checkout + BNPL + Venmo + fraud) | 전환비용 | ★★★☆☆ |
| Fastlane (게스트 checkout 가속) | 네트워크 확장 | ★★★☆☆ |

---

### 2-6. 경쟁우위 종합

PayPal의 해자는 **양면 네트워크(4.39억 소비자 / 3,600만 가맹점) + 브랜드 신뢰(25년, Buyer Protection)**에 기반한다. 가맹점 측 전환비용도 존재하나, 소비자 측 전환비용은 낮다(월렛 복수 사용이 기본).

모든 proxy 지표가 **"해자가 건재하고, FY2022 저점 이후 회복·강화 중"**을 가리킨다. 다만 이 강화가 구조적 개선인지, 일회성 구조조정 효과인지 분리가 필요하다.

**"Figma 사례" 분석 — Apple Pay는 PayPal에게 Figma인가?**

Figma는 UI/UX 디자인이라는 Adobe 왕국의 한 성벽을 무너뜨렸다(XD 13.5% → Figma 40.6%). Apple Pay가 branded checkout에서 동일한 패턴을 반복하는가?

| 비교 축 | Figma vs Adobe XD | Apple Pay vs PayPal |
| --- | --- | --- |
| 전문 서비스가 범용 플랫폼의 한 영역을 대체 | ✓ (협업 UI/UX에 특화) | ✓ (기기 내장 결제에 특화) |
| 현재 점유율 반전 | ✓ (이미 역전) | ✗ (PayPal 44% vs Apple Pay 14%) |
| 구조적 우위 | 브라우저 기반 실시간 협업 | 기기 레벨 통합 (Face ID + 탭) |
| 대체 범위 | UI/UX 영역만 (이미지/영상/레이아웃은 Adobe 유지) | 체크아웃 영역 (PSP/BNPL/P2P는 영향 제한적) |
| PayPal의 방어 | — | Fastlane, Buyer Protection, cross-border |

**판단**: Apple Pay는 PayPal에게 **"진행 중인 Figma"이나, 아직 초기 단계**. Figma가 Adobe XD를 역전하는 데 ~5년 걸렸고, Apple Pay의 온라인 checkout 점유율(14%)은 아직 PayPal(44%)에 크게 미달. 다만 Apple Pay는 iPhone 생태계라는 구조적 유통망이 있어, 가맹점 채택이 가속되면 faster displacement가 가능. **Branded checkout TPV 성장률(현재 +6% YoY)**이 둔화→역성장으로 전환되면 "Figma moment" 시그널.

**핵심 불확실성 2가지:**

**불확실성 1 — ROIC 개선이 구조적인가?**
FY2020 9.1% → FY2025 17.7%. 이 중 얼마가 (a) Braintree 재가격책정(지속 가능), (b) 비용 구조조정 일회성(fade out), (c) 금리 환경(OVAS 이자수익, 외생변수)인지 분리 필요. FY2026-27에 ROIC가 17-18%에서 안정되면 구조적, 15% 이하로 회귀하면 일시적.

**불확실성 2 — Branded checkout 점유율 방향**
PayPal의 bull/bear를 가르는 핵심 변수. Branded checkout은 PayPal의 최고 마진 제품이자 해자의 물리적 표현이다. 이 점유율이 안정(Fastlane 효과)이면 해자 건재, 하락(Apple Pay 침식)이면 해자 약화. 현재 데이터: branded checkout TPV +6% YoY(FY2025 [D]) — 둔화 추세이나 아직 양성장. 이 성장률이 0% 이하로 전환되면 Bear 시나리오 확률 대폭 상향.

---
