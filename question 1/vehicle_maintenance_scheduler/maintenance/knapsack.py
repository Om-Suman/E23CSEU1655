"""
0/1 Knapsack algorithm implementation for vehicle maintenance task optimization.

This module implements dynamic programming solution to select optimal subset of
maintenance tasks for each depot, maximizing impact while staying within
mechanic hour constraints.
"""

import logging
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)


class KnapsackOptimizer:
    """
    Dynamic programming-based knapsack optimizer for vehicle maintenance tasks.
    
    This class implements the 0/1 knapsack algorithm to find the optimal subset
    of maintenance tasks that maximizes impact while respecting time constraints.
    """
    
    def __init__(self):
        """Initialize the optimizer."""
        self.dp_table = None
        self.selected_tasks = None
    
    def optimize(
        self,
        tasks: List[Dict],
        capacity: int
    ) -> Tuple[int, List[Dict]]:
        """
        Optimize task selection using 0/1 knapsack algorithm.
        
        Args:
            tasks: List of task dictionaries with 'TaskID', 'Duration', 'Impact'
            capacity: Maximum available mechanic hours (knapsack capacity)
            
        Returns:
            Tuple of (total_impact: int, selected_tasks: List[Dict])
        """
        if not tasks or capacity <= 0:
            logger.info('No tasks or zero capacity provided')
            return 0, []
        
        n = len(tasks)
        
        # Validate task data
        try:
            validated_tasks = self._validate_tasks(tasks)
        except ValueError as e:
            logger.error(f'Invalid task data: {str(e)}')
            return 0, []
        
        # Create DP table: dp[i][w] = max impact using first i tasks with w hours
        dp = [[0] * (capacity + 1) for _ in range(n + 1)]
        
        # Fill the DP table
        for i in range(1, n + 1):
            task_duration = validated_tasks[i - 1]['Duration']
            task_impact = validated_tasks[i - 1]['Impact']
            
            for w in range(capacity + 1):
                # Don't take the task
                dp[i][w] = dp[i - 1][w]
                
                # Take the task if it fits
                if task_duration <= w:
                    dp[i][w] = max(
                        dp[i][w],
                        dp[i - 1][w - task_duration] + task_impact
                    )
        
        # Backtrack to find selected tasks
        selected_tasks = self._backtrack(
            dp, validated_tasks, n, capacity
        )
        
        max_impact = dp[n][capacity]
        
        logger.info(
            f'Optimization complete. Max impact: {max_impact}, '
            f'Selected {len(selected_tasks)} tasks'
        )
        
        return max_impact, selected_tasks
    
    def _validate_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """
        Validate task data for required fields and proper types.
        
        Args:
            tasks: List of task dictionaries
            
        Returns:
            List of validated tasks
            
        Raises:
            ValueError: If any task is invalid
        """
        validated = []
        required_fields = {'TaskID', 'Duration', 'Impact'}
        
        for idx, task in enumerate(tasks):
            missing_fields = required_fields - set(task.keys())
            if missing_fields:
                raise ValueError(
                    f'Task {idx} missing fields: {missing_fields}'
                )
            
            try:
                duration = int(task['Duration'])
                impact = int(task['Impact'])
                
                if duration < 0 or impact < 0:
                    raise ValueError(
                        f'Task {idx}: Duration and Impact must be non-negative'
                    )
                
                validated.append({
                    'TaskID': str(task['TaskID']),
                    'Duration': duration,
                    'Impact': impact
                })
            except (TypeError, ValueError) as e:
                raise ValueError(
                    f'Task {idx}: Invalid Duration or Impact - {str(e)}'
                )
        
        return validated
    
    def _backtrack(
        self,
        dp: List[List[int]],
        tasks: List[Dict],
        n: int,
        capacity: int
    ) -> List[Dict]:
        """
        Backtrack through DP table to find selected tasks.
        
        Args:
            dp: DP table from optimization
            tasks: Validated task list
            n: Number of tasks
            capacity: Knapsack capacity
            
        Returns:
            List of selected task dictionaries
        """
        selected = []
        w = capacity
        
        for i in range(n, 0, -1):
            # If value comes from including current task
            if w >= 0 and dp[i][w] != dp[i - 1][w]:
                task = tasks[i - 1]
                selected.append(task)
                w -= task['Duration']
        
        # Reverse to maintain original order
        selected.reverse()
        return selected
    
    def batch_optimize(
        self,
        depots: List[Dict],
        tasks: List[Dict]
    ) -> List[Dict]:
        """
        Optimize task selection for multiple depots.
        
        Args:
            depots: List of depot dictionaries with 'ID' and 'MechanicHours'
            tasks: List of available maintenance tasks
            
        Returns:
            List of optimization results for each depot
        """
        results = []
        
        if not depots or not tasks:
            logger.warning('Empty depots or tasks list for batch optimization')
            return results
        
        for depot in depots:
            try:
                depot_id = depot.get('ID')
                mechanic_hours = depot.get('MechanicHours', 0)
                
                if not depot_id or mechanic_hours <= 0:
                    logger.warning(
                        f'Invalid depot data: ID={depot_id}, '
                        f'MechanicHours={mechanic_hours}'
                    )
                    continue
                
                total_impact, selected_tasks = self.optimize(tasks, mechanic_hours)
                
                results.append({
                    'depotId': depot_id,
                    'mechanicHours': mechanic_hours,
                    'totalImpact': total_impact,
                    'selectedTasks': selected_tasks
                })
                
            except Exception as e:
                logger.error(f'Error optimizing depot {depot.get("ID")}: {str(e)}')
                continue
        
        return results


def get_knapsack_optimizer() -> KnapsackOptimizer:
    """
    Factory function to get an instance of KnapsackOptimizer.
    
    Returns:
        KnapsackOptimizer instance.
    """
    return KnapsackOptimizer()
