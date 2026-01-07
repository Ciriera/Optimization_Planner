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
        displayName: 'Simplex Method',
        description: 'Linear programming için ideal, hızlı ve kesin sonuç',
        category: 'Linear Programming',
        complexity: 'Medium',
        recommendedFor: ['Linear optimization', 'Constraint satisfaction', 'Resource allocation'],
        parameters: [
          { name: 'max_iterations', type: 'number', label: 'Max Iterations', description: 'Maximum number of iterations', defaultValue: 1000, min: 100, max: 5000 },
          { name: 'tolerance', type: 'range', label: 'Tolerance', description: 'Convergence tolerance', defaultValue: 0.001, min: 0.0001, max: 0.01, step: 0.0001 }
        ]
      },
      genetic: {
        name: 'genetic',
        displayName: 'Genetic Algorithm',
        description: 'Farklı yük dağılımlarını deneyimlemek için, evrimsel yaklaşım',
        category: 'Bio-inspired',
        complexity: 'Medium',
        recommendedFor: ['Complex optimization', 'Multiple objectives'],
        parameters: [
          { name: 'population_size', type: 'number', label: 'Population Size', description: 'Number of individuals in population', defaultValue: 50, min: 10, max: 200 },
          { name: 'generations', type: 'number', label: 'Generations', description: 'Number of generations', defaultValue: 100, min: 10, max: 500 },
          { name: 'mutation_rate', type: 'range', label: 'Mutation Rate', description: 'Probability of mutation', defaultValue: 0.1, min: 0.01, max: 0.5, step: 0.01 },
          { name: 'crossover_rate', type: 'range', label: 'Crossover Rate', description: 'Probability of crossover', defaultValue: 0.8, min: 0.1, max: 1.0, step: 0.1 }
        ]
      },
      simulated_annealing: {
        name: 'simulated_annealing',
        displayName: 'Simulated Annealing',
        description: 'Global optimizasyon için, yerel optimumlardan kaçınır',
        category: 'Metaheuristic',
        complexity: 'Medium',
        recommendedFor: ['Global optimization', 'Avoiding local optima'],
        parameters: [
          { name: 'initial_temperature', type: 'number', label: 'Initial Temperature', description: 'Starting temperature', defaultValue: 100.0, min: 10, max: 1000 },
          { name: 'cooling_rate', type: 'range', label: 'Cooling Rate', description: 'Temperature reduction rate', defaultValue: 0.01, min: 0.001, max: 0.1, step: 0.001 },
          { name: 'iterations', type: 'number', label: 'Iterations', description: 'Number of iterations', defaultValue: 1000, min: 100, max: 10000 },
          { name: 'acceptance_probability', type: 'range', label: 'Acceptance Probability', description: 'Base probability for accepting worse solutions', defaultValue: 0.7, min: 0.1, max: 1.0, step: 0.1 }
        ]
      },
      deep_search: {
        name: 'deep_search',
        displayName: 'Deep Search',
        description: 'Minimum sınıf geçişlerini belirlemek için, derinlemesine arama',
        category: 'Search-based',
        complexity: 'High',
        recommendedFor: ['Detailed exploration', 'Optimal solutions'],
        parameters: [
          { name: 'max_depth', type: 'number', label: 'Max Depth', description: 'Maximum search depth', defaultValue: 10, min: 5, max: 20 },
          { name: 'beam_width', type: 'number', label: 'Beam Width', description: 'Number of paths to keep', defaultValue: 5, min: 1, max: 10 }
        ]
      },
      ant_colony: {
        name: 'ant_colony',
        displayName: 'Ant Colony Optimization',
        description: 'Karınca kolonisi optimizasyonu, sürü zekası yaklaşımı',
        category: 'Metaheuristic',
        complexity: 'Medium',
        recommendedFor: ['Path optimization', 'Routing problems'],
        parameters: [
          { name: 'colony_size', type: 'number', label: 'Colony Size', description: 'Number of ants', defaultValue: 50, min: 5, max: 100 },
          { name: 'iterations', type: 'number', label: 'Iterations', description: 'Number of iterations', defaultValue: 100, min: 10, max: 500 },
          { name: 'evaporation_rate', type: 'range', label: 'Evaporation Rate', description: 'Pheromone evaporation rate', defaultValue: 0.1, min: 0.01, max: 0.5, step: 0.01 },
          { name: 'pheromone_factor', type: 'range', label: 'Pheromone Factor', description: 'Weight for pheromone trails', defaultValue: 1.0, min: 0.1, max: 5.0, step: 0.1 },
          { name: 'heuristic_factor', type: 'range', label: 'Heuristic Factor', description: 'Weight for heuristic information', defaultValue: 2.0, min: 0.1, max: 5.0, step: 0.1 }
        ]
      },
      greedy: {
        name: 'greedy',
        displayName: 'Greedy Algorithm',
        description: 'Açgözlü algoritma ile hızlı çözüm',
        category: 'Search-based',
        complexity: 'Low',
        recommendedFor: ['Quick solutions', 'Local optimization'],
        parameters: [
          { name: 'max_iterations', type: 'number', label: 'Max Iterations', description: 'Maximum iterations', defaultValue: 100, min: 10, max: 500 },
          { name: 'improvement_threshold', type: 'range', label: 'Improvement Threshold', description: 'Minimum improvement', defaultValue: 0.01, min: 0.001, max: 0.1, step: 0.001 }
        ]
      },
      tabu_search: {
        name: 'tabu_search',
        displayName: 'Tabu Search',
        description: 'Tabu Arama algoritması, hafıza tabanlı arama',
        category: 'Search-based',
        complexity: 'Medium',
        recommendedFor: ['Memory-based search', 'Avoiding cycles'],
        parameters: [
          { name: 'tabu_tenure', type: 'number', label: 'Tabu Tenure', description: 'Tabu list size', defaultValue: 10, min: 3, max: 50 },
          { name: 'max_iterations', type: 'number', label: 'Max Iterations', description: 'Maximum iterations', defaultValue: 200, min: 50, max: 1000 },
          { name: 'diversification', type: 'boolean', label: 'Diversification', description: 'Enable diversification', defaultValue: true }
        ]
      },
      pso: {
        name: 'pso',
        displayName: 'Particle Swarm Optimization (PSO)',
        description: 'Parçacık Sürü Optimizasyonu, sürü davranışı modeli',
        category: 'Metaheuristic',
        complexity: 'Medium',
        recommendedFor: ['Continuous optimization', 'Swarm intelligence'],
        parameters: [
          { name: 'swarm_size', type: 'number', label: 'Swarm Size', description: 'Number of particles', defaultValue: 30, min: 10, max: 100 },
          { name: 'iterations', type: 'number', label: 'Iterations', description: 'Number of iterations', defaultValue: 100, min: 20, max: 500 },
          { name: 'inertia_weight', type: 'range', label: 'Inertia Weight', description: 'Inertia weight', defaultValue: 0.7, min: 0.1, max: 1.0, step: 0.1 },
          { name: 'cognitive_coefficient', type: 'range', label: 'Cognitive Coeff.', description: 'Personal best coefficient', defaultValue: 1.5, min: 0.5, max: 4.0, step: 0.1 },
          { name: 'social_coefficient', type: 'range', label: 'Social Coeff.', description: 'Global best coefficient', defaultValue: 1.5, min: 0.5, max: 4.0, step: 0.1 }
        ]
      },
      harmony_search: {
        name: 'harmony_search',
        displayName: 'Harmony Search',
        description: 'Uyum Arama Algoritması, müzik armonisinden ilham',
        category: 'Metaheuristic',
        complexity: 'Medium',
        recommendedFor: ['Musical harmony inspired', 'Global optimization'],
        parameters: [
          { name: 'harmony_memory_size', type: 'number', label: 'Harmony Memory Size', description: 'Memory size', defaultValue: 30, min: 5, max: 50 },
          { name: 'iterations', type: 'number', label: 'Iterations', description: 'Number of improvisations', defaultValue: 100, min: 10, max: 500 },
          { name: 'harmony_memory_considering_rate', type: 'range', label: 'HMCR', description: 'Harmony memory considering rate', defaultValue: 0.9, min: 0.1, max: 1.0, step: 0.1 },
          { name: 'pitch_adjusting_rate', type: 'range', label: 'PAR', description: 'Pitch adjusting rate', defaultValue: 0.3, min: 0.1, max: 0.9, step: 0.1 },
          { name: 'bandwidth', type: 'range', label: 'Bandwidth', description: 'Maximum adjustment amount', defaultValue: 0.1, min: 0.01, max: 1.0, step: 0.01 }
        ]
      },
      firefly: {
        name: 'firefly',
        displayName: 'Firefly Algorithm',
        description: 'Ateşböceği Algoritması, ışık çekiciliği modeli',
        category: 'Metaheuristic',
        complexity: 'Medium',
        recommendedFor: ['Light attraction model', 'Multimodal optimization'],
        parameters: [
          { name: 'population_size', type: 'number', label: 'Population Size', description: 'Number of fireflies', defaultValue: 30, min: 10, max: 100 },
          { name: 'iterations', type: 'number', label: 'Iterations', description: 'Number of iterations', defaultValue: 100, min: 10, max: 500 },
          { name: 'alpha', type: 'range', label: 'Alpha', description: 'Randomization parameter', defaultValue: 0.5, min: 0.01, max: 1.0, step: 0.01 },
          { name: 'beta0', type: 'range', label: 'Beta0', description: 'Attractiveness at r=0', defaultValue: 1.0, min: 0.1, max: 2.0, step: 0.1 },
          { name: 'gamma', type: 'range', label: 'Gamma', description: 'Light absorption coefficient', defaultValue: 0.1, min: 0.01, max: 1.0, step: 0.01 }
        ]
      },
      grey_wolf: {
        name: 'grey_wolf',
        displayName: 'Grey Wolf Optimizer',
        description: 'Gri Kurt Optimizasyonu, kurt sürüsü hiyerarşisi',
        category: 'Metaheuristic',
        complexity: 'Medium',
        recommendedFor: ['Pack hierarchy model', 'Leadership-based optimization'],
        parameters: [
          { name: 'population_size', type: 'number', label: 'Population Size', description: 'Number of wolves', defaultValue: 30, min: 5, max: 50 },
          { name: 'iterations', type: 'number', label: 'Iterations', description: 'Maximum iterations', defaultValue: 100, min: 20, max: 500 }
        ]
      },
      nsga_ii: {
        name: 'nsga_ii',
        displayName: 'NSGA-II',
        description: 'Non-dominated Sorting Genetic Algorithm, çok amaçlı optimizasyon',
        category: 'Bio-inspired',
        complexity: 'High',
        recommendedFor: ['Multi-objective optimization', 'Pareto optimal solutions'],
        parameters: [
          { name: 'population_size', type: 'number', label: 'Population Size', description: 'Number of individuals', defaultValue: 100, min: 20, max: 200 },
          { name: 'generations', type: 'number', label: 'Generations', description: 'Number of generations', defaultValue: 50, min: 10, max: 200 },
          { name: 'crossover_rate', type: 'range', label: 'Crossover Rate', description: 'Probability of crossover', defaultValue: 0.8, min: 0.1, max: 1.0, step: 0.1 },
          { name: 'mutation_rate', type: 'range', label: 'Mutation Rate', description: 'Probability of mutation', defaultValue: 0.2, min: 0.01, max: 0.5, step: 0.01 }
        ]
      },
      cp_sat: {
        name: 'cp_sat',
        displayName: 'Constraint Programming (CP-SAT)',
        description: 'Kısıt Programlama, kesin kısıt çözümü',
        category: 'Mathematical',
        complexity: 'High',
        recommendedFor: ['Exact solutions', 'Hard constraints'],
        parameters: [
          { name: 'max_time_seconds', type: 'number', label: 'Max Time (seconds)', description: 'Maximum solving time', defaultValue: 60, min: 10, max: 600 },
          { name: 'num_search_workers', type: 'number', label: 'Search Workers', description: 'Number of parallel workers', defaultValue: 4, min: 1, max: 16 },
          { name: 'optimization_level', type: 'select', label: 'Optimization Level', description: 'Solver optimization level', defaultValue: 'normal', options: [
            { value: 'basic', label: 'Basic' },
            { value: 'normal', label: 'Normal' },
            { value: 'aggressive', label: 'Aggressive' }
          ]}
        ]
      },
      hybrid_cpsat_tabu_nsga: {
        name: 'hybrid_cpsat_tabu_nsga',
        displayName: 'Hybrid CP-SAT + Tabu + NSGA-II',
        description: 'Hibrit algoritma: CP-SAT feasibility + Tabu Search + Simulated Annealing + NSGA-II',
        category: 'Hybrid',
        complexity: 'High',
        recommendedFor: ['Complex optimization', 'Multi-objective problems', 'Guaranteed feasibility'],
        parameters: [
          { name: 'time_limit', type: 'number', label: 'Total Time Limit (s)', description: 'Total execution time limit', defaultValue: 180, min: 60, max: 600 },
          { name: 'cp_time_limit', type: 'number', label: 'CP-SAT Time Limit (s)', description: 'CP-SAT phase time limit', defaultValue: 30, min: 10, max: 120 },
          { name: 'tabu_iterations', type: 'number', label: 'Tabu Iterations', description: 'Number of Tabu Search iterations', defaultValue: 50, min: 10, max: 200 },
          { name: 'sa_iterations', type: 'number', label: 'SA Iterations', description: 'Number of Simulated Annealing iterations', defaultValue: 100, min: 20, max: 500 },
          { name: 'nsga_generations', type: 'number', label: 'NSGA-II Generations', description: 'Number of NSGA-II generations', defaultValue: 20, min: 5, max: 100 },
          { name: 'population_size', type: 'number', label: 'Population Size', description: 'Population size for NSGA-II', defaultValue: 30, min: 10, max: 100 }
        ]
      },
      lexicographic_advanced: {
        name: 'lexicographic_advanced',
        displayName: 'Advanced Lexicographic Optimization',
        description: 'Matematiksel kesinlik için CP-SAT lexicographic optimizasyon',
        category: 'Mathematical',
        complexity: 'High',
        recommendedFor: ['Mathematical optimization', 'Systematic approach', 'Priority-based objectives'],
        parameters: [
          { name: 'time_limit_seconds', type: 'number', label: 'Time Limit (s)', description: 'Total execution time limit', defaultValue: 180, min: 60, max: 600 },
          { name: 'stage_time_limit', type: 'number', label: 'Stage Time Limit (s)', description: 'Time limit per optimization stage', defaultValue: 60, min: 20, max: 180 },
          { name: 'num_search_workers', type: 'number', label: 'Search Workers', description: 'Number of parallel search workers', defaultValue: 8, min: 1, max: 16 }
        ]
      },
      // Backend'den gelen yeni algoritmalar
      lexicographic: {
        name: 'lexicographic',
        displayName: 'Lexicographic Optimization',
        description: 'Sıralı optimizasyon yaklaşımı, öncelik sırasına göre hedefler',
        category: 'Mathematical',
        complexity: 'High',
        recommendedFor: ['Priority-based optimization', 'Sequential objectives'],
        parameters: [
          { name: 'time_limit_seconds', type: 'number', label: 'Time Limit (s)', description: 'Total execution time limit', defaultValue: 180, min: 60, max: 600 },
          { name: 'num_search_workers', type: 'number', label: 'Search Workers', description: 'Number of parallel search workers', defaultValue: 8, min: 1, max: 16 }
        ]
      },
      hybrid_cp_sat_nsga: {
        name: 'hybrid_cp_sat_nsga',
        displayName: 'Hybrid CP-SAT + NSGA-II',
        description: 'Hibrit algoritma: CP-SAT feasibility + NSGA-II multi-objective optimization',
        category: 'Hybrid',
        complexity: 'High',
        recommendedFor: ['Multi-objective optimization', 'Constraint satisfaction'],
        parameters: [
          { name: 'time_limit', type: 'number', label: 'Total Time Limit (s)', description: 'Total execution time limit', defaultValue: 180, min: 60, max: 600 },
          { name: 'cp_time_limit', type: 'number', label: 'CP-SAT Time Limit (s)', description: 'CP-SAT phase time limit', defaultValue: 30, min: 10, max: 120 },
          { name: 'nsga_generations', type: 'number', label: 'NSGA-II Generations', description: 'Number of NSGA-II generations', defaultValue: 20, min: 5, max: 100 },
          { name: 'population_size', type: 'number', label: 'Population Size', description: 'Population size for NSGA-II', defaultValue: 30, min: 10, max: 100 }
        ]
      },
      artificial_bee_colony: {
        name: 'artificial_bee_colony',
        displayName: 'Artificial Bee Colony',
        description: 'Yapay arı kolonisi algoritması, arı davranışından ilham',
        category: 'Bio-inspired',
        complexity: 'Medium',
        recommendedFor: ['Combinatorial optimization', 'Exploration-exploitation balance'],
        parameters: [
          { name: 'colony_size', type: 'number', label: 'Colony Size', description: 'Number of bees', defaultValue: 50, min: 10, max: 100 },
          { name: 'iterations', type: 'number', label: 'Iterations', description: 'Number of iterations', defaultValue: 100, min: 10, max: 500 },
          { name: 'abandon_limit', type: 'number', label: 'Abandon Limit', description: 'Limit for abandoning food source', defaultValue: 10, min: 5, max: 20 }
        ]
      },
      cuckoo_search: {
        name: 'cuckoo_search',
        displayName: 'Cuckoo Search',
        description: 'Guguk kuşu arama algoritması, Levy uçuş davranışı',
        category: 'Metaheuristic',
        complexity: 'Medium',
        recommendedFor: ['Global optimization', 'Levy flight behavior'],
        parameters: [
          { name: 'population_size', type: 'number', label: 'Population Size', description: 'Number of cuckoos', defaultValue: 30, min: 10, max: 100 },
          { name: 'iterations', type: 'number', label: 'Iterations', description: 'Number of iterations', defaultValue: 100, min: 10, max: 500 },
          { name: 'pa', type: 'range', label: 'Pa (Discovery Rate)', description: 'Probability of discovery', defaultValue: 0.25, min: 0.1, max: 0.5, step: 0.05 }
        ]
      },
      branch_and_bound: {
        name: 'branch_and_bound',
        displayName: 'Branch and Bound',
        description: 'Dal ve sınır algoritması, kesin çözüm için',
        category: 'Mathematical',
        complexity: 'High',
        recommendedFor: ['Exact solutions', 'Small to medium problems'],
        parameters: [
          { name: 'time_limit', type: 'number', label: 'Time Limit (s)', description: 'Maximum solving time', defaultValue: 300, min: 60, max: 1800 },
          { name: 'gap_tolerance', type: 'range', label: 'Gap Tolerance', description: 'Optimality gap tolerance', defaultValue: 0.01, min: 0.001, max: 0.1, step: 0.001 }
        ]
      },
      dynamic_programming: {
        name: 'dynamic_programming',
        displayName: 'Dynamic Programming',
        description: 'Dinamik programlama, alt problemlerin çözümü',
        category: 'Mathematical',
        complexity: 'High',
        recommendedFor: ['Overlapping subproblems', 'Optimal substructure'],
        parameters: [
          { name: 'memoization', type: 'boolean', label: 'Memoization', description: 'Enable memoization', defaultValue: true },
          { name: 'recursion_limit', type: 'number', label: 'Recursion Limit', description: 'Maximum recursion depth', defaultValue: 1000, min: 100, max: 10000 }
        ]
      },
      whale_optimization: {
        name: 'whale_optimization',
        displayName: 'Whale Optimization Algorithm',
        description: 'Balina optimizasyon algoritması, balina avlanma davranışı',
        category: 'Metaheuristic',
        complexity: 'Medium',
        recommendedFor: ['Continuous optimization', 'Bubble-net feeding behavior'],
        parameters: [
          { name: 'population_size', type: 'number', label: 'Population Size', description: 'Number of whales', defaultValue: 30, min: 10, max: 100 },
          { name: 'iterations', type: 'number', label: 'Iterations', description: 'Number of iterations', defaultValue: 100, min: 10, max: 500 },
          { name: 'a', type: 'range', label: 'A Parameter', description: 'Control parameter', defaultValue: 2.0, min: 0.1, max: 4.0, step: 0.1 }
        ]
      },
      bat_algorithm: {
        name: 'bat_algorithm',
        displayName: 'Bat Algorithm',
        description: 'Yarasa algoritması, yarasa sonar davranışından ilham',
        category: 'Metaheuristic',
        complexity: 'Medium',
        recommendedFor: ['Continuous optimization', 'Echolocation behavior'],
        parameters: [
          { name: 'population_size', type: 'number', label: 'Population Size', description: 'Number of bats', defaultValue: 30, min: 10, max: 100 },
          { name: 'iterations', type: 'number', label: 'Iterations', description: 'Number of iterations', defaultValue: 100, min: 10, max: 500 },
          { name: 'frequency_min', type: 'range', label: 'Min Frequency', description: 'Minimum frequency', defaultValue: 0.0, min: 0.0, max: 1.0, step: 0.1 },
          { name: 'frequency_max', type: 'range', label: 'Max Frequency', description: 'Maximum frequency', defaultValue: 2.0, min: 1.0, max: 5.0, step: 0.1 }
        ]
      },
      dragonfly_algorithm: {
        name: 'dragonfly_algorithm',
        displayName: 'Dragonfly Algorithm',
        description: 'Yusufçuk algoritması, yusufçuk sürü davranışı',
        category: 'Metaheuristic',
        complexity: 'Medium',
        recommendedFor: ['Swarm behavior', 'Multi-objective optimization'],
        parameters: [
          { name: 'population_size', type: 'number', label: 'Population Size', description: 'Number of dragonflies', defaultValue: 30, min: 10, max: 100 },
          { name: 'iterations', type: 'number', label: 'Iterations', description: 'Number of iterations', defaultValue: 100, min: 10, max: 500 },
          { name: 's', type: 'range', label: 'Separation Weight', description: 'Separation weight', defaultValue: 2.0, min: 0.1, max: 5.0, step: 0.1 }
        ]
      },
      a_star_search: {
        name: 'a_star_search',
        displayName: 'En Kısa Yol Arama',
        description: 'A* algoritması ile optimal yol bulma, en kısa mesafe hesaplama',
        category: 'Search-based',
        complexity: 'Medium',
        recommendedFor: ['Yol bulma', 'Graf arama', 'Optimal çözüm'],
        parameters: [
          { name: 'heuristic_weight', type: 'range', label: 'Heuristic Ağırlığı', description: 'Heuristic fonksiyon ağırlığı', defaultValue: 1.0, min: 0.1, max: 2.0, step: 0.1 },
          { name: 'max_iterations', type: 'number', label: 'Maksimum İterasyon', description: 'Maksimum arama iterasyonu', defaultValue: 10000, min: 1000, max: 100000 }
        ]
      },
      integer_linear_programming: {
        name: 'integer_linear_programming',
        displayName: 'Integer Linear Programming',
        description: 'Tamsayılı doğrusal programlama, kesin çözüm',
        category: 'Mathematical',
        complexity: 'High',
        recommendedFor: ['Integer solutions', 'Linear constraints', 'Exact optimization'],
        parameters: [
          { name: 'time_limit', type: 'number', label: 'Time Limit (s)', description: 'Maximum solving time', defaultValue: 300, min: 60, max: 1800 },
          { name: 'gap_tolerance', type: 'range', label: 'Gap Tolerance', description: 'Optimality gap tolerance', defaultValue: 0.01, min: 0.001, max: 0.1, step: 0.001 }
        ]
      },
      genetic_local_search: {
        name: 'genetic_local_search',
        displayName: 'Genetic Local Search',
        description: 'Genetik algoritma + yerel arama hibrit yaklaşımı',
        category: 'Hybrid',
        complexity: 'High',
        recommendedFor: ['Hybrid optimization', 'Local refinement', 'Global exploration'],
        parameters: [
          { name: 'population_size', type: 'number', label: 'Population Size', description: 'Number of individuals', defaultValue: 50, min: 10, max: 200 },
          { name: 'generations', type: 'number', label: 'Generations', description: 'Number of generations', defaultValue: 100, min: 10, max: 500 },
          { name: 'local_search_iterations', type: 'number', label: 'Local Search Iterations', description: 'Local search iterations per individual', defaultValue: 10, min: 1, max: 50 }
        ]
      },
      comprehensive_optimizer: {
        name: 'comprehensive_optimizer',
        displayName: 'Kapsamlı Optimizasyon',
        description: '5 hedefli kapsamlı optimizasyon sistemi - yük dengesi, sınıf geçişi, saat bütünlüğü, oturum minimizasyonu ve kural uyumu',
        category: 'Multi-objective',
        complexity: 'High',
        recommendedFor: ['Tam optimizasyon', 'Tüm kriterlerin dengelenmesi', 'Gerçek dünya uygulamaları'],
        parameters: [
          { name: 'population_size', type: 'number', label: 'Popülasyon Boyutu', description: 'Genetik algoritma popülasyon boyutu', defaultValue: 100, min: 50, max: 300 },
          { name: 'generations', type: 'number', label: 'Nesil Sayısı', description: 'Optimizasyon nesil sayısı', defaultValue: 50, min: 20, max: 200 },
          { name: 'mutation_rate', type: 'range', label: 'Mutasyon Oranı', description: 'Gen mutasyon oranı', defaultValue: 0.1, min: 0.01, max: 0.3, step: 0.01 },
          { name: 'crossover_rate', type: 'range', label: 'Çaprazlama Oranı', description: 'Gen çaprazlama oranı', defaultValue: 0.8, min: 0.5, max: 1.0, step: 0.05 }
        ]
      },
      hungarian: {
        name: 'hungarian',
        displayName: 'Hungarian Algorithm (Kuhn-Munkres)',
        description: 'Klasik Hungarian (Kuhn-Munkres) algoritması ile atama problemlerini çözer. Çok kriterli ve çok kısıtlı akademik proje sınavı/jüri planlama için optimize edilmiştir.',
        category: 'Mathematical',
        complexity: 'Medium',
        recommendedFor: ['Atama problemleri', 'Proje-slot eşleştirme', 'Jüri atama', 'Optimal eşleştirme'],
        parameters: [
          { name: 'max_iterations', type: 'number', label: 'Max Iterations', description: 'Maximum number of iterations', defaultValue: 1000, min: 100, max: 5000 },
          { name: 'tolerance', type: 'range', label: 'Tolerance', description: 'Convergence tolerance', defaultValue: 0.001, min: 0.0001, max: 0.01, step: 0.0001 }
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
