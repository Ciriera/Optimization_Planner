import { api } from './authService';

export interface Algorithm {
  name: string;
  displayName: string;
  description: string;
  category: string;
  complexity: 'Low' | 'Medium' | 'High';
  recommendedFor: string[];
  parameters?: AlgorithmParameter[];
  bestFor?: string[];
  type?: string;
}

export interface AlgorithmParameter {
  name: string;
  type: 'number' | 'boolean' | 'select' | 'range';
  label: string;
  description: string;
  defaultValue: any;
  options?: { value: any; label: string }[];
  min?: number;
  max?: number;
  step?: number;
}

export interface AlgorithmRun {
  id: number;
  algorithm: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  params: Record<string, any>;
  result?: any;
  success_rate?: number;
  execution_time?: number;
  created_at: string;
}

export interface AlgorithmExecuteRequest {
  algorithm: string;
  params: Record<string, any>;
}

export const algorithmService = {
  async list(): Promise<string[]> {
    try {
      const res = await api.get<any[]>('/algorithms/list');
      // Backend artık obje döndürebilir; type ya da name alanını listele
      const items = Array.isArray(res.data) ? res.data : [];
      return items.map((it: any) => (it.type?.toString?.() || it.name || it));
    } catch (error) {
      // API hatası durumunda hardcoded listeyi döndür
      console.warn('API hatası, hardcoded algoritma listesi kullanılıyor:', error);
      return [
        'simplex',
        'genetic',
        'simulated_annealing',
        'ant_colony',
        'nsga_ii',
        'greedy',
        'tabu_search',
        'pso',
        'harmony_search',
        'firefly',
        'grey_wolf',
        'cp_sat',
        'deep_search',
        'hybrid_cpsat_tabu_nsga',
        'lexicographic_advanced',
        'comprehensive_optimizer',
        'hungarian'
      ];
    }
  },

  async execute(request: AlgorithmExecuteRequest): Promise<AlgorithmRun> {
    const res = await api.post<AlgorithmRun>('/algorithms/execute', request);
    return res.data;
  },

  async getResults(runId: number): Promise<AlgorithmRun> {
    const res = await api.get<AlgorithmRun>(`/algorithms/results/${runId}`);
    return res.data;
  },

  async getRecommendation(projectType?: string, optimizeFor?: string): Promise<any> {
    const params = new URLSearchParams();
    if (projectType) params.append('project_type', projectType);
    if (optimizeFor) params.append('optimize_for', optimizeFor);

    const res = await api.get(`/algorithms/recommend-best?${params.toString()}`);
    return res.data;
  },

  // Transform algorithm names to display-friendly format
  getAlgorithmDisplayInfo(algorithmName: string | any): Algorithm {
    // Eğer zaten Algorithm objesi ise, direkt döndür
    if (typeof algorithmName === 'object' && algorithmName !== null) {
      // Backend'den gelen obje formatını kontrol et
      const type = algorithmName.type || algorithmName.name || 'unknown';
      const name = algorithmName.name || algorithmName.type || 'unknown';

      // Eğer backend'den gelen name "Unknown Algorithm" ise, type'a göre display name bul
      let displayName = algorithmName.name;
      if (displayName === 'Unknown Algorithm' || !displayName) {
        const mappedAlgorithm = this.getAlgorithmDisplayInfo(type);
        displayName = mappedAlgorithm.displayName;
      }

      // Backend'den gelen boş kategori durumunda, type'a göre kategori belirle
      let category = algorithmName.category;
      if (!category || category === '') {
        const mappedAlgorithm = this.getAlgorithmDisplayInfo(type);
        category = mappedAlgorithm.category;
      }

      return {
        name: name,
        displayName: displayName || name,
        description: algorithmName.description || 'Algorithm description',
        category: category || 'Other',
        complexity: algorithmName.complexity || 'Medium',
        recommendedFor: Array.isArray(algorithmName.recommendedFor) ? algorithmName.recommendedFor :
          Array.isArray(algorithmName.bestFor) ? algorithmName.bestFor : ['General purpose'],
        bestFor: Array.isArray(algorithmName.bestFor) ? algorithmName.bestFor : [],
        type: type,
        parameters: algorithmName.parameters || []
      };
    }

    const algorithmMap: Record<string, Algorithm> = {
      simplex: {
        name: 'simplex',
        displayName: 'Simplex Optimizasyonu',
        description: 'Doğrusal programlama ile hızlı ve kesin çözümler üretir. Kısıt tabanlı problemler için idealdir.',
        category: 'Mathematical',
        complexity: 'Medium',
        recommendedFor: ['Doğrusal optimizasyon', 'Kısıt çözümleme', 'Kaynak dağılımı'],
        parameters: [
          { name: 'max_iterations', type: 'number', label: 'Max Iterations', description: 'Maximum number of iterations', defaultValue: 1000, min: 100, max: 5000 },
          { name: 'tolerance', type: 'range', label: 'Tolerance', description: 'Convergence tolerance', defaultValue: 0.001, min: 0.0001, max: 0.01, step: 0.0001 }
        ]
      },
      genetic: {
        name: 'genetic',
        displayName: 'Genetik Algoritma',
        description: 'Doğal seçilim prensiplerini kullanarak çözüm uzayını evrimsel olarak keşfeder.',
        category: 'Bio-inspired',
        complexity: 'Medium',
        recommendedFor: ['Karmaşık optimizasyon', 'Çoklu hedefler', 'Geniş arama uzayı'],
        parameters: [
          { name: 'population_size', type: 'number', label: 'Population Size', description: 'Number of individuals in population', defaultValue: 50, min: 10, max: 200 },
          { name: 'generations', type: 'number', label: 'Generations', description: 'Number of generations', defaultValue: 100, min: 10, max: 500 },
          { name: 'mutation_rate', type: 'range', label: 'Mutation Rate', description: 'Probability of mutation', defaultValue: 0.1, min: 0.01, max: 0.5, step: 0.01 },
          { name: 'crossover_rate', type: 'range', label: 'Crossover Rate', description: 'Probability of crossover', defaultValue: 0.8, min: 0.1, max: 1.0, step: 0.1 }
        ]
      },
      simulated_annealing: {
        name: 'simulated_annealing',
        displayName: 'Tavlama Simülasyonu',
        description: 'Metal tavlama sürecinden esinlenerek yerel optimumlardan kaçınır ve global çözüme ulaşır.',
        category: 'Metaheuristic',
        complexity: 'Medium',
        recommendedFor: ['Global optimizasyon', 'Yerel optimumdan kaçınma', 'Esnek çözüm'],
        parameters: [
          { name: 'initial_temperature', type: 'number', label: 'Initial Temperature', description: 'Starting temperature', defaultValue: 100.0, min: 10, max: 1000 },
          { name: 'cooling_rate', type: 'range', label: 'Cooling Rate', description: 'Temperature reduction rate', defaultValue: 0.01, min: 0.001, max: 0.1, step: 0.001 },
          { name: 'iterations', type: 'number', label: 'Iterations', description: 'Number of iterations', defaultValue: 1000, min: 100, max: 10000 }
        ]
      },
      deep_search: {
        name: 'deep_search',
        displayName: 'Derin Arama',
        description: 'Derinlemesine sistematik arama ile tüm olası çözümleri değerlendirir.',
        category: 'Search-based',
        complexity: 'High',
        recommendedFor: ['Detaylı keşif', 'Optimal çözüm', 'Küçük problemler'],
        parameters: [
          { name: 'max_depth', type: 'number', label: 'Max Depth', description: 'Maximum search depth', defaultValue: 10, min: 5, max: 20 },
          { name: 'beam_width', type: 'number', label: 'Beam Width', description: 'Number of paths to keep', defaultValue: 5, min: 1, max: 10 }
        ]
      },
      ant_colony: {
        name: 'ant_colony',
        displayName: 'Karınca Kolonisi',
        description: 'Karıncaların yiyecek arama davranışını taklit ederek en iyi yolu bulur.',
        category: 'Metaheuristic',
        complexity: 'Medium',
        recommendedFor: ['Yol optimizasyonu', 'Rotalama', 'Sürü zekası'],
        parameters: [
          { name: 'colony_size', type: 'number', label: 'Colony Size', description: 'Number of ants', defaultValue: 50, min: 5, max: 100 },
          { name: 'iterations', type: 'number', label: 'Iterations', description: 'Number of iterations', defaultValue: 100, min: 10, max: 500 },
          { name: 'evaporation_rate', type: 'range', label: 'Evaporation Rate', description: 'Pheromone evaporation rate', defaultValue: 0.1, min: 0.01, max: 0.5, step: 0.01 }
        ]
      },
      greedy: {
        name: 'greedy',
        displayName: 'Açgözlü Algoritma',
        description: 'Her adımda en iyi görünen seçimi yaparak hızlı sonuç üretir.',
        category: 'Search-based',
        complexity: 'Low',
        recommendedFor: ['Hızlı çözüm', 'Basit problemler', 'İlk yaklaşım'],
        parameters: [
          { name: 'max_iterations', type: 'number', label: 'Max Iterations', description: 'Maximum iterations', defaultValue: 100, min: 10, max: 500 }
        ]
      },
      tabu_search: {
        name: 'tabu_search',
        displayName: 'Tabu Arama',
        description: 'Yasaklı hareketler listesi tutarak döngülerden kaçınır ve yeni çözümler keşfeder.',
        category: 'Search-based',
        complexity: 'Medium',
        recommendedFor: ['Hafıza tabanlı arama', 'Döngüden kaçınma', 'Çeşitlilik'],
        parameters: [
          { name: 'tabu_tenure', type: 'number', label: 'Tabu Tenure', description: 'Tabu list size', defaultValue: 10, min: 3, max: 50 },
          { name: 'max_iterations', type: 'number', label: 'Max Iterations', description: 'Maximum iterations', defaultValue: 200, min: 50, max: 1000 }
        ]
      },
      pso: {
        name: 'pso',
        displayName: 'Parçacık Sürü Optimizasyonu',
        description: 'Kuş sürüsü davranışını modelleyerek kolektif zeka ile çözüm arar.',
        category: 'Metaheuristic',
        complexity: 'Medium',
        recommendedFor: ['Sürekli optimizasyon', 'Sürü zekası', 'Paralel arama'],
        parameters: [
          { name: 'swarm_size', type: 'number', label: 'Swarm Size', description: 'Number of particles', defaultValue: 30, min: 10, max: 100 },
          { name: 'iterations', type: 'number', label: 'Iterations', description: 'Number of iterations', defaultValue: 100, min: 20, max: 500 }
        ]
      },
      harmony_search: {
        name: 'harmony_search',
        displayName: 'Armoni Arama',
        description: 'Müzisyenlerin uyum arayışından esinlenerek optimal çözümü bulur.',
        category: 'Metaheuristic',
        complexity: 'Medium',
        recommendedFor: ['Müzikal ilham', 'Global optimizasyon', 'Yaratıcı arama'],
        parameters: [
          { name: 'harmony_memory_size', type: 'number', label: 'Harmony Memory Size', description: 'Memory size', defaultValue: 30, min: 5, max: 50 },
          { name: 'iterations', type: 'number', label: 'Iterations', description: 'Number of improvisations', defaultValue: 100, min: 10, max: 500 }
        ]
      },
      firefly: {
        name: 'firefly',
        displayName: 'Ateşböceği Algoritması',
        description: 'Ateşböceklerinin ışık çekiciliğini modelleyerek çözüme yakınsar.',
        category: 'Metaheuristic',
        complexity: 'Medium',
        recommendedFor: ['Işık modeli', 'Çok modlu optimizasyon', 'Paralel arama'],
        parameters: [
          { name: 'population_size', type: 'number', label: 'Population Size', description: 'Number of fireflies', defaultValue: 30, min: 10, max: 100 },
          { name: 'iterations', type: 'number', label: 'Iterations', description: 'Number of iterations', defaultValue: 100, min: 10, max: 500 }
        ]
      },
      grey_wolf: {
        name: 'grey_wolf',
        displayName: 'Gri Kurt Optimizasyonu',
        description: 'Kurt sürüsünün av stratejisini kullanarak liderlik tabanlı arama yapar.',
        category: 'Metaheuristic',
        complexity: 'Medium',
        recommendedFor: ['Sürü hiyerarşisi', 'Liderlik modeli', 'Takım çalışması'],
        parameters: [
          { name: 'population_size', type: 'number', label: 'Population Size', description: 'Number of wolves', defaultValue: 30, min: 5, max: 50 },
          { name: 'iterations', type: 'number', label: 'Iterations', description: 'Maximum iterations', defaultValue: 100, min: 20, max: 500 }
        ]
      },
      nsga_ii: {
        name: 'nsga_ii',
        displayName: 'NSGA-II',
        description: 'Çok amaçlı optimizasyon için Pareto optimal çözüm kümesi üretir.',
        category: 'Multi-objective',
        complexity: 'High',
        recommendedFor: ['Çok amaçlı optimizasyon', 'Pareto çözümler', 'Denge analizi'],
        parameters: [
          { name: 'population_size', type: 'number', label: 'Population Size', description: 'Number of individuals', defaultValue: 100, min: 20, max: 200 },
          { name: 'generations', type: 'number', label: 'Generations', description: 'Number of generations', defaultValue: 50, min: 10, max: 200 }
        ]
      },
      cp_sat: {
        name: 'cp_sat',
        displayName: 'Kısıt Programlama (CP-SAT)',
        description: 'Google OR-Tools ile güçlü kısıt çözücü, kesin ve garantili çözümler.',
        category: 'Mathematical',
        complexity: 'High',
        recommendedFor: ['Kesin çözüm', 'Kısıt memnuniyeti', 'Endüstriyel problemler'],
        parameters: [
          { name: 'max_time_seconds', type: 'number', label: 'Max Time (seconds)', description: 'Maximum solving time', defaultValue: 60, min: 10, max: 600 },
          { name: 'num_search_workers', type: 'number', label: 'Search Workers', description: 'Number of parallel workers', defaultValue: 4, min: 1, max: 16 }
        ]
      },
      hybrid_cpsat_tabu_nsga: {
        name: 'hybrid_cpsat_tabu_nsga',
        displayName: 'Hibrit Optimizasyon',
        description: 'CP-SAT, Tabu Arama ve NSGA-II kombinasyonu ile kapsamlı çözüm.',
        category: 'Hybrid',
        complexity: 'High',
        recommendedFor: ['Kapsamlı optimizasyon', 'Hibrit yaklaşım', 'Garantili fizibilite'],
        parameters: [
          { name: 'time_limit', type: 'number', label: 'Total Time Limit (s)', description: 'Total execution time limit', defaultValue: 180, min: 60, max: 600 }
        ]
      },
      lexicographic_advanced: {
        name: 'lexicographic_advanced',
        displayName: 'Leksikografik Optimizasyon',
        description: 'Öncelik sırasına göre hedefleri sırayla optimize eder.',
        category: 'Mathematical',
        complexity: 'High',
        recommendedFor: ['Öncelikli hedefler', 'Sistematik yaklaşım', 'Sıralı optimizasyon'],
        parameters: [
          { name: 'time_limit_seconds', type: 'number', label: 'Time Limit (s)', description: 'Total execution time limit', defaultValue: 180, min: 60, max: 600 }
        ]
      },
      lexicographic: {
        name: 'lexicographic',
        displayName: 'Sıralı Hedef Optimizasyonu',
        description: 'Hedefleri önem sırasına göre tek tek optimize eder.',
        category: 'Mathematical',
        complexity: 'High',
        recommendedFor: ['Öncelik bazlı', 'Sıralı hedefler', 'Hiyerarşik çözüm'],
        parameters: [
          { name: 'time_limit_seconds', type: 'number', label: 'Time Limit (s)', description: 'Total execution time limit', defaultValue: 180, min: 60, max: 600 }
        ]
      },
      hybrid_cp_sat_nsga: {
        name: 'hybrid_cp_sat_nsga',
        displayName: 'CP-SAT + NSGA-II Hibrit',
        description: 'Kısıt programlama ile çok amaçlı genetik algoritmayı birleştirir.',
        category: 'Hybrid',
        complexity: 'High',
        recommendedFor: ['Çok amaçlı', 'Kısıt memnuniyeti', 'Dengeli çözüm'],
        parameters: [
          { name: 'time_limit', type: 'number', label: 'Total Time Limit (s)', description: 'Total execution time limit', defaultValue: 180, min: 60, max: 600 }
        ]
      },
      artificial_bee_colony: {
        name: 'artificial_bee_colony',
        displayName: 'Yapay Arı Kolonisi',
        description: 'Bal arılarının yiyecek arama davranışını taklit eder.',
        category: 'Bio-inspired',
        complexity: 'Medium',
        recommendedFor: ['Keşif-sömürü dengesi', 'Kombinatoryal', 'Doğa ilhamı'],
        parameters: [
          { name: 'colony_size', type: 'number', label: 'Colony Size', description: 'Number of bees', defaultValue: 50, min: 10, max: 100 }
        ]
      },
      cuckoo_search: {
        name: 'cuckoo_search',
        displayName: 'Guguk Kuşu Araması',
        description: 'Guguk kuşunun yuva parazitliği ve Lévy uçuşunu kullanır.',
        category: 'Metaheuristic',
        complexity: 'Medium',
        recommendedFor: ['Global optimizasyon', 'Lévy hareketi', 'Rastgele arama'],
        parameters: [
          { name: 'population_size', type: 'number', label: 'Population Size', description: 'Number of cuckoos', defaultValue: 30, min: 10, max: 100 }
        ]
      },
      branch_and_bound: {
        name: 'branch_and_bound',
        displayName: 'Dal ve Sınır',
        description: 'Sistematik dallanma ile kesin optimal çözümü garanti eder.',
        category: 'Mathematical',
        complexity: 'High',
        recommendedFor: ['Kesin çözüm', 'Küçük-orta problemler', 'Garantili optimallik'],
        parameters: [
          { name: 'time_limit', type: 'number', label: 'Time Limit (s)', description: 'Maximum solving time', defaultValue: 300, min: 60, max: 1800 }
        ]
      },
      dynamic_programming: {
        name: 'dynamic_programming',
        displayName: 'Dinamik Programlama',
        description: 'Alt problemleri çözerek büyük problemi parçalar halinde çözer.',
        category: 'Mathematical',
        complexity: 'High',
        recommendedFor: ['Örtüşen alt problemler', 'Optimal alt yapı', 'Bellekleme'],
        parameters: [
          { name: 'memoization', type: 'boolean', label: 'Memoization', description: 'Enable memoization', defaultValue: true }
        ]
      },
      whale_optimization: {
        name: 'whale_optimization',
        displayName: 'Balina Optimizasyonu',
        description: 'Kambur balinaların kabarcık ağı avlanma stratejisini kullanır.',
        category: 'Metaheuristic',
        complexity: 'Medium',
        recommendedFor: ['Spiral hareket', 'Sürekli optimizasyon', 'Doğa ilhamı'],
        parameters: [
          { name: 'population_size', type: 'number', label: 'Population Size', description: 'Number of whales', defaultValue: 30, min: 10, max: 100 }
        ]
      },
      bat_algorithm: {
        name: 'bat_algorithm',
        displayName: 'Bat Algorithm',
        description: 'Yarasaların ekolokasyon (sonar) sistemini taklit eder.',
        category: 'Metaheuristic',
        complexity: 'Medium',
        recommendedFor: ['Frekans ayarlama', 'Sürekli optimizasyon', 'Ses dalgası modeli'],
        parameters: [
          { name: 'population_size', type: 'number', label: 'Population Size', description: 'Number of bats', defaultValue: 30, min: 10, max: 100 }
        ]
      },
      dragonfly_algorithm: {
        name: 'dragonfly_algorithm',
        displayName: 'Dragonfly Algorithm',
        description: 'Yusufçuk sürüsünün statik ve dinamik davranışlarını modeller.',
        category: 'Metaheuristic',
        complexity: 'Medium',
        recommendedFor: ['Sürü davranışı', 'Çok amaçlı', 'Keşif-sömürü'],
        parameters: [
          { name: 'population_size', type: 'number', label: 'Population Size', description: 'Number of dragonflies', defaultValue: 30, min: 10, max: 100 }
        ]
      },
      a_star_search: {
        name: 'a_star_search',
        displayName: 'A* Search',
        description: 'Sezgisel fonksiyon ile en kısa yolu bulan klasik graf algoritması.',
        category: 'Search-based',
        complexity: 'Medium',
        recommendedFor: ['Pathfinding', 'Graph search', 'Optimal path'],
        parameters: [
          { name: 'heuristic_weight', type: 'range', label: 'Heuristic Weight', description: 'Heuristic function weight', defaultValue: 1.0, min: 0.1, max: 2.0, step: 0.1 }
        ]
      },
      integer_linear_programming: {
        name: 'integer_linear_programming',
        displayName: 'Integer Linear Programming',
        description: 'Tamsayı kısıtları ile doğrusal optimizasyon problemi çözer.',
        category: 'Mathematical',
        complexity: 'High',
        recommendedFor: ['Tamsayı çözümler', 'Doğrusal kısıtlar', 'Kesin optimizasyon'],
        parameters: [
          { name: 'time_limit', type: 'number', label: 'Time Limit (s)', description: 'Maximum solving time', defaultValue: 300, min: 60, max: 1800 }
        ]
      },
      genetic_local_search: {
        name: 'genetic_local_search',
        displayName: 'Genetic Local Search',
        description: 'Genetik algoritma ile yerel arama kombinasyonu - hibrit güç.',
        category: 'Hybrid',
        complexity: 'High',
        recommendedFor: ['Hibrit optimizasyon', 'Yerel iyileştirme', 'Global keşif'],
        parameters: [
          { name: 'population_size', type: 'number', label: 'Population Size', description: 'Number of individuals', defaultValue: 50, min: 10, max: 200 }
        ]
      },
      comprehensive_optimizer: {
        name: 'comprehensive_optimizer',
        displayName: 'Comprehensive Optimizer',
        description: '5 objective comprehensive optimization: load balancing, class transition, time consistency.',
        category: 'Multi-objective',
        complexity: 'High',
        recommendedFor: ['Comprehensive optimization', 'All criteria balance', 'Real world'],
        parameters: [
          { name: 'population_size', type: 'number', label: 'Popülasyon Boyutu', description: 'Genetik algoritma popülasyon boyutu', defaultValue: 100, min: 50, max: 300 }
        ]
      }
    };

    return algorithmMap[algorithmName] || {
      name: algorithmName,
      displayName: algorithmName,
      description: 'Algoritma açıklaması',
      category: 'Other',
      complexity: 'Medium',
      recommendedFor: ['General purpose']
    };
  }
};
