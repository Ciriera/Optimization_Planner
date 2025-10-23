"""
Test Real Simplex Algorithm coverage to ensure all projects are assigned.
"""

import asyncio
from app.services.algorithm import AlgorithmService
from app.models.algorithm import AlgorithmType
from app.db.base import async_session


async def test_simplex_coverage():
    """Test Real Simplex algorithm project coverage."""
    
    print("=" * 80)
    print("Testing Real Simplex Algorithm - Project Coverage Check")
    print("=" * 80)
    
    async with async_session() as db:
        # Run Real Simplex algorithm
        result, run = await AlgorithmService.run_algorithm(
            algorithm_type=AlgorithmType.SIMPLEX,
            data={},  # Empty data will trigger loading from DB
            params=None
        )
        
        # Get assignments
        assignments = result.get("assignments", result.get("schedule", result.get("solution", [])))
        
        # Count assigned projects
        assigned_project_ids = set(a.get("project_id") for a in assignments)
        
        # Get all projects from data
        from sqlalchemy import text
        result_query = await db.execute(text("SELECT id, type FROM projects"))
        all_projects = result_query.fetchall()
        
        total_projects = len(all_projects)
        total_bitirme = sum(1 for p in all_projects if p[1] and p[1].lower() == "bitirme")
        total_ara = sum(1 for p in all_projects if p[1] and p[1].lower() == "ara")
        
        # Count assigned by type
        assigned_bitirme = 0
        assigned_ara = 0
        
        for project in all_projects:
            if project[0] in assigned_project_ids:
                if project[1] and project[1].lower() == "bitirme":
                    assigned_bitirme += 1
                elif project[1] and project[1].lower() == "ara":
                    assigned_ara += 1
        
        # Print results
        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)
        print(f"Total Projects: {total_projects}")
        print(f"  - Bitirme: {total_bitirme}")
        print(f"  - Ara: {total_ara}")
        print("")
        print(f"Assigned Projects: {len(assigned_project_ids)}/{total_projects} ({len(assigned_project_ids)/total_projects*100:.1f}%)")
        print(f"  - Bitirme: {assigned_bitirme}/{total_bitirme} ({assigned_bitirme/total_bitirme*100:.1f}%)")
        print(f"  - Ara: {assigned_ara}/{total_ara} ({assigned_ara/total_ara*100:.1f}%)")
        print("")
        
        # Check if all projects assigned
        if len(assigned_project_ids) == total_projects:
            print("✅ SUCCESS: All projects assigned!")
        else:
            missing_count = total_projects - len(assigned_project_ids)
            missing_bitirme = total_bitirme - assigned_bitirme
            missing_ara = total_ara - assigned_ara
            print(f"⚠️ WARNING: {missing_count} projects NOT assigned!")
            print(f"  - Missing Bitirme: {missing_bitirme}")
            print(f"  - Missing Ara: {missing_ara}")
            
            # Find which projects are missing
            missing_ids = set(p[0] for p in all_projects) - assigned_project_ids
            print(f"\nMissing project IDs: {sorted(missing_ids)}")
        
        print("=" * 80)
        
        return {
            "total": total_projects,
            "assigned": len(assigned_project_ids),
            "coverage": len(assigned_project_ids) / total_projects if total_projects > 0 else 0,
            "bitirme": {"total": total_bitirme, "assigned": assigned_bitirme},
            "ara": {"total": total_ara, "assigned": assigned_ara}
        }


if __name__ == "__main__":
    result = asyncio.run(test_simplex_coverage())
    print(f"\nFinal coverage: {result['coverage']*100:.1f}%")

