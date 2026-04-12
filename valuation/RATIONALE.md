# Valuation Design Rationale

## Owner Earnings 정의

현재 DCF 엔진의 Owner Earnings(OE)는:

```text
OE = CFO_TTM − CAPEX_TTM
```

CFO(Cash Flow from Operations)를 출발점으로 삼는 이유:

- 발생주의 조정이 이미 반영됨 (운전자본 변동, 비현금 비용).
- 순이익보다 조작이 어렵고, 실제 현금 창출력을 더 잘 반영.
- 버핏의 Owner Earnings 개념(순이익 + D&A − CAPEX)과 방향이 같되, D&A를 별도로 더하는 대신 CFO에서 출발하여 계산을 단순화.

## 한계 1: Stock-Based Compensation (SBC) 미반영

CFO에는 SBC가 non-cash expense add-back으로 포함된다.
회계상 SBC는 비현금이지만, 주주에게는 실질적 비용이다:

- 신규 주식 발행 → 기존 주주 희석.
- 기업이 buyback으로 희석을 상쇄하면, 그 buyback 비용이 실질적 현금 유출.

**영향:**
OE가 SBC 금액만큼 과대평가됨. SaaS/Tech 기업처럼 SBC가 매출의 5-10%에 달하는 경우 유의미한 차이.

예시: CFO $10B, CAPEX $200M, SBC $2B인 기업

- 현재 OE: $10B − $0.2B = **$9.8B**
- SBC 조정 OE: $10B − $2B − $0.2B = **$7.8B** (20% 낮음)

**향후 조정 방안:**
파이프라인에 SBC 메트릭을 추가하고 `sbc_adjusted` 정책을 등록하면 해결 가능.

- XBRL 태그: `ShareBasedCompensation` (현금흐름표, YTD), `AllocatedShareBasedCompensationExpense` (손익계산서, fallback)
- 새 정책: Pre-Maintenance OE = CFO_TTM − SBC_TTM
- 등록: `pre_maint_oe: 'sbc_adjusted'`

## 한계 2: buyback_rate와 SBC의 상호작용

DCF 엔진은 두 가지 경로로 주당 가치를 계산한다:

1. OE가 growth_path에 따라 성장.
2. Shares가 buyback_rate에 따라 매년 감소.

`buyback_rate`는 최근 5년간 실제 주식수 변화의 CAGR로, SBC 희석과 buyback 상쇄의 **순효과**를 반영한다. 따라서 shares 경로 자체에 이중 반영은 없다.

그러나 OE 경로에서 SBC가 CFO에 포함된 채로 사용되면:

- OE가 SBC만큼 과대 → OE/share도 과대.
- shares가 줄어들어도, 분자(OE)가 이미 부풀어 있으므로 과대평가가 증폭됨.

**결론:** 기술적 이중 반영(double-counting)은 아니지만, SBC 미차감 상태에서 buyback_rate를 적용하면 낙관적 편향이 강화된다. SBC 조정 OE를 사용하면 이 문제가 해소됨.

## 한계 3: Fiscal Year 라벨링

SEC XBRL의 `fy` 필드는 **filing이 속한 fiscal year**를 나타낸다.
대부분의 기업(12월 결산)에서는 `fy`와 공식 FY가 일치하지만,
비표준 결산 기업에서는 불일치가 발생한다.

예시 (11월 결산 기업):

| SEC fy | fp | end date | 공식 FY |
|--------|----|----------|---------|
| 2025 | FY | 2024-11-29 | FY2024 |
| 2026 | Q1 | 2025-02-28 | Q1 FY2025 |

Gold 패널에서는 `fy`를 `fiscal_year`로 그대로 사용하므로,
리포트 작성 시 `end` 날짜를 기준으로 공식 FY를 판별해야 한다.
