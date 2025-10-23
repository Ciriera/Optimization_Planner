"""
Automation script to update all algorithms with standardized fitness evaluation.

This script:
1. Scans all algorithm files in app/algorithms/
2. Adds fitness_helpers import if missing
3. Updates evaluate_fitness() method to use standardized FitnessMetrics
4. Creates backup of original files
5. Generates update report

Usage:
    python scripts/update_all_algorithms.py [--dry-run] [--backup]
"""

import os
import re
import shutil
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime


ALGORITHM_DIR = Path("app/algorithms")
BACKUP_DIR = Path("backup/algorithms_" + datetime.now().strftime("%Y%m%d_%H%M%S"))

# Algorithm categories and their specific weight configurations
ALGORITHM_WEIGHTS = {
    # Evolutionary/Genetic Algorithms
    "genetic": {
        "slot_reward": 0.25,
        "coverage": 0.25,
        "gap_penalty": 0.20,
        "duplicate_penalty": 0.15,
        "load_balance": 0.10,
        "late_slot_penalty": 0.05
    },
    
    # Swarm Intelligence
    "swarm": {
        "slot_reward": 0.25,
        "coverage": 0.25,
        "gap_penalty": 0.20,
        "duplicate_penalty": 0.15,
        "load_balance": 0.10,
        "late_slot_penalty": 0.05
    },
    
    # Local Search
    "local_search": {
        "slot_reward": 0.30,
        "coverage": 0.25,
        "gap_penalty": 0.20,
        "duplicate_penalty": 0.15,
        "load_balance": 0.05,
        "late_slot_penalty": 0.05
    },
    
    # Mathematical Programming (ILP, Simplex, etc.)
    "math_prog": {
        "slot_reward": 0.20,
        "coverage": 0.30,
        "gap_penalty": 0.25,
        "duplicate_penalty": 0.15,
        "load_balance": 0.05,
        "late_slot_penalty": 0.05
    },
    
    # Constraint Programming
    "constraint": {
        "slot_reward": 0.20,
        "coverage": 0.30,
        "gap_penalty": 0.25,
        "duplicate_penalty": 0.15,
        "load_balance": 0.05,
        "late_slot_penalty": 0.05
    },
    
    # Search Algorithms
    "search": {
        "slot_reward": 0.25,
        "coverage": 0.25,
        "gap_penalty": 0.20,
        "duplicate_penalty": 0.15,
        "load_balance": 0.10,
        "late_slot_penalty": 0.05
    }
}

# Map algorithm files to categories
ALGORITHM_CATEGORIES = {
    # Genetic/Evolutionary
    "genetic_algorithm.py": "genetic",
    "optimized_genetic_algorithm.py": "genetic",
    "genetic_local_search.py": "genetic",
    "nsga_ii.py": "genetic",
    
    # Swarm
    "pso.py": "swarm",
    "grey_wolf.py": "swarm",
    "ant_colony.py": "swarm",
    "artificial_bee_colony.py": "swarm",
    "bat_algorithm.py": "swarm",
    "firefly.py": "swarm",
    "cuckoo_search.py": "swarm",
    "dragonfly_algorithm.py": "swarm",
    "whale_optimization.py": "swarm",
    
    # Local Search
    "greedy.py": "local_search",
    "tabu_search.py": "local_search",
    "simulated_annealing.py": "local_search",
    "simulated_annealing_new.py": "local_search",
    
    # Mathematical Programming
    "integer_linear_programming.py": "math_prog",
    "simplex_optimized.py": "math_prog",
    "simplex_new.py": "math_prog",
    "real_simplex.py": "math_prog",
    "lexicographic.py": "math_prog",
    
    # Constraint Programming
    "cp_sat.py": "constraint",
    "hybrid_cp_sat_nsga.py": "constraint",
    
    # Search
    "a_star_search.py": "search",
    "branch_and_bound.py": "search",
    "deep_search.py": "search",
    "dynamic_programming.py": "search",
    "harmony_search.py": "search",
}


