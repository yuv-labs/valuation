# IDEXX Laboratories (IDXX) Shallow Dive — Fisher 트랙 — 2026-04-18

기준일: 2026-04-18 | 데이터: SEC EDGAR 10-K, Gold 패널, Stooq, Web Research | 주가: $558.32 (2026-03-27 stooq 종가; 4월 중순 $560~$570대)
실행 모드: 배치 세션 2026-04-18 (IDXX + ALGN + VLTO)
프레임 초기 가정: 피셔형

## 1. 유니버스 하한선

| 항목 | 조건 | 판정 | 근거 |
| ------ | ------ | ------ | ------ |
| 상장 기간 | ≥ 5년 | PASS | NASDAQ IPO 1991-06-21. 약 34년 |
| 컨퍼런스콜 | 정기 운영 + Q&A 전사본 공개 | PASS | 분기별 earnings call, Motley Fool/Seeking Alpha 전사본 상시 공개 |
| 현 경영진 재직 | ≥ 3년 | **MARGINAL** | Mazelsky CEO 2019-10~(약 6.5년). **2026-05-12부 Michael Erickson(신임) 교체** 예정. CFO Andrew Emerson 2025-03~(약 1년) — 두 자리 다 전환기 |
| 임원 이직률 파악 | 추적 가능 | PASS | SEC DEF 14A(위임장) + 10-K Part III + LinkedIn |
| 업계 평판 접근 | 최소 한 단계 거쳐 닿음 | PASS | 수의사 커뮤니티(VIN, AVMA), Vetstreet, Petfood Industry 등 2차 접근 가능. 실무 접근은 지인 수의사 거쳐 가능 |

**판정: 조건부 PASS.** 상장 34년·공시 풍부·컨콜 투명. 다만 CEO·CFO 쌍방 교체 구간(2025-03 CFO, 2026-05 CEO 예정)으로 경영진 연속성 평가가 교차 시점에 걸림. 진행한다.

## 2. 2분 테스트 + 사업모델

### 2분 테스트

IDEXX는 동물병원에 VetLab·Catalyst·ProCyte 등 **분석장비(instrument)** 를 심어 놓고, 매 검사마다 소비되는 **시약·소모품(consumables)** 과 검체를 위탁받는 **레퍼런스 랩 서비스** 로 반복적 수익을 거둔다. 면도기-면도날(razor-blade) 구조에 의료 전문성과 SaaS성 소프트웨어(Cornerstone·ezyVet 실무관리)까지 묶어 교체 비용(switching cost)을 극도로 높여 놓았기에, 반려동물 방문수가 감소해도 **검사 빈도 × 단가 × 믹스 상향** 으로 7~10%대 recurring 성장을 유지할 수 있어 훌륭할 수 있다.

### 사업모델 한 페이지

| 항목 | 내용 |
| ------ | ------ |
| 제품/서비스 | CAG(Companion Animal Group) — 분석장비 + 소모품 + 레퍼런스 랩 + 수의 SW(Cornerstone/ezyVet) + rapid assay(SNAP 테스트). Water(수질 미생물 검사), LPD(가축·가금·낙농 진단) |
| 주요 고객 | 동물병원(세계 ~130개국), 수질 관리 기관, 축산·낙농 사업자 |
| 수익 모델 | **recurring ~85~90%**: CAG Diagnostics recurring(소모품·레퍼런스 랩·rapid assay) 대부분 + SW subscription. Premium instrument 설치 기반 +12% YoY로 razor 확장 |
| 고정비 vs 변동비 | 레퍼런스 랩 네트워크(고정)·R&D·마케팅 준고정. 소모품 제조(COGS) 변동. GM 60%+ 유지 |
| 규모의 경제 작동 여부 | 강하게 작동: 설치 기반 확장 → 소모품 pull-through → 레퍼런스 랩 처리량 확대 → 단가 협상력. 최근 5년 EBIT 마진 29%→32% 확대 |

## 3. 정량 기초 5년

> 출처: SEC 10-K via Gold 패널 (USD M). 회계연도: 캘린더 Dec 31.

