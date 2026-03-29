# 가치평가 정책 카탈로그

이 문서는 기업의 비즈니스 모델과 산업 특성에 따라
가장 적합한 DCF 가치평가 정책 조합을 제언합니다.

## 1. 기업 유형별 권장 정책 조합

| 유형 | 예시 | pre_maint_oe | terminal | growth |
|:--|:--|:--|:--|:--|
| 고성장 Tech | GOOGL | `ttm` | `gordon` | `avg_oe_3y` |
| 안정 배당주 | KO, KT&G | `avg_3y` | `gordon` | `fixed_0p02` |
| 시클리컬 | 기아 | `normalized_margin:0.08:0.20` | `exit_multiple_7x` | `fixed_0p03` |
| 자본집약형 | 현대차 | `normalized_roic:0.15:0.30` | `exit_multiple_7x` | `fixed_0p02` |
| 턴어라운드 | 적자탈출 | `avg_3y` | `exit_multiple_5x` | `fixed_0p05` |

공통: fade=`linear`, shares=`avg_5y`.
시클리컬/자본집약: 할인율 10~12%, 예측기간 5년.
고성장/안정: 할인율 7~10%, 예측기간 5~10년.

---

## 2. 정책별 상세 가이드

### A. Pre-Maintenance OE (기초 이익 설정)

과거 실적 중 어느 시점의 데이터를 미래 예측의 출발점으로 삼을지 결정합니다.

- `ttm`: 현재(TTM) 실적이 미래에도 지속될 가능성이 높을 때.
- `avg_3y`: 최근 3년 평균치로 단기 변동성을 제거.
- `normalized_margin:<m>:<r>`: 과거 평균 마진율을 현재 매출에 적용.
  예: `normalized_margin:0.08:0.20` (마진 8%, 재투자율 20%)
- `normalized_roic:<roic>:<r>`: 자본 효율성(ROIC) 회귀 가정.
  예: `normalized_roic:0.15:0.30` (ROIC 15%, 재투자율 30%)

### B. Terminal Value (영구 가치 계산)

예측 기간(5~10년) 이후의 기업 가치를 산정하는 방식입니다.

- `gordon`: 영구 성장률(`g_terminal`) 가정. 경제 성장률 수준.
- `exit_multiple_Nx`: 마지막 해 이익에 배수를 곱하여 산정.
  시클리컬 기업의 과대평가 방지에 탁월.

### C. Growth & Fade (성장률 및 감쇄)

- `growth`: 초기 성장률. `avg_oe_3y` 또는 `fixed_0p03` 등.
- `fade`: 초기→영구 성장률 수렴 방식. 보통 `linear`.

---

## 3. 시나리오 설정 단계

1. **기업 분석**: 시클리컬인가? 성장주인가?
2. **유형 선택**: 위 카탈로그에서 가장 유사한 유형 선택.
3. **변수 조정**:
   - Bull: 낙관적 마진율 + 높은 Exit Multiple
   - Base: 평균 마진율 + 평균 Exit Multiple
   - Bear: 보수적 마진율 + 낮은 Exit Multiple
4. **검증**: 산출된 가치 밴드가 역사적 주가 범위와 부합하는지 확인.
