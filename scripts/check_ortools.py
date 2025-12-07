"""
OR-Tools yüklü mü ve çalışıyor mu kontrol scripti.
Bu script hem mevcut Python'u hem de belirtilen Python path'ini kontrol eder.
"""
import sys
import os

def check_ortools(python_path=None):
    """OR-Tools'ın yüklü olup olmadığını ve çalışıp çalışmadığını kontrol eder."""
    print("=" * 60)
    print("OR-Tools Kontrol Scripti")
    print("=" * 60)
    
    # Python bilgisi
    print(f"\nPython Bilgisi:")
    print(f"   Executable: {sys.executable}")
    print(f"   Version: {sys.version}")
    if python_path:
        print(f"   Kontrol edilen path: {python_path}")
    
    # 1. Import kontrolü
    print("\n1. Import kontrolü...")
    try:
        from ortools.linear_solver import pywraplp
        print("   ✓ OR-Tools başarıyla import edildi")
        # Versiyon bilgisi
        try:
            import ortools
            print(f"   OR-Tools versiyonu: {ortools.__version__}")
        except:
            pass
    except ImportError as e:
        print(f"   ✗ OR-Tools import hatası: {e}")
        print("   → Çözüm: pip install ortools")
        if python_path:
            print(f"   → Bu Python için: {python_path} -m pip install ortools")
        return False
    
    # 2. Solver kontrolü
    print("\n2. Solver kontrolü...")
    solvers_to_try = ['SCIP', 'CBC', 'GLOP', 'SAT']
    available_solvers = []
    
    for solver_name in solvers_to_try:
        try:
            solver = pywraplp.Solver.CreateSolver(solver_name)
            if solver:
                available_solvers.append(solver_name)
                print(f"   ✓ {solver_name} solver mevcut")
            else:
                print(f"   ✗ {solver_name} solver mevcut değil")
        except Exception as e:
            print(f"   ✗ {solver_name} solver hatası: {e}")
    
    if not available_solvers:
        print("\n   ⚠ Hiçbir solver mevcut değil!")
        print("   → SCIP ve CBC solver'ları için ek paketler gerekebilir")
        return False
    
    # 3. Basit test problemi
    print("\n3. Basit test problemi çözme...")
    try:
        solver = pywraplp.Solver.CreateSolver('CBC')
        if not solver:
            solver = pywraplp.Solver.CreateSolver('GLOP')
        
        if solver:
            # Basit LP problemi: max x + y, x + y <= 1, x >= 0, y >= 0
            x = solver.NumVar(0, solver.infinity(), 'x')
            y = solver.NumVar(0, solver.infinity(), 'y')
            
            solver.Add(x + y <= 1)
            solver.Maximize(x + y)
            
            status = solver.Solve()
            if status == pywraplp.Solver.OPTIMAL:
                print(f"   ✓ Test problemi çözüldü: x={x.solution_value():.2f}, y={y.solution_value():.2f}")
                print(f"   ✓ Objective değeri: {solver.Objective().Value():.2f}")
                return True
            else:
                print(f"   ✗ Test problemi çözülemedi: status={status}")
                return False
        else:
            print("   ✗ Hiçbir solver oluşturulamadı")
            return False
    except Exception as e:
        print(f"   ✗ Test problemi hatası: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Komut satırı argümanı varsa o Python'u kontrol et
    python_path = None
    if len(sys.argv) > 1:
        python_path = sys.argv[1]
        print(f"Belirtilen Python path'i kontrol ediliyor: {python_path}")
        if not os.path.exists(python_path):
            print(f"✗ Hata: Python executable bulunamadı: {python_path}")
            sys.exit(1)
    
    success = check_ortools(python_path)
    print("\n" + "=" * 60)
    if success:
        print("SONUÇ: OR-Tools çalışıyor ✓")
    else:
        print("SONUÇ: OR-Tools çalışmıyor ✗")
        print("\nYükleme komutu:")
        if python_path:
            print(f"  {python_path} -m pip install ortools")
        else:
            print(f"  {sys.executable} -m pip install ortools")
    print("=" * 60)
    sys.exit(0 if success else 1)

