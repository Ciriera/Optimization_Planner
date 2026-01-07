"""
Test script for Excel to PNG conversion.
Run this to debug PNG generation issues.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.planner_export_service import exportPlannerToExcel
from app.services.excel_to_image_service import excel_to_png
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test data
test_planner_data = {
    "classes": ["D106", "D107", "D108"],
    "timeSlots": ["09:00", "09:30", "10:00", "10:30"],
    "projects": [
        {
            "class": "D106",
            "time": "09:00",
            "projectTitle": "Test Proje 1",
            "type": "Bitirme",
            "responsible": "Test Hoca 1",
            "jury": ["Test Jüri 1", "Test Jüri 2"],
            "color": "#A8E0FF"
        },
        {
            "class": "D107",
            "time": "09:30",
            "projectTitle": "Test Proje 2",
            "type": "Ara",
            "responsible": "Test Hoca 2",
            "jury": ["Test Jüri 3"],
            "color": "#FFA8A8"
        }
    ],
    "hocaLoad": {"Test Hoca 1": 5, "Test Hoca 2": 3},
    "title": "Test Jüri Programı",
    "date": "2025"
}

def test_excel_to_png():
    try:
        print("1. Generating Excel file...")
        excel_bytes = exportPlannerToExcel(test_planner_data)
        print(f"   ✓ Excel generated: {len(excel_bytes)} bytes")
        
        print("2. Converting Excel to PNG...")
        png_bytes = excel_to_png(excel_bytes, sheet_name="Jüri Programı", max_width=2400)
        print(f"   ✓ PNG generated: {len(png_bytes)} bytes")
        
        if len(png_bytes) < 100:
            print(f"   ✗ ERROR: PNG is too small ({len(png_bytes)} bytes)")
            return False
        
        print("3. Saving PNG to file for inspection...")
        with open("test_planner_calendar.png", "wb") as f:
            f.write(png_bytes)
        print(f"   ✓ PNG saved to test_planner_calendar.png")
        
        print("\n✓ SUCCESS: Excel to PNG conversion works!")
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_excel_to_png()
    sys.exit(0 if success else 1)















