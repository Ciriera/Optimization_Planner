"""
Jury matching service for automatic jury assignment
"""

from typing import Dict, Any, List, Optional, Tuple
import random
from datetime import datetime
from sqlalchemy.orm import Session

# Models are not directly used, we work with dict data


class JuryMatchingService:
    """
    Service for automatic jury matching and assignment
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def match_jury(self, projects: List[Dict[str, Any]], 
                   instructors: List[Dict[str, Any]], 
                   constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Match juries to projects based on expertise and constraints.
        
        Args:
            projects: List of projects requiring juries
            instructors: List of available instructors
            constraints: Additional matching constraints
            
        Returns:
            Jury matching results with assignments and reasoning
        """
        try:
            constraints = constraints or {}
            
            # Analyze project requirements
            project_requirements = self._analyze_project_requirements(projects)
            
            # Analyze instructor expertise
            instructor_expertise = self._analyze_instructor_expertise(instructors)
            
            # Perform matching
            assignments = self._perform_matching(
                projects, instructors, project_requirements, 
                instructor_expertise, constraints
            )
            
            # Calculate matching quality metrics
            quality_metrics = self._calculate_matching_quality(
                assignments, project_requirements, instructor_expertise
            )
            
            return {
                "status": "success",
                "assignments": assignments,
                "quality_metrics": quality_metrics,
                "total_projects": len(projects),
                "total_instructors": len(instructors),
                "matching_algorithm": "expertise_based_weighted_matching",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Jury matching failed: {str(e)}",
                "assignments": [],
                "quality_metrics": {},
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _analyze_project_requirements(self, projects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze project requirements for jury matching."""
        requirements = {}
        
        for project in projects:
            project_id = project.get("id")
            project_type = project.get("type", "ara")
            advisor_id = project.get("advisor_id")
            
            # Determine jury size requirements
            if project_type == "bitirme":
                required_instructors = 2
                can_have_ra = True
            else:  # ara project
                required_instructors = 1
                can_have_ra = True
            
            # Analyze project domain/expertise needed
            domain_keywords = self._extract_domain_keywords(project)
            
            requirements[project_id] = {
                "project_type": project_type,
                "advisor_id": advisor_id,
                "required_instructors": required_instructors,
                "can_have_ra": can_have_ra,
                "domain_keywords": domain_keywords,
                "title": project.get("title", ""),
                "description": project.get("description", "")
            }
        
        return requirements
    
    def _analyze_instructor_expertise(self, instructors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze instructor expertise and availability."""
        expertise = {}
        
        for instructor in instructors:
            instructor_id = instructor.get("id")
            
            # Extract expertise areas
            expertise_areas = self._extract_expertise_areas(instructor)
            
            # Calculate availability
            availability_score = self._calculate_availability_score(instructor)
            
            # Get teaching load
            current_load = instructor.get("current_load", 0)
            max_load = instructor.get("max_load", 10)
            
            expertise[instructor_id] = {
                "name": instructor.get("name", ""),
                "expertise_areas": expertise_areas,
                "availability_score": availability_score,
                "current_load": current_load,
                "max_load": max_load,
                "load_utilization": current_load / max(max_load, 1),
                "department": instructor.get("department", ""),
                "title": instructor.get("title", "")
            }
        
        return expertise
    
    def _extract_domain_keywords(self, project: Dict[str, Any]) -> List[str]:
        """Extract domain keywords from project information."""
        keywords = []
        
        # Extract from title
        title = project.get("title", "").lower()
        keywords.extend(self._tokenize_and_filter(title))
        
        # Extract from description
        description = project.get("description", "").lower()
        keywords.extend(self._tokenize_and_filter(description))
        
        # Common computer science domains
        cs_domains = [
            "artificial intelligence", "machine learning", "deep learning",
            "computer vision", "natural language processing", "data science",
            "web development", "mobile development", "database systems",
            "computer networks", "cybersecurity", "software engineering",
            "algorithms", "data structures", "operating systems",
            "computer graphics", "game development", "embedded systems",
            "distributed systems", "cloud computing", "blockchain"
        ]
        
        # Match against known domains
        matched_domains = []
        for domain in cs_domains:
            if any(keyword in title or keyword in description for keyword in domain.split()):
                matched_domains.append(domain)
        
        return list(set(keywords + matched_domains))
    
    def _extract_expertise_areas(self, instructor: Dict[str, Any]) -> List[str]:
        """Extract expertise areas from instructor information."""
        expertise = []
        
        # Extract from research areas
        research_areas = instructor.get("research_areas", "")
        if research_areas:
            expertise.extend(self._tokenize_and_filter(research_areas.lower()))
        
        # Extract from teaching areas
        teaching_areas = instructor.get("teaching_areas", "")
        if teaching_areas:
            expertise.extend(self._tokenize_and_filter(teaching_areas.lower()))
        
        # Extract from department
        department = instructor.get("department", "").lower()
        if department:
            expertise.append(department)
        
        return list(set(expertise))
    
    def _tokenize_and_filter(self, text: str) -> List[str]:
        """Tokenize text and filter meaningful words."""
        import re
        
        # Remove special characters and split into words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
        
        # Filter out common stop words
        stop_words = {
            "the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
            "by", "from", "up", "about", "into", "through", "during", "before",
            "after", "above", "below", "between", "among", "this", "that", "these",
            "those", "i", "you", "he", "she", "it", "we", "they", "is", "are",
            "was", "were", "be", "been", "being", "have", "has", "had", "do",
            "does", "did", "will", "would", "could", "should", "may", "might",
            "must", "can", "shall"
        }
        
        return [word.lower() for word in words if word.lower() not in stop_words]
    
    def _calculate_availability_score(self, instructor: Dict[str, Any]) -> float:
        """Calculate instructor availability score."""
        # Base availability (can be modified based on actual availability data)
        base_score = 1.0
        
        # Reduce score based on current load
        current_load = instructor.get("current_load", 0)
        max_load = instructor.get("max_load", 10)
        
        if max_load > 0:
            load_ratio = current_load / max_load
            availability_score = base_score * (1 - load_ratio * 0.5)
        else:
            availability_score = base_score
        
        return max(availability_score, 0.1)  # Minimum 10% availability
    
    def _perform_matching(self, projects: List[Dict[str, Any]], 
                         instructors: List[Dict[str, Any]],
                         project_requirements: Dict[str, Any],
                         instructor_expertise: Dict[str, Any],
                         constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform the actual jury matching."""
        assignments = []
        used_instructors = set()
        
        for project in projects:
            project_id = project.get("id")
            requirements = project_requirements.get(project_id, {})
            
            # Find suitable instructors
            suitable_instructors = self._find_suitable_instructors(
                project_id, requirements, instructors, 
                instructor_expertise, used_instructors
            )
            
            # Select jury members
            jury_members = self._select_jury_members(
                suitable_instructors, requirements, constraints
            )
            
            # Create assignment
            assignment = {
                "project_id": project_id,
                "project_title": requirements.get("title", ""),
                "project_type": requirements.get("project_type", "ara"),
                "advisor_id": requirements.get("advisor_id"),
                "jury_members": jury_members,
                "matching_scores": {
                    member["instructor_id"]: member["matching_score"] 
                    for member in jury_members
                },
                "total_matching_score": sum(
                    member["matching_score"] for member in jury_members
                ) / len(jury_members) if jury_members else 0
            }
            
            assignments.append(assignment)
            
            # Mark instructors as used
            for member in jury_members:
                used_instructors.add(member["instructor_id"])
        
        return assignments
    
    def _find_suitable_instructors(self, project_id: int, requirements: Dict[str, Any],
                                 instructors: List[Dict[str, Any]],
                                 instructor_expertise: Dict[str, Any],
                                 used_instructors: set) -> List[Dict[str, Any]]:
        """Find instructors suitable for a project."""
        suitable = []
        
        advisor_id = requirements.get("advisor_id")
        project_keywords = requirements.get("domain_keywords", [])
        
        for instructor in instructors:
            instructor_id = instructor.get("id")
            
            # Skip if already used
            if instructor_id in used_instructors:
                continue
            
            # Skip advisor (they can't be in their own jury)
            if instructor_id == advisor_id:
                continue
            
            # Calculate matching score
            matching_score = self._calculate_matching_score(
                instructor, instructor_expertise.get(instructor_id, {}),
                project_keywords, requirements
            )
            
            if matching_score > 0.3:  # Minimum threshold
                suitable.append({
                    "instructor_id": instructor_id,
                    "instructor_name": instructor_expertise.get(instructor_id, {}).get("name", ""),
                    "matching_score": matching_score,
                    "expertise_match": self._calculate_expertise_match(
                        instructor_expertise.get(instructor_id, {}), project_keywords
                    ),
                    "availability_score": instructor_expertise.get(instructor_id, {}).get("availability_score", 0)
                })
        
        # Sort by matching score
        suitable.sort(key=lambda x: x["matching_score"], reverse=True)
        
        return suitable
    
    def _calculate_matching_score(self, instructor: Dict[str, Any],
                                expertise_info: Dict[str, Any],
                                project_keywords: List[str],
                                requirements: Dict[str, Any]) -> float:
        """Calculate how well an instructor matches a project."""
        score = 0.0
        
        # Expertise matching (60% weight)
        expertise_match = self._calculate_expertise_match(expertise_info, project_keywords)
        score += expertise_match * 0.6
        
        # Availability (20% weight)
        availability_score = expertise_info.get("availability_score", 0)
        score += availability_score * 0.2
        
        # Load balance (20% weight)
        load_utilization = expertise_info.get("load_utilization", 0)
        load_score = max(0, 1 - load_utilization)  # Prefer less loaded instructors
        score += load_score * 0.2
        
        return min(score, 1.0)
    
    def _calculate_expertise_match(self, expertise_info: Dict[str, Any], 
                                 project_keywords: List[str]) -> float:
        """Calculate expertise matching score."""
        instructor_expertise = expertise_info.get("expertise_areas", [])
        
        if not project_keywords or not instructor_expertise:
            return 0.5  # Neutral score
        
        # Calculate keyword overlap
        overlap = len(set(project_keywords) & set(instructor_expertise))
        total_keywords = len(set(project_keywords) | set(instructor_expertise))
        
        if total_keywords == 0:
            return 0.5
        
        return overlap / total_keywords
    
    def _select_jury_members(self, suitable_instructors: List[Dict[str, Any]],
                           requirements: Dict[str, Any],
                           constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Select jury members from suitable instructors."""
        required_count = requirements.get("required_instructors", 1)
        can_have_ra = requirements.get("can_have_ra", True)
        
        # Select top instructors
        selected = suitable_instructors[:required_count]
        
        # Add RA placeholder if needed and allowed
        if can_have_ra and len(selected) < 3:
            selected.append({
                "instructor_id": "ra_placeholder",
                "instructor_name": "Araştırma Görevlisi (Atanacak)",
                "matching_score": 0.5,
                "expertise_match": 0.5,
                "availability_score": 1.0,
                "is_placeholder": True
            })
        
        return selected
    
    def _calculate_matching_quality(self, assignments: List[Dict[str, Any]],
                                  project_requirements: Dict[str, Any],
                                  instructor_expertise: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall matching quality metrics."""
        if not assignments:
            return {
                "overall_score": 0,
                "coverage": 0,
                "load_balance": 0,
                "expertise_match": 0
            }
        
        # Overall matching score
        total_scores = [assignment.get("total_matching_score", 0) for assignment in assignments]
        overall_score = sum(total_scores) / len(total_scores) if total_scores else 0
        
        # Coverage (percentage of projects with complete juries)
        complete_juries = sum(
            1 for assignment in assignments
            if len(assignment.get("jury_members", [])) >= 
            project_requirements.get(assignment["project_id"], {}).get("required_instructors", 1)
        )
        coverage = complete_juries / len(assignments) if assignments else 0
        
        # Load balance
        instructor_loads = {}
        for assignment in assignments:
            for member in assignment.get("jury_members", []):
                instructor_id = member.get("instructor_id")
                if instructor_id != "ra_placeholder":
                    instructor_loads[instructor_id] = instructor_loads.get(instructor_id, 0) + 1
        
        if instructor_loads:
            loads = list(instructor_loads.values())
            load_balance = 1 - (max(loads) - min(loads)) / max(max(loads), 1)
        else:
            load_balance = 1
        
        # Expertise match
        expertise_matches = []
        for assignment in assignments:
            for member in assignment.get("jury_members", []):
                if not member.get("is_placeholder", False):
                    expertise_matches.append(member.get("expertise_match", 0))
        
        expertise_match = sum(expertise_matches) / len(expertise_matches) if expertise_matches else 0
        
        return {
            "overall_score": overall_score,
            "coverage": coverage,
            "load_balance": load_balance,
            "expertise_match": expertise_match,
            "total_assignments": len(assignments),
            "complete_juries": complete_juries,
            "instructor_utilization": len(instructor_loads)
        }
