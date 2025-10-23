"""
NSGA-II (Non-dominated Sorting Genetic Algorithm II) algoritması sınıfı - CP-SAT özellikli versiyon.
"""
from typing import Dict, Any, List, Tuple, Optional
import random
import numpy as np
import logging
from operator import itemgetter

from app.algorithms.base import OptimizationAlgorithm
from app.algorithms.gap_free_assignment import GapFreeAssignment

logger = logging.getLogger(__name__)

class NSGAII(OptimizationAlgorithm):
    """
    NSGA-II (Non-dominated Sorting Genetic Algorithm II) algoritması sınıfı.
    Çok amaçlı optimizasyon için NSGA-II algoritması kullanarak proje atama problemini çözer.
    """
    
    
    def _prioritize_projects_for_gap_free(self) -> List[Dict[str, Any]]:
        """Projeleri gap-free için önceliklendir."""
        bitirme_normal = [p for p in self.projects if p.get("type") == "bitirme" and not p.get("is_makeup", False)]
        ara_normal = [p for p in self.projects if p.get("type") == "ara" and not p.get("is_makeup", False)]
        bitirme_makeup = [p for p in self.projects if p.get("type") == "bitirme" and p.get("is_makeup", False)]
        ara_makeup = [p for p in self.projects if p.get("type") == "ara" and p.get("is_makeup", False)]
        return bitirme_normal + ara_normal + bitirme_makeup + ara_makeup

