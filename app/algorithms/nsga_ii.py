"""
NSGA-II (Non-dominated Sorting Genetic Algorithm II) algoritması sınıfı.
"""
from typing import Dict, Any, List, Tuple
import random
import numpy as np
from operator import itemgetter

from app.algorithms.base import OptimizationAlgorithm

class NSGAII(OptimizationAlgorithm):
    """
    NSGA-II (Non-dominated Sorting Genetic Algorithm II) algoritması sınıfı.
    Çok amaçlı optimizasyon için NSGA-II algoritması kullanarak proje atama problemini çözer.
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        """
        NSGA-II algoritması başlatıcı.
        
        Args:
            params: Algoritma parametreleri.
        """
        super().__init__(params)
        params = params or {}
        self.population_size = params.get("population_size", 100)
        self.n_generations = params.get("n_generations", 50)
        self.crossover_rate = params.get("crossover_rate", 0.8)
        self.mutation_rate = params.get("mutation_rate", 0.2)
        self.tournament_size = params.get("tournament_size", 3)
        self.best_solution = None
        self.best_fitness = None
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        NSGA-II algoritmasını başlangıç verileri ile başlatır.
        
        Args:
            data: Algoritma giriş verileri.
        """
        self.instructors = data.get("instructors", [])
        self.projects = data.get("projects", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])
        
        # Popülasyonu başlat
        self.population = self._initialize_population()
    
    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        NSGA-II algoritmasını çalıştırır.
        
        Args:
            data: Algoritma giriş verileri.
            
        Returns:
            Dict[str, Any]: Optimizasyon sonucu.
        """
        # İlk popülasyonu değerlendir
        self._evaluate_population(self.population)
        
        # Nesil döngüsü
        for generation in range(self.n_generations):
            # Ebeveyn seçimi
            parents = self._select_parents()
            
            # Yeni nesil oluştur
            offspring = self._create_offspring(parents)
            
            # Yeni nesli değerlendir
            self._evaluate_population(offspring)
            
            # Popülasyonu güncelle (elitizm)
            self.population = self._update_population(self.population, offspring)
        
        # En iyi çözümü bul
        self._find_best_solution()
        
        # Sonucu döndür
        return {
            "schedule": self.best_solution,
            "fitness": self.best_fitness,
            "generations": self.n_generations
        }
    
    def _initialize_population(self) -> List[Dict[str, Any]]:
        """
        Başlangıç popülasyonunu oluşturur.
        
        Returns:
            List[Dict[str, Any]]: Başlangıç popülasyonu.
        """
        population = []
        
        for _ in range(self.population_size):
            # Rastgele bir çözüm oluştur
            solution = self._create_random_solution()
            
            # Çözümü popülasyona ekle
            population.append({
                "solution": solution,
                "objectives": None,  # Henüz değerlendirilmedi
                "rank": None,        # Henüz sıralanmadı
                "crowding_distance": None  # Henüz hesaplanmadı
            })
        
        return population
    
    def _create_random_solution(self) -> List[Dict[str, Any]]:
        """
        Rastgele bir çözüm oluşturur.
        
        Returns:
            List[Dict[str, Any]]: Rastgele çözüm.
        """
        solution = []
        
        # Proje, sınıf ve zaman dilimi atamalarını takip et
        assigned_projects = set()
        assigned_classrooms_timeslots = set()  # (classroom_id, timeslot_id) çiftleri
        
        # Projeleri rastgele sırala
        projects = list(self.projects)
        random.shuffle(projects)
        
        for project in projects:
            # Rastgele bir sınıf ve zaman dilimi seç
            available_classrooms = list(self.classrooms)
            random.shuffle(available_classrooms)
            
            assigned = False
            
            for classroom in available_classrooms:
                if assigned:
                    break
                    
                available_timeslots = list(self.timeslots)
                random.shuffle(available_timeslots)
                
                for timeslot in available_timeslots:
                    if (classroom.get("id"), timeslot.get("id")) not in assigned_classrooms_timeslots:
                        # Sorumlu öğretim üyesi
                        responsible_id = project.get("responsible_id", None)
                        instructors = [responsible_id] if responsible_id else []
                        
                        # Rastgele 1-2 yardımcı katılımcı ekle
                        available_instructors = [i for i in self.instructors if i.get("id") != responsible_id]
                        if available_instructors:
                            # Proje tipine göre katılımcı sayısını belirle
                            if project.get("type") == "bitirme":
                                # Bitirme projesi için en az 2 hoca olmalı
                                hocas = [i for i in available_instructors if i.get("role") == "hoca"]
                                aras_gors = [i for i in available_instructors if i.get("role") == "aras_gor"]
                                
                                if len(hocas) > 0:
                                    # En az bir hoca ekle
                                    instructors.append(random.choice(hocas).get("id"))
                                    
                                    # Üçüncü kişi olarak hoca veya araş. gör. ekle
                                    if len(hocas) > 1 and random.random() > 0.5:
                                        instructors.append(random.choice(hocas).get("id"))
                                    elif aras_gors:
                                        instructors.append(random.choice(aras_gors).get("id"))
                            else:
                                # Ara proje için rastgele 2 kişi ekle
                                selected = random.sample(available_instructors, min(2, len(available_instructors)))
                                for instructor in selected:
                                    instructors.append(instructor.get("id"))
                        
                        # Atamayı ekle
                        assignment = {
                            "project_id": project.get("id"),
                            "classroom_id": classroom.get("id"),
                            "timeslot_id": timeslot.get("id"),
                            "instructors": instructors
                        }
                        
                        solution.append(assignment)
                        assigned_projects.add(project.get("id"))
                        assigned_classrooms_timeslots.add((classroom.get("id"), timeslot.get("id")))
                        assigned = True
                        break
        
        return solution
    
    def _evaluate_population(self, population: List[Dict[str, Any]]) -> None:
        """
        Popülasyondaki her bireyin amaç fonksiyonlarını değerlendirir.
        
        Args:
            population: Değerlendirilecek popülasyon.
        """
        for individual in population:
            solution = individual["solution"]
            
            # Çoklu amaç fonksiyonlarını hesapla
            objectives = self._calculate_objectives(solution)
            
            # Bireyin amaç fonksiyonu değerlerini güncelle
            individual["objectives"] = objectives
    
    def _calculate_objectives(self, solution: List[Dict[str, Any]]) -> List[float]:
        """
        Verilen çözümün çoklu amaç fonksiyonu değerlerini hesaplar.
        
        Args:
            solution: Değerlendirilecek çözüm.
            
        Returns:
            List[float]: Amaç fonksiyonu değerleri.
        """
        # Çözüm geçerli mi?
        if not self._is_valid_solution(solution):
            return [float('-inf'), float('-inf'), float('-inf')]
        
        # Amaç 1: Hocaların sınıf geçişlerini minimize et
        instructor_changes = self._count_instructor_classroom_changes(solution)
        obj1 = -instructor_changes  # Negatif, çünkü minimize etmek istiyoruz
        
        # Amaç 2: Yük dengesini maksimize et
        load_balance = self._calculate_load_balance(solution)
        obj2 = load_balance
        
        # Amaç 3: Proje kurallarına uygunluğu maksimize et
        rule_compliance = self._calculate_rule_compliance(solution)
        obj3 = rule_compliance
        
        return [obj1, obj2, obj3]
    
    def _select_parents(self) -> List[Dict[str, Any]]:
        """
        Ebeveyn seçimi yapar.
        
        Returns:
            List[Dict[str, Any]]: Seçilen ebeveynler.
        """
        # Popülasyonu sırala
        self._fast_non_dominated_sort(self.population)
        
        # Kalabalık mesafesini hesapla
        self._calculate_crowding_distance(self.population)
        
        parents = []
        
        # Turnuva seçimi
        for _ in range(self.population_size):
            # Rastgele turnuva adayları seç
            tournament_candidates = random.sample(self.population, self.tournament_size)
            
            # En iyi adayı seç (rank ve crowding_distance'a göre)
            best_candidate = min(tournament_candidates, key=lambda x: (x["rank"], -x["crowding_distance"]))
            
            parents.append(best_candidate)
        
        return parents
    
    def _create_offspring(self, parents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ebeveynlerden yeni nesil oluşturur.
        
        Args:
            parents: Ebeveyn popülasyonu.
            
        Returns:
            List[Dict[str, Any]]: Yeni nesil.
        """
        offspring = []
        
        # Ebeveynleri karıştır
        random.shuffle(parents)
        
        # Çaprazlama ve mutasyon
        for i in range(0, len(parents), 2):
            if i + 1 < len(parents):
                parent1 = parents[i]
                parent2 = parents[i + 1]
                
                # Çaprazlama
                if random.random() < self.crossover_rate:
                    child1, child2 = self._crossover(parent1["solution"], parent2["solution"])
                else:
                    child1, child2 = parent1["solution"], parent2["solution"]
                
                # Mutasyon
                if random.random() < self.mutation_rate:
                    child1 = self._mutate(child1)
                if random.random() < self.mutation_rate:
                    child2 = self._mutate(child2)
                
                # Yeni bireyleri ekle
                offspring.append({
                    "solution": child1,
                    "objectives": None,
                    "rank": None,
                    "crowding_distance": None
                })
                
                offspring.append({
                    "solution": child2,
                    "objectives": None,
                    "rank": None,
                    "crowding_distance": None
                })
        
        return offspring
    
    def _crossover(self, solution1: List[Dict[str, Any]], solution2: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        İki çözüm arasında çaprazlama yapar.
        
        Args:
            solution1: Birinci ebeveyn çözümü.
            solution2: İkinci ebeveyn çözümü.
            
        Returns:
            Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]: İki yavru çözüm.
        """
        # Tek noktalı çaprazlama
        if not solution1 or not solution2:
            return solution1, solution2
        
        # Çaprazlama noktası
        crossover_point = random.randint(1, min(len(solution1), len(solution2)) - 1)
        
        # Yeni çözümler
        child1 = solution1[:crossover_point] + solution2[crossover_point:]
        child2 = solution2[:crossover_point] + solution1[crossover_point:]
        
        # Çözümleri düzelt (çakışmaları gider)
        child1 = self._repair_solution(child1)
        child2 = self._repair_solution(child2)
        
        return child1, child2
    
    def _mutate(self, solution: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Çözüme mutasyon uygular.
        
        Args:
            solution: Mutasyon uygulanacak çözüm.
            
        Returns:
            List[Dict[str, Any]]: Mutasyona uğramış çözüm.
        """
        if not solution:
            return solution
        
        # Rastgele bir atamayı değiştir
        mutation_idx = random.randint(0, len(solution) - 1)
        assignment = solution[mutation_idx]
        
        # Rastgele bir sınıf veya zaman dilimi değiştir
        if random.random() < 0.5:
            # Sınıfı değiştir
            available_classrooms = [c for c in self.classrooms if c.get("id") != assignment["classroom_id"]]
            if available_classrooms:
                new_classroom = random.choice(available_classrooms)
                assignment["classroom_id"] = new_classroom.get("id")
        else:
            # Zaman dilimini değiştir
            available_timeslots = [t for t in self.timeslots if t.get("id") != assignment["timeslot_id"]]
            if available_timeslots:
                new_timeslot = random.choice(available_timeslots)
                assignment["timeslot_id"] = new_timeslot.get("id")
        
        # Çözümü düzelt (çakışmaları gider)
        solution = self._repair_solution(solution)
        
        return solution
    
    def _repair_solution(self, solution: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Çözümdeki çakışmaları giderir.
        
        Args:
            solution: Düzeltilecek çözüm.
            
        Returns:
            List[Dict[str, Any]]: Düzeltilmiş çözüm.
        """
        # Proje, sınıf ve zaman dilimi atamalarını takip et
        assigned_projects = set()
        assigned_classrooms_timeslots = set()  # (classroom_id, timeslot_id) çiftleri
        
        # Geçerli atamaları koru
        valid_assignments = []
        
        for assignment in solution:
            project_id = assignment.get("project_id")
            classroom_id = assignment.get("classroom_id")
            timeslot_id = assignment.get("timeslot_id")
            
            # Çakışma kontrolü
            if project_id not in assigned_projects and (classroom_id, timeslot_id) not in assigned_classrooms_timeslots:
                valid_assignments.append(assignment)
                assigned_projects.add(project_id)
                assigned_classrooms_timeslots.add((classroom_id, timeslot_id))
        
        return valid_assignments
    
    def _update_population(self, population: List[Dict[str, Any]], offspring: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Popülasyonu günceller (elitizm).
        
        Args:
            population: Mevcut popülasyon.
            offspring: Yeni nesil.
            
        Returns:
            List[Dict[str, Any]]: Güncellenmiş popülasyon.
        """
        # Popülasyon ve yeni nesli birleştir
        combined = population + offspring
        
        # Baskınlık sıralaması
        self._fast_non_dominated_sort(combined)
        
        # Kalabalık mesafesini hesapla
        self._calculate_crowding_distance(combined)
        
        # Yeni popülasyonu oluştur
        new_population = []
        
        # Sıralama ve kalabalık mesafesine göre sırala
        sorted_combined = sorted(combined, key=lambda x: (x["rank"], -x["crowding_distance"]))
        
        # En iyi bireyleri seç
        new_population = sorted_combined[:self.population_size]
        
        return new_population
    
    def _fast_non_dominated_sort(self, population: List[Dict[str, Any]]) -> None:
        """
        Hızlı baskınlık sıralaması yapar.
        
        Args:
            population: Sıralanacak popülasyon.
        """
        # Her birey için baskınlık sayısı ve baskıladığı bireyler
        n = {}  # Bireyin baskılandığı sayı
        S = {}  # Bireyin baskıladığı bireyler
        
        # Sıralama
        fronts = [[]]  # İlk cephe
        
        for p_idx, p in enumerate(population):
            n[p_idx] = 0
            S[p_idx] = []
            
            for q_idx, q in enumerate(population):
                if p_idx != q_idx:
                    # p, q'yu baskılıyor mu?
                    if self._dominates(p, q):
                        S[p_idx].append(q_idx)
                    # q, p'yi baskılıyor mu?
                    elif self._dominates(q, p):
                        n[p_idx] += 1
            
            # Eğer p hiçbir birey tarafından baskılanmıyorsa, ilk cepheye ekle
            if n[p_idx] == 0:
                p["rank"] = 0
                fronts[0].append(p_idx)
        
        # Diğer cepheleri oluştur
        i = 0
        while fronts[i]:
            next_front = []
            
            for p_idx in fronts[i]:
                for q_idx in S[p_idx]:
                    n[q_idx] -= 1
                    if n[q_idx] == 0:
                        population[q_idx]["rank"] = i + 1
                        next_front.append(q_idx)
            
            i += 1
            if next_front:
                fronts.append(next_front)
    
    def _calculate_crowding_distance(self, population: List[Dict[str, Any]]) -> None:
        """
        Kalabalık mesafesini hesaplar.
        
        Args:
            population: Mesafesi hesaplanacak popülasyon.
        """
        if not population:
            return
        
        # Her birey için kalabalık mesafesini sıfırla
        for individual in population:
            individual["crowding_distance"] = 0
        
        # Her amaç fonksiyonu için
        n_objectives = len(population[0]["objectives"])
        
        for obj_idx in range(n_objectives):
            # Amaç fonksiyonuna göre sırala
            sorted_pop = sorted(population, key=lambda x: x["objectives"][obj_idx])
            
            # Sınır bireyleri için sonsuz mesafe
            sorted_pop[0]["crowding_distance"] = float('inf')
            sorted_pop[-1]["crowding_distance"] = float('inf')
            
            # Amaç fonksiyonu değerlerinin aralığı
            obj_min = sorted_pop[0]["objectives"][obj_idx]
            obj_max = sorted_pop[-1]["objectives"][obj_idx]
            
            # Aralık sıfır değilse
            if obj_max - obj_min > 0:
                # Diğer bireyler için mesafeyi hesapla
                for i in range(1, len(sorted_pop) - 1):
                    sorted_pop[i]["crowding_distance"] += (
                        sorted_pop[i + 1]["objectives"][obj_idx] - sorted_pop[i - 1]["objectives"][obj_idx]
                    ) / (obj_max - obj_min)
    
    def _dominates(self, p: Dict[str, Any], q: Dict[str, Any]) -> bool:
        """
        p'nin q'yu baskılayıp baskılamadığını kontrol eder.
        
        Args:
            p: Birinci birey.
            q: İkinci birey.
            
        Returns:
            bool: p, q'yu baskılıyorsa True, değilse False.
        """
        if p["objectives"] is None or q["objectives"] is None:
            return False
        
        better_in_one = False
        
        for p_obj, q_obj in zip(p["objectives"], q["objectives"]):
            if p_obj < q_obj:
                return False
            if p_obj > q_obj:
                better_in_one = True
        
        return better_in_one
    
    def _find_best_solution(self) -> None:
        """
        En iyi çözümü bulur.
        """
        # İlk cephedeki çözümler arasından en iyi olanı seç
        first_front = [ind for ind in self.population if ind["rank"] == 0]
        
        if first_front:
            # En yüksek kalabalık mesafesine sahip çözümü seç
            best_individual = max(first_front, key=lambda x: x["crowding_distance"])
            
            self.best_solution = best_individual["solution"]
            self.best_fitness = best_individual["objectives"]
    
    def _is_valid_solution(self, solution: List[Dict[str, Any]]) -> bool:
        """
        Çözümün geçerli olup olmadığını kontrol eder.
        
        Args:
            solution: Kontrol edilecek çözüm.
            
        Returns:
            bool: Çözüm geçerliyse True, değilse False.
        """
        if not solution:
            return False
        
        # Proje, sınıf ve zaman dilimi atamalarını takip et
        assigned_projects = set()
        assigned_classrooms_timeslots = set()  # (classroom_id, timeslot_id) çiftleri
        
        for assignment in solution:
            project_id = assignment.get("project_id")
            classroom_id = assignment.get("classroom_id")
            timeslot_id = assignment.get("timeslot_id")
            
            # Bir proje birden fazla kez atanmamalı
            if project_id in assigned_projects:
                return False
            
            # Bir sınıf-zaman dilimi çifti birden fazla kez atanmamalı
            if (classroom_id, timeslot_id) in assigned_classrooms_timeslots:
                return False
            
            assigned_projects.add(project_id)
            assigned_classrooms_timeslots.add((classroom_id, timeslot_id))
        
        return True
    
    def _count_instructor_classroom_changes(self, solution: List[Dict[str, Any]]) -> int:
        """
        Öğretim üyelerinin sınıf değişim sayısını hesaplar.
        
        Args:
            solution: Atama planı
            
        Returns:
            int: Toplam sınıf değişim sayısı
        """
        if not solution:
            return 0
        
        # Öğretim üyesi başına sınıf değişim sayısını hesapla
        instructor_locations = {}
        changes = 0
        
        # Zaman dilimine göre sırala
        sorted_solution = sorted(solution, key=lambda x: x["timeslot_id"])
        
        for assignment in sorted_solution:
            classroom_id = assignment["classroom_id"]
            for instructor_id in assignment["instructors"]:
                if instructor_id in instructor_locations:
                    if instructor_locations[instructor_id] != classroom_id:
                        changes += 1
                        instructor_locations[instructor_id] = classroom_id
                else:
                    instructor_locations[instructor_id] = classroom_id
        
        return changes
    
    def _calculate_load_balance(self, solution: List[Dict[str, Any]]) -> float:
        """
        Öğretim üyesi yük dengesini hesaplar.
        
        Args:
            solution: Atama planı
            
        Returns:
            float: Yük dengesi skoru (0-1 arası, 1 en iyi)
        """
        if not solution:
            return 0.0
        
        # Öğretim üyesi başına atama sayısını hesapla
        instructor_loads = {}
        
        for assignment in solution:
            for instructor_id in assignment["instructors"]:
                instructor_loads[instructor_id] = instructor_loads.get(instructor_id, 0) + 1
        
        # Yük dengesini hesapla (Gini katsayısı)
        if not instructor_loads:
            return 0.0
        
        loads = list(instructor_loads.values())
        
        # Gini katsayısı hesapla
        array = np.array(loads)
        if np.amin(array) < 0:
            array -= np.amin(array)
        array += 0.0000001
        array = np.sort(array)
        index = np.arange(1, array.shape[0] + 1)
        n = array.shape[0]
        gini = ((np.sum((2 * index - n - 1) * array)) / (n * np.sum(array)))
        
        # Gini katsayısı 0 (tam eşitlik) ile 1 (tam eşitsizlik) arasındadır
        # Biz dengeyi istediğimiz için 1 - gini döndürüyoruz
        return 1.0 - gini
    
    def _calculate_rule_compliance(self, solution: List[Dict[str, Any]]) -> float:
        """
        Proje kurallarına uygunluğu hesaplar.
        
        Args:
            solution: Atama planı
            
        Returns:
            float: Kural uygunluk skoru (0-1 arası, 1 en iyi)
        """
        if not solution:
            return 0.0
        
        total_rules = 0
        satisfied_rules = 0
        
        for assignment in solution:
            project_id = assignment["project_id"]
            instructors = assignment["instructors"]
            
            # Projeyi bul
            project = next((p for p in self.projects if p.get("id") == project_id), None)
            if not project:
                continue
            
            # Kural 1: Her projede 3 katılımcı olmalı
            total_rules += 1
            if len(instructors) == 3:
                satisfied_rules += 1
            
            # Kural 2: İlk kişi projenin sorumlu hocası olmalı
            total_rules += 1
            if instructors and instructors[0] == project.get("responsible_id"):
                satisfied_rules += 1
            
            # Proje tipine göre kurallar
            if project.get("type") == "bitirme":
                # Kural 3: Bitirme projesinde en az 2 hoca olmalı
                total_rules += 1
                hoca_count = 0
                for instructor_id in instructors:
                    instructor = next((i for i in self.instructors if i.get("id") == instructor_id), None)
                    if instructor and instructor.get("role") == "hoca":
                        hoca_count += 1
                
                if hoca_count >= 2:
                    satisfied_rules += 1
            
            elif project.get("type") == "ara":
                # Kural 4: Ara projede en az 1 hoca olmalı
                total_rules += 1
                has_hoca = False
                for instructor_id in instructors:
                    instructor = next((i for i in self.instructors if i.get("id") == instructor_id), None)
                    if instructor and instructor.get("role") == "hoca":
                        has_hoca = True
                        break
                
                if has_hoca:
                    satisfied_rules += 1
        
        # Kural uygunluk oranını hesapla
        if total_rules > 0:
            return satisfied_rules / total_rules
        else:
            return 0.0 