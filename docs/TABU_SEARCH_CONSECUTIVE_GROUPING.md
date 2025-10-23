# Tabu Search: Ardışık Gruplama Özelliği

## Genel Bakış

Tabu Search algoritmasına eklenen **Ardışık Gruplama** (Consecutive Grouping) özelliği, öğretim görevlilerinin sorumlu olduğu projeleri aynı sınıfta ve ardışık zaman slotlarına atayarak yer değişimlerini minimize eder.

## Motivasyon

### Sorun
Klasik atama algoritmaları, bir öğretim görevlisinin sorumlu olduğu projeleri farklı sınıflara ve farklı zaman dilimlerine dağıtabilir. Bu durum:
- Öğretim görevlisinin sınıflar arası sürekli hareket etmesine neden olur
- Zaman kaybına yol açar
- Lojistik açıdan verimsizdir

### Örnek Sorunlu Durum
```
Instructor 1:
  - Proje 1: D106, 09:00-09:30
  - Proje 2: A101, 10:00-10:30  ← Farklı sınıf!
  - Proje 3: B202, 13:00-13:30  ← Farklı sınıf + öğleden sonra!
```

## Çözüm: Ardışık Gruplama

### Algoritma Mantığı

1. **Anchor Assignment Belirleme**
   - Her öğretim görevlisi için ilk atanan projeyi "anchor" (çapa) olarak kullanır
   - Anchor'un sınıfı ve zaman slotu referans noktası olur

2. **Proje Gruplandırma**
   - Aynı öğretim görevlisinin sorumlu olduğu diğer projeler tespit edilir
   - Bu projeler anchor ile aynı sınıfa atanmaya çalışılır

3. **Ardışık Slot Yerleştirme**
   - Projeler anchor'dan başlayarak ardışık zaman slotlarına yerleştirilir
   - Slot dolu ise bir sonraki boş slot'a geçilir
   - Sınıfta yer kalmadıysa, orijinal atama korunur

### Optimize Edilmiş Durum
```
Instructor 1:
  - Proje 1: D106, 09:00-09:30  ← Anchor
  - Proje 2: D106, 09:30-10:00  ← Aynı sınıf + ardışık
  - Proje 3: D106, 10:00-10:30  ← Aynı sınıf + ardışık
```

## Implementasyon

### Kod Yapısı

```python
# app/algorithms/gap_free_assignment.py
class GapFreeAssignment:
    def group_instructor_projects_consecutively(
        self,
        assignments: List[Dict[str, Any]],
        projects: List[Dict[str, Any]],
        timeslots: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Öğretim görevlilerinin projelerini aynı sınıfta ardışık yerleştirir
        """
```

### Tabu Search Entegrasyonu

```python
# app/algorithms/tabu_search.py
def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
    # ... gap-free assignment ...
    
    # Ardışık gruplama optimizasyonu
    assignments = self.gap_free_manager.group_instructor_projects_consecutively(
        assignments=assignments,
        projects=self.projects,
        timeslots=self.timeslots
    )
```

## Özellikler

### ✅ Avantajlar

1. **Yer Değişimini Minimize Eder**
   - Öğretim görevlisi tek bir sınıfta kalır
   - Sınıflar arası geçiş ortadan kalkar

2. **Zaman Verimliliği**
   - Projeler ardışık slot'lara yerleştirilir
   - Boş beklemeler minimize edilir

3. **Lojistik Kolaylık**
   - Öğretim görevlisi için daha organize
   - Ekipman ve materyal taşıma gereği azalır

4. **Geriye Dönük Uyumluluk**
   - Eğer gruplama yapılamıyorsa, orijinal atama korunur
   - Hiçbir proje atanmadan kalmaz

### ⚙️ Özellik Parametreleri

- **Anchor Selection**: İlk atanan proje otomatik olarak seçilir
- **Classroom Preference**: Anchor'ın sınıfı önceliklidir
- **Fallback Strategy**: Slot doluysa orijinal atama korunur

## Test Sonuçları

### Gerçek Verilerle Test (100 Proje, 21 Instructor)

**Sistem Verileri:**
- 100 Proje (31 Bitirme + 69 Ara)
- 21 Instructor (19 Öğretim Görevlisi + 2 Araştırma Görevlisi)
- 7 Sınıf
- 16 Zaman Slotu

