"""
Detailed Real Simplex coverage check with actual database data.
"""

import asyncio
from app.services.algorithm import AlgorithmService
from app.models.algorithm import AlgorithmType
from app.db.base import async_session
from sqlalchemy import text
from collections import defaultdict


async def detailed_simplex_check():
    """Detailed Real Simplex algorithm coverage check."""
    
    print("=" * 100)
    print("DETAILED REAL SIMPLEX COVERAGE CHECK")
    print("=" * 100)
    
    async with async_session() as db:
        # Get actual project counts from database
        print("\n📊 DATABASE PROJECTS:")
        print("-" * 100)
        
        result = await db.execute(text("""
            SELECT 
                id,
                title,
                type,
                responsible_instructor_id
            FROM projects
            ORDER BY id
        """))
        all_projects = result.fetchall()
        
        print(f"Total projects in database: {len(all_projects)}")
        
        # Count by type
        type_counts = defaultdict(int)
        for project in all_projects:
            project_type = project[2] if project[2] else "unknown"
            type_counts[project_type.lower()] += 1
        
        print(f"\nBreakdown by type:")
        for ptype, count in sorted(type_counts.items()):
            print(f"  - {ptype}: {count}")
        
        # Get instructor info
        print("\n👥 INSTRUCTORS WITH PROJECTS:")
        print("-" * 100)
        
        result = await db.execute(text("""
            SELECT 
                i.id,
                i.full_name,
                COUNT(p.id) as project_count
            FROM instructors i
            LEFT JOIN projects p ON p.responsible_instructor_id = i.id
            GROUP BY i.id, i.full_name
            ORDER BY project_count DESC
        """))
        instructors = result.fetchall()
        
        print(f"Total instructors: {len(instructors)}")
        print(f"\nTop instructors by project count:")
        for i, (inst_id, name, count) in enumerate(instructors[:10], 1):
            print(f"  {i}. Instructor {inst_id} ({name}): {count} projects")
        
        # Run Real Simplex algorithm
        print("\n🔄 RUNNING REAL SIMPLEX ALGORITHM...")
        print("-" * 100)
        
        result, run = await AlgorithmService.run_algorithm(
            algorithm_type=AlgorithmType.SIMPLEX,
            data={},
            params=None
        )
        
        # Get assignments
        assignments = result.get("assignments", result.get("schedule", result.get("solution", [])))
        
        print(f"\nAlgorithm execution completed!")
        print(f"Execution time: {result.get('execution_time', 0):.2f}s")
        print(f"Status: {result.get('status', 'unknown')}")
        print(f"Success: {result.get('success', False)}")
        
        # Analyze assignments
        print("\n📋 ASSIGNMENT ANALYSIS:")
        print("-" * 100)
        
        print(f"Total assignments returned: {len(assignments)}")
        
        # Get unique project IDs from assignments
        assigned_project_ids = set()
        for assignment in assignments:
            project_id = assignment.get("project_id")
            if project_id:
                assigned_project_ids.add(project_id)
        
        print(f"Unique projects assigned: {len(assigned_project_ids)}")
        
        # Compare with database
        database_project_ids = set(p[0] for p in all_projects)
        
        print(f"\n✅ COVERAGE COMPARISON:")
        print("-" * 100)
        print(f"Projects in database: {len(database_project_ids)}")
        print(f"Projects assigned: {len(assigned_project_ids)}")
        print(f"Coverage: {len(assigned_project_ids)}/{len(database_project_ids)} ({len(assigned_project_ids)/len(database_project_ids)*100:.1f}%)")
        
        # Find missing projects
        missing_project_ids = database_project_ids - assigned_project_ids
        
        if missing_project_ids:
            print(f"\n⚠️ MISSING PROJECTS: {len(missing_project_ids)}")
            print("-" * 100)
            
            # Get details of missing projects
            missing_projects_list = [p for p in all_projects if p[0] in missing_project_ids]
            
            # Count by type
            missing_by_type = defaultdict(list)
            for project in missing_projects_list:
                project_id, title, ptype, instructor_id = project
                ptype_key = ptype.lower() if ptype else "unknown"
                missing_by_type[ptype_key].append({
                    'id': project_id,
                    'title': title,
                    'instructor_id': instructor_id
                })
            
            print(f"\nMissing projects by type:")
            for ptype, projects in sorted(missing_by_type.items()):
                print(f"\n  {ptype.upper()}: {len(projects)} projects")
                for p in sorted(projects, key=lambda x: x['id'])[:10]:  # Show first 10
                    print(f"    - Project {p['id']}: {p['title'][:50]} (Instructor {p['instructor_id']})")
                if len(projects) > 10:
                    print(f"    ... and {len(projects) - 10} more")
            
            # Check if missing projects have instructors
            print(f"\n🔍 MISSING PROJECT ANALYSIS:")
            print("-" * 100)
            
            missing_no_instructor = [p for p in missing_projects_list if not p[3]]
            missing_with_instructor = [p for p in missing_projects_list if p[3]]
            
            print(f"Missing projects WITHOUT instructor: {len(missing_no_instructor)}")
            if missing_no_instructor:
                for p in missing_no_instructor[:5]:
                    print(f"  - Project {p[0]}: {p[1][:50]}")
            
            print(f"\nMissing projects WITH instructor: {len(missing_with_instructor)}")
            if missing_with_instructor:
                # Group by instructor
                by_instructor = defaultdict(list)
                for p in missing_with_instructor:
                    by_instructor[p[3]].append(p)
                
                print(f"\nMissing projects by instructor:")
                for inst_id, projects in sorted(by_instructor.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
                    print(f"  Instructor {inst_id}: {len(projects)} missing projects")
                    for p in projects[:3]:
                        print(f"    - Project {p[0]}: {p[1][:40]}")
        else:
            print(f"\n✅ ALL PROJECTS ASSIGNED! NO MISSING PROJECTS!")
        
        # Check for duplicate assignments
        print(f"\n🔍 DUPLICATE CHECK:")
        print("-" * 100)
        
        assignment_project_ids = [a.get("project_id") for a in assignments if a.get("project_id")]
        duplicates = [pid for pid in set(assignment_project_ids) if assignment_project_ids.count(pid) > 1]
        
        if duplicates:
            print(f"⚠️ WARNING: {len(duplicates)} projects have duplicate assignments!")
            for dup_id in sorted(duplicates)[:10]:
                count = assignment_project_ids.count(dup_id)
                print(f"  - Project {dup_id}: assigned {count} times")
        else:
            print(f"✅ No duplicate assignments found")
        
        # Analyze assigned projects by type
        print(f"\n📊 ASSIGNED PROJECTS BY TYPE:")
        print("-" * 100)
        
        assigned_projects = [p for p in all_projects if p[0] in assigned_project_ids]
        assigned_by_type = defaultdict(int)
        for project in assigned_projects:
            ptype = project[2].lower() if project[2] else "unknown"
            assigned_by_type[ptype] += 1
        
        for ptype in sorted(type_counts.keys()):
            total = type_counts[ptype]
            assigned = assigned_by_type.get(ptype, 0)
            percentage = (assigned / total * 100) if total > 0 else 0
            status = "✅" if assigned == total else "⚠️"
            print(f"  {status} {ptype}: {assigned}/{total} ({percentage:.1f}%)")
        
        # Check algorithm metrics
        print(f"\n📈 ALGORITHM METRICS:")
        print("-" * 100)
        
        metrics = result.get("metrics", {})
        if metrics:
            print(f"Total score: {metrics.get('total_score', 'N/A')}")
            print(f"Instructor pairs: {metrics.get('instructor_pairs', 'N/A')}")
            print(f"Bidirectional jury count: {metrics.get('bidirectional_jury_count', 'N/A')}")
            print(f"Consecutive instructors: {metrics.get('consecutive_instructors', 'N/A')}/{metrics.get('total_instructors', 'N/A')}")
            print(f"Consecutive percentage: {metrics.get('consecutive_percentage', 'N/A'):.1f}%")
            print(f"Soft conflicts: {metrics.get('soft_conflicts', 'N/A')}")
        else:
            print("No metrics available")
        
        print("\n" + "=" * 100)
        
        return {
            "database_total": len(database_project_ids),
            "assigned_total": len(assigned_project_ids),
            "missing_total": len(missing_project_ids),
            "coverage": len(assigned_project_ids) / len(database_project_ids) if len(database_project_ids) > 0 else 0,
            "missing_ids": sorted(missing_project_ids) if missing_project_ids else []
        }


if __name__ == "__main__":
    result = asyncio.run(detailed_simplex_check())
    
    print("\n📊 FINAL SUMMARY:")
    print("=" * 100)
    print(f"Database projects: {result['database_total']}")
    print(f"Assigned projects: {result['assigned_total']}")
    print(f"Missing projects: {result['missing_total']}")
    print(f"Coverage: {result['coverage']*100:.1f}%")
    
    if result['missing_ids']:
        print(f"\nMissing project IDs: {result['missing_ids']}")
    else:
        print(f"\n✅ ALL PROJECTS SUCCESSFULLY ASSIGNED!")
    
    print("=" * 100)

