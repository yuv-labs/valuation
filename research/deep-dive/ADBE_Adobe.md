# Adobe Inc.(ADBE) Deep Dive — 2026-04-12

기준일: 2026-04-10 | 주가: $225.35 (NASDAQ)

> 이 문서는 [shallow dive](../shallow-dive/ADBE_Adobe_shallow_dive.md)의 후속 심층 분석이다.
> Shallow dive에서 도출한 "저평가" 결론의 전제를 검증하고, 사업 구조를 상세히 분석한다.

---

## 용어 사전

| 약어 | 정의 |
|------|------|
| CC | Creative Cloud — Photoshop, Illustrator 등 크리에이티브 앱 구독 |
| DC | Document Cloud — Acrobat, Acrobat Sign 등 문서 솔루션 |
| EC | Experience Cloud — AEM, CDP, Analytics 등 엔터프라이즈 마케팅 플랫폼 |
| C&M | Creative & Marketing Professionals — 전문가 고객 그룹 (CC + EC) |
| BPC | Business Professionals & Consumers — 비전문가 고객 그룹 (Acrobat + Express) |
| DM | Digital Media — 구 세그먼트 (CC + DC). FY2025까지 공시, 이후 중단 |
| DX | Digital Experience — 구 세그먼트 (EC). FY2025까지 공시, 이후 C&M에 통합 |
| ARR | Annualized Recurring Revenue — 연환산 반복 매출 |
| RPO | Remaining Performance Obligations — 미이행 계약 잔액 |
| SBC | Stock-Based Compensation — 주식 기반 보상 |
| OE | Owner Earnings — 주주 귀속 현금이익 (CFO − CAPEX) |
| FCF | Free Cash Flow — 잉여현금흐름 (CFO − CAPEX). OE와 동일 |
| ROIC | Return on Invested Capital — 투하자본수익률 |
| GP margin | Gross Profit margin — 매출총이익률 |
| IC | Invested Capital — 투하자본 (총자산 − 유동부채 − 현금) |
| ARPU | Average Revenue Per User — 유저 1명당 평균 매출 |
| Goodwill | 영업권 — 기업 인수 시 순자산보다 비싸게 산 프리미엄. 인수 사업 부진 시 감손 리스크 |

---

## 1. 사업 분석

### 1-1. Adobe는 어떻게 돈을 버는가

Adobe의 매출을 두 가지 축으로 분해한다. 축1(제품 기준)이 사업 이해에 가장 직관적이고, 축2(고객 그룹)가 현재 공시 기준이다.

#### 축1: 제품 기준 (비공식 — 사업 이해용)

```text
Adobe 총매출 ~$25.6B (Q1 FY2026 연환산)
│
├── 크리에이티브 프로 도구 ············· ~$11.4B (추정¹)
│   Photoshop, Illustrator, InDesign, Premiere Pro,
│   After Effects, Lightroom, Substance 3D, XD 등
│   → 전문 디자이너/영상편집자/사진작가의 핵심 워크플로우
│
├── 문서 + 생산성 ····················· ~$7.1B (공시: BPC 구독매출 연환산²)
│   Acrobat (Reader/Standard/Pro), Acrobat Sign,
│   Acrobat AI Assistant, Acrobat Studio, Adobe Express,
│   Firefly credits (BPC 내)
│   → 지식노동자/일반 소비자의 문서·콘텐츠 생산성
│
├── 엔터프라이즈 마케팅 플랫폼 ········ ~$6.1B (추정³)
│   AEM, Real-Time CDP, Analytics, Target, Campaign,
│   Journey Optimizer, GenStudio
│   → 대기업 마케팅/CX 부서의 디지털 경험 관리
│
└── 기타 ······························ ~$0.9B
    제품 라이선스, 컨설팅/교육, OEM 등
```

> **수치 소스:**
> ¹ 추정. C&M 구독매출($4,389M/Q, 공시) − EC 구독매출(~$1,540M/Q, 추정) = ~$2,849M/Q → 연환산 ~$11.4B. EC 구독매출은 FY2025 Q4 Digital Experience 구독매출 $1,413M(공시)에서 Q1 FY2026 ~9% YoY 성장 가정.
> ² 공시. Q1 FY2026 BPC 구독매출 $1,782M × 4 = $7.1B. (실제 연간은 분기별 성장 반영 시 상이할 수 있음.)
> ³ 추정. FY2025까지 Digital Experience 세그먼트로 별도 공시($5.86B, +9% YoY). Q1 FY2026부터 C&M에 통합되어 공시 중단. ~9% 성장 가정 → 연환산 ~$6.1B.
>
> 주의: 이 분해는 사업을 이해하기 위한 추정이며, 정확한 제품별 매출이 아님. Adobe는 10-K에서 cross-product integration으로 인해 정확한 제품별 매출 분리가 불가능하다고 공시.

#### 축2: 고객 그룹 (공식 공시 기준, Q1 FY2025~)

Q1 FY2026부터 Adobe는 단일 운영 세그먼트로 통합하고, 구독매출을 고객 그룹별로 공시한다.

| 고객 그룹 | 정의 | Q1 FY2026 구독매출 | YoY | 포함 제품 |
|-----------|------|-------------------|-----|-----------|
| **C&M** (Creative & Marketing Professionals) | 전문 크리에이터 + 마케터 | $4,389M (공시) | +12% | CC 프로 앱 전체 + Experience Cloud 전체 |
| **BPC** (Business Professionals & Consumers) | 지식노동자 + 일반 소비자 | $1,782M (공시) | +16% | Acrobat 제품군 + Adobe Express + Firefly credits |
| 기타 | OEM 등 | $27M (공시) | — | |
| **구독 소계** | | **$6,198M** (공시) | +13% | |
| 제품 + 서비스 | | $200M (공시) | | 라이선스, 컨설팅 |
| **총매출** | | **$6,398M** (공시) | +12% | |

**BPC의 정의:**
Adobe 10-K 원문: "직관적이고 올인원인 솔루션으로 웹/모바일에서 생산성과 창의성을 통합하려는 사용자." 핵심은 **비전문가** — 디자이너가 아니라 회사원, 영업사원, 학생, 일반인이 PDF 읽고, 서명하고, 간단한 디자인 만드는 영역. Acrobat Studio는 Acrobat + Express를 통합한 "AI 문서 허브"로, BPC의 성장 엔진.