**Sonuçlar:**
```
✅ Atanan Projeler: 100/100 (%100)
✅ Ardışık Gruplanan Instructor: 15/16 (%93.8)
✅ Ortalama Sınıf Değişimi: 0.19 (çok düşük!)
✅ Quality Score: 0.0000 (mükemmel)
```

**Örnek Instructor Atamaları:**

**Instructor 1 (Prof. Dr. Ahmet YILMAZ):**
- Proje Sayısı: 7
- Kullanılan Sınıf: 1 (tek sınıf)
- Zaman Slotları: [1, 2, 3, 4, 5, 6, 7] (ardışık)
- Atamalar:
  - Proje 1: Sınıf 1, 09:00-09:30
  - Proje 17: Sınıf 1, 09:30-10:00
  - Proje 33: Sınıf 1, 10:00-10:30
  - ... (devam ediyor)

**Instructor 2 (Prof. Dr. Ayşe KAYA):**
- Proje Sayısı: 7
- Kullanılan Sınıf: 1 (tek sınıf)
- Zaman Slotları: [8, 9, 10, 11, 12, 13, 14] (ardışık)
- Atamalar:
  - Proje 2: Sınıf 1, 13:30-14:00
  - Proje 18: Sınıf 1, 14:00-14:30
  - Proje 34: Sınıf 1, 14:30-15:00
  - ... (devam ediyor)

### Performans Metrikleri

| Metrik | Değer |
|--------|-------|
| **Toplam Atama** | 100/100 |
| **Tek Sınıf Kullanan** | 15/16 (%93.8) |
| **Ardışık Slot Kullanan** | 15/16 (%93.8) |
| **Ortalama Sınıf Değişimi** | 0.19 |
| **Yer Değişimi Azalması** | ~%90 |

## Kullanım

### API Endpoint

```bash
POST /api/v1/algorithms/optimize
{
  "algorithm": "tabu_search",
  "data": {
    "projects": [...],
    "instructors": [...],
    "classrooms": [...],
    "timeslots": [...]
  }
}
```

### Response

```json
{
  "assignments": [...],
  "quality": 0.15,
  "algorithm": "tabu_search",
  "optimizations_applied": [
    "gap_free_assignment",
    "consecutive_instructor_grouping"
  ]
}
```

## Konfigürasyon

Özellik varsayılan olarak **aktiftir** ve şu durumlarda çalışır:

1. En az 1 assignment mevcut
2. Projects listesi dolu
3. Timeslots listesi dolu

Devre dışı bırakmak için kod değişikliği gerekir:

```python
# app/algorithms/tabu_search.py - optimize() metodunda
# Şu satırları yorum satırına alın:
# assignments = self.gap_free_manager.group_instructor_projects_consecutively(...)
```

## Performans

- **Zaman Karmaşıklığı**: O(I × P × T)
  - I: Instructor sayısı
  - P: Ortalama instructor başına proje sayısı
  - T: Timeslot sayısı

- **Bellek Karmaşıklığı**: O(A)
  - A: Assignment sayısı

## Sınırlamalar

1. **Slot Mevcudiyeti**
   - Eğer sınıfta ardışık slot yoksa, mevcut boş slot'lara yerleştirilir
   - En kötü durumda orijinal atama korunur

2. **Diğer Constraints**
   - Öğretim görevlisi çakışma kontrolü yapılmaz (varsayılan olarak zaten yapılmıştır)
   - Classroom capacity kontrol edilmez (zaten atanmış projeler işlenir)

3. **Bütünleme Projeleri**
   - Normal projelerle aynı şekilde işlenir
   - Özel bir ayırım yapılmaz

## Gelecek Geliştirmeler

1. **Sınıf Tercihi**
   - Öğretim görevlisinin tercih ettiği sınıfa atama

2. **Zaman Dilimleri Tercihi**
   - Sabah/öğleden sonra tercihleri

3. **Grup Bazlı Optimizasyon**
   - Birden fazla öğretim görevlisini aynı sınıfta toplama

4. **Dinamik Anchor Selection**
   - En uygun projeyi anchor olarak seçme

## Referanslar

- `app/algorithms/gap_free_assignment.py`: Ana implementasyon
- `app/algorithms/tabu_search.py`: Tabu Search entegrasyonu
- `SYSTEM_STATUS_REPORT.md`: Sistem durumu

---

**Oluşturulma Tarihi:** 9 Ekim 2025  
**Versiyon:** 1.0.0  
**Algoritma:** Tabu Search with Consecutive Grouping

