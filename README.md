# Yaskawa GP35L 로봇 3D → Unity 관절 제어 프로젝트

최종 업데이트: 2026-09-08

## 1. 프로젝트 목표

`C:\Users\Administrator\Downloads\GP35L_3D` 안에 있는 야스카와(Motoman) **GP35L** 6축 수직다관절 로봇의 CAD 파일(STEP/IGES/shrink_wrap)을 Unity로 임포트하고, 터틀봇/ROS 스타일로 **관절각을 조절**할 수 있게 만드는 프로젝트.

총 3가지 제어 방식을 모두 구현하는 것을 목표로 함:

1. **C# 스크립트 + 슬라이더 UI** — 씬에서 직접 각 관절각 조정
2. **Unity ArticulationBody** — 관절 물리/충돌이 포함된 버전
3. **ROS2 연동** — Unity Robotics Hub / ROS-TCP-Connector 로 joint_state 제어

## 2. 작업 환경

| 항목 | 구성 |
|---|---|
| OS | Windows (win32) |
| FreeCAD | `C:\Users\Administrator\Downloads\FreeCAD_1.1.1-Windows-x86_64-py311\bin\freecad.exe` / `freecadcmd.exe` / `python.exe` |
| Blender | `C:\Program Files\Blender Foundation\Blender 5.2\blender-launcher.exe` |
| Unity | Unity 2022.3.62f3, Unity 6000.3.20f1 (Editor 설치는 Unity Hub `C:\Program Files\Unity Hub`) |
| 프로젝트 작업공간 | `C:\Users\Administrator\Projects\GP35L_Unity` |
| 원본 데이터 | `C:\Users\Administrator\Downloads\GP35L_3D` |

## 3. 원본 파일 구조

```
GP35L_3D/
├── iges/          # IGES 개별 파트 7개 (base_axis, s_axis, l_axis, u_axis, r_axis, b_axis, t_axis)
├── step/          # 000_gp35l_asm_asm.stp (어셈블리 전체, 38MB)
└── shrink_wrap/   # Creo(Pro/E) 네이티브 파트 .prt.1 (직접 사용 불가)
```

GP35L 축 명명(야스카와 규약):

| 파트 | 축 | 회전 |
|---|---|---|
| base_axis | 베이스/페데스탈 | 고정 |
| s_axis | J1 (주축/베이스 회전) | 수직 |
| l_axis | J2 (하부 암) | 어깨 |
| u_axis | J3 (상부 암) | 엘보 |
| r_axis | J4 (포어암 롤) | 롤 |
| b_axis | J5 (리스트 피치) | 피치 |
| t_axis | J6 (툴/플랜지) | 롤 |

## 4. 진행 내용 / 검토 결과

### 4.1 FreeCAD STEP 읽기 문제 (해결)

- `App.openDocument()` 로 STEP을 열면 다음 오류 발생:
  `Invalid project file ... ios_base::failbit set : iostream stream error`
- **해결**: `Import.insert(STEP, "docname")` 를 사용하면 정상적으로 읽힘 (객체 120개).
- freecadcmd.exe 대신 FreeCAD 번들 `python.exe`에 `sys.path.insert(0, <bin>)` 후 직접 실행하는 방식이 안정적.

```python
import sys
sys.path.insert(0, r"C:\Users\Administrator\Downloads\FreeCAD_1.1.1-Windows-x86_64-py311\bin")
import FreeCAD as App, Import
doc = App.newDocument("step")
Import.insert(STEP, "step")   # App.openDocument 는 실패
```

### 4.2 STEP 어셈블리 구조 (컴포넌트 매핑)

STEP(120 객체) 안의 주요 컴포넌트와 그 안의 솔리드 라벨:

| 컴포넌트 | 내부 솔리드 라벨 | 부피(mm³) |
|---|---|---|
| BASE_AXIS | `BASE_AXIS` (Part::Feature) | 38,461,507 |
| S_AXIS (App::Part) | `SOLID` | 40,630,171 |
| L_AXIS002 (App::Part) | `L_AXIS`, `L_AXIS001` | 31,592,242 + 1,481,500 |
| U_AXIS (App::Part) | `SOLID001` | 31,356,337 |
| R_AXIS (App::Part) | `SOLID002` | 7,226,285 |
| B_AXIS | `B_AXIS` (Part::Feature) | 3,132,585 |
| T_AXIS (App::Part) | `SOLID003` | 128,532 |

전체 어셈블리 `000_GP35L_ASM_ASM` 바운딩박스(mm):
`X[-412.9, 1545.0]  Y[-0.5, 2091.0]  Z[-257.9, 348.2]`  → 로봇 높이 약 2,091mm

