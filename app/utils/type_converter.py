"""
Type conversion utilities
"""
import enum

class InstructorType(str, enum.Enum):
    INSTRUCTOR = "instructor"  # Öğretim üyesi (hoca)
    ASSISTANT = "assistant"    # Araştırma görevlisi

def convert_instructor_type(type_str: str) -> InstructorType:
    """Convert string type to InstructorType enum
    
    Args:
        type_str: String representation of instructor type
        
    Returns:
        InstructorType enum value
    """
    # Map legacy values to enum values
    type_mapping = {
        "professor": InstructorType.INSTRUCTOR,
        "research_assistant": InstructorType.ASSISTANT,
        "hoca": InstructorType.INSTRUCTOR,
        "aras_gor": InstructorType.ASSISTANT,
    }
    
    if type_str in type_mapping:
        return type_mapping[type_str]
    
    # Try direct conversion if it's already an enum value
    try:
        return InstructorType(type_str)
    except ValueError:
        # Default to INSTRUCTOR if unknown
        return InstructorType.INSTRUCTOR 