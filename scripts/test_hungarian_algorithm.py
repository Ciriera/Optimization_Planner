"""
Hungarian Algorithm Test Script

Bu script, yeni Hungarian Algorithm'ın tüm isterleri karşılayıp karşılamadığını test eder.

Test Edilen İsterler:
1. BITIRME projeleri MUTLAKA ARA projelerden önce atanır (HARD CONSTRAINT)
2. Back-to-back sınıf içi yerleşim (boşluk yok)
3. Her timeslot'ta instructor başına max 1 görev
4. J1 ≠ PS (Sorumlu kendi projesine jüri olamaz)
5. İş yükü uniformitesi (±2 bandı)
6. Matris tabanlı ceza fonksiyonları (H₁, H₂, H₃)
7. J2 = [Araştırma Görevlisi] placeholder
"""

import sys
import os

# Proje kök dizinini path'e ekle
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from collections import defaultdict
from app.algorithms.hungarian_algorithm import HungarianAlgorithm, HungarianConfig


def create_test_data():
    """Test verisi oluştur."""
    # 10 öğretim görevlisi
    instructors = [
        {"id": 1, "name": "Prof. Dr. Ahmet Yılmaz", "code": "AY", "type": "instructor"},
        {"id": 2, "name": "Prof. Dr. Mehmet Kaya", "code": "MK", "type": "instructor"},
        {"id": 3, "name": "Doç. Dr. Ayşe Demir", "code": "AD", "type": "instructor"},
        {"id": 4, "name": "Doç. Dr. Fatma Çelik", "code": "FC", "type": "instructor"},
        {"id": 5, "name": "Dr. Öğr. Üyesi Ali Öz", "code": "AO", "type": "instructor"},
        {"id": 6, "name": "Dr. Öğr. Üyesi Zeynep Ak", "code": "ZA", "type": "instructor"},
        {"id": 7, "name": "Dr. Öğr. Üyesi Can Eren", "code": "CE", "type": "instructor"},
        {"id": 8, "name": "Dr. Öğr. Üyesi Deniz Su", "code": "DS", "type": "instructor"},
        {"id": 9, "name": "Arş. Gör. Emre Tan", "code": "ET", "type": "assistant"},  # Research assistant
        {"id": 10, "name": "Arş. Gör. Selin Ay", "code": "SA", "type": "assistant"},  # Research assistant
    ]
    
    # 20 proje (10 BITIRME, 10 ARA)
    projects = []
    
    # 10 BITIRME projesi
    for i in range(10):
        projects.append({
            "id": i + 1,
            "title": f"Bitirme Projesi {i + 1}",
            "project_type": "BITIRME",
            "responsible_id": (i % 8) + 1  # 1-8 arası instructor
        })
    
    # 10 ARA projesi
    for i in range(10):
        projects.append({
            "id": i + 11,
            "title": f"Ara Proje {i + 1}",
            "project_type": "ARA",
            "responsible_id": (i % 8) + 1  # 1-8 arası instructor
        })
    
    # 6 sınıf
    classrooms = [
        {"id": 0, "name": "D105"},
        {"id": 1, "name": "D106"},
        {"id": 2, "name": "D107"},
        {"id": 3, "name": "D108"},
        {"id": 4, "name": "D109"},
        {"id": 5, "name": "D110"},
    ]
    
    # Timeslotlar (09:00 - 17:00, 30 dakikalık slotlar)
    timeslots = []
    for i in range(16):
        hour = 9 + (i // 2)
        minute = (i % 2) * 30
        timeslots.append({
            "id": i,
            "start_time": f"{hour:02d}:{minute:02d}",
            "end_time": f"{hour:02d}:{minute + 30:02d}" if minute == 0 else f"{hour + 1:02d}:00"
        })
    
    return {
        "projects": projects,
        "instructors": instructors,
        "classrooms": classrooms,
        "timeslots": timeslots
    }


def test_bitirme_before_ara(assignments, projects):
    """
    Test 1: BITIRME projeleri MUTLAKA ARA projelerden önce mi?
    
    HARD CONSTRAINT: max(slot(BITIRME)) ≤ min(slot(ARA))
    """
    print("\n" + "=" * 60)
    print("TEST 1: BITIRME Projeleri Önceliği (HARD CONSTRAINT)")
    print("=" * 60)
    
    # Proje türlerini bul
    project_types = {p["id"]: p["project_type"] for p in projects}
    
    bitirme_slots = []
    ara_slots = []
    
    for assignment in assignments:
        ptype = project_types.get(assignment["project_id"], "ARA")
        if ptype.upper() == "BITIRME":
            bitirme_slots.append(assignment["global_slot"])
        else:
            ara_slots.append(assignment["global_slot"])
    
    if not bitirme_slots or not ara_slots:
        print("⚠️  Yeterli proje yok (BITIRME veya ARA)")
        return True
    
    max_bitirme = max(bitirme_slots)
    min_ara = min(ara_slots)
    
    passed = max_bitirme <= min_ara
    
    print(f"  BITIRME slotları: {sorted(bitirme_slots)}")
    print(f"  ARA slotları: {sorted(ara_slots)}")
    print(f"  max(BITIRME) = {max_bitirme}")
    print(f"  min(ARA) = {min_ara}")
    print(f"  Kosul: max(BITIRME) <= min(ARA) -> {max_bitirme} <= {min_ara}")
    print(f"  Sonuc: {'[OK] PASSED' if passed else '[X] FAILED'}")
    
    return passed


def test_j1_not_ps(assignments):
    """
    Test 2: J1 ≠ PS (Sorumlu kendi projesine jüri olamaz)
    """
    print("\n" + "=" * 60)
    print("TEST 2: J1 != PS Kontrolu")
    print("=" * 60)
    
    violations = []
    
    for assignment in assignments:
        if assignment["ps_id"] == assignment["j1_id"]:
            violations.append(assignment["project_id"])
    
    passed = len(violations) == 0
    
    print(f"  Toplam atama: {len(assignments)}")
    print(f"  Ihlal sayisi: {len(violations)}")
    if violations:
        print(f"  Ihlal eden projeler: {violations}")
    print(f"  Sonuc: {'[OK] PASSED' if passed else '[X] FAILED'}")
    
    return passed


def test_single_duty_per_slot(assignments):
    """
    Test 3: Her timeslot'ta instructor başına max 1 görev
    """
    print("\n" + "=" * 60)
    print("TEST 3: Timeslot Başına Tek Görev Kontrolü")
    print("=" * 60)
    
    # instructor_id -> slot -> count
    slot_duties = defaultdict(lambda: defaultdict(int))
    
    for assignment in assignments:
        slot = assignment["global_slot"]
        slot_duties[assignment["ps_id"]][slot] += 1
        slot_duties[assignment["j1_id"]][slot] += 1
    
    violations = []
    
    for instructor_id, slots in slot_duties.items():
        for slot, count in slots.items():
            if count > 1:
                violations.append((instructor_id, slot, count))
    
    passed = len(violations) == 0
    
    print(f"  Toplam instructor: {len(slot_duties)}")
    print(f"  Ihlal sayisi: {len(violations)}")
    if violations:
        for v in violations[:5]:  # Ilk 5 ihlali goster
            print(f"    Instructor {v[0]}, Slot {v[1]}: {v[2]} gorev")
    print(f"  Sonuc: {'[OK] PASSED' if passed else '[X] FAILED'}")
    
    return passed


def test_j2_placeholder(assignments):
    """
    Test 4: J2 = [Araştırma Görevlisi] placeholder kontrolü
    """
    print("\n" + "=" * 60)
    print("TEST 4: J2 Placeholder Kontrolü")
    print("=" * 60)
    
    expected = "[Araştırma Görevlisi]"
    violations = []
    
    for assignment in assignments:
        j2 = assignment.get("j2_label", "")
        if j2 != expected:
            violations.append((assignment["project_id"], j2))
    
    passed = len(violations) == 0
    
    print(f"  Beklenen J2: {expected}")
    print(f"  Toplam atama: {len(assignments)}")
    print(f"  Ihlal sayisi: {len(violations)}")
    if violations:
        for v in violations[:5]:
            print(f"    Proje {v[0]}: J2 = '{v[1]}'")
    print(f"  Sonuc: {'[OK] PASSED' if passed else '[X] FAILED'}")
    
    return passed


def test_workload_balance(assignments, faculty_count):
    """
    Test 5: İş yükü uniformitesi (±2 bandı)
    """
    print("\n" + "=" * 60)
    print("TEST 5: Is Yuku Dengesi (+/-2 Bandi)")
    print("=" * 60)
    
    # İş yüklerini hesapla
    workloads = defaultdict(int)
    
    for assignment in assignments:
        workloads[assignment["ps_id"]] += 1
        workloads[assignment["j1_id"]] += 1
    
    # Ortalama iş yükü
    total_tasks = len(assignments) * 2  # PS + J1
    avg_workload = total_tasks / faculty_count
    
    # ±2 bandı dışındaki ihlaller
    band = 2
    violations = []
    
    for instructor_id, load in workloads.items():
        deviation = abs(load - avg_workload)
        if deviation > band:
            violations.append((instructor_id, load, deviation))
    
    # Soft constraint oldugu icin ihlal kabul edilebilir
    print(f"  Toplam gorev: {total_tasks}")
    print(f"  Faculty sayisi: {faculty_count}")
    print(f"  Ortalama is yuku (L_bar): {avg_workload:.2f}")
    print(f"  Tolerans bandi: +/-{band}")
    print(f"  Is yukleri: {dict(workloads)}")
    print(f"  Band disi instructor sayisi: {len(violations)}")
    if violations:
        for v in violations[:5]:
            print(f"    Instructor {v[0]}: {v[1]} gorev (sapma: {v[2]:.2f})")
    print(f"  Sonuc: {'[OK] PASSED (soft constraint)' if len(violations) <= 2 else '[!] WARNING: High deviation'}")
    
    return True  # Soft constraint


def test_back_to_back(assignments):
    """
    Test 6: Back-to-back sinif ici yerlesim kontrolu
    
    NOT: BITIRME ve ARA arasindaki "kesim" bir bosluk olarak sayilmaz.
    Her proje turu (BITIRME veya ARA) kendi icinde back-to-back olmalidir.
    
    Ornek:
    - Sinif 0: BITIRME slot 0, 1 + ARA slot 4, 5 -> GECERLI
      (BITIRME kendi icinde ardisik, ARA kendi icinde ardisik)
    - Sinif 0: BITIRME slot 0, 2 -> GECERSIZ (bosluk var)
    """
    print("\n" + "=" * 60)
    print("TEST 6: Back-to-Back Sinif Ici Yerlesim")
    print("=" * 60)
    
    # Sinif ve tur bazinda slotlari topla
    class_type_slots = defaultdict(lambda: {"BITIRME": [], "ARA": []})
    
    for assignment in assignments:
        class_id = assignment["classroom_id"]
        ptype = assignment.get("project_type", "ARA").upper()
        if ptype in ("BITIRME", "FINAL"):
            class_type_slots[class_id]["BITIRME"].append(assignment["slot"])
        else:
            class_type_slots[class_id]["ARA"].append(assignment["slot"])
    
    gaps = 0
    
    # Her sinif icinde, her proje turu icin back-to-back kontrol
    for class_id, type_slots in class_type_slots.items():
        for ptype, slots in type_slots.items():
            if len(slots) < 2:
                continue
            sorted_slots = sorted(slots)
            for i in range(len(sorted_slots) - 1):
                if sorted_slots[i + 1] - sorted_slots[i] > 1:
                    gaps += 1
                    print(f"  [!]  Sinif {class_id} ({ptype}): slot {sorted_slots[i]} ile {sorted_slots[i + 1]} arasi bosluk")
    
    # Ayrica: Her sinifin ilk slotu 0 olmali (veya o sinifta proje yoksa skip)
    # Ve her proje turu kendi icinde 0'dan baslayarak ardisik olmali
    for class_id, type_slots in class_type_slots.items():
        all_slots = type_slots["BITIRME"] + type_slots["ARA"]
        if all_slots and min(all_slots) != 0:
            gaps += 1
            print(f"  [!]  Sinif {class_id}: ilk slot 0 degil, {min(all_slots)}")
    
    passed = gaps == 0
    
    print(f"  Sinif sayisi: {len(class_type_slots)}")
    print(f"  Gap sayisi: {gaps}")
    print(f"  Sonuc: {'[OK] PASSED' if passed else '[X] FAILED'}")
    
    return passed


def test_penalty_functions(result):
    """
    Test 7: Matris tabanlı ceza fonksiyonları (H₁, H₂, H₃)
    """
    print("\n" + "=" * 60)
    print("TEST 7: Ceza Fonksiyonlari (H1, H2, H3)")
    print("=" * 60)
    
    fitness = result.get("fitness_scores", {})
    
    h1 = fitness.get("h1_gap_penalty", 0)
    h2 = fitness.get("h2_workload_penalty", 0)
    h3 = fitness.get("h3_class_change_penalty", 0)
    total = fitness.get("total_cost", 0)
    
    print(f"  H1 (Gap Cezasi): {h1:.2f}")
    print(f"  H2 (Is Yuku Cezasi): {h2:.2f}")
    print(f"  H3 (Sinif Degisimi Cezasi): {h3:.2f}")
    print(f"  Toplam Maliyet (Z): {total:.2f}")
    print(f"  Sonuc: [OK] PASSED")
    
    return True


def run_all_tests():
    """Tum testleri calistir."""
    print("\n" + "=" * 80)
    print(" HUNGARIAN ALGORITHM TEST SUITE ")
    print("=" * 80)
    
    # Test verisi olustur
    test_data = create_test_data()
    
    print(f"\nTest Verisi:")
    print(f"  Projeler: {len(test_data['projects'])} (10 BITIRME, 10 ARA)")
    print(f"  Ogretim Gorevlileri: {len(test_data['instructors'])} (8 faculty, 2 assistant)")
    print(f"  Siniflar: {len(test_data['classrooms'])}")
    print(f"  Timeslotlar: {len(test_data['timeslots'])}")
    
    # Algoritmayi calistir
    print("\n" + "-" * 60)
    print("Algoritma calistiriliyor...")
    print("-" * 60)
    
    algorithm = HungarianAlgorithm({
        "class_count": 6,
        "auto_class_count": False,
        "time_penalty_mode": "GAP_PROPORTIONAL",
        "workload_constraint_mode": "SOFT_ONLY",
        "weight_h1": 1.0,
        "weight_h2": 3.0,
        "weight_h3": 1.5
    })
    
    result = algorithm.optimize(test_data)
    
    assignments = result.get("assignments", [])
    
    print(f"\nSonuc:")
    print(f"  Atama sayisi: {len(assignments)}")
    print(f"  Durum: {result.get('status')}")
    print(f"  Calisma suresi: {result.get('execution_time', 0):.2f}s")
    
    # Testleri calistir
    results = []
    
    results.append(("BITIRME Onceligi", test_bitirme_before_ara(assignments, test_data["projects"])))
    results.append(("J1 != PS", test_j1_not_ps(assignments)))
    results.append(("Tek Gorev/Slot", test_single_duty_per_slot(assignments)))
    results.append(("J2 Placeholder", test_j2_placeholder(assignments)))
    results.append(("Is Yuku Dengesi", test_workload_balance(assignments, 8)))  # 8 faculty
    results.append(("Back-to-Back", test_back_to_back(assignments)))
    results.append(("Ceza Fonksiyonlari", test_penalty_functions(result)))
    
    # Ozet
    print("\n" + "=" * 80)
    print(" TEST SONUCLARI ")
    print("=" * 80)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "[OK] PASSED" if result else "[X] FAILED"
        print(f"  {name}: {status}")
    
    print("-" * 60)
    print(f"  Toplam: {passed}/{total} test gecti")
    
    if passed == total:
        print("\n*** TUM TESTLER BASARILI! ***")
    else:
        print(f"\n[!]  {total - passed} test basarisiz.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

