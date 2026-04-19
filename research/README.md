# 투자 리서치 인덱스

## 디렉토리 구조

- **`shallow-dive/`** — **통합 Shallow Dive 산출물** (2026-04-18~). 버핏형·피셔형 트랙 판정은 Phase 10 Track Gate에서. 산출물 YAML frontmatter에 `track_verdict` 명시.
- `buffett/shallow-dive/` — **legacy Buffett Shallow** (2026-04-18 이전. BBWI·KMB·AMAT·ADBE·기아·에스엘). 신규 작성 금지.
- `buffett/deep-dive/` — Buffett 트랙 Deep (DCF 3시나리오 중심). 현재 ADBE.
- `fisher/shallow-dive/` — **legacy Fisher Shallow** (2026-04-18 이전. ONON·IDXX·ALGN·VLTO). 신규 작성 금지.
- `fisher/deep-dive/` — Fisher 트랙 Deep (Stream A~F). 현재 ONON·IDXX.
- `_template.md` — 공통 메타데이터 스캐폴딩
- `192080-KS.md` — 프레임 미배정 단일 리포트
- 프레임·프로세스·템플릿 문서는 `../playbook/` — **통합 Shallow는 `../playbook/SHALLOW_DIVE.md`**, Deep은 `../playbook/{buffett|fisher}/DEEP_DIVE.md`

## 관리 종목