**C&M에 Experience Cloud가 묶인 이유:**
Experience Cloud(AEM, CDP, GenStudio 등)의 실제 사용자가 기업 마케팅 부서의 **전문가**이기 때문. CC 프로 사용자와 같은 고객층이라는 논리. 다만 이 묶음으로 인해 Q1 FY2026부터 EC 단독 매출/성장률을 외부에서 직접 확인하기 어려워짐.

### 1-2. 분기별 추적 가능 지표

| 지표 | 공시 여부 | 시작 | 추적 방법 |
|------|----------|------|----------|
| **BPC 구독매출** | 공시 | Q1 FY2025~ | 분기 어닝 |
| **C&M 구독매출** | 공시 | Q1 FY2025~ | 분기 어닝 |
| **Total Adobe ARR** | 공시 | 수년 | 분기 어닝 |
| **RPO** | 공시 | 수년 | enterprise 계약 파이프라인 proxy |
| Enterprise vs Individual 비중 | **미공시** | — | 불가 |
| Churn rate / NRR | **미공시** | — | 불가 |

**축1 제품별 매출 추적 방법:**

- 문서+생산성: **BPC 구독매출**로 직접 추적 (공시)
- 엔터프라이즈 마케팅: FY2025까지 Digital Experience 매출(공시)로 직접 추적. 이후 과거 성장률(~9-10%)로 외삽하여 C&M에서 역산 (추정)
- 크리에이티브 프로: C&M 구독매출(공시) − EC 구독매출(추정) = CC 프로 구독매출 (추정)

### 1-3. 분기별 실적 추이

**축1 기준: 제품별 분기 (추정 — Q1 FY2025~):**

| 분기 | CC 프로 구독 (YoY) | BPC 구독 (YoY) | EC 구독 (YoY) |
|------|-------------------|---------------|--------------|
| Q1 FY2025 | ~$2,528M (-) | $1,534M (-) | ~$1,394M (-) |
| Q2 FY2025 | ~$2,588M (-) | $1,607M (-) | ~$1,411M (-) |
| Q3 FY2025 | ~$2,636M (-) | $1,652M (-) | ~$1,460M (-) |
| Q4 FY2025 | ~$2,840M (-) | $1,717M (-) | ~$1,413M (-) |
| Q1 FY2026 | ~$2,849M (+13%) | $1,782M (+16%) | ~$1,540M (+10%) |

> 수치 소스: BPC는 공시. EC 구독은 FY2025까지 DX 구독매출(공시)로 대용. CC 프로 = C&M(공시) − EC. Q1 FY2026 EC는 Q4 FY2025 $1,413M에 YoY +9% 가정(추정⁴). FY2025는 공시 첫해라 YoY 없음.

**축2 기준: 고객 그룹 (공시 — Q1 FY2025~):**

| 분기 | C&M 구독 (YoY) | BPC 구독 (YoY) |
|------|---------------|---------------|
| Q1 FY2025 | $3,922M (-) | $1,534M (-) |
| Q2 FY2025 | $3,999M (-) | $1,607M (-) |
| Q3 FY2025 | $4,096M (-) | $1,652M (-) |
| Q4 FY2025 | $4,253M (-) | $1,717M (-) |
| Q1 FY2026 | $4,389M (+12%) | $1,782M (+16%) |

> 수치 소스: Q1 FY2026 10-Q 및 Q4 FY2025 어닝 릴리즈 (공시). FY2025는 이 분류의 첫해라 YoY 없음.
>
> 참고: Adobe 매출의 ~40%가 해외. Q1 FY2026 reported +12% vs constant currency +11%.

**ARR 추이 (공시):**

| 시점 | Total Adobe ARR (YoY) |
|------|-----------------------|
| Q4 FY2024 | $22.61B (-) |
| Q4 FY2025 | $25.20B (+11%) |
| Q1 FY2026 | $26.06B (+11%) |

> 수치 소스: Adobe 분기별 어닝 릴리즈 (공시).

---

## 2. 경쟁우위 + 산업구조

### 2-1. 스크리닝 시그널 → 해자 원인 매핑

screening_20260411.csv 기준 Adobe moat_score **97** (최고점).
RATIONALE의 해자 종류 시그널을 대입:

| 시그널 | Adobe 수치 | 기준 | 해자 종류 추정 |
|--------|-----------|------|---------------|
| GP margin 89.1% > 40% | ✓ | 브랜드/가격결정력 | 극강 — SaaS 중 최상위 |
| GP margin std 0.7% < 5% | ✓ | 마진 안정성 | 경기/경쟁에 거의 흔들리지 않음 |
| 구독매출 97% | ✓ | 전환비용/락인 | 월/연 반복구매 고정 |
| FCF/NI 1.36 > 0.8 | ✓ | 이익의 질 | 순이익보다 현금이 더 많이 나옴 |
| ROIC 3y min 34.7% > 7% | ✓ | 해자 공고 | 최악의 해에도 자본비용의 3.5배 |
| Debt/Equity 0.53 < 1.0 | ✓ | 차입 불필요 | 자체 현금으로 충분 |

> 수치 소스: screening_20260411.csv (SEC XBRL 기반 정량 스크리닝)

**외부 소스 교차검증:**

| 지표 | 우리 값 | 외부 소스 | 일치 여부 |
|------|---------|----------|----------|
| GP margin | 89.1% | GuruFocus 89.5%, MacroTrends 89.3% (FY2025) | ✓ 일치 (시점 차이 ±0.4%p) |
| Debt/Equity | 0.53 | GuruFocus 0.57 (Nov 2025) | ✓ 일치 (Q3 vs Q4 시점 차이) |
| FCF/NI 3y avg | 1.36 (3년 평균. FY2025 단년: 1.38, Q1 FY2026 TTM: 1.43) | FY2025 단년: CFO $10.0B − CAPEX $0.18B = FCF $9.85B / NI $7.13B = 1.38 | ✓ 일치 |
| ROIC | 3y avg 39.9% | GuruFocus 26.1%, Finbox 36.7% (FY2025) | ⚠️ 정의 차이 |