def __init__(self, params: Dict[str, Any] = None):
        """
        NSGA-II algoritması başlatıcı - CP-SAT özellikli versiyon.

    def _select_instructors_for_project_gap_free(self, project: Dict[str, Any], instructor_timeslot_usage: Dict[int, Set[int]]) -> List[int]:
        """
        Proje için instructor seçer (gap-free versiyonu).
        
        Kurallar:
        - Bitirme: 1 sorumlu + en az 1 jüri (hoca veya araştırma görevlisi)
        - Ara: 1 sorumlu
        - Aynı kişi hem sorumlu hem jüri OLAMAZ
        
        Args:
            project: Proje
            instructor_timeslot_usage: Kullanım bilgisi
            
        Returns:
            Instructor ID listesi
        """
        instructors = []
        project_type = project.get("type", "ara")
        responsible_id = project.get("responsible_id")
        
        # Sorumlu her zaman ilk sırada
        if responsible_id:
            instructors.append(responsible_id)
        else:
            logger.error(f"{self.__class__.__name__}: Project {project.get("id")} has NO responsible_id!")
            return []
        
        # Proje tipine göre ek instructor seç
        if project_type == "bitirme":
            # Bitirme için EN AZ 1 jüri gerekli (sorumlu hariç)
            available_jury = [i for i in self.instructors 
                            if i.get("id") != responsible_id]
            
            # Önce hocaları tercih et, sonra araştırma görevlileri
            faculty = [i for i in available_jury if i.get("type") == "instructor"]
            assistants = [i for i in available_jury if i.get("type") == "assistant"]
            
            # En az 1 jüri ekle (tercihen faculty)
            if faculty:
                instructors.append(faculty[0].get("id"))
            elif assistants:
                instructors.append(assistants[0].get("id"))
            else:
                logger.warning(f"{self.__class__.__name__}: No jury available for bitirme project {project.get("id")}")
                return []  # Bitirme için jüri zorunlu!
        
        # Ara proje için sadece sorumlu yeterli
        return instructors

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

        # CP-SAT özellikleri
        self.time_limit = params.get("time_limit", 60) if params else 60  # Saniye cinsinden zaman limiti
        self.max_load_tolerance = params.get("max_load_tolerance", 2) if params else 2  # ortalamanın +2 fazlasını geçmesin
        self.best_solution = None
        self.best_fitness = float('-inf')

        # CP-SAT özellikleri için ek veri yapıları
        self._instructor_timeslot_usage = {}
    
    def initialize(self, data: Dict[str, Any]) -> None:
        """
        NSGA-II algoritmasını başlangıç verileri ile başlatır - CP-SAT özellikli versiyon.

        Args:
            data: Algoritma giriş verileri.
        """
        self.instructors = data.get("instructors", [])
        self.projects = data.get("projects", [])
        self.classrooms = data.get("classrooms", [])
        self.timeslots = data.get("timeslots", [])

        # CP-SAT özelliği: instructor timeslot kullanım takibi
        self._instructor_timeslot_usage = {}
        for inst in self.instructors:
            self._instructor_timeslot_usage[inst.get("id")] = set()

        # Popülasyonu başlat
        self.population = self._initialize_population()
    
    def optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        NSGA-II algoritmasını çalıştırır - CP-SAT özellikli versiyon.

        Args:
            data: Algoritma giriş verileri.

        Returns:
            Dict[str, Any]: Optimizasyon sonucu.
        """
        import time
        start_time = time.time()

        # İlk popülasyonu değerlendir
        try:
            logger.info(f"NSGA-II: Initializing population with {len(self.population)} individuals")
            logger.info(f"NSGA-II: Projects: {len(self.projects)}, Instructors: {len(self.instructors)}, Classrooms: {len(self.classrooms)}, Timeslots: {len(self.timeslots)}")
            self._evaluate_population(self.population)
            logger.info(f"NSGA-II: Population evaluation completed")
        except Exception as e:
            print(f"Error in NSGA-II population evaluation: {e}")
            return {"assignments": [], "error": str(e)}

        # CP-SAT özelliği: En iyi çözümü başlat
        self._find_best_solution()

        # CP-SAT özelliği: Nesil döngüsü (zaman limiti içinde)
        generation = 0
        while time.time() - start_time < self.time_limit and generation < self.n_generations:
            try:
                # Ebeveyn seçimi
                parents = self._select_parents()

                # Yeni nesil oluştur
                offspring = self._create_offspring(parents)
            except Exception as e:
                print(f"Error in NSGA-II generation {generation}: {e}")
                break

            # Yeni nesli değerlendir
            self._evaluate_population(offspring)

            # Popülasyonu güncelle (elitizm)
            self.population = self._update_population(self.population, offspring)

            # En iyi çözümü güncelle
            self._find_best_solution()

            generation += 1

        # Sonucu döndür
        return {
            "schedule": self.best_solution or [],
            "fitness": self.best_fitness,
            "generations": generation,
            "execution_time": time.time() - start_time
        }
    
    def _initialize_population(self) -> List[Dict[str, Any]]:
        """
        Başlangıç popülasyonunu oluşturur.
        
        Returns:
            List[Dict[str, Any]]: Başlangıç popülasyonu.
        """
        population = []
        
        logger.info(f"NSGA-II: Creating population of size {self.population_size}")

        for i in range(self.population_size):
            # Rastgele bir çözüm oluştur
            solution = self._create_random_solution()
            logger.info(f"NSGA-II: Individual {i} solution length: {len(solution)}")
            
            # Çözümü popülasyona ekle
            population.append({
                "solution": solution,
                "objectives": [0.0, 0.0, 0.0, 0.0, 0.0],  # Initialize with 5 objectives
                "rank": None,        # Henüz sıralanmadı
                "crowding_distance": 0.0  # Initialize with default value
            })
        
        logger.info(f"NSGA-II: Population created with {len(population)} individuals")
        return population
    
    def _create_random_solution(self) -> List[Dict[str, Any]]:
        """
        Rastgele bir çözüm oluşturur (tüm projeler için geçerli atamalar).
        
        Returns:
            List[Dict[str, Any]]: Rastgele çözüm.
        """
        solution = []

        logger.info(f"NSGA-II: Creating random solution for {len(self.projects)} projects")
        logger.info(f"NSGA-II: Data check - Projects: {len(self.projects)}, Instructors: {len(self.instructors)}, Classrooms: {len(self.classrooms)}, Timeslots: {len(self.timeslots)}")
        
        # Ensure we have valid data
        if not self.projects or not self.instructors or not self.classrooms or not self.timeslots:
            logger.warning(f"NSGA-II: Missing data - Projects: {len(self.projects)}, Instructors: {len(self.instructors)}, Classrooms: {len(self.classrooms)}, Timeslots: {len(self.timeslots)}")
            return solution
        
        # Tüm projeleri atamak için gerekli veri yapıları
        assigned_projects = set()
        assigned_classrooms_timeslots = set()  # (classroom_id, timeslot_id) çiftleri
        instructor_timeslot_usage = {}  # instructor_id -> set of timeslot_ids

        # Her öğretim üyesi için timeslot kullanımını başlat
        for instructor in self.instructors:
            instructor_timeslot_usage[instructor.get("id")] = set()

        # Tüm projeleri atamak için döngü
        unassigned_projects = list(self.projects)
        random.shuffle(unassigned_projects)

        max_attempts = len(unassigned_projects) * 10  # Her proje için maksimum deneme sayısı
        attempts = 0

        while unassigned_projects and attempts < max_attempts:
            project = unassigned_projects[0]

            # Bu proje için uygun sınıf ve zaman dilimi bul
            valid_assignment = self._find_valid_assignment_for_project(
                project, assigned_classrooms_timeslots, instructor_timeslot_usage
            )

            if valid_assignment:
                solution.append(valid_assignment)
                assigned_projects.add(project.get("id"))
                assigned_classrooms_timeslots.add((valid_assignment["classroom_id"], valid_assignment["timeslot_id"]))

                # Öğretim üyelerinin timeslot kullanımını güncelle
                for instructor_id in valid_assignment["instructors"]:
                    instructor_timeslot_usage[instructor_id].add(valid_assignment["timeslot_id"])

                unassigned_projects.remove(project)
            else:
                attempts += 1
                # Başarısız olan projeyi listede tut ve tekrar dene

        # Hala atanmamış projeler varsa, onları da atamaya çalış (daha gevşek kurallarla)
        for project in unassigned_projects[:]:
            fallback_assignment = self._create_fallback_assignment(project, assigned_classrooms_timeslots)
            if fallback_assignment:
                solution.append(fallback_assignment)
                assigned_classrooms_timeslots.add((fallback_assignment["classroom_id"], fallback_assignment["timeslot_id"]))

        logger.info(f"NSGA-II: Random solution completed with {len(solution)} assignments")
        return solution

    def _find_valid_assignment_for_project(self, project: Dict[str, Any],
                                         assigned_classrooms_timeslots: set,
                                         instructor_timeslot_usage: Dict[int, set]) -> Optional[Dict[str, Any]]:
        """
        Belirtilen proje için geçerli bir atama bulur.

        Args:
            project: Atanacak proje
            assigned_classrooms_timeslots: Atanmış (sınıf, zaman dilimi) çiftleri
            instructor_timeslot_usage: Öğretim üyesi zaman dilimi kullanımı

        Returns:
            Optional[Dict[str, Any]]: Geçerli atama veya None
        """
        logger.info(f"NSGA-II: Finding assignment for project {project.get('id', 'unknown')}")
        # Uygun sınıfları bul (kapasite kontrolü)
        suitable_classrooms = []
        project_student_count = getattr(project, 'student_count', 30)

        for classroom in self.classrooms:
            if classroom.get("capacity", 0) >= project_student_count:
                suitable_classrooms.append(classroom)

        if not suitable_classrooms:
            suitable_classrooms = self.classrooms  # Kapasite kontrolü yoksa tüm sınıfları kullan

        random.shuffle(suitable_classrooms)

        # Eğer uygun sınıf ve zaman dilimi bulunamadıysa, herhangi birini kullan
        if suitable_classrooms:
            classroom = random.choice(suitable_classrooms)
            available_timeslots = [t for t in self.timeslots
                                 if (classroom.get("id"), t.get("id")) not in assigned_classrooms_timeslots]

            if available_timeslots:
                timeslot = random.choice(available_timeslots)
                instructors = self._select_instructors_for_project(project, timeslot.get("id"), instructor_timeslot_usage)

                if instructors:
                    return {
                        "project_id": project.get("id"),
                        "classroom_id": classroom.get("id"),
                        "timeslot_id": timeslot.get("id"),
                        "instructors": instructors
                    }
                else:
                    # Minimum instructors
                    instructors = [project.get("responsible_id")] if project.get("responsible_id") else []
                    if not instructors and self.instructors:
                        instructors = [self.instructors[0].get("id")]

                    return {
                            "project_id": project.get("id"),
                            "classroom_id": classroom.get("id"),
                            "timeslot_id": timeslot.get("id"),
                            "instructors": instructors
                        }
                        
        logger.warning(f"NSGA-II: No valid assignment found for project {project.get('id', 'unknown')}")
        return None

    def _select_instructors_for_project(self, project: Dict[str, Any],
                                      timeslot_id: int,
                                      instructor_timeslot_usage: Dict[int, set]) -> List[int]:
        """
        Belirtilen proje için uygun öğretim üyelerini seçer.

        Args:
            project: Proje
            timeslot_id: Zaman dilimi ID'si
            instructor_timeslot_usage: Öğretim üyesi zaman dilimi kullanımı

        Returns:
            List[int]: Seçilen öğretim üyesi ID'leri
        """
        logger.info(f"NSGA-II: Selecting instructors for project {project.get('id', 'unknown')}")
        logger.info(f"NSGA-II: Project type: {project.get('type', 'ara')}, responsible_id: {project.get('responsible_id')}")
        logger.info(f"NSGA-II: Available instructors: {len(self.instructors)}")
        logger.info(f"NSGA-II: Instructor timeslot usage: {instructor_timeslot_usage}")
        logger.info(f"NSGA-II: Instructor timeslot usage keys: {list(instructor_timeslot_usage.keys())}")
        logger.info(f"NSGA-II: First instructor: {self.instructors[0] if self.instructors else 'No instructors'}")
        instructors = []
        project_type = project.get("type", "ara")
        responsible_id = project.get("responsible_id")

        # Sorumlu öğretim üyesi müsait mi?
        if responsible_id:
            if timeslot_id not in instructor_timeslot_usage.get(responsible_id, set()):
                instructors.append(responsible_id)

        # Proje tipine göre ek öğretim üyeleri seç
        available_instructors = [i for i in self.instructors
                               if i.get("id") != responsible_id and
                               timeslot_id not in instructor_timeslot_usage.get(i.get("id"), set())]
        logger.info(f"NSGA-II: Available instructors after filtering: {len(available_instructors)}")
        logger.info(f"NSGA-II: Instructor timeslot usage sample: {list(instructor_timeslot_usage.values())[0] if instructor_timeslot_usage else 'No instructors'}")
        logger.info(f"NSGA-II: Timeslot ID: {timeslot_id}")
        logger.info(f"NSGA-II: Responsible ID: {responsible_id}")
        logger.info(f"NSGA-II: Available instructors IDs: {[i.get('id') for i in available_instructors]}")

        if project_type == "bitirme":
            # Bitirme projesi için en az 2 hoca
            hocas = [i for i in available_instructors if i.get("type") == "instructor"]
            if len(hocas) >= 2:
                selected_hocas = random.sample(hocas, 2)
                instructors.extend([h.get("id") for h in selected_hocas])
            elif len(hocas) >= 1:
                instructors.append(hocas[0].get("id"))
                # Üçüncü kişi için araş. gör. ekle
                aras_gors = [i for i in available_instructors if i.get("type") == "assistant"]
                if aras_gors:
                    instructors.append(random.choice(aras_gors).get("id"))
        else:
            # Ara proje için 1-2 kişi
            if len(available_instructors) >= 2:
                selected = random.sample(available_instructors, 2)
                instructors.extend([i.get("id") for i in selected])
            elif len(available_instructors) >= 1:
                instructors.append(available_instructors[0].get("id"))

        logger.info(f"NSGA-II: Selected {len(instructors)} instructors for project {project.get('id', 'unknown')}: {instructors}")
        if not instructors:
            logger.warning(f"NSGA-II: No instructors selected for project {project.get('id', 'unknown')}")
            logger.warning(f"NSGA-II: Available instructors count: {len(self.instructors)}")
            logger.warning(f"NSGA-II: Available instructors after filtering: {len(available_instructors)}")
            logger.warning(f"NSGA-II: Project type: {project_type}")
            logger.warning(f"NSGA-II: Responsible ID: {responsible_id}")
            logger.warning(f"NSGA-II: Timeslot ID: {timeslot_id}")
            logger.warning(f"NSGA-II: Instructor timeslot usage keys: {list(instructor_timeslot_usage.keys())}")
            logger.warning(f"NSGA-II: Instructor timeslot usage: {instructor_timeslot_usage}")
            logger.warning(f"NSGA-II: First instructor: {self.instructors[0] if self.instructors else 'No instructors'}")
            logger.warning(f"NSGA-II: Available instructors list: {self.instructors}")
        return instructors

    def _create_fallback_assignment(self, project: Dict[str, Any],
                                  assigned_classrooms_timeslots: set) -> Optional[Dict[str, Any]]:
        """
        Başarısız olan proje için fallback atama oluşturur.

        Args:
            project: Atanacak proje
            assigned_classrooms_timeslots: Atanmış (sınıf, zaman dilimi) çiftleri

        Returns:
            Optional[Dict[str, Any]]: Fallback atama
        """
        # En az kısıtlı sınıfları seç
        available_classrooms = [c for c in self.classrooms
                              if (c.get("id"), self.timeslots[0].get("id")) not in assigned_classrooms_timeslots]

        if not available_classrooms:
            available_classrooms = self.classrooms

        classroom = random.choice(available_classrooms)

        # İlk müsait zaman dilimini seç
        for timeslot in self.timeslots:
            if (classroom.get("id"), timeslot.get("id")) not in assigned_classrooms_timeslots:
                instructors = [project.get("responsible_id")] if project.get("responsible_id") else []
                return {
                    "project_id": project.get("id"),
                    "classroom_id": classroom.get("id"),
                    "timeslot_id": timeslot.get("id"),
                    "instructors": instructors
                }

        return None
    
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
            List[float]: Amaç fonksiyonu değerleri [classroom_changes, load_balance, rule_compliance].
        """
        # Çözüm geçerli mi?
        if not self._is_valid_solution(solution):
            return [float('-inf'), float('-inf'), float('-inf'), float('-inf'), float('-inf')]
        
        # Amaç 1: Hocaların sınıf geçişlerini minimize et (daha düşük daha iyi)
        instructor_changes = self._count_instructor_classroom_changes(solution)
        obj1 = instructor_changes
        
        # Amaç 2: Yük dengesini maksimize et (daha yüksek daha iyi)
        load_balance = self._calculate_load_balance(solution)
        obj2 = load_balance
        
        # Amaç 3: Proje kurallarına uygunluğu maksimize et (daha yüksek daha iyi)
        rule_compliance = self._calculate_rule_compliance(solution)
        obj3 = rule_compliance
        
        # Amaç 4: Zaman slot cezası - 16:30 sonrası çok ağır, 16:00–16:30 orta seviye
        time_penalty = self._calculate_time_slot_penalty(solution)
        obj4 = -time_penalty  # Negatif ceza, minimize etmek istiyoruz

        # Amaç 5: İki slot arasında boş slot kuralı cezası
        gap_penalty = self._calculate_gap_penalty(solution)
        obj5 = gap_penalty  # -9999 ceza eklenir

        return [obj1, obj2, obj3, obj4, obj5]
    
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
        
        # Check if objectives exist and are valid
        if not population[0].get("objectives") or len(population[0]["objectives"]) == 0:
            # Initialize objectives if missing
            for individual in population:
                if not individual.get("objectives"):
                    individual["objectives"] = [0.0, 0.0, 0.0, 0.0, 0.0]
            return
        
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
    
    def _calculate_time_slot_penalty(self, solution: List[Dict[str, Any]]) -> float:
        """Standart baz ceza (pozitif) uygular ve fitness tarafından düşülür."""
        return super()._calculate_time_slot_penalty(solution)

    def _calculate_gap_penalty(self, solution: List[Dict[str, Any]]) -> float:
        """
        İki slot arasında boş slot kuralı cezası hesaplar.
        Örneğin: 09:00-09:30 ve 10:00-10:30 doluysa, 09:30-10:00 boş olamaz.

        Bu kural, ardışık olmayan zaman slotları arasında boşluk olmamasını sağlar.
        Eğer herhangi bir slot grubu arasında boşluk varsa -9999 ceza verir.

        Args:
            solution: Değerlendirilecek çözüm.

        Returns:
            float: Ceza puanı (-9999 eğer kural ihlal edilmişse, yoksa 0).
        """
        if not solution:
            return 0.0

        # Tüm kullanılan slotları topla
        all_used_slots = set()

        for assignment in solution:
            timeslot_id = assignment.get("timeslot_id")
            timeslot = next((t for t in self.timeslots if t.get("id") == timeslot_id), None)

            if timeslot:
                all_used_slots.add(timeslot_id)

        # Tüm slotları indekse göre kontrol et
        gaps = self._check_consecutive_gaps(list(all_used_slots))

        # Eğer herhangi bir boşluk varsa -9999 ceza ver
        if gaps > 0:
            return -9999.0

        return 0.0

    def _check_consecutive_gaps(self, slot_ids: List[int]) -> int:
        """
        Verilen slot listesinde ardışık slotlarda boşluk olup olmadığını kontrol eder.

        Args:
            slot_ids: Kontrol edilecek zaman dilimi ID'leri.

        Returns:
            int: Boşluk sayısı.
        """
        if len(slot_ids) < 2:
            return 0

        # Slotları indekse göre sırala
        slot_indices = []
        for slot_id in slot_ids:
            # Timeslot ID'sini indekse çevir
            for idx, ts in enumerate(self.timeslots):
                if ts.get("id") == slot_id:
                    slot_indices.append(idx)
                    break

        if not slot_indices:
            return 0

        # Slot indekslerini sırala
        slot_indices.sort()

        gaps = 0

        # Ardışık slotlarda boşluk kontrolü
        for i in range(len(slot_indices) - 1):
            current_idx = slot_indices[i]
            next_idx = slot_indices[i + 1]

            # Eğer ardışık indeksler arasında boşluk varsa
            if next_idx - current_idx > 1:
                # Bu iki slot arasında boş slot(lar) var
                gaps += 1

        return gaps
    
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
        array = np.array(loads, dtype=np.float64)
        if np.amin(array) < 0:
            array -= np.amin(array)
        array += 0.0000001
        array = np.sort(array)
        index = np.arange(1, array.shape[0] + 1, dtype=np.float64)
        n = float(array.shape[0])
        gini = ((np.sum((2 * index - n - 1) * array)) / (n * np.sum(array)))
        
        # Gini katsayısı 0 (tam eşitlik) ile 1 (tam eşitsizlik) arasındadır
        # Biz dengeyi istediğimiz için 1 - gini döndürüyoruz
        return 1.0 - gini
    
    def evaluate_fitness(self, solution: Dict[str, Any]) -> float:
        """CP-SAT özelliği: Verilen çözümün uygunluğunu değerlendirir."""
        if not solution:
            return float('-inf')

        assignments = solution.get("solution", solution.get("schedule", []))
        if not assignments:
            return float('-inf')

        # Çözüm geçerli mi?
        if not self._is_valid_solution(assignments):
            return float('-inf')

        score = 0.0

        # Kural uygunluğu
        rule_compliance = self._calculate_rule_compliance(assignments)
        score += rule_compliance * 100.0

        # Sınıf değişim sayısını minimize et
        instructor_changes = self._count_instructor_classroom_changes(assignments)
        score -= instructor_changes * 10.0

        # Yük dengesini maksimize et
        load_balance = self._calculate_load_balance(assignments)
        score += load_balance * 50.0

        # Zaman slot cezası - 16:30 sonrası çok ağır, 16:00–16:30 orta seviye
        time_penalty = self._calculate_time_slot_penalty(assignments)
        score -= time_penalty

        return score
    
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
                    if instructor and instructor.get("type") == "instructor":
                        hoca_count += 1
                
                if hoca_count >= 2:
                    satisfied_rules += 1
            
            elif project.get("type") == "ara":
                # Kural 4: Ara projede en az 1 hoca olmalı
                total_rules += 1
                has_hoca = False
                for instructor_id in instructors:
                    instructor = next((i for i in self.instructors if i.get("id") == instructor_id), None)
                    if instructor and instructor.get("type") == "instructor":
                        has_hoca = True
                        break
                
                if has_hoca:
                    satisfied_rules += 1
        
        # Kural uygunluk oranını hesapla
        if total_rules > 0:
            return satisfied_rules / total_rules
        else:
            return 0.0 