> 각 파트가 **동일한 월드 좌표계를 공유**하고 있어, 회전 축 계산과 조립 위치를 그대로 사용할 수 있음.

### 4.3 좌표계 규약 (중요)

- CAD 좌표계: **Y = 위(수직)**, X = 전후(팔 뻗는 방향), Z = 좌우, 단위는 **mm**.
- IGES에서도 동일한 월드 좌표가 유지됨(모든 파트 bbox가 서로 맞물림).
- 반면 Pro/E가 내보낸 곡면은 대부분 `SurfaceOfRevolution`/BSpline으로, `surf.Axis` / circle `Curve.Axis` 의 방향 벡터는 **수치 오버플로우(garbage/nan)**. 
  → **원심(원의 중심점) 데이터만 신뢰**하고, 동심원 중심점의 최소자승직선 피팅으로 축을 복원하는 방식 사용 (스크립트 11, 12).

### 4.4 관절 축 식별 결과 (핵심)

원형 에지(원의 중심) 클러스터링 결과 관절 축이 확정됨. 모든 좌표는 CAD mm, Y up 기준:

| 관절 | 축 이름 | 축 위치(axis point) | 방향 | 근거 (원형 링 중심) |
|---|---|---|---|---|
| J1 | S | (X=0, Y=임의, Z=0) | **+Y** | BASE: r=290@(0,0,0), r=287, r=248, r=229 | 
| J2 | L | (145, 540, ·) | **+Z** | S_AXIS r=162.5@(145,540), L_AXIS r=150/165/143/133/147/125@(145,540) |
| J3 | U | (145, 1690, ·) | **+Z** | L_AXIS r=125@(145,1690), U_AXIS r=122@(145,1690,86.97), r=79 |
| J4 | R | (·, 1900, 0) | **+X** | R_AXIS r=74 (포어암 관, Y=1900 Z=0), U_AXIS r=127@(318,1900,0), r=81.5@(588,1900,0) |
| J5 | B | (1370, 1900, ·) | **+Z** | B_AXIS r=92@(1370,1900,z), r=91.5 |
| J6 | T | (·, 1900, 0) | **+X** | T_AXIS r=55@(1532,1900,0), r=49, r=25 |

- **리스트 중심(=J4·J5 교점)**: `(1370, 1900, 0)` — J5(Z축)와 J4/J6(X축)이 한 점에서 교차하는 전형적 동심 리스트 구조.
- **툴 플랜지 면**: X≈1545mm (T_AXIS 전면), 플랜지 중심 `(1545, 1900, 0)`.
- J6 축은 J4 축과 같은 기하축(Y=1900, Z=0) 위에 있으며 회전 지점만 다름(각각 1370 / 1545).

## 4.5 분석 결과 파일 (results/)

| 파일 | 내용 |
|---|---|
| `results/joint_axis_lines.txt` | 관절 축 분석 로그 (원형 에지 → 축 클러스터, script 12 출력) |
| `results/circle_axis_clusters.txt` | 원형 에지 클러스터링 로그 (script 11 출력) |
| `results/iges_parts_bbox.txt` | IGES 7파트 bbox/부피 (script 03 출력) |
| `results/step_objects.txt` | STEP 120객체 전체 덤프 (script 10 출력) |
| `results/GP35L_joints.json` | **관절 구성 데이터 (기계가독형, Unity 조립에 직접 사용)** |

> 참고: 분석 시점 이후 원본 데이터가 `Downloads\GP35L_3D`에서 삭제됨.
> 스크립트들은 `GP35L_3D/` (본 폴더 내 사본) 기준으로 재패치되어 있어 재실행 가능.

## 5. 작성된 스크립트 목록

