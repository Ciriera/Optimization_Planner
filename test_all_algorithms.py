"""
Test script to evaluate multiple algorithms based on specified criteria.

This script tests Real Simplex, Genetic, Simulated Annealing, Tabu Search, CP-SAT, 
Lexicographic and Dynamic Programming algorithms against the following criteria:
1. Hard constraints: Should have none
2. AI-based features: Should be fully AI-based
3. Fitness score: Should be high (80+)
4. Objective function achievement: How well does it meet objectives
5. Algorithm nature: Does it work according to its theoretical design
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# Import the algorithm service
from app.services.algorithm import AlgorithmService
from app.models.algorithm import AlgorithmType
from app.db.base import async_session


class AlgorithmTester:
    """Class to test and evaluate algorithms."""
    
    def __init__(self):
        """Initialize the tester."""
        self.results = {}
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = f"algorithm_test_results_{self.timestamp}"
        os.makedirs(self.output_dir, exist_ok=True)
        
    async def test_algorithm(self, algorithm_type: AlgorithmType, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Test a specific algorithm and evaluate its performance.
        
        Args:
            algorithm_type: The algorithm type to test
            params: Optional parameters for the algorithm
            
        Returns:
            Dict[str, Any]: Test results
        """
        print(f"\n\n{'='*80}")
        print(f"Testing {algorithm_type.value.upper()} algorithm")
        print(f"{'='*80}")
        
        # Run the algorithm
        async with async_session() as db:
            try:
                result, run = await AlgorithmService.run_algorithm(
                    algorithm_type=algorithm_type,
                    data={},  # Empty data will trigger loading from DB
                    params=params
                )
                
                # Extract basic metrics
                execution_time = run.execution_time
                status = run.status
                error = run.error
                
                # Get schedule data
                schedule = result.get("schedule", result.get("assignments", result.get("solution", [])))
                
                # Evaluate hard constraints
                hard_constraints = self._check_hard_constraints(result, schedule)
                
                # Evaluate AI features
                ai_features = self._check_ai_features(algorithm_type, result)
                
                # Calculate fitness score
                fitness_score = self._calculate_fitness_score(result, schedule)
                
                # Evaluate objective achievement
                objective_achievement = self._evaluate_objective_achievement(algorithm_type, result, schedule)
                
                # Check algorithm nature compliance
                algorithm_nature = self._check_algorithm_nature(algorithm_type, result)
                
                # Save detailed results
                detailed_result = {
                    "algorithm_type": algorithm_type.value,
                    "status": status,
                    "error": error,
                    "execution_time": execution_time,
                    "schedule_count": len(schedule) if isinstance(schedule, list) else 0,
                    "hard_constraints": hard_constraints,
                    "ai_features": ai_features,
                    "fitness_score": fitness_score,
                    "objective_achievement": objective_achievement,
                    "algorithm_nature": algorithm_nature,
                    "raw_result": result
                }
                
                # Save to file
                with open(f"{self.output_dir}/{algorithm_type.value}_results.json", "w", encoding="utf-8") as f:
                    json.dump(detailed_result, f, indent=2, default=str)
                
                # Add to results
                self.results[algorithm_type.value] = {
                    "status": status,
                    "error": error,
                    "execution_time": execution_time,
                    "schedule_count": len(schedule) if isinstance(schedule, list) else 0,
                    "hard_constraints": hard_constraints["summary"],
                    "ai_features": ai_features["summary"],
                    "fitness_score": fitness_score["score"],
                    "objective_achievement": objective_achievement["summary"],
                    "algorithm_nature": algorithm_nature["summary"]
                }
                
                return detailed_result
                
            except Exception as e:
                error_result = {
                    "algorithm_type": algorithm_type.value,
                    "status": "failed",
                    "error": str(e),
                    "execution_time": None,
                    "schedule_count": 0,
                    "hard_constraints": {"summary": "Error"},
                    "ai_features": {"summary": "Error"},
                    "fitness_score": {"score": 0},
                    "objective_achievement": {"summary": "Error"},
                    "algorithm_nature": {"summary": "Error"}
                }
                
                self.results[algorithm_type.value] = {
                    "status": "failed",
                    "error": str(e),
                    "execution_time": None,
                    "schedule_count": 0,
                    "hard_constraints": "Error",
                    "ai_features": "Error",
                    "fitness_score": 0,
                    "objective_achievement": "Error",
                    "algorithm_nature": "Error"
                }
                
                return error_result
    
    def _check_hard_constraints(self, result: Dict[str, Any], schedule: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check if there are any hard constraints in the result.
        
        Args:
            result: Algorithm result
            schedule: Schedule data
            
        Returns:
            Dict[str, Any]: Hard constraints evaluation
        """
        hard_constraints = {
            "instructor_conflicts": 0,
            "classroom_conflicts": 0,
            "timeslot_conflicts": 0,
            "late_slots": 0,
            "summary": ""
        }
        
        # Check for explicit constraint violations in result
        if "constraints" in result:
            constraints = result.get("constraints", {})
            hard_constraints["instructor_conflicts"] = constraints.get("instructor_conflicts", 0)
            hard_constraints["classroom_conflicts"] = constraints.get("classroom_conflicts", 0)
            hard_constraints["timeslot_conflicts"] = constraints.get("timeslot_conflicts", 0)
        
        # Check for late slots (after 16:30)
        if "policy_summary" in result:
            policy = result.get("policy_summary", {}).get("lists", {})
            for key, summary in policy.items():
                if "late" in summary:
                    hard_constraints["late_slots"] += summary.get("late", 0)
        
        # Check for gap report
        if "gap_report_service_level" in result:
            gap_report = result.get("gap_report_service_level", {})
            for key, report in gap_report.items():
                if "total_gaps" in report and report["total_gaps"] is not None:
                    hard_constraints["gaps"] = report.get("total_gaps", 0)
        
        # Determine if there are hard constraints
        total_hard_constraints = sum([
            hard_constraints["instructor_conflicts"],
            hard_constraints["classroom_conflicts"],
            hard_constraints["timeslot_conflicts"]
        ])
        
        if total_hard_constraints == 0:
            hard_constraints["summary"] = "PASS - No hard constraints detected"
        else:
            hard_constraints["summary"] = f"FAIL - {total_hard_constraints} hard constraints detected"
        
        return hard_constraints
    
    def _check_ai_features(self, algorithm_type: AlgorithmType, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if the algorithm is fully AI-based.
        
        Args:
            algorithm_type: The algorithm type
            result: Algorithm result
            
        Returns:
            Dict[str, Any]: AI features evaluation
        """
        # Get algorithm info from service
        algorithm_info = AlgorithmService.get_algorithm_info(algorithm_type)
        
        # Extract AI features from description
        description = algorithm_info.get("description", "")
        name = algorithm_info.get("name", "")
        
        ai_features = {
            "ai_based": "🤖" in name or "🤖" in description or "AI-" in name or "AI-" in description,
            "feature_count": 0,
            "features": [],
            "summary": ""
        }
        
        # Count AI features in parameters
        params = algorithm_info.get("parameters", {})
        for param_name, param_info in params.items():
            param_desc = param_info.get("description", "")
            if "🤖 AI FEATURE" in param_desc:
                ai_features["feature_count"] += 1
                feature_num = param_desc.split("🤖 AI FEATURE")[1].split(":")[0].strip()
                feature_desc = param_desc.split(":", 1)[1].strip() if ":" in param_desc else param_desc
                ai_features["features"].append(f"Feature {feature_num}: {feature_desc}")
        
        # Determine if fully AI-based
        if ai_features["ai_based"] and ai_features["feature_count"] >= 5:
            ai_features["summary"] = f"PASS - Fully AI-based with {ai_features['feature_count']} AI features"
        elif ai_features["ai_based"]:
            ai_features["summary"] = f"PARTIAL - AI-based with {ai_features['feature_count']} AI features"
        else:
            ai_features["summary"] = "FAIL - Not AI-based"
        
        return ai_features
    
    def _calculate_fitness_score(self, result: Dict[str, Any], schedule: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate the fitness score of the result.
        
        Args:
            result: Algorithm result
            schedule: Schedule data
            
        Returns:
            Dict[str, Any]: Fitness score evaluation
        """
        fitness = {
            "score": 0,
            "components": {},
            "summary": ""
        }
        
        # Extract fitness score from result
        if "fitness" in result:
            fitness_data = result.get("fitness", {})
            if isinstance(fitness_data, dict):
                fitness["score"] = fitness_data.get("total", 0)
                # Extract components
                for key, value in fitness_data.items():
                    if key != "total":
                        fitness["components"][key] = value
            elif isinstance(fitness_data, (int, float)):
                fitness["score"] = fitness_data
        elif "score" in result:
            fitness["score"] = result.get("score", 0)
        elif "objective_value" in result:
            fitness["score"] = result.get("objective_value", 0)
        
        # If no explicit score, calculate based on schedule size and constraints
        if fitness["score"] == 0 and schedule:
            # Base score from schedule size
            schedule_size = len(schedule)
            fitness["score"] = min(100, max(0, schedule_size * 2))
            
            # Reduce for constraints
            hard_constraints = result.get("constraints", {})
            total_constraints = sum([
                hard_constraints.get("instructor_conflicts", 0),
                hard_constraints.get("classroom_conflicts", 0),
                hard_constraints.get("timeslot_conflicts", 0)
            ])
            fitness["score"] = max(0, fitness["score"] - (total_constraints * 5))
        
        # Determine fitness quality
        if fitness["score"] >= 80:
            fitness["summary"] = f"EXCELLENT - Score: {fitness['score']}"
        elif fitness["score"] >= 60:
            fitness["summary"] = f"GOOD - Score: {fitness['score']}"
        elif fitness["score"] >= 40:
            fitness["summary"] = f"FAIR - Score: {fitness['score']}"
        else:
            fitness["summary"] = f"POOR - Score: {fitness['score']}"
        
        return fitness
    
    def _evaluate_objective_achievement(self, algorithm_type: AlgorithmType, result: Dict[str, Any], schedule: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate how well the algorithm achieves its objectives.
        
        Args:
            algorithm_type: The algorithm type
            result: Algorithm result
            schedule: Schedule data
            
        Returns:
            Dict[str, Any]: Objective achievement evaluation
        """
        objective = {
            "achieved": False,
            "details": {},
            "summary": ""
        }
        
        # Check if schedule is created
        if not schedule:
            objective["summary"] = "FAIL - No schedule generated"
            return objective
        
        # Check schedule coverage
        schedule_size = len(schedule)
        projects_count = len(result.get("projects", []))
        if projects_count > 0:
            coverage = schedule_size / projects_count
            objective["details"]["coverage"] = coverage
            if coverage >= 0.9:
                objective["details"]["coverage_status"] = "Excellent"
            elif coverage >= 0.7:
                objective["details"]["coverage_status"] = "Good"
            else:
                objective["details"]["coverage_status"] = "Poor"
        
        # Check algorithm-specific objectives
        if algorithm_type == AlgorithmType.SIMPLEX:
            # Check for consecutive grouping
            if "consecutive_groups" in result:
                objective["details"]["consecutive_groups"] = result.get("consecutive_groups", 0)
            
            # Check for instructor pairing
            if "pairing_quality" in result:
                objective["details"]["pairing_quality"] = result.get("pairing_quality", 0)
        
        elif algorithm_type == AlgorithmType.GENETIC_ALGORITHM:
            # Check for diversity
            if "diversity" in result:
                objective["details"]["diversity"] = result.get("diversity", 0)
            
            # Check for convergence
            if "convergence" in result:
                objective["details"]["convergence"] = result.get("convergence", 0)
        
        elif algorithm_type == AlgorithmType.NSGA_II:
            # Check for Pareto front
            if "pareto_front" in result:
                objective["details"]["pareto_front_size"] = len(result.get("pareto_front", []))
            
            # Check for strategic pairing
            if "strategic_pairing" in result:
                objective["details"]["strategic_pairing"] = result.get("strategic_pairing", 0)
        
        elif algorithm_type == AlgorithmType.DYNAMIC_PROGRAMMING:
            # Check for aggressive early slot usage
            if "early_slot_usage" in result:
                objective["details"]["early_slot_usage"] = result.get("early_slot_usage", 0)
            
            # Check for adaptive learning
            if "adaptive_learning" in result:
                objective["details"]["adaptive_learning"] = result.get("adaptive_learning", 0)
        
        # Determine overall objective achievement
        if schedule_size > 0:
            if "fitness" in result or "score" in result or "objective_value" in result:
                objective["achieved"] = True
                objective["summary"] = "PASS - Objectives achieved"
            else:
                objective["achieved"] = True
                objective["summary"] = "PARTIAL - Schedule generated but no explicit fitness metrics"
        else:
            objective["summary"] = "FAIL - No schedule generated"
        
        return objective
    
    def _check_algorithm_nature(self, algorithm_type: AlgorithmType, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if the algorithm works according to its theoretical nature.
        
        Args:
            algorithm_type: The algorithm type
            result: Algorithm result
            
        Returns:
            Dict[str, Any]: Algorithm nature evaluation
        """
        nature = {
            "compliant": False,
            "details": {},
            "summary": ""
        }
        
        # Check algorithm-specific nature
        if algorithm_type == AlgorithmType.SIMPLEX:
            # Check for linear programming characteristics
            if "iterations" in result:
                nature["details"]["iterations"] = result.get("iterations", 0)
                nature["compliant"] = True
        
        elif algorithm_type == AlgorithmType.GENETIC_ALGORITHM:
            # Check for evolutionary characteristics
            if "generations" in result:
                nature["details"]["generations"] = result.get("generations", 0)
                nature["compliant"] = True
            if "population_size" in result:
                nature["details"]["population_size"] = result.get("population_size", 0)
            if "mutation_rate" in result:
                nature["details"]["mutation_rate"] = result.get("mutation_rate", 0)
        
        elif algorithm_type == AlgorithmType.SIMULATED_ANNEALING:
            # Check for annealing characteristics
            if "temperature" in result:
                nature["details"]["final_temperature"] = result.get("temperature", 0)
                nature["compliant"] = True
            if "iterations" in result:
                nature["details"]["iterations"] = result.get("iterations", 0)
        
        elif algorithm_type == AlgorithmType.TABU_SEARCH:
            # Check for tabu characteristics
            if "tabu_list" in result:
                nature["details"]["tabu_list_size"] = len(result.get("tabu_list", []))
                nature["compliant"] = True
            if "iterations" in result:
                nature["details"]["iterations"] = result.get("iterations", 0)
        
        elif algorithm_type == AlgorithmType.CP_SAT:
            # Check for constraint programming characteristics
            if "solver_time" in result:
                nature["details"]["solver_time"] = result.get("solver_time", 0)
                nature["compliant"] = True
            if "variables" in result:
                nature["details"]["variables"] = result.get("variables", 0)
            if "constraints" in result:
                nature["details"]["constraints_count"] = len(result.get("constraints", {}))
        
        elif algorithm_type == AlgorithmType.NSGA_II:
            # Check for multi-objective characteristics
            if "pareto_front" in result:
                nature["details"]["pareto_front_size"] = len(result.get("pareto_front", []))
                nature["compliant"] = True
            if "objectives" in result:
                nature["details"]["objectives_count"] = len(result.get("objectives", []))
        
        elif algorithm_type == AlgorithmType.DYNAMIC_PROGRAMMING:
            # Check for dynamic programming characteristics
            if "states" in result:
                nature["details"]["states"] = result.get("states", 0)
                nature["compliant"] = True
            if "subproblems" in result:
                nature["details"]["subproblems"] = result.get("subproblems", 0)
        
        # If no specific characteristics found, check for schedule generation
        if not nature["compliant"] and "schedule" in result:
            nature["compliant"] = True
            nature["details"]["schedule_generated"] = True
        
        # Determine overall compliance
        if nature["compliant"]:
            nature["summary"] = "PASS - Algorithm works according to its theoretical nature"
        else:
            nature["summary"] = "FAIL - Algorithm does not exhibit expected characteristics"
        
        return nature
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """
        Run tests for all specified algorithms.
        
        Returns:
            Dict[str, Any]: Test results for all algorithms
        """
        # Define algorithms to test
        algorithms = [
            AlgorithmType.SIMPLEX,
            AlgorithmType.GENETIC_ALGORITHM,
            AlgorithmType.SIMULATED_ANNEALING,
            AlgorithmType.TABU_SEARCH,
            AlgorithmType.CP_SAT,
            AlgorithmType.LEXICOGRAPHIC,
            AlgorithmType.DYNAMIC_PROGRAMMING
        ]
        
        # Run tests for each algorithm
        for algorithm in algorithms:
            await self.test_algorithm(algorithm)
        
        # Save summary results
        with open(f"{self.output_dir}/summary_results.json", "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, default=str)
        
        return self.results
    
    def generate_report(self) -> str:
        """
        Generate a human-readable report of the test results.
        
        Returns:
            str: Human-readable report
        """
        report = []
        report.append("# Algorithm Evaluation Report")
        report.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Summary table
        report.append("## Summary")
        report.append("| Algorithm | Status | Hard Constraints | AI-Based | Fitness Score | Objective Achievement | Algorithm Nature |")
        report.append("|-----------|--------|------------------|----------|---------------|------------------------|-----------------|")
        
        for algo, result in self.results.items():
            status = "PASS" if result["status"] == "completed" else "FAIL"
            hard = "PASS" if "PASS" in str(result["hard_constraints"]) else "FAIL"
            ai = "PASS" if "PASS" in str(result["ai_features"]) else ("PARTIAL" if "PARTIAL" in str(result["ai_features"]) else "FAIL")
            fitness = f"{result['fitness_score']:.2f}" if isinstance(result["fitness_score"], (int, float)) else str(result["fitness_score"])
            objective = "PASS" if "PASS" in str(result["objective_achievement"]) else ("PARTIAL" if "PARTIAL" in str(result["objective_achievement"]) else "FAIL")
            nature = "PASS" if "PASS" in str(result["algorithm_nature"]) else "FAIL"
            
            report.append(f"| {algo} | {status} | {hard} | {ai} | {fitness} | {objective} | {nature} |")
        
        report.append("\n")
        
        # Detailed results for each algorithm
        for algo, result in self.results.items():
            report.append(f"## {algo}")
            
            if result["status"] != "completed":
                report.append(f"**Status:** {result['status']}")
                report.append(f"**Error:** {result['error']}")
                report.append("")
                continue
            
            report.append(f"**Execution Time:** {result['execution_time']:.2f} seconds")
            report.append(f"**Schedule Count:** {result['schedule_count']}")
            report.append("")
            
            report.append("### Hard Constraints")
            report.append(f"**Result:** {result['hard_constraints']}")
            report.append("")
            
            report.append("### AI Features")
            report.append(f"**Result:** {result['ai_features']}")
            report.append("")
            
            report.append("### Fitness Score")
            report.append(f"**Score:** {result['fitness_score']}")
            report.append("")
            
            report.append("### Objective Achievement")
            report.append(f"**Result:** {result['objective_achievement']}")
            report.append("")
            
            report.append("### Algorithm Nature")
            report.append(f"**Result:** {result['algorithm_nature']}")
            report.append("")
            
            # Improvement recommendations
            report.append("### Improvement Recommendations")
            
            if "FAIL" in str(result["hard_constraints"]):
                report.append("- **Hard Constraints:** Eliminate all hard constraints by implementing soft constraint handling.")
            
            if "FAIL" in str(result["ai_features"]) or "PARTIAL" in str(result["ai_features"]):
                report.append("- **AI Features:** Enhance AI capabilities by adding more intelligent features like adaptive parameters, learning mechanisms, and pattern recognition.")
            
            if isinstance(result["fitness_score"], (int, float)) and result["fitness_score"] < 80:
                report.append("- **Fitness Score:** Improve fitness score by optimizing the objective function, adding more sophisticated scoring components, and fine-tuning weights.")
            
            if "FAIL" in str(result["objective_achievement"]) or "PARTIAL" in str(result["objective_achievement"]):
                report.append("- **Objective Achievement:** Enhance objective achievement by focusing on the core goals of the algorithm and ensuring all constraints are properly addressed.")
            
            if "FAIL" in str(result["algorithm_nature"]):
                report.append("- **Algorithm Nature:** Ensure the algorithm follows its theoretical design principles and exhibits expected characteristics.")
            
            report.append("")
        
        # Overall recommendations
        report.append("## Overall Recommendations")
        
        # Check for common issues across algorithms
        hard_issues = sum(1 for r in self.results.values() if "FAIL" in str(r.get("hard_constraints", "")))
        ai_issues = sum(1 for r in self.results.values() if "FAIL" in str(r.get("ai_features", "")))
        fitness_issues = sum(1 for r in self.results.values() if isinstance(r.get("fitness_score", 0), (int, float)) and r.get("fitness_score", 0) < 80)
        
        if hard_issues > 0:
            report.append("1. **Hard Constraints:** Implement a global constraint handling mechanism that can be shared across all algorithms.")
        
        if ai_issues > 0:
            report.append("2. **AI Features:** Develop a common AI framework that can be integrated into all algorithms, focusing on adaptive parameters, learning mechanisms, and pattern recognition.")
        
        if fitness_issues > 0:
            report.append("3. **Fitness Scoring:** Standardize the fitness scoring system across all algorithms to ensure consistent evaluation and comparison.")
        
        report.append("4. **Integration:** Ensure seamless integration between algorithms to allow for hybrid approaches that combine the strengths of multiple algorithms.")
        
        report.append("5. **Documentation:** Improve documentation of algorithm parameters, features, and expected behavior to facilitate better understanding and usage.")
        
        return "\n".join(report)


async def main():
    """Main function to run the tests."""
    tester = AlgorithmTester()
    results = await tester.run_all_tests()
    
    # Generate and save report
    report = tester.generate_report()
    with open(f"{tester.output_dir}/evaluation_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n\n{'='*80}")
    print("Testing complete. Results saved to:")
    print(f"- Summary: {tester.output_dir}/summary_results.json")
    print(f"- Report: {tester.output_dir}/evaluation_report.md")
    print(f"- Individual results: {tester.output_dir}/<algorithm>_results.json")
    print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(main())