| 지표 | FY2021 | FY2022 | FY2023 | FY2024 | FY2025 |
| ------ | -------: | -------: | -------: | -------: | -------: |
| 매출 | 3,215 | 3,367 | 3,661 | 3,898 | 4,304 |
| 매출 성장률 | — | +4.7% | +8.7% | +6.5% | **+10.4%** |
| EBIT | 932 | 899 | 1,097 | 1,128 | 1,360 |
| EBIT Margin | 29.0% | 26.7% | 30.0% | 29.0% | **31.6%** |
| 당기순이익 | 745 | 679 | 845 | 888 | 1,059 |
| CFO | 755 | 543 | 907 | 929 | 1,182 |
| Capex | 120 | 149 | 134 | 121 | 125 |
| **FCF** | **636** | **394** | **773** | **808** | **1,057** |
| ROIC | 47.5% | 50.1% | 46.1% | 45.4% | **52.5%** |
| CFO/NI | 1.01x | 0.80x | 1.07x | 1.05x | 1.12x |
| 발행주식수(M) | 86.6 | 84.6 | 84.0 | 83.2 | 81.0 |

> ROIC = EBIT × (1−0.22) / (총자산 − 유동부채 − 현금). FY2022 CFO 일시 하락은 COVID 재고 정상화 과정의 운전자본 드로우.

**5년 추세 한 줄 코멘트**: 매출은 7~10%대 단조 성장(FY22 일시 둔화 후 FY25 재가속), 마진·ROIC·FCF 모두 우상향. Capex ~3% 정체·주식수 꾸준한 축소(-6.5%)로 주당지표 상향. 피셔형 compounder 궤적에 가장 가까운 형태.

## 4. 경영진 기본 프로필

| 항목 | 내용 |
| ------ | ------ |
| 현 CEO | **Jay Mazelsky** / 재직 6.5년(2019-10~). 前 EVP North American Companion Animal Commercial(2012~2019). 이전 Philips Healthcare SVP/GM, Agilent, HP 엔지니어 경력 |
| 차기 CEO | **Michael Erickson, PhD** — 2026-05-12부 President & CEO. Mazelsky는 Executive Chair로 이동, 2027-05 AGM 이후 완전 퇴임 예정 (2026-01-13 공시) |
| 현 CFO | **Andrew Emerson** / 재직 1년(2025-03~). 이전 CFO Brian McKeon(2014~2025) 은퇴 |
| 자사주 보유 | Mazelsky 직접 보유 공시상 소규모(0.1% 수준, proxy 기준) — 전형적 전문경영 CEO로 창업자 지분 유형은 아님 |
| 위기 대응 | (1) 2019년 전임 CEO Jonathan Ayers **의료 사유 사임**(2019-06-27 자전거 사고로 척수손상 → 7월 의료 휴직 공시 → 10/24 사임 발표 → 11/1 Mazelsky permanent). Mazelsky는 2012년 입사 내부 승진자(前 EVP North American Companion Animal Commercial). **4개월 내 내부 승계**로 전환 잡음 최소화. Ayers는 2024-11-08 이사회·finance committee에서 완전 사임. (2) COVID 충격 직후 FY20 매출 +17% 성장 방어(반려동물 방문 일시 급감을 원격 진단·telemedicine 통합으로 offset) |
| 인상적 문장 | (Q4 2025 컨콜, 2026-02-02) Mazelsky — "Diagnostic frequency +1.0% and diagnostic utilization +7.0% more than offset negative clinical visit growth (-1.5%) in Q4 2025" — 방문수 마이너스 구간에서도 **검사 빈도·단가 상향** 으로 상쇄되는 razor-blade 구조의 자신감 |

## 5. 산업 지도

| 항목 | 내용 |
| ------ | ------ |
| 주요 경쟁사 | Zoetis(Vetscan 장비), Mars Petcare(Heska 2023 인수 + Antech 레퍼런스 랩), Thermo Fisher, bioMérieux, FUJIFILM |
| 시장 집중도 | 상위 5사 ~60%. **IDEXX 단독 ~45%** — 독점에 가까운 리더 |
| 산업 성장률 | 수의 진단 글로벌 CAGR ~7% (2023~2028, Kalorama). 선진국 반려동물 인구·1인당 지출 증가 드라이버 |
| IDEXX 위치 | **지배적 리더(Dominant Leader)**. 분석장비 설치기반 압도적, 레퍼런스 랩 네트워크 규모 차별 — **배급망·설치기반·소모품 잠금** 3중 해자. Mars의 Heska+Antech 통합이 유일 구조적 도전 |

