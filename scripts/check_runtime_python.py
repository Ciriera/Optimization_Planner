"""
Uygulama çalışma zamanında hangi Python'u kullanıyor kontrol scripti.
Bu script, uygulamanın gerçekten Python39'u kullanıp kullanmadığını kontrol eder.
"""
import sys
import os

def check_runtime_python():
    """Uygulama çalışma zamanında hangi Python'u kullandığını gösterir."""
    print("=" * 60)
    print("Python Runtime Kontrol Scripti")
    print("=" * 60)
    
    print(f"\nMevcut Python Bilgisi:")
    print(f"   Executable: {sys.executable}")
    print(f"   Version: {sys.version}")
    print(f"   Platform: {sys.platform}")
    print(f"   Path: {sys.path[:3]}...")  # İlk 3 path
    
    # Python39 path'i
    python39_path = r"C:\Users\cavul\AppData\Local\Programs\Python\Python39\python.exe"
    
    print(f"\nBeklenen Python39 Path:")
    print(f"   {python39_path}")
    
    # Karşılaştır
    if sys.executable.lower() == python39_path.lower():
        print("\n✓ Uygulama doğru Python'u (Python39) kullanıyor!")
    else:
        print("\n⚠ Uygulama farklı bir Python kullanıyor!")
        print(f"   Beklenen: {python39_path}")
        print(f"   Kullanılan: {sys.executable}")
        print("\n→ COMMANDS.md'deki Python path'ini kontrol edin")
        print("→ Veya uygulamayı şu komutla başlatın:")
        print(f'   &"{python39_path}" -u -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000')
    
    # OR-Tools kontrolü
    print("\n" + "-" * 60)
    print("OR-Tools Kontrolü:")
    try:
        from ortools.linear_solver import pywraplp
        print("   ✓ OR-Tools yüklü")
        
        solver = pywraplp.Solver.CreateSolver('SCIP')
        if solver:
            print("   ✓ SCIP solver mevcut")
        else:
            solver = pywraplp.Solver.CreateSolver('CBC')
            if solver:
                print("   ✓ CBC solver mevcut")
            else:
                print("   ✗ Hiçbir solver mevcut değil")
    except ImportError as e:
        print(f"   ✗ OR-Tools yüklü değil: {e}")
        print(f"   → Yükleme: {sys.executable} -m pip install ortools")
    
    print("=" * 60)

if __name__ == "__main__":
    check_runtime_python()