def generate_fitness_method(category: str, algorithm_name: str) -> str:
    """Generate standardized evaluate_fitness method for an algorithm."""
    
    weights = ALGORITHM_WEIGHTS.get(category, ALGORITHM_WEIGHTS["genetic"])
    
    template = f'''    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
        """
        Standardized fitness evaluation using FitnessMetrics helper.
        
        Category: {category}
        Algorithm: {algorithm_name}
        
        Returns normalized score 0-100 based on:
        - Slot rewards (early hours preferred): {weights["slot_reward"]:.0%}
        - Coverage (81 projects: 50 Ara + 31 Bitirme): {weights["coverage"]:.0%}
        - Gap penalty (no gaps between slots): {weights["gap_penalty"]:.0%}
        - Duplicate penalty (no duplicate projects): {weights["duplicate_penalty"]:.0%}
        - Load balance (±1 tolerance): {weights["load_balance"]:.0%}
        - Late slot penalty (avoid 16:30+): {weights["late_slot_penalty"]:.0%}
        """
        if not solution:
            return float('-inf')

        assignments = solution.get("solution") or solution.get("schedule") or solution.get("assignments") or []
        if not assignments:
            return float('-inf')

        # Create fitness calculator (cached in algorithm instance)
        if not hasattr(self, '_fitness_calculator'):
            try:
                from app.algorithms.fitness_helpers import create_fitness_calculator
                self._fitness_calculator = create_fitness_calculator(
                    self.projects,
                    self.instructors,
                    self.classrooms,
                    self.timeslots
                )
            except Exception:
                # Fallback to basic fitness if helper not available
                return float('-inf')
        
        # Calculate standardized fitness (0-100)
        weights = {{
            "slot_reward": {weights["slot_reward"]},
            "coverage": {weights["coverage"]},
            "gap_penalty": {weights["gap_penalty"]},
            "duplicate_penalty": {weights["duplicate_penalty"]},
            "load_balance": {weights["load_balance"]},
            "late_slot_penalty": {weights["late_slot_penalty"]}
        }}
        
        try:
            fitness = self._fitness_calculator.calculate_total_fitness(assignments, weights)
            
            # Additional bonuses (5% each)
            classroom_switch_score = self._fitness_calculator.calculate_classroom_switch_score(assignments)
            role_score = self._fitness_calculator.calculate_role_compliance_score(assignments)
            
            fitness = fitness + (classroom_switch_score * 0.025) + (role_score * 0.025)
            
            return min(100.0, max(0.0, fitness))
        except Exception as e:
            # Log error and return low fitness
            import logging
            logging.getLogger(__name__).error(f"Fitness calculation error: {{e}}")
            return 0.0
'''
    
    return template


def add_fitness_import(content: str) -> Tuple[str, bool]:
    """Add fitness_helpers import if not present."""
    
    # Check if import already exists
    if "from app.algorithms.fitness_helpers import" in content:
        return content, False
    
    # Find the last import statement
    import_pattern = r'^from app\.algorithms\.base import.*$'
    match = re.search(import_pattern, content, re.MULTILINE)
    
    if match:
        # Insert after base import
        insert_pos = match.end()
        new_import = "\nfrom app.algorithms.fitness_helpers import create_fitness_calculator"
        content = content[:insert_pos] + new_import + content[insert_pos:]
        return content, True
    
    return content, False


