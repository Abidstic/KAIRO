# Baseline Models

Four baseline reviewer recommendation algorithms used for comparison against the KAIRO approach.

## Algorithms

| Algorithm | Approach | Reference |
|-----------|----------|-----------|
| **RevFinder** | File-path similarity (LCP, LCSuff, LCSubstr, LCSubseq + Borda fusion) | Thongtanunam et al., SANER 2015 |
| **cHRev** | Comment/contribution history with recency weighting | Zanjani et al., IEEE TSE 2016 |
| **TurnoverRec** | Knowledge distribution and learning opportunity | Mirsaeedi & Rigby, ICSE 2020 |
| **Sofia** | Hybrid: routes to TurnoverRec or cHRev based on file risk | Mirsaeedi & Rigby, ICSE 2020 |

## Prerequisites

### 1. Crawl repository data

Use the GitHub crawler in `data-collection/` to collect repository data:

```bash
cd ../data-collection
python3 main.py --owner expressjs --repo express
```

### 2. Set environment variable

Point to the crawled data directory:

```bash
export DATA_BASE_DIR=/path/to/data-collection/crawled-data
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Interactive mode

```bash
cd src
python3 interactive_manager.py
```

### Command line

```bash
cd src
python3 manager.py --r_owner expressjs --r_name express algo-revFinder
python3 manager.py --r_owner expressjs --r_name express algo-chRev
python3 manager.py --r_owner expressjs --r_name express algo-turnoverRec
python3 manager.py --r_owner expressjs --r_name express algo-sofia
```

### Run evaluation

```bash
python3 manager.py evaluate --r_owner expressjs --r_name express
```

## Evaluation Metrics

Precision@1/3/5/10, Hit Rate@K, MRR, MAP, DCG, algorithm coverage, and score distribution statistics.

Results are saved to `evaluation_results/` as JSON and CSV.

## Pre-computed Results

Pre-computed baseline evaluation results for all subject repositories are in `../results/baseline-models/`.