## 6. Fisher 15 정량 5개

| # | 기준 | 지표 | 판정 | 근거 |
| --- | ------ | ------ | ------ | ------ |
| 1 | 매출 성장 잠재력 | 5년 CAGR +7.6%, FY25 +10.4% 재가속, FY26 가이던스 organic +8~10% | **PASS** | 산업 성장률(7%) 대비 동등~상회. 프리미엄 설치기반 +12%, 검사 utilization +7%가 구조적 드라이버 |
| 3 | R&D 투입 대비 성과 | R&D 개시 약 4~5%/매출(10-K 기준). 신제품 — inVue Dx(2024), ProCyte One(2022), Cornerstone SW 업데이트 출시 지속 | **PASS** | 제품 출시 주기 일관, 설치기반 갱신 수요 재창출 |
| 5 | 충분한 이익률 | EBIT Margin 31.6% | **PASS** | Zoetis(30%대)와 동급, Mars/Heska 미공개. 수의 진단 업계 최상위 |
| 6 | 이익률 유지/개선 | EBIT Margin 29.0%(FY21) → 31.6%(FY25) — 소폭 확대. FY22 dip 후 복원 | **PASS** | 5년간 단조 확대. 소모품 믹스·프리미엄 instrument placement이 구조 드라이버 |
| 10 | 원가/회계 관리 | CFO/NI 1.05~1.12x, FY22 0.80x 일시 저하 후 복원. 재고·매출채권 회전 안정 | **PASS** | 회계 잡음 없음. FY22 dip은 재고 정상화 과정으로 설명 가능 |

**정량 5개 요약: 5/5 PASS.** Deep Dive 진입 기준(PASS ≥ 3) 강하게 충족.

## 7. 밸류에이션 현재 위치

| 지표 | 값 | 해석 |
| ------ | ----- | ------ |
| 주가 추이 | 5년 고점 ~$707(2021), 2023~2024 횡보 $450~640, 현재 $558(2026-03-27) | 고점 대비 -21%, 횡보 구간 중립. 2026 YTD -14% |
| 시가총액 | ~$45.2B (주식수 81.0M × $558) | — |
| PER (현재) | ~42.7x | 프리미엄 구간. 성장률 +10% 대비 높음. 단 ROIC 52% 반영 |
| EV/EBIT | ~33x (순현금 조정 미반영) | 고퀄 compounder 벤치마크 내 |
| PBR | ~28x | 자산경량 사업 특성(대차대조표 소형) |
| FCF Yield | 2.34% | 고평가 구간. 성장·복리 속도가 yield 희석 |

> 피셔식 10년 기대수익률 계산은 Deep Stream C에서 수행. 현 멀티플은 "compounder 프리미엄" 구간으로 단순 저PER 판단 금지 (N+1차항 논리).

## 8. 1차 가설 + 리스크 톱3

### 1차 가설

IDEXX Laboratories는 글로벌 수의 진단 시장의 **45% 점유 독점적 리더**로, CAG Diagnostics recurring 매출(전체의 ~85~90%)·프리미엄 설치기반 확장·레퍼런스 랩 네트워크가 결합된 razor-blade 구조를 보유하고 있어 반려동물 방문수가 마이너스로 꺾여도 **검사 빈도·단가·믹스 상향** 으로 7~10%대 organic 성장을 유지하고 있다. 앞으로 3~5년간 ProCyte One·inVue Dx 등 신장비 교체 주기와 신흥시장(APAC·EU) 침투가 추가 드라이버가 될 수 있으며, 2026-05 예정 CEO 교체가 Mars(Heska+Antech) 통합 도전에 대한 대응 전략 분수령으로 작용할 것으로 보인다.

### 리스크 톱3