def update_algorithm_file(file_path: Path, dry_run: bool = False) -> Dict[str, any]:
    """Update a single algorithm file."""
    
    result = {
        "file": file_path.name,
        "success": False,
        "changes": [],
        "errors": []
    }
    
    try:
        # Read file
        content = file_path.read_text(encoding="utf-8")
        original_content = content
        
        # Determine category
        category = ALGORITHM_CATEGORIES.get(file_path.name, "genetic")
        algorithm_name = file_path.stem
        
        # Add import
        content, import_added = add_fitness_import(content)
        if import_added:
            result["changes"].append("Added fitness_helpers import")
        
        # Find and replace evaluate_fitness method
        # Pattern to match evaluate_fitness method
        fitness_pattern = r'(    def evaluate_fitness\(self.*?\n(?:        .*\n)*?)(?=\n    def |\nclass |\Z)'
        
        match = re.search(fitness_pattern, content, re.MULTILINE | re.DOTALL)
        
        if match:
            # Generate new method
            new_method = generate_fitness_method(category, algorithm_name)
            
            # Replace
            content = content[:match.start()] + new_method + content[match.end():]
            result["changes"].append("Updated evaluate_fitness method")
        else:
            result["errors"].append("evaluate_fitness method not found")
        
        # Write updated content (if not dry-run)
        if not dry_run and content != original_content:
            file_path.write_text(content, encoding="utf-8")
            result["success"] = True
        elif dry_run:
            result["success"] = True
            result["changes"].append("[DRY-RUN] Would update file")
        
    except Exception as e:
        result["errors"].append(str(e))
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Update all algorithms with standardized fitness")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without applying")
    parser.add_argument("--backup", action="store_true", help="Create backup before updating")
    parser.add_argument("--algorithms", nargs="+", help="Specific algorithms to update (default: all)")
    
    args = parser.parse_args()
    
    # Create backup if requested
    if args.backup and not args.dry_run:
        print(f"Creating backup in {BACKUP_DIR}...")
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        for file_path in ALGORITHM_DIR.glob("*.py"):
            if file_path.name in ALGORITHM_CATEGORIES:
                shutil.copy2(file_path, BACKUP_DIR / file_path.name)
        print(f"✓ Backup created")
    
    # Get list of files to update
    if args.algorithms:
        files_to_update = [ALGORITHM_DIR / f"{alg}.py" if not alg.endswith('.py') else ALGORITHM_DIR / alg 
                          for alg in args.algorithms]
    else:
        files_to_update = [ALGORITHM_DIR / fname for fname in ALGORITHM_CATEGORIES.keys()]
    
    # Update each file
    results = []
    print(f"\n{'=' * 60}")
    print(f"Updating {len(files_to_update)} algorithm files...")
    print(f"{'=' * 60}\n")
    
    for file_path in files_to_update:
        if not file_path.exists():
            print(f"⚠  {file_path.name}: File not found")
            continue
        
        print(f"Processing: {file_path.name}...")
        result = update_algorithm_file(file_path, dry_run=args.dry_run)
        results.append(result)
        
        if result["success"]:
            print(f"  ✓ Success: {', '.join(result['changes'])}")
        else:
            print(f"  ✗ Failed: {', '.join(result['errors'])}")
    
    # Summary
    print(f"\n{'=' * 60}")
    print(f"Update Summary")
    print(f"{'=' * 60}")
    
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    
    print(f"Total: {len(results)}")
    print(f"✓ Successful: {successful}")
    print(f"✗ Failed: {failed}")
    
    if args.dry_run:
        print(f"\n⚠ DRY-RUN MODE: No files were modified")
    
    # Write detailed report
    report_path = Path(f"reports/algorithm_update_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("Algorithm Fitness Update Report\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Mode: {'DRY-RUN' if args.dry_run else 'LIVE'}\n")
        f.write(f"Backup: {'YES' if args.backup else 'NO'}\n\n")
        
        for result in results:
            f.write(f"\n{result['file']}:\n")
            f.write(f"  Status: {'SUCCESS' if result['success'] else 'FAILED'}\n")
            if result['changes']:
                f.write(f"  Changes: {', '.join(result['changes'])}\n")
            if result['errors']:
                f.write(f"  Errors: {', '.join(result['errors'])}\n")
    
    print(f"\n✓ Detailed report saved to: {report_path}")


if __name__ == "__main__":
    main()


