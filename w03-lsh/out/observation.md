# Week 03 observations

## Task 1
각 row에서 hash 값을 한 번 계산한 뒤 그 row를 포함하는 모든 column의 최솟값을 갱신했다. column마다 전체 matrix를 다시 읽으면 대용량 입력을 반복해서 읽어야 하므로 한 번의 row 순회가 적합하다.
signature 길이가 bands로 나누어떨어지지 않으면 나머지 row를 앞쪽 band에 하나씩 배분한다. 모든 row를 사용하며 빈 band는 허용하지 않는다.
S1–S4는 단 두 hash에서 모두 일치해 estimate가 1.0이지만 실제 교집합/합집합은 2/3이다. 짧은 signature의 표본 오차이며, hash 수를 늘리면 오차가 대략 1/√n로 줄지만 계산량과 signature 메모리는 n에 비례해 증가한다.

## Task 2
로컬 Windows PC의 i7-12700F / 물리 RAM 31.86 GiB에서 250–8,000의 6개 크기(32배 범위)를 측정했다. Codex와 Python이 실행 중이었으며 다른 앱은 확인하지 않았다. 측정상 최초 LSH 우세 n은 500으로, crossover는 250 < n ≤ 500 구간이다(정확한 n은 중간 크기 추가 측정 필요).
doubling n의 brute runtime 비율은 3.939, 4.164, 4.184, 4.015, 4.250배(평균 4.111), 지수는 1.978–2.088로 약 O(n²)에 부합했다. 최대 n=8,000의 peak는 brute 0.069 MiB / LSH 29.697 MiB이며, 별도 tracemalloc 실행의 추가 Python 할당량이므로 입력 문서와 전체 프로세스 RAM은 제외한다.
n=8,000에서 brute 실행만 131.39초(LSH 5.05초)로 1분을 넘겨 시간 대기가 먼저 불편한 기준에 도달했다. n=4,000에서도 전체 측정은 87.42초였지만 brute 자체는 30.91초였으므로 메모리 추적 비용으로 인한 대기와 구분했다. 작은 n에서는 LSH의 row 인덱싱·128개 hash·32개 band bucket 구축 비용이 비교 절약보다 크다.

## Task 3
n=128, b=32, r=128/32=4이며 step=(1/32)^(1/4)=0.420448, P(candidate|s=0.6)=1−(1−0.6^4)^32=0.988224이다. threshold 0.6보다 아래에 step을 두어 경계 근처의 유사 쌍을 놓칠 확률을 줄였다.
hash 수를 유지하고 b=16, r=8로 바꾸면 step=0.707107, P(s=0.6)=0.237400이며 실제 recall은 94/121=77.69%로 떨어졌다. 최종 b=32는 120/121=99.17% recall, 100% precision, 123 comparisons, 99.9945% avoided로 Strong 기준을 만족했다.
benchmark의 comparison 점수에는 hashing과 bucket 비용이 빠지지만 출력 wall time에는 포함된다. 큰 어휘·많은 문서에서는 row membership 검사, 128개 hash의 signature 계산·저장 및 bucket 메모리가 커지므로 similarity 호출 수만으로 실제 시간과 메모리 효율을 판단할 수 없다.