| 티커 | 종목명 | 프레임 | 단계 | 상태 | 한줄 Thesis | 최근 업데이트 |
|------|--------|--------|------|------|-------------|---------------|
| [ADBE](buffett/deep-dive/ADBE_Adobe.md) | Adobe | Buffett | Deep + Monitoring | ✅ 보유 | — | 2026-04-12 |
| [AMAT](buffett/shallow-dive/AMAT_Applied_Materials.md) | Applied Materials | Buffett | Shallow | 🔍 분석중 | — | 2026-04-12 |
| [KMB](buffett/shallow-dive/KMB_Kimberly_Clark.md) | Kimberly-Clark | Buffett | Shallow | 🔍 분석중 | — | 2026-04-11 |
| [000270.KS](buffett/shallow-dive/000270_기아.md) | 기아 | Buffett | Shallow | 🔍 분석중 | — | 2026-04-11 |
| [005850.KS](buffett/shallow-dive/005850_에스엘.md) | 에스엘 | Buffett | Shallow | 🔍 분석중 | — | 2026-04-12 |
| [8111.T](buffett/shallow-dive/8111_Goldwin.md) | Goldwin | Buffett | Shallow | 🔍 분석중 | TNF 영구 상표권 + ROIC 24% 자본 경량 모델, PER 12.7x 일본 디스카운트 | 2026-04-17 |
| [TDC](buffett/shallow-dive/TDC_Teradata.md) | Teradata | Buffett | Shallow | 🔍 분석중 | 전환비용 해자의 depleting asset — P/FCF 8.9x 가치함정 vs 턴어라운드 | 2026-04-17 |
| [AOS](buffett/shallow-dive/AOS_AO_Smith.md) | A.O. Smith | Buffett | Shallow | 🔍 분석중 | 북미 온수기 과점 + ROIC 31% 캐시카우, PER 16.4x 적정가 — Watchlist | 2026-04-17 |
| [IDXX](buffett/shallow-dive/IDXX_IDEXX_Laboratories.md) | IDEXX Laboratories | Buffett | Shallow | 🔍 분석중 | 수의 진단 글로벌 1위, ROIC 44% 최상급 프랜차이즈이나 PER 44x — 품질 프리미엄 vs 고평가 딜레마 | 2026-04-17 |
| [VLTO](buffett/shallow-dive/VLTO_Veralto.md) | Veralto | Buffett | Shallow | 🔍 분석중 | Danaher DNA 산업재 캐시카우, 사업 최상급이나 PER 24x 안전마진 부재 — Watchlist | 2026-04-17 |
| [FTNT](buffett/shallow-dive/FTNT_Fortinet.md) | Fortinet | Buffett | Shallow | 🔍 분석중 | ROIC 58% See's급 프랜차이즈, ASIC 원가해자 최상급이나 PER 34x 낙관 가정 — Watchlist $55~65 | 2026-04-17 |
| [ITT](buffett/shallow-dive/ITT_ITT_Inc.md) | ITT Inc. | Buffett | Shallow | 🔍 분석중 | 전환비용 해자 산업재 ROIC 21%, SPX FLOW $4.8B 인수로 PER 35x — 시너지 전제 고평가, Pro-forma 확인 후 재평가 | 2026-04-17 |
| [192080.KS](192080-KS.md) | 더블유게임즈 | — | 단일 리포트 | 🔍 분석중 | 규제 오버행이 붙은 현금창출주 | 2026-03-30 |
| [ONON](fisher/shallow-dive/ONON_on-holding.md) | On Holding | Fisher | Deep | 🔍 분석중 | Nike 점유율 이전의 프리미엄 러닝 compounder | 2026-04-14 |
| [IDXX](fisher/shallow-dive/IDXX_idexx-laboratories.md) | IDEXX Laboratories | Fisher | Shallow | 🔍 분석중 (Deep 진입 예정) | 45% 점유 수의진단 razor-blade | 2026-04-18 |
| [ALGN](fisher/shallow-dive/ALGN_align-technology.md) | Align Technology | Fisher→Buffett 재분류 | Shallow | ⏸️ 파킹 | Fisher 궤적 이탈, Buffett 저평가 scan 대기 | 2026-04-18 |
| [VLTO](fisher/shallow-dive/VLTO_veralto.md) | Veralto | Fisher | Shallow | ⏸️ 파킹 | Danaher 스핀오프 razor-blade, 상장이력 2.5년 게이트 미달 | 2026-04-18 |
| [BBWI](buffett/shallow-dive/BBWI_Bath_Body_Works.md) | Bath & Body Works | Buffett | Shallow (legacy) | 🔍 분석중 | 브랜드 소비재 저PER, 부채 이슈 | 2026-04 |
| [PM](shallow-dive/PM_Philip_Morris_International.md) | Philip Morris International | **Buffett (4/4 HIGH)** | Shallow (통합) | 🔍 Deep 진입 예정 | Smoke-free 전환(Zyn 67% 점유) + 배당 compounder | 2026-04-18 |
| [RMD](shallow-dive/RMD_resmed.md) | ResMed | **Buffett (3:1 中)** | Shallow (통합) | 🔍 Deep 진입 예정 | CPAP razor-blade, P/E 22x vs 5yr 평균 40x — quality on sale | 2026-04-18 |
| [DECK](shallow-dive/DECK_deckers-outdoor.md) | Deckers Outdoor | **Fisher (3.5:0.5 中上)** | Shallow (통합) | 🔍 Deep 진입 예정 | Hoka + UGG, P/E 14x 디레이팅, ONON 선례 재활용 | 2026-04-18 |
| [PCTY](shallow-dive/PCTY_Paylocity.md) | Paylocity | **Fisher (4/4 中)** | Shallow (통합) | ⏸️ Keep (감속 관찰) | HCM SaaS, 매출 CAGR 25.9%→9% 급감속 — 1~2분기 관찰 | 2026-04-18 |
| [PYPL](shallow-dive/PYPL_paypal.md) | PayPal | **Buffett (3:1 中)** | Deep S1-2 완료 | ⏸️ 파킹 | 해자 건재하나 경영진 트랙레코드 부족(Chriss 2.5yr) — 3-4년 후 재검토 | 2026-04-19 |

## 상태 범례

| 상태 | 의미 |
|------|------|
| 🔍 | 분석중 |
| 👀 | 관심 |
| ✅ | 보유 |
| ❌ | 패스 |
| ⏸️ | 파킹 (외부 이벤트/시간 대기) |

## 단계 범례

| 단계 | 의미 |
|------|------|
| Shallow (legacy) | 2026-04-18 이전 트랙별 Shallow Dive 리포트 |
| Shallow (통합) | 통합 playbook 기반 신규 Shallow, Phase 10 Track Gate로 배정 판정 |
| Deep | Deep Dive 리포트 (배정 트랙 playbook 준수) |
| Monitoring | 편입 후 분기 모니터링 중 |