| 순위 | 리스크 | 발생 시 영향 | 관찰 지표 |
| ------ | -------- | -------------- | ----------- |
| 1 | **FTC·독과점 소송 확장**: 2013 FTC 유통 배타성 합의 존속 + 2022 class-action(pet owner/vet practice)의 anti-competitive pricing 청구 진행 중 | 소모품 가격 결정력 훼손 → GM 압박 + 벌과금 가능 | 소송 진행 상황, 분기별 소모품 GM 변동, FTC 추가 inquiry 여부 |
| 2 | **미국 반려동물 방문수 지속 하락**: 2022 -3.5%, 2023 -1.4%, 2024 -2.6%, 2025 -3.1%; 2026 가이던스 -2% 반영 | 검사 빈도·단가 상향이 방문 감소를 지속적으로 offset 못 할 경우 CAG 8~10% 성장 가이던스 미달 | 분기별 US same-store visit 추이, CAG Dx recurring organic growth, 프리미엄 설치기반 성장률 |
| 3 | **경영진 쌍방 전환기**: CFO Emerson(2025-03, 재직 1년) + CEO 승계(2026-05-12 Erickson 취임, Mazelsky는 2027-05까지 Executive Chair) 연속 교체. *단, Erickson은 2011년 입사 내부 승진자(현 EVP/GM Global POC Diagnostics & Telemedicine, McKinsey Associate Principal 출신, PhD). 2019 Ayers→Mazelsky도 내부 승계였던 점과 함께 **내부 pipeline 기반 계획된 승계** 구조* | 자본배분 정책·M&A 대응·가이던스 정확도 리스크는 여전. Mars의 Heska+Antech 공세 대응 전략 연속성은 내부 승진자라는 점에서 일부 완화 | Erickson 첫 분기 가이던스(2026 Q2 실적), 자본환원(자사주) 정책 변화, 인접 M&A 시도 |

## 9. (배치 모드) 배치 비교 코멘트

IDXX + ALGN + VLTO 3개 대비:

- **IDXX**: 정량 5/5 PASS, ROIC 52% — 3종목 중 품질 최상위. 경영진 쌍방 교체가 유일 흠.
- **ALGN**: 성장·마진 동시 둔화 — Fisher 프레임 궤적에서 이탈 의심.
- **VLTO**: 품질 우수하나 상장 2.5년으로 유니버스 게이트 미달.

상대 서열: **IDXX > VLTO > ALGN** (정량·해자·경영 연속성 종합).

## 10. 판정

**Deep Dive 진입** | 확신도: **중간**

| 근거 | 내용 |
| ------ | ------ |
| 유니버스 | 조건부 PASS (경영진 쌍방 교체기) |
| 사업모델 | razor-blade + 레퍼런스 랩 네트워크, 2분 테스트 명료 |
| 정량 5개 | 5/5 PASS (기준 ≥ 3 강하게 충족) |
| 가설 강도 | 45% 독점 + 방문수 마이너스 흡수 + 검사 믹스 상향 — 내러티브 일관 |
| 밸류에이션 | PER 43x·FCF yield 2.3% — 프리미엄. Deep에서 10년 기대수익률로 재판정 |

**확신도가 "중간"인 이유:**

- CEO 교체(2026-05 Erickson)·CFO 교체(2025-03 Emerson) 쌍방 전환기가 13년을 아우르는 경영진 연속성 평가를 잠재적 이슈화 *(단, Stream B 2026-04-18 조사에서 Erickson이 2011년 입사 15년차 내부 승진자로 확인 — 연속성 우려는 부분 완화)*
- 미국 반려동물 방문수 마이너스의 구조적 지속 여부는 아직 3~5년 데이터 부족
- 현 멀티플(PER 43x)이 성장 둔화 시 하방 10~15% 재평가 리스크
- *Stream B 중 **2022 class action 대부분 각하**(25주 중 MN/MO/NC 3주만 standing) 확인. 리스크 #1의 하방은 Shallow 시점보다 축소*

**다음 단계:** Deep Dive 진행 중. Stream B(경영진 정성 15조건)에서 Erickson 신임 CEO 배경·전략 시나리오를 조사 중이며 초기 발견은 `research/fisher/deep-dive/IDXX_idexx-laboratories.md` Stream B 섹션 참조. Stream C(밸류에이션)에서 visit 마이너스 -2~-4% 시나리오별 10년 기대수익률을 검증할 것.