> ROIC 차이 원인: 우리 계산은 IC = 총자산 − 유동부채 − 현금. GuruFocus는 IC = 자기자본 + 장기부채 − 현금으로 분모가 더 큼. **방향은 동일** (자본비용 10% 대비 모두 크게 초과). 절대값은 IC 정의에 따라 26-59% 범위에서 변동.
>
> 검증 소스: [GuruFocus GP margin](https://www.gurufocus.com/term/gross-margin/ADBE), [GuruFocus ROIC](https://www.gurufocus.com/term/roic/ADBE), [GuruFocus D/E](https://www.gurufocus.com/term/debt-to-equity/ADBE), [MacroTrends](https://www.macrotrends.net/stocks/charts/ADBE/adobe/gross-margin)

6개 시그널 전부 점등. 세 가지 해자(브랜드 + 전환비용 + 규모의 경제)가 동시에 작동.

### 2-2. 해자 분석

#### 해자 1: 파일 포맷 + 워크플로우 락인 (전환비용)

Adobe의 가장 깊은 해자. GP margin 89%의 근본 원인.

**메커니즘:**

- .PSD(Photoshop), .AI(Illustrator), .INDD(InDesign), .PRPROJ(Premiere Pro) → 업계 표준 파일 포맷
- 에이전시 ↔ 클라이언트, 디자이너 ↔ 인쇄소, 영상팀 ↔ 후반작업 간 워크플로우가 Adobe 포맷에 의존
- 30년간 축적된 플러그인, 프리셋, 액션, 템플릿 자산 — 개인이 쌓은 생산성 투자
- 학교에서 Adobe로 배움 → 직장에서 Adobe 사용 → 다음 세대도 Adobe (교육 파이프라인)

**정량 증거:**

- Enterprise churn rate ≈ 0에 가까움 (Morningstar 분석)
- 구독매출 비중 97% (Q1 FY2026 10-Q, 공시)
- GP margin std 0.7% — 3년간 이탈로 인한 매출 변동이 거의 없음

**취약점:**

- 개인/프리랜서는 전환비용이 상대적으로 낮음 — Canva, Affinity로 이탈 가능
- UI/UX 디자인에서는 이미 Figma에게 패배 (Figma 40.6% vs Adobe XD 13.5%)
- AI가 파일 포맷 의존도를 약화시킬 수 있음 (텍스트 → 결과물 워크플로우에서는 .PSD 파일 교환 불필요)

#### 해자 2: 브랜드 + 가격결정력

**메커니즘:**

- "Photoshop"은 동사("포토샵하다") — 카테고리 자체를 정의하는 브랜드
- PDF는 Adobe가 만든 포맷이 ISO 표준이 된 사례 — 문서 세계의 공용어
- 전문가 시장에서 "Adobe를 쓴다"는 것 자체가 신뢰 시그널

**정량 증거:**

- GP margin 89.1% — 매출의 89%가 원가를 제외한 순수 마진
- 2025년 Creative Cloud 가격 인상(Teams/Pro Edition) 단행 — 가격을 올려도 이탈 제한적
- Op margin 30% → 37% V자 회복 — FY2024 일시적 비용(Figma 인수 관련) 이후 마진 원복

**취약점:**

- 비전문가 시장에서 Adobe 브랜드 = "비싸고 복잡" → Canva의 "쉽고 무료"가 더 매력적
- DOJ 소송($150M 합의) — "해지를 어렵게 만들었다"는 이미지 → 브랜드 신뢰 일부 훼손

#### 해자 3: 규모의 경제 + 데이터 우위

**메커니즘:**

- R&D ~$3B/yr을 20개+ 앱에 분산 → 개별 경쟁자가 따라잡기 어려운 투자 규모
- Adobe Stock + Adobe Fonts → Firefly AI 학습 데이터 = IP-safe (저작권 문제 없음)
- 41M 구독자의 사용 데이터 → 제품 개선 피드백 루프

**정량 증거:**

- CAPEX/Revenue 0.78% — 소프트웨어를 한번 만들면 추가 배포 비용 ≈ 0
- FCF/NI 1.43 — 이익보다 현금이 43% 더 많이 나옴 (기존 자산이 현금 창출)

### 2-3. 산업 구조: 세그먼트별 경쟁 지형

#### 프로 크리에이티브 도구 (~$11.4B, 추정)

| 영역 | Adobe | 경쟁자 | 위협 |
|------|-------|--------|------|
| 이미지 편집 | Photoshop (1위, ~34% 전체 시장) | GIMP(무료), Affinity Photo($70 일회) | 낮음 |
| 벡터 그래픽 | Illustrator (1위, 세부시장 ≈ 독점) | Affinity Designer, CorelDRAW | 낮음 |
| 영상 편집 | Premiere Pro (1위) | DaVinci Resolve(무료/$295 일회) | **중간** |
| 모션 그래픽 | After Effects (1위) | Blender(무료), Nuke | 낮음 |
| UI/UX 디자인 | XD (13.5%, **패배**) | Figma (40.6%, 1위) | **높음 — 이미 졌음** |
| 레이아웃 | InDesign (1위) | Affinity Publisher | 낮음 |
| 사진 관리 | Lightroom (1위) | Capture One, Luminar | 낮음 |

> 점유율 소스: 6W Research, Statista, ProgrammingHelper (2025-2026 기준).

#### 문서 + 생산성 (~$7.1B, BPC)

| 영역 | Adobe | 경쟁자 | 위협 |
|------|-------|--------|------|
| PDF 편집 | Acrobat (1위, PDF = Adobe가 만든 표준) | Foxit, Nitro | 낮음 |
| 전자서명 | Acrobat Sign (25-30%) | DocuSign (35-40%), HelloSign | **중간** |
| 비전문가 디자인 | Adobe Express | Canva (265M MAU, $4B ARR) | **높음** |
| AI 문서 허브 | Acrobat Studio | Microsoft Copilot | 초기 |

> Microsoft는 M365 Copilot(문서 자동화) + Designer(디자인) + Clipchamp(영상)을 번들로 4.3억 M365 사용자에게 제공. Adobe BPC의 가장 큰 잠재적 위협.
>
> 전자서명 점유율: eSignGlobal 2026 (업계 추정). Canva: SaaStr, Backlinko (2025-2026).

#### 엔터프라이즈 마케팅 (~$6.1B, 추정)

| 영역 | Adobe | 경쟁자 | 위협 |
|------|-------|--------|------|
| 콘텐츠 관리 | AEM | Sitecore, Contentful | 낮음 |
| 고객 데이터 | Real-Time CDP | Salesforce Data Cloud, Segment | 중간 |
| 마케팅 자동화 | Campaign/Marketo | Salesforce MC, HubSpot | 중간 |
| 분석/개인화 | Analytics/Target | Google Analytics, Mixpanel | 중간 |
| AI 콘텐츠 생산 | GenStudio | 신규 카테고리 | 초기 |

> MarTech 시장 규모: $176B(2025) → $297B(2030), CAGR 11% (MarketsandMarkets).

#### 경쟁자 규모 비교

| 기업 | 매출/ARR | 성장률 | 시총/밸류에이션 | Adobe와의 관계 |
|------|---------|--------|---------------|---------------|
| **Adobe** | ~$25.6B | +11-12% | $92.6B | — |
| **Canva** | $4B ARR | +35-43% | $42B (비상장) | BPC 경쟁 (Express vs Canva) |
| **Figma** | $1.06B | +41% | ~$13B (주가 하락 후) | UI/UX에서 승리. CC 일부 경쟁 |
| **Salesforce** | ~$38B | +8-9% | ~$230B | EC 경쟁 (마케팅 클라우드) |
| **DocuSign** | $3.14B | +5% | ~$15B | Acrobat Sign 경쟁 |

> Canva: SaaStr. Figma: 10-Q/IPO 자료. Salesforce/DocuSign: 최근 어닝.

### 2-4. 생태계 해자 Proxy 지표 — 실측

| Proxy 지표 | 최신값 | 3년 추이 | 의미 |
|-----------|--------|---------|------|
| **FCF/NI** | 1.43 | 1.22 → 1.43 ↑ | 순이익보다 43% 더 많은 현금 창출. 캐시카우 구조 강화 |
| **ROIC** | 59.1% | 34.1% → 59.1% ↑ | 자본비용의 6배. 단, 바이백으로 IC 축소 효과 포함 |
| **CAPEX/Revenue** | 0.78% | 2.38% → 0.78% ↓ | 매출의 1% 미만 재투자. See's Candies 모델 |
| **GP margin** | 89.1% | std 0.7% | 3년간 변동 0.7%p. 가격결정력 안정 |
| **Op margin** | 37.8% (Q1 FY2026 GAAP) | 30.0% → 37.8% ↑ | FY2024 일시 하락 후 V자 회복 |
| **주식수** | 410.8M (diluted weighted average, Q1 FY2026 10-Q) | 459.1M → 410.8M ↓ | 3년 -10.5%. YoY -6.1%로 가속 |
| **Debt/Equity** | 0.53 | — | 차입 의존도 낮음 |

> 수치 소스: Gold 패널 (SEC XBRL 기반 직접 계산). RPO($22.22B, +13%)는 Q1 FY2026 10-Q 공시.

### 2-5. 해자 위협 vs 방어

**위협:**

| 위협 | 영향받는 해자 | 심각도 | 시간축 |
|------|------------|--------|--------|
| Canva의 비전문가 시장 장악 | 브랜드 (비전문가 영역) | ★★★☆☆ | 진행 중 |
| Figma의 UI/UX 지배 | 워크플로우 락인 (디자인) | ★★★★☆ | 이미 발생 |
| AI seat compression | 전환비용 (프로 시장) | ★★★☆☆ | 2-5년 |
| DaVinci Resolve 무료 모델 | 가격결정력 (영상) | ★★☆☆☆ | 느리게 진행 |
| 오픈소스 AI (Midjourney 등) | 브랜드 + 규모의 경제 | ★★☆☆☆ | 초기 |

**방어:**

| 방어 | 보호하는 해자 | 강도 |
|------|------------|------|
| Firefly IP-safe 학습 데이터 | 규모의 경제 + enterprise 신뢰 | ★★★★☆ |
| Content Credentials (C2PA 표준) | enterprise 락인 (법적 컴플라이언스) | ★★★☆☆ |
| CC ↔ DC ↔ EC 크로스셀 | 전환비용 (생태계) | ★★★★☆ |
| Generative Credits 과금 모델 | 가격결정력 (AI 시대) | ★★★☆☆ |
| 41M 구독자 기반 | 규모의 경제 + 데이터 | ★★★★★ |

### 2-6. 경쟁우위 종합

Adobe의 해자는 **하나의 킬러 앱이 아니라 생태계 전체**에 있다. 개별 제품에서는 밀릴 수 있지만 (UI/UX→Figma, 비전문가→Canva), 번들 생태계를 통째로 대체할 경쟁자는 없다.

모든 proxy 지표가 **"해자가 건재하고, 최근 3년간 오히려 강화"**를 가리킨다.

**불확실성 1 — AI가 파일 포맷 락인을 약화시키는가:**
텍스트→결과물 워크플로우가 주류가 되면 .PSD 교환이 불필요해지고, 전환비용이 줄어든다. 다만 현재 데이터(Photoshop 내 AI 사용률 66% (Summit Stocks 인용, Adobe 베타 사용자 데이터), Firefly ARR $250M+)는 AI가 Adobe를 대체하기보다 강화하는 방향.

**불확실성 2 — "Figma 사례"의 반복:**
Figma는 UI/UX라는 Adobe 왕국의 한 성벽을 무너뜨렸다. 이런 일이 여러 영역에서 반복되면 생태계 자체가 무너질 수 있다.

| 영역 | "Figma급 위협" 후보 | 현재 상태 |
|------|-------------------|----------|
| 이미지 편집 | 없음 | 안전 |
| 벡터 그래픽 | 없음 | 안전 |
| 영상 편집 | DaVinci Resolve | **관찰 필요** |
| 비전문가 디자인 | Canva ($4B ARR) | **이미 발생** |
| 전자서명 | DocuSign (35-40%) | 공존 |
| 마케팅 자동화 | HubSpot, Salesforce | 공존 |

---

## 3. 경영진 / 지배구조

### 3-1. CEO — Shantanu Narayen (2007~현재)

**재임:** 2007년 12월~. 퇴임 예정 (후임 확정 시).

**핵심 실적:**

- 매출 ~$1B → $25B+ (18년간 25배)
- **SaaS 전환 (2013):** 패키지(Creative Suite) → 월정액 구독(Creative Cloud). SaaS 전환의 교과서적 성공 사례
- **플랫폼 확장:** 2009년 Omniture 인수를 시작으로 Experience Cloud 구축 → 현재 ~$6B 사업
- **AI 전략:** Firefly 출시, Generative Credits 과금 모델, Content Credentials(C2PA) 표준 주도

**판단 실수:**

- Figma 인수 시도($20B, 50배 ARR, 2022) — 규제로 무산. 위약금 $1B. 해자 잠식에 대한 위기감의 반영

### 3-2. CEO 전환 — 현재 상황

| 항목 | 상태 |
|------|------|
| 발표일 | 2026년 3월 12일 |
| 퇴임 시점 | 후임 확정 후. "수개월 내" 예상 |
| 퇴임 후 역할 | Board Chair 잔류 |
| 승계 위원회 | Frank Calderoni(Lead Independent Director) 주도. 내외부 후보 검토 |
| 유력 후보 | **David Wadhwani** (Digital Media 사장) |
| 다른 후보 | **Anil Chakravarthy** (Digital Experience 사장) |

참고: Scott Belsky(전 Chief Strategy Officer)는 2025년 3월 퇴사하여 A24로 이직. 핵심 전략 임원 이탈은 리더십 리스크의 일부. 외부 보도에 따르면 이사회는 Google/OpenAI 출신 외부 'AI-native' 리더도 검토 중.

**David Wadhwani의 AI 전략 리더십 실적:**

| 이니셔티브 | 출시 | 결과 (공시 기준) |
|-----------|------|----------------|
| Firefly | 2023.03 | ARR $250M+ (Q1 FY2026). Fortune 500의 75% 채택 |
| Generative Credits | 2024~ | 분기 대비 3배 사용량 성장 |
| Acrobat AI Assistant | 2024~ | ARR 전년 대비 ~3배 (Q1 FY2026) |
| Acrobat Studio | 2025~ | MAU +20% YoY 기여 |
| Adobe Express 2.0 | 2024~ | BPC 구독 +16% YoY의 핵심 동력 |
| Content Credentials | 2024~ | enterprise 컴플라이언스 차별화 |

> 수치 소스: Q1 FY2026 어닝 릴리즈, 어닝콜 코멘터리 (공시).

**평가:** 결과만 보면 양호. Firefly를 2년 만에 $250M+ ARR까지 키웠고, 기존 제품에 AI를 임베딩하여 해지 없이 새 매출을 만든 전략도 성공적. 다만 이 실적이 Wadhwani 개인의 역량인지 Narayen 체제의 조직력인지 분리하기 어려움.

### 3-3. 자본 배분

| 연도 | 자사주 매입 | 비고 |
|------|-----------|------|
| FY2022 | ~$6.3B | Figma 인수 발표 ($20B) |
| FY2023 | $4.4B | Figma 무산, 위약금 $1B |
| FY2024 | $9.5B | Figma 자금 → 바이백 + AI 전환 |
| FY2025 | $11.281B (역대 최대) | 주식 수 10%+ 감소 |

> 수치 소스: Adobe 10-K (SEC filing).

- 2024년 3월: **$25B 신규 바이백 프로그램** 승인 (2028년 3월까지)
- **배당 없음.** 잉여현금 전액을 바이백 + R&D + M&A에 투입

```text
Figma 실패 이전: M&A 적극적 (Omniture, Marketo, Magento, Figma 시도)
Figma 실패 이후: M&A → 바이백 + AI 자체 개발로 전략 선회
```

### 3-4. 보상 구조 (2026 Proxy 기준)

| 항목 | 내용 |
|------|------|
| 경영진 현금 보너스 | 매출 + EPS 목표 95% 이상 달성 시 지급. 최대 목표의 155% |
| 성과주 | 50% 3년 상대 TSR (NASDAQ-100 대비) + 50% 연간 Net New Sales Goal (FY2026부터 Total Adobe ending ARR growth 기준). 0~200% 범위 |
| 이사 보수 | 연 $330K 상당 RSU + 현금 |
| 보상위원회 | 전원 사외이사 (독립성 확보) |

> 수치 소스: Adobe 2026 Proxy Statement (공시).

### 3-5. 1분 신뢰성 테스트

`knowledge/경영진_지배구조.md` 프레임워크 적용:

| # | 항목 | Adobe | 판정 |
|---|------|-------|------|
| 1 | ROE 10%+ (30%+ 지속가능성 의심) | 63% | ⚠️ 바이백으로 자기자본 축소 → ROE 인위 증폭. 순수 사업 수익성은 Op margin 37%로 판단 |
| 2 | ROA 7%+ | 24.2% | ✅ 극강 |
| 3 | 재무상태표 | 현금 $6.3B, 부채 $6.2B. Goodwill ~$13B (총자산의 44%) | ⚠️ Goodwill 큼 |
| 4 | 영업외/일회성 비용 | DOJ 합의 $150M, Figma 위약금 $1B | ⚠️ 과거 일회성, 반복 패턴 아님 |
| 5 | 배당 여부 | 없음. 바이백으로 대체 | 보통 |

### 3-6. 경영진 종합

**강점:** Narayen 18년 세 번의 대전환 성공. FCF 대부분 바이백 투입. 보상이 ARR+TSR에 연동.

**리스크:** CEO 전환이 최대 불확실성. Figma 인수 시도는 방어적 M&A. Goodwill $13B. SBC ~$2B/yr.

**밸류에이션 반영 포인트:**

- CEO 확정 시 → Bull 확률↑, Bear 확률↓ (re-valuation 트리거)
- SBC ~$2B → OE에서 차감 필요 (전 시나리오 공통)
- CEO 미확정 → Bear 확률 유지 또는 상향

---

## 4. 시장 내러티브 vs 우리 분석

### 4-1. Bull Case — 시장 낙관론

| # | 논점 | 근거 | 소스 |
|---|------|------|------|
| B1 | **극단적 저밸류에이션** | P/FCF 10x (SBC 조정 시 12x) | Summit Stocks, Seeking Alpha |
| B2 | **AI bear case가 숫자에 안 나타남** | MAU 850M (+17% YoY), 구독매출 +13% 가속, $10M+ ARR 고객 +20% YoY | Summit Stocks, Q1 FY2026 어닝 (공시) |
| B3 | **Firefly 수익화 진행 중** | Firefly ARR $250M+, AI-first ARR 3배, Generative Credits QoQ +45% | Q1 FY2026 어닝 (공시) |
| B4 | **Enterprise 분배 해자** | Fortune 500의 99%가 Express 사용, 75%가 Firefly 채택 | 어닝콜 코멘터리 |

### 4-2. Bear Case — 시장 비관론

| # | 논점 | 근거 | 소스 |
|---|------|------|------|
| R1 | **Seat compression** | AI가 디자이너 생산성↑ → 더 적은 시트로 같은 결과물 | Carbon Finance, SA Bear |
| R2 | **매출 성장 둔화** | FY2025 +11% → FY2026 매출 가이던스 +8.9-9.8%, ARR 가이던스 +10.2%. Seq. Total ARR net add $400M | FY2026 가이던스 (공시) |
| R3 | **AI 수익화 미미** | Firefly $250M = 전체 $26B ARR의 1% | SA "Stop the Wishful Thinking" |
| R4 | **멀티플 붕괴 정당** | PER 56x(2021) → 16x(현재). 성장 프리미엄 제거 | Goldman Sachs Sell ($220) |
| R5 | **CEO 공백 + 규제** | Narayen 퇴임, DOJ $150M 합의 | 다수 |
| R6 | **Stock 사업 붕괴** | 생성형 AI가 스톡 이미지 대체 | Summit Stocks |

### 4-3. 애널리스트 컨센서스

| 항목 | 수치 | 소스 |
|------|------|------|
| 컨센서스 등급 | **Hold** | Public.com, MarketBeat |
| Buy / Hold / Sell | 23 / 13 / 4 (51명) | Benzinga |
| 평균 목표가 | **$343-365** | StockAnalysis, MarketScreener |
| 최고 / 최저 | $510 (Morgan Stanley) / $220 (Goldman Sachs) | Benzinga |

### 4-4. 동의/반대 매핑

| 논점 | 시장 | 우리 판단 | 근거 |
|------|------|----------|------|
| B1: 저밸류에이션 | Bull | **동의** | P/FCF 10-12x, OE Yield 9-11% |
| B2: AI bear 숫자에 없음 | Bull | **동의** | MAU +17%, 구독 +13%, 해자 proxy 건강 |
| B3: Firefly 수익화 | Bull | **부분 동의** | 진행 중이지만 전체의 1% |
| R1: Seat compression | Bear | **부분 동의** | 아직 미확인. 2-5년 시계 |
| R2: 매출 성장 둔화 | Bear | **동의** | 매출 가이던스 하단 8.9%. 다만 ~9%+37%마진에 PER 16x는 여전히 쌈 |
| R3: AI 매출 미미 | Bear | **부분 동의** | "안 보인다" ≠ "실패했다" |
| R4: 멀티플 붕괴 정당 | Bear | **부분 반대** | 해자 proxy가 현재까지 강화 추세이나, 이는 과거 데이터. AI 전환의 full impact는 아직 반영되지 않았을 수 있음 |
| R5: CEO + 규제 | Bear | **동의 (단기)** | 확정 시 해소되는 시한부 리스크 |
| R6: Stock 사업 붕괴 | Bear | **동의** | 구조적. 다만 비중 작음 |

### 4-5. 핵심 결론

**Bear 포인트는 전부 밸류에이션에 반영되는 변수이거나, 밸류에이션의 결과 자체다.**

| Bear 포인트 | 밸류에이션 변수 매핑 |
|------------|-------------------|
| R1: Seat compression | → **성장률** 가정 |
| R2: 매출 성장 둔화 | → **성장률** 그 자체 |
| R3: AI 매출 미미 | → **성장률** (Bull 상방 제한) |
| R4: 멀티플 붕괴 정당 | → **밸류에이션의 결과 자체** |
| R5: CEO + 규제 | → **시나리오 확률** (확률 조정으로 반영) |
| R6: Stock 사업 붕괴 | → **성장률** (소규모 하향) |

"Adobe가 망한다"는 bear가 아니다. **"얼마나 느리게 성장할 것이며, 시장이 얼마를 지불해야 하는가"**가 논쟁의 본질. 사업 모델 붕괴가 아닌 성장 속도 둔화라면, 시나리오별 성장률 가정으로 답이 나오는 문제다.

**R4(멀티플 붕괴 정당)에 대한 부분 반대:** 해자 proxy 전부 강화 추세, 매출 +10-12%, Op margin V자 회복, Firefly/BPC 신규 성장 동력. PER 16x는 "이미 일어난 훼손"이 아니라 **"앞으로 일어날 훼손"을 과도하게 선반영**한 것으로 판단. 단, 과거 데이터 기반이므로 AI 전환의 full impact가 아직 반영되지 않았을 가능성은 인정.

**투자 가설:**

> 시나리오별 가설과 실현 조건은 Section 6(밸류에이션) 참조. 현재 실적(Q1 FY2026)은 Base 궤도에 정렬.
>
> 가설이 맞으려면: C&M YoY > 8%, BPC > 12%, AI ARR 가속 지속.
> 가설이 틀리려면: seat compression이 숫자로 나타남 (C&M < 5%), CEO 전략 표류, Firefly 성장 정체.

Sources:

- [Summit Stocks — AI Bear Case Still Isn't Showing](https://summitstocks.substack.com/p/adobe-the-ai-bear-case-still-isnt)
- [Seeking Alpha — Hated, Cheap, and Growing](https://seekingalpha.com/article/4889759-adobe-hated-cheap-and-growing)
- [Seeking Alpha — Stop the Wishful Thinking](https://seekingalpha.com/article/4888743-adobe-stop-the-wishful-thinking-and-face-the-reality)
- [MarketBeat — ADBE Forecast](https://www.marketbeat.com/stocks/NASDAQ/ADBE/forecast/)
- [Benzinga — Analyst Ratings](https://www.benzinga.com/quote/ADBE/analyst-ratings)
- [Morningstar — Adobe Switching Costs](https://www.morningstar.com/company-reports/1181008-adobes-creative-dominance-is-supported-by-steep-switching-costs)
- [GuruFocus GP margin](https://www.gurufocus.com/term/gross-margin/ADBE)

---

## 5. 위기/기회 통합 매트릭스

### 5-1. 기회

| # | 기회 | 실현 가능성 | 영향도 | 밸류에이션 반영 | 모니터링 |
|---|------|-----------|--------|---------------|---------|
| O1 | BPC +16% — 비전문가 시장 확장 | **높음** (실적 확인) | **중간** | Base 성장률에 반영 | BPC YoY |
| O2 | Firefly $250M+ ARR, AI-first ARR 3배, AI-influenced ARR $8B+ — AI 수익화 시작 | **중간** (초기) | **높음** | Bull에만 반영 | AI ARR |
| O6 | Op margin 30%→37% 회복 | **높음** (실현) | **중간** | Base 마진 가정 | Op margin |
| O7 | MarTech 시장 $176B→$297B | **높음** | **낮음** | Base에 소폭 반영 | EC 추정 매출 |
| O8 | Enterprise churn ≈ 0, RPO +13% | **높음** | **높음** | 성장률 하방 지지 | RPO YoY |

### 5-2. 리스크

| # | 리스크 | 실현 가능성 | 영향도 | 밸류에이션 반영 | 모니터링 |
|---|--------|-----------|--------|---------------|---------|
| R1 | AI seat compression | **중간** (R6 $70M이 선행 지표) | **높음** | Bear 성장률 3% | C&M YoY < 5% |
| R2 | 매출 성장 둔화 — 가이던스 +8.9-9.8%, Seq. Total ARR net add $400M | **높음** | **중-높음** | Base 성장률 9% | 매출 YoY, Seq. ARR add |
| R3 | CEO 미확정 | **높음** | **중간** | 확률 가중으로 반영 | CEO 발표 |
| R4 | Figma 사례 반복 (DaVinci, Canva) | **낮~중간** | **높음** | Bear에 반영 | 경쟁자 트래킹 |
| R5 | SBC ~$2B/yr | **확정** | **높음** (OE -19%) | **전 시나리오** OE 차감 | SBC/매출 |
| R6 | Stock 사업 $70M ARR 이탈 (실측) | **높음** (초기 실현) | **낮음** | Bear에 소폭 반영 | Stock ARR |
| R7 | Goodwill $13B 감손 | **낮음** | **높음** (발생 시) | 미반영 (발생 시 재평가) | 분기 감손 |
| R8 | DOJ 해지 간소화 | **중간** | **낮음** | Bear에 소폭 반영 | BPC churn |

### 5-3. 핵심 원칙

**할인율 = 기회비용 (전 시나리오 10% 고정).** 불확실성(CEO, AI, 경쟁)은 모두 현금흐름(성장률+마진)과 시나리오 확률에서 반영. (knowledge/할인율_기대수익률.md — 버핏 원칙)

**Bear 포인트는 전부 밸류에이션 변수(성장률/OE)이거나 그 결과 자체.** 사업 모델 붕괴가 아닌 성장 속도 둔화가 논쟁의 본질.

### 5-4. R3(CEO 리스크) 해소 경로

| 단계 | 이벤트 | 확률 조정 |
|------|--------|----------|
| 현재 | CEO 미확정 | Bull 5% / Base 50% / Bear 45% |
| Step 1 | Wadhwani 확정 | Bull 5%→10%, Bear 45%→40% |
| Step 2 | 리더십 검증 (2-3분기 실적) | Bull 10%→15%, Bear 40%→35% |

### 5-5. 시나리오 매핑

| 가정 | Bull | Base | Bear |
|------|------|------|------|
| **OE** | $8.3B | $8.3B | $8.3B |
| **성장률** | 12% | 9% | 3% |
| **할인율** | 10% | 10% | 10% |
| **터미널** | 3% | 2.5% | 2% |
| **기간** | 10년 | 10년 | 7년 |
| **확률** | 5% | 50% | 45% |

---

## 6. 밸류에이션

### 6-1. 시나리오별 가설

| 시나리오 | 가설 | 실현 조건 |
|----------|------|----------|
| **Bull** | AI가 Adobe를 강화. Firefly 수익화 가속 + BPC 확장 + CEO 안정 전환 | C&M YoY > 12%, AI ARR 가속, CEO 확정 + 리더십 검증 |
| **Base** | AI 영향 중립. 현행 성장 지속, 해자 유지, 가이던스 수준 | C&M YoY 8-10%, BPC > 12%, Op margin 35%+ |
| **Bear** | AI가 seat compression 유발. 경쟁 심화로 마진 압축 + CEO 전환 불안 | C&M YoY < 5%, Op margin < 33%, 경쟁자 점유율 확대 |

> 성장률은 linear fade (초기 성장률 → 터미널+1%로 수렴). 예: Bull 12%→4%(10년), Base 9%→3.5%(10년), Bear 3%→3%(7년, fade 없음).

### 6-2. OE 산출 근거

전 시나리오 공통 OE $8.3B (현재 마진 기준, 마진 변동은 성장률에 내포):

```text
OE = CFO TTM − SBC TTM − CAPEX TTM
   = $10,507M − $1,976M − $190M
   = $8,341M ≈ $8.3B

- CFO TTM: FY2025 $10,031M + Q1 FY2026 $2,958M − Q1 FY2025 $2,482M = $10,507M (공시)
- SBC TTM: FY2025 $1,942M + Q1 FY2026 $509M − Q1 FY2025 $475M = $1,976M (XBRL 직접 확인)
- CAPEX TTM: ~$190M (공시)
- Shares: 410.8M (diluted weighted average, Q1 FY2026 10-Q)
```

> OE = CFO − SBC − CAPEX. SBC ~$2B 전 시나리오 차감. valuation/RATIONALE.md 참조.

### 6-3. DCF 결과

| 시나리오 | IV/주 | 안전마진 |
|----------|-------|---------|
| **Bull** | **$442** | 49% |
| **Base** | **$371** | 39% |
| **Bear** | **$272** | 17% |

- Bear IV $272은 현재가 $225과 가깝다. 보수적 가치 범위 하단이 현재가 근처.
- Base가 실현되면 현재가 대비 유의미한 상승 여력

### 6-4. 확률가중 적정주가

| 시나리오 | IV | 확률 | 기여 |
|----------|-----|------|------|
| Bull | $442 | 5% | $22 |
| Base | $371 | 50% | $186 |
| Bear | $272 | 45% | $122 |
| **확률가중** | | | **$330** |

중심가치는 대략 $300대 초반이나, 리스크 가정에 따라 달라짐

> **확률 산정 (주관적 판단):**
>
> - Bull 5%: CEO + AI 수익화 두 조건이 모두 충족되어야 함. 현재 둘 다 미해소.
> - Bear 45%: CEO 미확정 + AI seat compression 선행 지표(Stock ARR $70M 이탈) 존재. 단, 핵심 실적(C&M +12%, 구독 +13%)은 아직 Bear가 아님. 보수적 접근.
> - Base 50%: 현재 실적이 Base 궤도. 가장 높은 확률이지만 Bear와 비슷하게 잡은 것은 보수적 접근.
>
> 참고: Bear IV($272)가 현재가($225) 근처이므로 확률 배분에 대한 민감도가 높지는 않다. 다만 Bear IV 자체가 과대평가일 가능성도 6-9에서 점검.

### 6-5. 민감도 분석

OE $8.3B, 10yr, Gordon 2.5%. 할인율 × 성장률:

|  | g=0% | g=3% | g=5% | g=7% | g=9% | g=12% |
|--|------|------|------|------|------|-------|
| **r=8%** | $350 | $399 | $434 | $472 | $513 | $581 |
| **r=10%** | $257 | $291 | $316 | $342 | $371 | $418 |
| **r=12%** | $203 | $229 | $247 | $267 | $289 | $324 |

현재가 $225는 r=12%/g=3% 이하에서만 도달. r=10%에서는 g=0%에서도 $257.

### 6-6. Reverse DCF

| 가정 | 현재가를 정당화하는 implied growth |
|------|--------------------------------------|
| OE $8.3B, r=10%, buyback 0%, 10년/Gordon 2.5% | **-3.2%** (매년 감소) |
| OE $8.3B, r=10%, buyback 0%, 7년/Gordon 2.0% | **-3.1%** (매년 감소) |

시장은 "OE가 매년 3% 줄어드는 세계"를 가격에 반영. 성장률 0%만 유지해도 현재가 대비 상승 여력 존재.

### 6-7. DCF 한계

1. **SBC 수동 차감:** 파이프라인 미구현. 수동으로 SBC $2B 차감. (valuation/RATIONALE.md)
2. **마진 변동 미반영:** OE $8.3B는 현재 마진(op margin ~37%) 기준. 마진이 변동하면 OE도 변동하지만, 본 모델에서는 마진 변화를 성장률에 내포시킴.

### 6-8. 종합 판단

Adobe는 현금을 잘 버는 좋은 소프트웨어 회사다. 현재 주가는 비관론을 상당 부분 반영하고 있고, 보수적 기준에서도 싸 보이는 구간이다. 다만 AI와 CEO 전환 리스크가 아직 진행 중이라, '확실히 싸다'보다는 '싸 보인다'가 더 솔직한 표현이다.

| 조건 | 판정 |
|------|------|
| Bear IV($272) vs 현재가($225) | 보수적 가치 범위 하단이 현재가 근처 |
| 확률가중 IV($330) | 중심가치는 $300대 초반이나, 가정에 민감 |

다음 분기 어닝에서 확인할 것: C&M 성장률이 유지되는지, CEO 후임이 정해지는지, AI 매출이 가시화되는지.

### 6-9. 과신 점검 — 내가 틀렸다면

Bear IV $272이 과대평가인 시나리오:

**1. Seat compression이 예상보다 빠르고 깊으면 — ⚠️ 초기 증거 존재**
C&M YoY가 마이너스 전환 + op margin < 25%까지 하락하는 세계. Bear 3% 성장이 아닌 매출 역성장 → OE 자체가 축소. 이 경우 현재의 Bear보다 훨씬 나쁨.
**초기 데이터:** 그래픽 아티스트 구인공고가 2024년 -12%, 2025년 **-33%** 감소 (Bloomberry, 1.8억 구인공고 분석). 미국 경영진의 37%가 2026년 말까지 AI로 일자리 대체 계획 (HR Dive). 이는 seat compression의 가장 직접적인 선행 지표.
**반론:** 구인 감소 ≠ 기존 시트 해지. 더 적은 디자이너가 AI로 더 많은 결과물 → 시트당 가치↑로 상쇄 가능. 또한 AI 해고 후 고용주의 55%가 후회 (Forrester) → 일부 역전 가능.
→ 대응: C&M YoY 추적. 2분기 연속 < 5%에서 즉시 재평가.

**2. Adobe의 해자가 "파일 포맷 락인"이 아니라 "관성"이라면**
AI가 텍스트→결과물 워크플로우를 주류로 만들면, .PSD 파일 교환 자체가 불필요해짐. 전환비용이 소멸하면 GP margin 89%를 유지할 근거 없음. 현재까지의 증거(Photoshop 내 AI 사용률 66%, 출처: Summit Stocks/Adobe 베타 데이터)는 AI가 Adobe **안에서** 쓰이고 있음을 보여주지만, 이 추세가 영구적이라는 보장은 없음.
→ 대응: GP margin 추이 모니터링. 하락 시작 시 해자 재평가.

**3. 크리에이티브 일자리 시장 자체가 구조적으로 축소되면 — ⚠️ 새로운 우려**
\#1의 확장. 구인 -33%가 일시적 조정이 아니라 구조적 추세라면, Adobe의 TAM(총 시장 규모) 자체가 줄어드는 시나리오. 현재 모델은 "성장이 둔화"하지만 "시장이 축소"하지는 않는다고 가정 — 이 가정이 틀릴 수 있음. 더 적은 디자이너 × 동일한 시트당 가격 = 매출 감소.
→ 대응: BLS(노동통계국) 디자인 직종 고용 데이터, 분기별 Adobe MAU 추이 감시.

\#1~\#3 모두 monitoring으로 감시. 특히 \#1의 구인 데이터(-33%)는 Bear 시나리오 확률을 높이는 방향.

---

## 7. 모니터링

→ [ADBE_monitoring.md](ADBE_monitoring.md)
