"""
Real Simplex algoritmasının OR-Tools kullanıp kullanmadığını test eder.
"""
import sys
import os

# Proje root dizinine ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_ortools_import():
    """OR-Tools import'unun çalışıp çalışmadığını test eder."""
    print("=" * 60)
    print("Real Simplex OR-Tools Kullanım Testi")
    print("=" * 60)
    
    # 1. OR-Tools import kontrolü
    print("\n1. OR-Tools Import Kontrolü:")
    try:
        from ortools.linear_solver import pywraplp
        print("   ✓ OR-Tools başarıyla import edildi")
        ORTOOLS_AVAILABLE = True
    except ImportError as e:
        print(f"   ✗ OR-Tools import hatası: {e}")
        ORTOOLS_AVAILABLE = False
        return False
    
    # 2. Real Simplex modülündeki flag kontrolü
    print("\n2. Real Simplex Modülü ORTOOLS_AVAILABLE Flag Kontrolü:")
    try:
        # Modülü import et
        from app.algorithms.real_simplex import ORTOOLS_AVAILABLE as RS_ORTOOLS_AVAILABLE
        
        # Modül seviyesindeki flag'i kontrol et
        # Not: Bu modül import edildiğinde kontrol edilir
        if RS_ORTOOLS_AVAILABLE:
            print("   ✓ real_simplex.py modülünde ORTOOLS_AVAILABLE = True")
        else:
            print("   ✗ real_simplex.py modülünde ORTOOLS_AVAILABLE = False")
            print("   → Modül import edildiğinde OR-Tools bulunamadı")
            return False
    except Exception as e:
        print(f"   ✗ Modül import hatası: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. Solver oluşturma testi
    print("\n3. Solver Oluşturma Testi:")
    try:
        solver = pywraplp.Solver.CreateSolver('SCIP')
        if solver:
            print("   ✓ SCIP solver oluşturuldu")
        else:
            solver = pywraplp.Solver.CreateSolver('CBC')
            if solver:
                print("   ✓ CBC solver oluşturuldu")
            else:
                print("   ✗ Hiçbir solver oluşturulamadı")
                return False
    except Exception as e:
        print(f"   ✗ Solver oluşturma hatası: {e}")
        return False
    
    # 4. Real Simplex sınıfını test et
    print("\n4. RealSimplexAlgorithm Sınıfı Testi:")
    try:
        from app.algorithms.real_simplex import RealSimplexAlgorithm
        
        # Algoritma instance'ı oluştur
        algorithm = RealSimplexAlgorithm()
        print("   ✓ RealSimplexAlgorithm instance oluşturuldu")
        
        # ORTOOLS_AVAILABLE flag'ini kontrol et (modül seviyesinde)
        import app.algorithms.real_simplex as rs_module
        if rs_module.ORTOOLS_AVAILABLE:
            print("   ✓ Modül seviyesinde ORTOOLS_AVAILABLE = True")
            print("   → Algoritma OR-Tools kullanacak")
        else:
            print("   ✗ Modül seviyesinde ORTOOLS_AVAILABLE = False")
            print("   → Algoritma heuristic kullanacak")
            return False
    except Exception as e:
        print(f"   ✗ RealSimplexAlgorithm test hatası: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("SONUÇ: Real Simplex OR-Tools kullanacak ✓")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_ortools_import()
    sys.exit(0 if success else 1)

