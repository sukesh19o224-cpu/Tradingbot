"""
V5.5 ULTRA - Strategy Optimizer
Uses genetic algorithms to find optimal strategy parameters
"""
import numpy as np
import random
from typing import Dict, List, Tuple
import logging
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import json

logger = logging.getLogger(__name__)


class StrategyOptimizer:
    """
    Optimize strategy parameters using genetic algorithm

    Features:
    - Evolves parameters over generations
    - Fitness scoring based on profitability, win rate, risk
    - Multi-objective optimization
    - Parameter bounds validation
    - Saves best configurations
    """

    def __init__(self, population_size=20, generations=50, mutation_rate=0.1):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate

        # Parameter ranges for each strategy
        self.PARAMETER_RANGES = {
            'MOMENTUM': {
                'MIN_MOMENTUM_SCORE': (60, 85),
                'MIN_VOLUME_RATIO': (1.2, 2.5),
                'MIN_TREND_DAYS': (3, 10),
                'STOP_LOSS': (0.03, 0.10),
                'TARGETS': [(0.04, 0.08), (0.08, 0.15), (0.15, 0.30)]
            },
            'MEAN_REVERSION': {
                'MIN_RSI_OVERSOLD': (20, 35),
                'MAX_RSI_OVERBOUGHT': (65, 80),
                'BOLLINGER_THRESHOLD': (1.5, 2.5),
                'STOP_LOSS': (0.03, 0.08),
                'TARGETS': [(0.03, 0.06), (0.06, 0.12), (0.12, 0.25)]
            },
            'BREAKOUT': {
                'MIN_CONSOLIDATION_DAYS': (5, 15),
                'BREAKOUT_VOLUME_SURGE': (1.5, 3.0),
                'CONSOLIDATION_RANGE': (0.02, 0.08),
                'STOP_LOSS': (0.04, 0.10),
                'TARGETS': [(0.05, 0.10), (0.10, 0.18), (0.18, 0.35)]
            },
            'POSITIONAL': {
                'MIN_UPTREND_DAYS': (15, 30),
                'MIN_PREDICTED_RETURN': (3.0, 8.0),
                'MIN_PREDICTION_CONFIDENCE': (50, 75),
                'STOP_LOSS': (0.08, 0.15),
                'TARGETS': [(0.06, 0.12), (0.12, 0.20), (0.20, 0.35)]
            }
        }

    def optimize_strategy(self, strategy_name: str, historical_data: Dict) -> Dict:
        """
        Main optimization function

        Args:
            strategy_name: Name of strategy to optimize
            historical_data: Historical price data for testing

        Returns:
            Best parameters found
        """
        logger.info(f"🧬 Starting genetic optimization for {strategy_name}...")

        if strategy_name not in self.PARAMETER_RANGES:
            logger.error(f"Unknown strategy: {strategy_name}")
            return {}

        # Initialize population
        population = self._initialize_population(strategy_name)

        best_individual = None
        best_fitness = -float('inf')

        for generation in range(self.generations):
            # Evaluate fitness
            fitness_scores = [
                self._evaluate_fitness(individual, strategy_name, historical_data)
                for individual in population
            ]

            # Track best
            gen_best_idx = np.argmax(fitness_scores)
            if fitness_scores[gen_best_idx] > best_fitness:
                best_fitness = fitness_scores[gen_best_idx]
                best_individual = deepcopy(population[gen_best_idx])

            logger.info(f"Generation {generation+1}/{self.generations} - Best Fitness: {best_fitness:.4f}")

            # Selection
            selected = self._selection(population, fitness_scores)

            # Crossover
            offspring = self._crossover(selected, strategy_name)

            # Mutation
            population = self._mutation(offspring, strategy_name)

        logger.info(f"✅ Optimization complete for {strategy_name}")
        logger.info(f"Best fitness: {best_fitness:.4f}")
        logger.info(f"Best parameters: {best_individual}")

        return best_individual

    def _initialize_population(self, strategy_name: str) -> List[Dict]:
        """Create initial random population"""
        population = []
        ranges = self.PARAMETER_RANGES[strategy_name]

        for _ in range(self.population_size):
            individual = {}

            for param, param_range in ranges.items():
                if param == 'TARGETS':
                    # Special handling for target arrays
                    individual[param] = [
                        random.uniform(r[0], r[1]) for r in param_range
                    ]
                else:
                    if isinstance(param_range[0], int):
                        individual[param] = random.randint(param_range[0], param_range[1])
                    else:
                        individual[param] = random.uniform(param_range[0], param_range[1])

            population.append(individual)

        return population

    def _evaluate_fitness(self, parameters: Dict, strategy_name: str,
                         historical_data: Dict) -> float:
        """
        Evaluate fitness of parameter set

        Fitness = weighted combination of:
        - Total return (40%)
        - Win rate (30%)
        - Risk-adjusted return (20%)
        - Number of trades (10%)
        """
        # Simulate trades with these parameters
        results = self._simulate_strategy(parameters, strategy_name, historical_data)

        # Calculate fitness components
        total_return = results['total_return']
        win_rate = results['win_rate']
        sharpe_ratio = results['sharpe_ratio']
        num_trades = results['num_trades']

        # Normalize and weight
        fitness = (
            0.40 * self._normalize_return(total_return) +
            0.30 * (win_rate / 100.0) +
            0.20 * self._normalize_sharpe(sharpe_ratio) +
            0.10 * self._normalize_trades(num_trades)
        )

        return fitness

    def _simulate_strategy(self, parameters: Dict, strategy_name: str,
                          historical_data: Dict) -> Dict:
        """
        Simulate strategy performance with given parameters

        This is a simplified simulation - in production you'd run actual backtests
        """
        # Simplified simulation for demonstration
        # In real implementation, this would run actual strategy logic

        # Random simulation for now (replace with actual backtesting)
        num_trades = random.randint(20, 100)
        wins = int(num_trades * random.uniform(0.4, 0.7))
        losses = num_trades - wins

        avg_win = random.uniform(0.03, 0.10)
        avg_loss = random.uniform(0.02, 0.05)

        total_return = (wins * avg_win - losses * avg_loss) * 100
        win_rate = (wins / num_trades * 100) if num_trades > 0 else 0

        # Calculate Sharpe ratio (simplified)
        returns = [avg_win] * wins + [-avg_loss] * losses
        sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if len(returns) > 1 else 0

        return {
            'total_return': total_return,
            'win_rate': win_rate,
            'sharpe_ratio': sharpe_ratio,
            'num_trades': num_trades
        }

    def _normalize_return(self, return_pct: float) -> float:
        """Normalize return to 0-1 range (assuming -50% to +100% range)"""
        return max(0, min(1, (return_pct + 50) / 150))

    def _normalize_sharpe(self, sharpe: float) -> float:
        """Normalize Sharpe ratio to 0-1 range (assuming -2 to +4 range)"""
        return max(0, min(1, (sharpe + 2) / 6))

    def _normalize_trades(self, num_trades: int) -> float:
        """Normalize trade count (prefer 30-60 trades, penalize too few or too many)"""
        if 30 <= num_trades <= 60:
            return 1.0
        elif num_trades < 30:
            return num_trades / 30
        else:
            return max(0, 1.0 - (num_trades - 60) / 100)

    def _selection(self, population: List[Dict], fitness_scores: List[float]) -> List[Dict]:
        """Tournament selection"""
        selected = []
        tournament_size = 3

        for _ in range(self.population_size):
            # Random tournament
            tournament_indices = random.sample(range(len(population)), tournament_size)
            tournament_fitness = [fitness_scores[i] for i in tournament_indices]

            # Select best from tournament
            winner_idx = tournament_indices[np.argmax(tournament_fitness)]
            selected.append(deepcopy(population[winner_idx]))

        return selected

    def _crossover(self, selected: List[Dict], strategy_name: str) -> List[Dict]:
        """Single-point crossover"""
        offspring = []

        for i in range(0, len(selected), 2):
            parent1 = selected[i]
            parent2 = selected[i+1] if i+1 < len(selected) else selected[0]

            # Create children
            child1 = {}
            child2 = {}

            params = list(parent1.keys())
            crossover_point = random.randint(1, len(params) - 1)

            for j, param in enumerate(params):
                if j < crossover_point:
                    child1[param] = deepcopy(parent1[param])
                    child2[param] = deepcopy(parent2[param])
                else:
                    child1[param] = deepcopy(parent2[param])
                    child2[param] = deepcopy(parent1[param])

            offspring.append(child1)
            if len(offspring) < self.population_size:
                offspring.append(child2)

        return offspring[:self.population_size]

    def _mutation(self, population: List[Dict], strategy_name: str) -> List[Dict]:
        """Random mutation"""
        ranges = self.PARAMETER_RANGES[strategy_name]

        for individual in population:
            if random.random() < self.mutation_rate:
                # Mutate random parameter
                param = random.choice(list(individual.keys()))
                param_range = ranges[param]

                if param == 'TARGETS':
                    # Mutate one target
                    idx = random.randint(0, len(individual[param]) - 1)
                    individual[param][idx] = random.uniform(
                        param_range[idx][0], param_range[idx][1]
                    )
                else:
                    if isinstance(param_range[0], int):
                        individual[param] = random.randint(param_range[0], param_range[1])
                    else:
                        individual[param] = random.uniform(param_range[0], param_range[1])

        return population

    def optimize_all_strategies(self, historical_data: Dict) -> Dict:
        """Optimize all strategies and return best parameters"""
        optimized = {}

        for strategy in self.PARAMETER_RANGES.keys():
            logger.info(f"\n{'='*60}")
            logger.info(f"Optimizing {strategy}...")
            logger.info('='*60)

            optimized[strategy] = self.optimize_strategy(strategy, historical_data)

        return optimized

    def save_optimized_parameters(self, parameters: Dict, filepath='config/optimized_params.json'):
        """Save optimized parameters to file"""
        with open(filepath, 'w') as f:
            json.dump(parameters, f, indent=2)

        logger.info(f"✅ Saved optimized parameters to {filepath}")

    def load_optimized_parameters(self, filepath='config/optimized_params.json') -> Dict:
        """Load previously optimized parameters"""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"No optimized parameters found at {filepath}")
            return {}
