# Algorithm Evaluation Report
Generated on: 2025-10-17 23:36:44

## Summary
| Algorithm | Status | Hard Constraints | AI-Based | Fitness Score | Objective Achievement | Algorithm Nature |
|-----------|--------|------------------|----------|---------------|------------------------|-----------------|
| simplex | FAIL | FAIL | FAIL | 0.00 | FAIL | FAIL |
| genetic_algorithm | PASS | PASS | PASS | 100.00 | PARTIAL | PASS |
| simulated_annealing | PASS | PASS | PASS | 100.00 | PARTIAL | PASS |
| tabu_search | PASS | PASS | PARTIAL | 100.00 | PARTIAL | PASS |
| cp_sat | PASS | PASS | PASS | 100.00 | PARTIAL | PASS |
| lexicographic | PASS | PASS | FAIL | 100.00 | PARTIAL | PASS |
| dynamic_programming | PASS | PASS | PASS | 100.00 | PARTIAL | PASS |


## simplex
**Status:** failed
**Error:** (builtins.TypeError) keys must be str, int, float, bool or None, not tuple
[SQL: UPDATE algorithm_runs SET status=$1::VARCHAR, result=$2::JSON, execution_time=$3::FLOAT, completed_at=$4::TIMESTAMP WITH TIME ZONE WHERE algorithm_runs.id = $5::INTEGER]
[parameters: [{'status': 'completed', 'execution_time': 0.27037477493286133, 'completed_at': datetime.datetime(2025, 10, 17, 23, 32, 43, 635305), 'result': {'assign ... (30148 characters truncated) ... None}, 'solution': {'total_gaps': None}}, 'policy_summary': {'lists': {'schedule': {}, 'assignments': {}, 'solution': {}}}}, 'algorithm_runs_id': 506}]]

## genetic_algorithm
**Execution Time:** 239.94 seconds
**Schedule Count:** 90

### Hard Constraints
**Result:** PASS - No hard constraints detected

### AI Features
**Result:** PASS - Fully AI-based with 8 AI features

### Fitness Score
**Score:** 100

### Objective Achievement
**Result:** PARTIAL - Schedule generated but no explicit fitness metrics

### Algorithm Nature
**Result:** PASS - Algorithm works according to its theoretical nature

### Improvement Recommendations
- **Objective Achievement:** Enhance objective achievement by focusing on the core goals of the algorithm and ensuring all constraints are properly addressed.

## simulated_annealing
**Execution Time:** 0.21 seconds
**Schedule Count:** 90

### Hard Constraints
**Result:** PASS - No hard constraints detected

### AI Features
**Result:** PASS - Fully AI-based with 6 AI features

### Fitness Score
**Score:** 100

### Objective Achievement
**Result:** PARTIAL - Schedule generated but no explicit fitness metrics

### Algorithm Nature
**Result:** PASS - Algorithm works according to its theoretical nature

### Improvement Recommendations
- **Objective Achievement:** Enhance objective achievement by focusing on the core goals of the algorithm and ensuring all constraints are properly addressed.

## tabu_search
**Execution Time:** 0.06 seconds
**Schedule Count:** 90

### Hard Constraints
**Result:** PASS - No hard constraints detected

### AI Features
**Result:** PARTIAL - AI-based with 4 AI features

### Fitness Score
**Score:** 100

### Objective Achievement
**Result:** PARTIAL - Schedule generated but no explicit fitness metrics

### Algorithm Nature
**Result:** PASS - Algorithm works according to its theoretical nature

### Improvement Recommendations
- **AI Features:** Enhance AI capabilities by adding more intelligent features like adaptive parameters, learning mechanisms, and pattern recognition.
- **Objective Achievement:** Enhance objective achievement by focusing on the core goals of the algorithm and ensuring all constraints are properly addressed.

## cp_sat
**Execution Time:** 0.05 seconds
**Schedule Count:** 90

### Hard Constraints
**Result:** PASS - No hard constraints detected

### AI Features
**Result:** PASS - Fully AI-based with 7 AI features

### Fitness Score
**Score:** 100

### Objective Achievement
**Result:** PARTIAL - Schedule generated but no explicit fitness metrics

### Algorithm Nature
**Result:** PASS - Algorithm works according to its theoretical nature

### Improvement Recommendations
- **Objective Achievement:** Enhance objective achievement by focusing on the core goals of the algorithm and ensuring all constraints are properly addressed.

## lexicographic
**Execution Time:** 0.35 seconds
**Schedule Count:** 90

### Hard Constraints
**Result:** PASS - No hard constraints detected

### AI Features
**Result:** FAIL - Not AI-based

### Fitness Score
**Score:** 100

### Objective Achievement
**Result:** PARTIAL - Schedule generated but no explicit fitness metrics

### Algorithm Nature
**Result:** PASS - Algorithm works according to its theoretical nature

### Improvement Recommendations
- **AI Features:** Enhance AI capabilities by adding more intelligent features like adaptive parameters, learning mechanisms, and pattern recognition.
- **Objective Achievement:** Enhance objective achievement by focusing on the core goals of the algorithm and ensuring all constraints are properly addressed.

## dynamic_programming
**Execution Time:** 0.05 seconds
**Schedule Count:** 90

### Hard Constraints
**Result:** PASS - No hard constraints detected

### AI Features
**Result:** PASS - Fully AI-based with 18 AI features

### Fitness Score
**Score:** 100

### Objective Achievement
**Result:** PARTIAL - Schedule generated but no explicit fitness metrics

### Algorithm Nature
**Result:** PASS - Algorithm works according to its theoretical nature

### Improvement Recommendations
- **Objective Achievement:** Enhance objective achievement by focusing on the core goals of the algorithm and ensuring all constraints are properly addressed.

## Overall Recommendations
2. **AI Features:** Develop a common AI framework that can be integrated into all algorithms, focusing on adaptive parameters, learning mechanisms, and pattern recognition.
3. **Fitness Scoring:** Standardize the fitness scoring system across all algorithms to ensure consistent evaluation and comparison.
4. **Integration:** Ensure seamless integration between algorithms to allow for hybrid approaches that combine the strengths of multiple algorithms.
5. **Documentation:** Improve documentation of algorithm parameters, features, and expected behavior to facilitate better understanding and usage.