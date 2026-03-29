# 가치평가 정책 카탈로그 (Valuation Policy Catalog)

이 문서는 기업의 비즈니스 모델과 산업 특성에 따라 가장 적합한 DCF 가치평가 정책 조합을 제언합니다.

## 1. 기업 유형별 권장 정책 조합

| 기업 유형 | 예시 종목 | pre_maint_oe | terminal | growth | fade | 할인율 | 예측기간 |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **고성장 Tech** | GOOGL, MSFT | `ttm` | `gordon` | `avg_oe_3y` | `linear` | 8~10% | 10년 |
| **안정 배당주** | KO, PG, KT&G | `avg_3y` | `gordon` | `fixed_0p02` | `linear` | 7~8% | 5~7년 |
| **시클리컬 (제조)** | 기아, POSCO | `normalized_margin` | `exit_multiple` | `fixed_0p03` | `linear` | 10~12% | 5년 |
| **자본집약형** | 현대차, 중공업 | `normalized_roic` | `exit_multiple` | `fixed_0p02` | `linear` | 10~12% | 5년 |
| **턴어라운드** | 적자탈출 기업 | `avg_3y` | `exit_multiple` | `fixed_0p05` | `linear` | 12~15% | 5년 |

---

## 2. 정책별 상세 가이드

### A. Pre-Maintenance OE (기초 이익 설정)
과거 실적 중 어느 시점의 데이터를 미래 예측의 출발점으로 삼을지 결정합니다.

*   **`ttm`**: 현재(Trailing 12 Months) 실적이 미래에도 지속될 가능성이 높을 때 사용. (예: 경제적 해자가 확실한 고성장주)
*   **`avg_3y`**: 최근 3년 평균치를 사용하여 단기 변동성을 제거하고 싶을 때 사용. (일반적인 기업에 무난함)
*   **`normalized_margin`**: 매출은 유지되나 마진율이 사이클에 따라 출렁이는 경우, 과거 평균 마진율을 현재 매출에 적용. (예: 자동차, 반도체)
*   **`normalized_roic`**: 기업의 자본 효율성(ROIC)이 일정 수준으로 회귀한다고 가정할 때 사용. (예: 장기 자본 투자가 중요한 장치 산업)

### B. Terminal Value (영구 가치 계산)
예측 기간(5~10년) 이후의 기업 가치를 산정하는 방식입니다.

*   **`gordon` (Gordon Growth Model)**: 기업이 영구적으로 일정 비율(`g_terminal`)만큼 성장한다고 가정. 경제 성장률(2~3%) 수준이 적절함.
*   **`exit_multiple`**: 예측 기간 마지막 해의 이익에 특정 배수(PER/EV/EBITDA 등)를 곱하여 청산 가치를 산정. 시클리컬 기업의 과대평가를 방지하는 데 탁월함.

### C. Growth & Fade (성장률 및 감쇄)
*   **`growth`**: 초기 성장률. 고성장주는 과거 OE 성장률(`avg_oe_3y`)을, 보수적 관점에서는 고정치(`fixed_0p03`)를 사용.
*   **`fade`**: 초기 성장률이 영구 성장률로 수렴하는 방식. 일반적으로 `linear`를 사용.

---

## 3. 시나리오 설정 단계 (Example)

1.  **기업 분석**: 시클리컬인가? 성장주인가?
2.  **유형 선택**: 위 카탈로그에서 가장 유사한 유형 선택.
3.  **변수 조정**:
    *   **Bull**: 낙관적 마진율 + 높은 Exit Multiple
    *   **Base**: 평균 마진율 + 평균 Exit Multiple
    *   **Bear**: 보수적 마진율 + 낮은 Exit Multiple
4.  **검증**: 산출된 가치 밴드가 역사적 주가 범위와 상식적으로 부합하는지 확인.
