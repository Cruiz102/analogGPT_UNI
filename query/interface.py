"""
Query interface for searching and filtering simulation data.
"""
from typing import List, Dict, Optional, Any
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import joinedload

from database import (
    get_database,
    Simulation,
    Category,
    SimulationParameter,
    SweepConfiguration,
    DataSeries,
    DataSeriesSweepParam,
    DataPoint,
    OptimizationMetric
)


class SimulationQuery:
    """
    Query interface for simulation database.
    """
    
    def __init__(self):
        """Initialize the query interface."""
        self.db = get_database()
    
    def search_simulations(
        self,
        name: Optional[str] = None,
        circuit_name: Optional[str] = None,
        categories: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> List[Simulation]:
        """
        Search for simulations by name, circuit, or categories.
        
        Args:
            name: Simulation name (partial match)
            circuit_name: Circuit name (partial match)
            categories: List of category names (any match)
            limit: Maximum number of results
            
        Returns:
            List of Simulation objects
        """
        with self.db.get_session() as session:
            query = session.query(Simulation).options(
                joinedload(Simulation.categories)
            )
            
            # Filter by name
            if name:
                query = query.filter(Simulation.name.like(f'%{name}%'))
            
            # Filter by circuit name
            if circuit_name:
                query = query.filter(Simulation.circuit_name.like(f'%{circuit_name}%'))
            
            # Filter by categories
            if categories:
                query = query.join(Simulation.categories).filter(
                    Category.name.in_(categories)
                )
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            # Execute query and convert to dicts
            results = []
            for sim in query.all():
                results.append({
                    'id': sim.id,
                    'name': sim.name,
                    'circuit_name': sim.circuit_name,
                    'description': sim.description,
                    'categories': [cat.name for cat in sim.categories]
                })
            
            return results
    
    def filter_by_metric(
        self,
        metric_name: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter simulations by optimization metric values.
        
        Args:
            metric_name: Name of the metric (e.g., 'error_percentage', 'gain')
            min_value: Minimum metric value (inclusive)
            max_value: Maximum metric value (inclusive)
            limit: Maximum number of results
            
        Returns:
            List of dictionaries containing simulation and metric info with sweep parameters
        """
        with self.db.get_session() as session:
            query = session.query(
                Simulation,
                OptimizationMetric,
                DataSeries
            ).join(
                OptimizationMetric,
                OptimizationMetric.simulation_id == Simulation.id
            ).outerjoin(
                DataSeries,
                DataSeries.id == OptimizationMetric.data_series_id
            ).filter(
                OptimizationMetric.metric_name == metric_name
            )
            
            # Filter by value range
            if min_value is not None:
                query = query.filter(OptimizationMetric.metric_value >= min_value)
            if max_value is not None:
                query = query.filter(OptimizationMetric.metric_value <= max_value)
            
            # Order by metric value
            query = query.order_by(OptimizationMetric.metric_value)
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            # Execute and format results
            results = []
            for sim, metric, series in query.all():
                result = {
                    'simulation_id': sim.id,
                    'simulation_name': sim.name,
                    'circuit_name': sim.circuit_name,
                    'metric_name': metric.metric_name,
                    'metric_value': metric.metric_value,
                    'metric_unit': metric.unit,
                }
                if series:
                    result['signal_path'] = series.signal_path
                    result['data_series_id'] = series.id
                    
                    # Get sweep parameters for this data series
                    sweep_params = session.query(DataSeriesSweepParam).filter(
                        DataSeriesSweepParam.data_series_id == series.id
                    ).all()
                    
                    result['sweep_parameters'] = {
                        sp.parameter_name: sp.parameter_value 
                        for sp in sweep_params
                    }
                results.append(result)
            
            return results
    
    def get_simulation_details(self, simulation_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a simulation.
        
        Args:
            simulation_id: Simulation ID
            
        Returns:
            Dictionary with simulation details or None if not found
        """
        with self.db.get_session() as session:
            sim = session.query(Simulation).options(
                joinedload(Simulation.parameters),
                joinedload(Simulation.categories),
                joinedload(Simulation.sweep_configs),
                joinedload(Simulation.optimization_metrics)
            ).get(simulation_id)
            
            if not sim:
                return None
            
            # Format details
            details = {
                'id': sim.id,
                'name': sim.name,
                'circuit_name': sim.circuit_name,
                'description': sim.description,
                'created_at': sim.created_at.isoformat() if sim.created_at else None,
                'assumptions': {
                    'vdd': sim.vdd,
                    'vt': sim.vt,
                    'temperature': sim.temperature
                },
                'categories': [cat.name for cat in sim.categories],
                'parameters': [
                    {
                        'name': p.parameter_name,
                        'value': p.parameter_value,
                        'unit': p.unit
                    }
                    for p in sim.parameters
                ],
                'sweep_parameters': [
                    sc.parameter_name for sc in sim.sweep_configs
                ],
                'metrics': [
                    {
                        'name': m.metric_name,
                        'value': m.metric_value,
                        'unit': m.unit
                    }
                    for m in sim.optimization_metrics
                ]
            }
            
            return details
    
    def get_data_series(
        self,
        simulation_id: int,
        signal_path: Optional[str] = None,
        sweep_filters: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get data series for a simulation.
        
        Args:
            simulation_id: Simulation ID
            signal_path: Filter by signal path
            sweep_filters: Filter by sweep parameter values (e.g., {'Nm_In_W': 2.4e-07})
            
        Returns:
            List of data series with their points
        """
        with self.db.get_session() as session:
            query = session.query(DataSeries).filter(
                DataSeries.simulation_id == simulation_id
            )
            
            # Filter by signal path
            if signal_path:
                query = query.filter(DataSeries.signal_path == signal_path)
            
            series_list = query.all()
            
            results = []
            for series in series_list:
                # Get sweep parameters
                sweep_params = {}
                for sp in series.sweep_params:
                    sweep_params[sp.parameter_name] = sp.parameter_value
                
                # Check sweep filters
                if sweep_filters:
                    matches = True
                    for param_name, param_value in sweep_filters.items():
                        if sweep_params.get(param_name) != param_value:
                            matches = False
                            break
                    if not matches:
                        continue
                
                # Get data points
                points = session.query(DataPoint).filter(
                    DataPoint.data_series_id == series.id
                ).order_by(DataPoint.sequence).all()
                
                result = {
                    'series_id': series.id,
                    'signal_path': series.signal_path,
                    'sweep_parameters': sweep_params,
                    'data_points': [
                        {
                            'x': p.x_value,
                            'y': p.y_value,
                            'sequence': p.sequence
                        }
                        for p in points
                    ]
                }
                results.append(result)
            
            return results
    
    def list_categories(self) -> List[Dict[str, Any]]:
        """
        List all categories with simulation counts.
        
        Returns:
            List of category information
        """
        with self.db.get_session() as session:
            categories = session.query(Category).all()
            
            results = []
            for cat in categories:
                results.append({
                    'id': cat.id,
                    'name': cat.name,
                    'description': cat.description,
                    'simulation_count': len(cat.simulations)
                })
            
            return results
    
    def get_metric_statistics(
        self,
        metric_name: str,
        circuit_name: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Get statistics for a specific metric across simulations.
        
        Args:
            metric_name: Name of the metric
            circuit_name: Optional circuit name filter
            
        Returns:
            Dictionary with min, max, avg, count
        """
        with self.db.get_session() as session:
            query = session.query(
                func.min(OptimizationMetric.metric_value).label('min'),
                func.max(OptimizationMetric.metric_value).label('max'),
                func.avg(OptimizationMetric.metric_value).label('avg'),
                func.count(OptimizationMetric.id).label('count')
            ).filter(
                OptimizationMetric.metric_name == metric_name
            )
            
            # Filter by circuit
            if circuit_name:
                query = query.join(Simulation).filter(
                    Simulation.circuit_name.like(f'%{circuit_name}%')
                )
            
            result = query.first()
            
            return {
                'metric_name': metric_name,
                'min': result.min if result.min is not None else 0,
                'max': result.max if result.max is not None else 0,
                'avg': result.avg if result.avg is not None else 0,
                'count': result.count if result.count is not None else 0
            }