작업공간: `C:\Users\Administrator\Projects\GP35L_Unity\cad\scripts\`

| 파일 | 역할 | 상태 |
|---|---|---|
| `01_inspect_step.py` | STEP을 `App.openDocument`로 열어 객체/솔리드 확인 | 실패 케이스(오류 재현용) |
| `02_inspect_iges.py` | IGES 단일 파트 `Import.insert` 로딩 테스트 | 통과 |
| `03_inspect_all_iges.py` | IGES 7개 파트 bbox/부피 일괄 확인 → 월드좌표 공유 확인 | 통과 |
| `04_find_joint_axes.py` | 솔리드에서 원통 형상 후보 탐색 (중간 단계) | 보완(05~12로 이관) |
| `05_face_types.py` | 면 타입 분포 확인 → `GeomSurfaceOfRevolution` 발견 | 통과 |
| `06_revolution_axes.py` | Revolution 면의 축 추출 시도 (Location/Direction 사용) | 방향 벡터 오버플로우 확인 |
| `07_debug_rev.py` | SurfaceOfRevolution 속성 확인 (Location/BasisCurve만 유효) | 통과 |
| `08_axis3pt.py` | 3점 외접원 재구성 시도 | 부분 실패(파라미터 가정 문제) |
| `09_step_insert.py` | **STEP `Import.insert` 성공 확인** (솔리드/부피 목록) | 통과 (중요) |
| `10_step_objects.py` | STEP 120객체 전체 덤프 (라벨/타입/bbox) | 통과 |
| `11_circle_axes.py` | 원형 에지(GeomCircle) 수집 + 중심 평균 클러스터링 | 통과 |
| `12_axis_lines.py` | **원형 에지 중심점 → 최소자승축 피팅** (핵심 분석) | 통과 |
| `zz_debug.py`, `zz_probe.py` | 임시 디버깅 프로브 | 폐기 대상 |

## 6. Unity 변환 계획 (다음 단계)

### 6.1 파이프라인

```
STEP (000_gp35l_asm.stp)
  → FreeCAD (python) per-component OBJ 익스포트 (월드좌표 mm, 편차 1mm 당각 0.5°)
  → Blender 5.2 (입포트, decimate/정리, 관절 축에 대한 오리진 정렬)
  → FBX/glTF 익스포트 (mm→m 스케일, Y up)
  → Unity:
      Root(base) → S → L → U → R → B → T  계층 구조
      각 노드 트랜스폼 원점 = 관절 축 지점
      메시 자식 = (CAD world 위치 - 관절 지점) 오프셋
```

### 6.2 Unity 계층 구조 (기본 포즈 = CAD 좌표 값)

```
GP35L (root, (0,0,0))
├── base_mesh            # BASE_AXIS 메시, CAD 좌표 그대로
├── S_AXIS (pivot (0, 0, 0))  → J1 라인은 X=Z=0 → pivot (0,0,0), 회전: Y
│   └── s_mesh
├── L_AXIS (pivot (145, 540, 0)) → 회전: Z
│   └── l_mesh
├── U_AXIS (pivot (145, 1690, 0)) → 회전: Z
│   └── u_mesh
├── R_AXIS (pivot (663, 1900, 0)) → 회전: X
│   └── r_mesh
├── B_AXIS (pivot (1370, 1900, 0)) → 회전: Z
│   └── b_mesh
└── T_AXIS (pivot (1545, 1900, 0)) → 회전: X
    └── t_mesh
```

각 관절 회전 축(Unity 로컬 기준): J1=Y, J2=Z, J3=Z, J4=X, J5=Z, J6=X.

## 7. 축소/디테일 관리 (리스트)

- 원본 IGES/STEP 은 20~40MB급 파트가 많아 그대로 쓰면 폴리곤 수가 폭발함.
- FreeCAD `Shape.tessellate(lin_dev, ang_dev)` 로 편차 1mm 이내 재생성 → OBJ.
- 이후 Blender에서 `Decimate`/`Remesh` 로 정리 후 FBX(스케일 0.001)로 내보내기.

## 8. 현재 상태 (Todo)

- [x] STEP 어셈블리 로딩 (Import.insert) 확인
- [x] 컴포넌트 ↔ 솔리드 라벨 매핑
- [x] 좌표계 규약 확인 (Y up, mm, 공통 월드좌표)
- [x] 관절 축 J1~J6 좌표/방향 식별
- [ ] FreeCAD로 per-component OBJ 익스포트 (스크립트 13)
- [ ] Blender 정리/디셰이메이트 + FBX 익스포트
- [ ] Unity 프로젝트 + 계층 구조 조립
- [ ] C# 슬라이더 UI 제어
- [ ] ArticulationBody 버전
- [ ] ROS2(ROS-TCP-Connector) 연동

## 9. 참고 사항

1. **shrink_wrap 파일**은 Creo 네이티브(.prt.1)로 FreeCAD/Blender에서 직접 읽을 수 없음 → `step` 또는 `iges` 폴더 사용.
2. **IGES 개별 파트**도 월드좌표를 공유하므로, STEP가 안 되는 환경에서는 IGES 7파트를 한 문서로 합쳐 동일 좌표 프레임을 구성할 수 있음.
3. 곡면 타입이 `Part::GeomSurfaceOfRevolution` / `Part::GeomBSplineSurface`로 내려오므로, 축 방향은 **원심 신뢰 기반**으로 계산(script 12)해야 안정적.
4. `Base.Vector.scale(x,y,z)` 는 3인자를 요구 — 스칼라곱은 `.multiply()` 사용.
5. Unity 기본 단위는 미터 → FBX 익스포트 시 mm를 0.001로 스케일하거나 Unity 임포트 스케일 팩터 사용.