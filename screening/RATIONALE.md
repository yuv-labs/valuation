# Screening Design Rationale

## 용어 사전

| 약어 | 한글 | 계산 |
| --- | --- | --- |
| ROIC | 투하자본수익률 | 영업이익 / 투하자본 |
| FCF | 잉여현금흐름 | 영업현금흐름 − Capex |
| Gross margin | 매출총이익률 | (매출 − 매출원가) / 매출 |
| SGA | 판매관리비 | Selling, General & Administrative |
| Debt-to-equity | 부채비율 | 총부채 / 자기자본 |
| Capex | 자본지출 | Capital Expenditure |
| Depreciation | 감가상각비 | |
| PE | 주가수익비율 | 주가 / 주당순이익 |
| FCF yield | 잉여현금흐름 수익률 | FCF / 시가총액 |
| ROA | 총자산수익률 | 순이익 / 총자산 |

## 스크리닝 구조 (v2, 2026-04-19)

### Gate → Label → Score → Rank

기존 Track A(해자 필터) → Track B(기회 필터) 파이프라인을 폐지하고, Gold 패널에서 계산된 gate/track/score 체계로 전환.

1. **Gate** (Gold `gate_pass`): trust_score >= 3, debt/assets <= 0.8, 연속 ROIC 음수 아님, 시총 >= 파라미터. 미통과 = 제외.
2. **Track Label** (Gold `track_signal`): ROIC 추세, 재투자율, 매출 CAGR 3축으로 buffett / fisher / mixed 자동 분류.
3. **Quant Score** (Gold): Fisher 정량 5개 + Buffett 정량 5개를 각각 0/1/2 티어 x 가중치로 0-22점 산출.
4. **Supplemental Score** (run.py): moat_score, fear_score, opportunity_score를 보조 컬럼으로 계산.
5. **Rank**: Fisher 기업은 fisher_quant_score, Buffett 기업은 buffett_quant_score, Mixed는 max(둘)로 정렬.

### 왜 전환했는가

기존 해자 필터 체인(MoatExistence → MoatHealth → Opportunity)은 Buffett형 현금 회수 기업에 최적화되어 있어, Fisher형 성장주가 구조적으로 탈락했다. Gate + Track Label 체계는 두 투자 철학을 동시에 수용한다.

### 실무 워크플로

1. **스크리닝 (코드)**: gate → track label → quant score → 상위 N개 추출
2. **Shallow Dive (AI + 사람)**: 추출된 후보에 대해 Phase 1-11 실행. 트랙 확정 + Deep 진입 여부 판단.
3. **Deep Dive (AI + 사람)**: 확정된 트랙의 Deep playbook 실행.

## 시가총액 기준

| 시장 | 기준 | 근거 |
| --- | --- | --- |
| US | $2B | S&P 500급 유동성, 소형주 노이즈 제거 |
| KR | ₩300B | 중형 우량주 포괄 (에스엘, 에스원 등 3000억대 moat 기업) |

KR 기준은 당초 ₩500B(5000억)이었으나, 시총 3000억~5000억 구간에
경쟁력 있는 중형주가 다수 존재하여 ₩300B로 하향.

## 참고

- knowledge/현대_투자환경_안전마진.md
- knowledge/워런_버핏_경제적해자.md (경제적 해자, 오너 어닝)
- knowledge/경쟁력_분석.md (ROA 선호 이유, 기술력의 함정)
- knowledge/벤저민_그레이엄_안전마진.md (시나리오별 가치평가)
