#!/usr/bin/env python3
"""
Advanced Shot Analytics Engine
Calculates comprehensive metrics for espresso shot analysis
"""

import json
import math
import statistics
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ShotAnalytics:
    """Advanced analytics calculator for espresso shots"""
    
    # Industry standard ranges for quality assessment
    IDEAL_EXTRACTION_YIELD = 0.18  # 18-22% is ideal
    IDEAL_TDS = 0.09  # 9-11% TDS is ideal
    IDEAL_BREW_RATIO = 2.0  # 1:2 ratio is standard
    IDEAL_EXTRACTION_TIME = 25.0  # 25-30 seconds is ideal
    IDEAL_PEAK_PRESSURE = 9.0  # 9 bar is ideal
    IDEAL_FLOW_RATE = 2.0  # 2 ml/s average flow
    
    def __init__(self, shot_data: Dict):
        """Initialize analytics with shot data"""
        self.shot = shot_data
        self.time_series = shot_data.get('time_series_data', [])
        self.phases = shot_data.get('phase_metrics', [])
        
    def calculate_all_analytics(self) -> Dict:
        """Calculate all analytics metrics"""
        analytics = {
            'basic': self._calculate_basic_metrics(),
            'extraction': self._calculate_extraction_metrics(),
            'flow_analysis': self._calculate_flow_analysis(),
            'pressure_analysis': self._calculate_pressure_analysis(),
            'phase_analysis': self._calculate_phase_analysis(),
            'quality': self._calculate_quality_score(),
            'recommendations': self._generate_recommendations(),
            'trends': self._calculate_trends(),
            'comparison': self._calculate_comparison_metrics()
        }
        return analytics
    
    def _calculate_basic_metrics(self) -> Dict:
        """Calculate basic shot metrics"""
        total_time = self.shot.get('total_time', 0)
        total_weight = self.shot.get('total_weight', 0)
        grind_weight = self.shot.get('grind_weight', 0)
        ratio = self.shot.get('ratio', 0)
        
        # Calculate flow rate (ml/s) - assuming 1g ≈ 1ml for espresso
        avg_flow_rate = (total_weight / total_time) if total_time > 0 else 0
        
        # Calculate shot efficiency
        efficiency = (total_weight / grind_weight) if grind_weight > 0 else 0
        
        return {
            'total_time': total_time,
            'total_weight': total_weight,
            'grind_weight': grind_weight,
            'ratio': ratio,
            'average_flow_rate': avg_flow_rate,
            'efficiency': efficiency,
            'time_to_first_drip': self.shot.get('time_to_first_drip', 0),
            'pre_infusion_time': self.shot.get('pre_infusion_time', 0)
        }
    
    def _calculate_extraction_metrics(self) -> Dict:
        """Calculate extraction yield and TDS estimates"""
        grind_weight = self.shot.get('grind_weight', 0)
        total_weight = self.shot.get('total_weight', 0)
        total_time = self.shot.get('total_time', 0)
        peak_pressure = self.shot.get('peak_pressure', 0)
        avg_pressure = self.shot.get('average_pressure', 0)
        avg_flow = self.shot.get('average_flow', 0)
        
        # Extraction Yield Calculation
        # EY = (Brewed Coffee Weight * TDS) / Ground Coffee Weight
        # We estimate TDS based on pressure, flow, and time
        
        # TDS Estimation Model (simplified)
        # Based on industry research: TDS correlates with pressure, flow, and extraction time
        # Higher pressure + longer time = higher extraction
        # Optimal flow rate = better extraction
        
        # Base TDS estimate (8-12% range)
        base_tds = 0.10  # 10% base
        
        # Pressure factor (higher pressure = higher extraction)
        pressure_factor = min(peak_pressure / 9.0, 1.2)  # Normalize to 9 bar
        
        # Flow factor (optimal flow = 2 ml/s)
        flow_factor = 1.0
        if avg_flow > 0:
            optimal_flow = 2.0
            flow_deviation = abs(avg_flow - optimal_flow) / optimal_flow
            flow_factor = max(0.8, 1.0 - (flow_deviation * 0.3))
        
        # Time factor (25-30s is optimal)
        time_factor = 1.0
        if total_time > 0:
            if 25 <= total_time <= 30:
                time_factor = 1.0
            elif total_time < 25:
                time_factor = 0.85 + (total_time / 25.0) * 0.15
            else:
                time_factor = 1.0 - min((total_time - 30) / 30.0, 0.2)
        
        # Calculate estimated TDS
        estimated_tds = base_tds * pressure_factor * flow_factor * time_factor
        estimated_tds = max(0.07, min(0.13, estimated_tds))  # Clamp to realistic range
        
        # Calculate Extraction Yield
        extraction_yield = (total_weight * estimated_tds) / grind_weight if grind_weight > 0 else 0
        
        # Extraction Yield Percentage
        extraction_yield_percent = extraction_yield * 100
        
        # Strength (TDS as percentage)
        strength_percent = estimated_tds * 100
        
        return {
            'extraction_yield': extraction_yield,
            'extraction_yield_percent': extraction_yield_percent,
            'estimated_tds': estimated_tds,
            'strength_percent': strength_percent,
            'extraction_classification': self._classify_extraction(extraction_yield_percent),
            'strength_classification': self._classify_strength(strength_percent)
        }
    
    def _classify_extraction(self, ey_percent: float) -> str:
        """Classify extraction yield"""
        if ey_percent < 16:
            return 'Under-extracted'
        elif ey_percent < 18:
            return 'Slightly Under-extracted'
        elif ey_percent <= 22:
            return 'Optimal'
        elif ey_percent <= 24:
            return 'Slightly Over-extracted'
        else:
            return 'Over-extracted'
    
    def _classify_strength(self, strength_percent: float) -> str:
        """Classify strength (TDS)"""
        if strength_percent < 8:
            return 'Weak'
        elif strength_percent < 9:
            return 'Light'
        elif strength_percent <= 11:
            return 'Balanced'
        elif strength_percent <= 12:
            return 'Strong'
        else:
            return 'Very Strong'
    
    def _calculate_flow_analysis(self) -> Dict:
        """Advanced flow rate analysis"""
        if not self.time_series or len(self.time_series) < 2:
            return {
                'peak_flow': self.shot.get('peak_flow', 0),
                'average_flow': self.shot.get('average_flow', 0),
                'flow_stability': self.shot.get('flow_stability', 0),
                'flow_consistency': 0,
                'flow_profile': 'unknown'
            }
        
        # Extract flow data points
        flow_points = [point.get('flow', 0) for point in self.time_series if point.get('flow') is not None]
        
        if not flow_points:
            return {'error': 'No flow data available'}
        
        # Calculate flow metrics
        peak_flow = max(flow_points)
        avg_flow = statistics.mean(flow_points)
        median_flow = statistics.median(flow_points)
        
        # Flow stability (coefficient of variation)
        if avg_flow > 0:
            flow_std = statistics.stdev(flow_points) if len(flow_points) > 1 else 0
            flow_cv = (flow_std / avg_flow) * 100  # Coefficient of variation
            flow_stability = max(0, 100 - flow_cv)  # Invert so higher = more stable
        else:
            flow_stability = 0
        
        # Flow consistency (how close to median)
        deviations = [abs(f - median_flow) for f in flow_points]
        avg_deviation = statistics.mean(deviations) if deviations else 0
        flow_consistency = max(0, 100 - (avg_deviation / median_flow * 100)) if median_flow > 0 else 0
        
        # Flow profile classification
        flow_profile = self._classify_flow_profile(flow_points)
        
        # Flow rate changes (acceleration/deceleration)
        flow_changes = []
        for i in range(1, len(flow_points)):
            change = flow_points[i] - flow_points[i-1]
            flow_changes.append(change)
        
        avg_flow_change = statistics.mean(flow_changes) if flow_changes else 0
        
        return {
            'peak_flow': peak_flow,
            'average_flow': avg_flow,
            'median_flow': median_flow,
            'min_flow': min(flow_points),
            'max_flow': peak_flow,
            'flow_stability': flow_stability,
            'flow_consistency': flow_consistency,
            'flow_profile': flow_profile,
            'flow_variance': statistics.variance(flow_points) if len(flow_points) > 1 else 0,
            'flow_acceleration': avg_flow_change
        }
    
    def _classify_flow_profile(self, flow_points: List[float]) -> str:
        """Classify flow profile type"""
        if len(flow_points) < 3:
            return 'unknown'
        
        # Split into thirds
        third = len(flow_points) // 3
        first_third = statistics.mean(flow_points[:third])
        middle_third = statistics.mean(flow_points[third:2*third])
        last_third = statistics.mean(flow_points[2*third:])
        
        # Classify based on flow progression
        if first_third < middle_third < last_third:
            return 'increasing'  # Flow increases over time
        elif first_third > middle_third > last_third:
            return 'decreasing'  # Flow decreases over time
        elif abs(first_third - last_third) < (statistics.mean(flow_points) * 0.1):
            return 'stable'  # Relatively constant
        elif middle_third > first_third and middle_third > last_third:
            return 'peak_mid'  # Peak in middle
        else:
            return 'variable'
    
    def _calculate_pressure_analysis(self) -> Dict:
        """Advanced pressure profiling analysis"""
        if not self.time_series or len(self.time_series) < 2:
            return {
                'peak_pressure': self.shot.get('peak_pressure', 0),
                'average_pressure': self.shot.get('average_pressure', 0),
                'pressure_stability': self.shot.get('pressure_stability', 0)
            }
        
        # Extract pressure data points
        pressure_points = [point.get('pressure', 0) for point in self.time_series if point.get('pressure') is not None]
        
        if not pressure_points:
            return {'error': 'No pressure data available'}
        
        peak_pressure = max(pressure_points)
        avg_pressure = statistics.mean(pressure_points)
        median_pressure = statistics.median(pressure_points)
        min_pressure = min(pressure_points)
        
        # Pressure stability
        if avg_pressure > 0:
            pressure_std = statistics.stdev(pressure_points) if len(pressure_points) > 1 else 0
            pressure_cv = (pressure_std / avg_pressure) * 100
            pressure_stability = max(0, 100 - pressure_cv)
        else:
            pressure_stability = 0
        
        # Pressure profile
        pressure_profile = self._classify_pressure_profile(pressure_points)
        
        # Pressure ramp-up time (time to reach 90% of peak)
        peak_90 = peak_pressure * 0.9
        ramp_up_time = 0
        for i, p in enumerate(pressure_points):
            if p >= peak_90:
                ramp_up_time = i * (self.shot.get('total_time', 0) / len(pressure_points))
                break
        
        # Pressure hold time (time spent within 10% of peak)
        peak_10_range = peak_pressure * 0.1
        hold_time = 0
        for p in pressure_points:
            if abs(p - peak_pressure) <= peak_10_range:
                hold_time += (self.shot.get('total_time', 0) / len(pressure_points))
        
        return {
            'peak_pressure': peak_pressure,
            'average_pressure': avg_pressure,
            'median_pressure': median_pressure,
            'min_pressure': min_pressure,
            'pressure_stability': pressure_stability,
            'pressure_profile': pressure_profile,
            'ramp_up_time': ramp_up_time,
            'hold_time': hold_time,
            'pressure_variance': statistics.variance(pressure_points) if len(pressure_points) > 1 else 0
        }
    
    def _classify_pressure_profile(self, pressure_points: List[float]) -> str:
        """Classify pressure profile type"""
        if len(pressure_points) < 3:
            return 'unknown'
        
        third = len(pressure_points) // 3
        first_third = statistics.mean(pressure_points[:third])
        middle_third = statistics.mean(pressure_points[third:2*third])
        last_third = statistics.mean(pressure_points[2*third:])
        
        if first_third < middle_third and middle_third > last_third:
            return 'traditional'  # Ramp up, hold, decline
        elif abs(first_third - last_third) < (statistics.mean(pressure_points) * 0.15):
            return 'flat'  # Constant pressure
        elif first_third > middle_third and middle_third < last_third:
            return 'bloom'  # High-low-high (blooming)
        elif first_third < middle_third < last_third:
            return 'increasing'  # Gradually increasing
        elif first_third > middle_third > last_third:
            return 'decreasing'  # Gradually decreasing
        else:
            return 'variable'
    
    def _calculate_phase_analysis(self) -> Dict:
        """Analyze extraction phases"""
        if not self.phases:
            return {'phases': [], 'phase_transitions': []}
        
        phase_analysis = []
        total_phase_time = 0
        
        for phase in self.phases:
            phase_name = phase.get('name', 'unknown')
            duration = phase.get('duration', 0)
            avg_flow = phase.get('avg_flow', 0)
            avg_pressure = phase.get('avg_pressure', 0)
            weight_gain = phase.get('weight_gain', 0)
            
            total_phase_time += duration
            
            phase_analysis.append({
                'name': phase_name,
                'duration': duration,
                'percentage': (duration / self.shot.get('total_time', 1)) * 100 if self.shot.get('total_time', 0) > 0 else 0,
                'avg_flow': avg_flow,
                'avg_pressure': avg_pressure,
                'weight_gain': weight_gain,
                'flow_rate': weight_gain / duration if duration > 0 else 0
            })
        
        return {
            'phases': phase_analysis,
            'total_phase_time': total_phase_time,
            'phase_count': len(self.phases)
        }
    
    def _calculate_quality_score(self) -> Dict:
        """Calculate overall quality score (0-100)"""
        scores = []
        
        # Extraction yield score (0-25 points)
        ey_percent = self._calculate_extraction_metrics().get('extraction_yield_percent', 0)
        if 18 <= ey_percent <= 22:
            ey_score = 25
        elif 16 <= ey_percent < 18 or 22 < ey_percent <= 24:
            ey_score = 20
        elif 14 <= ey_percent < 16 or 24 < ey_percent <= 26:
            ey_score = 15
        else:
            ey_score = 10
        scores.append(('extraction_yield', ey_score, 25))
        
        # Time score (0-20 points)
        total_time = self.shot.get('total_time', 0)
        if 25 <= total_time <= 30:
            time_score = 20
        elif 20 <= total_time < 25 or 30 < total_time <= 35:
            time_score = 15
        elif 15 <= total_time < 20 or 35 < total_time <= 40:
            time_score = 10
        else:
            time_score = 5
        scores.append(('time', time_score, 20))
        
        # Pressure score (0-20 points)
        peak_pressure = self.shot.get('peak_pressure', 0)
        if 8.5 <= peak_pressure <= 9.5:
            pressure_score = 20
        elif 8.0 <= peak_pressure < 8.5 or 9.5 < peak_pressure <= 10.0:
            pressure_score = 15
        elif 7.5 <= peak_pressure < 8.0 or 10.0 < peak_pressure <= 10.5:
            pressure_score = 10
        else:
            pressure_score = 5
        scores.append(('pressure', pressure_score, 20))
        
        # Flow stability score (0-15 points)
        flow_stability = self.shot.get('flow_stability', 0)
        flow_score = (flow_stability / 100) * 15
        scores.append(('flow_stability', flow_score, 15))
        
        # Pressure stability score (0-10 points)
        pressure_stability = self.shot.get('pressure_stability', 0)
        pressure_stab_score = (pressure_stability / 100) * 10
        scores.append(('pressure_stability', pressure_stab_score, 10))
        
        # Target weight achievement (0-10 points)
        target_reached = self.shot.get('target_weight_reached', False)
        weight_deviation = abs(self.shot.get('weight_deviation', 0))
        if target_reached:
            weight_score = 10
        elif weight_deviation < 2:
            weight_score = 8
        elif weight_deviation < 5:
            weight_score = 5
        else:
            weight_score = 2
        scores.append(('target_weight', weight_score, 10))
        
        # Calculate total score
        total_score = sum(score for _, score, _ in scores)
        max_score = sum(max_points for _, _, max_points in scores)
        quality_percent = (total_score / max_score) * 100 if max_score > 0 else 0
        
        # Quality classification
        if quality_percent >= 90:
            quality_class = 'Excellent'
        elif quality_percent >= 75:
            quality_class = 'Very Good'
        elif quality_percent >= 60:
            quality_class = 'Good'
        elif quality_percent >= 45:
            quality_class = 'Fair'
        else:
            quality_class = 'Needs Improvement'
        
        return {
            'overall_score': round(quality_percent, 1),
            'quality_class': quality_class,
            'component_scores': {name: score for name, score, _ in scores},
            'max_score': max_score,
            'total_score': total_score
        }
    
    def _generate_recommendations(self) -> List[Dict]:
        """Generate improvement recommendations"""
        recommendations = []
        
        # Check extraction yield
        ey_percent = self._calculate_extraction_metrics().get('extraction_yield_percent', 0)
        if ey_percent < 18:
            recommendations.append({
                'type': 'extraction',
                'priority': 'high',
                'message': f'Extraction yield is {ey_percent:.1f}% (target: 18-22%). Consider finer grind or longer extraction time.',
                'metric': 'extraction_yield',
                'current_value': ey_percent,
                'target_range': '18-22%'
            })
        elif ey_percent > 22:
            recommendations.append({
                'type': 'extraction',
                'priority': 'medium',
                'message': f'Extraction yield is {ey_percent:.1f}% (target: 18-22%). Consider coarser grind or shorter extraction time.',
                'metric': 'extraction_yield',
                'current_value': ey_percent,
                'target_range': '18-22%'
            })
        
        # Check time
        total_time = self.shot.get('total_time', 0)
        if total_time < 25:
            recommendations.append({
                'type': 'time',
                'priority': 'medium',
                'message': f'Shot time is {total_time:.1f}s (target: 25-30s). Consider finer grind to slow extraction.',
                'metric': 'total_time',
                'current_value': total_time,
                'target_range': '25-30s'
            })
        elif total_time > 35:
            recommendations.append({
                'type': 'time',
                'priority': 'medium',
                'message': f'Shot time is {total_time:.1f}s (target: 25-30s). Consider coarser grind to speed up extraction.',
                'metric': 'total_time',
                'current_value': total_time,
                'target_range': '25-30s'
            })
        
        # Check pressure
        peak_pressure = self.shot.get('peak_pressure', 0)
        if peak_pressure < 8.5:
            recommendations.append({
                'type': 'pressure',
                'priority': 'low',
                'message': f'Peak pressure is {peak_pressure:.1f} bar (target: 9 bar). Machine may need adjustment.',
                'metric': 'peak_pressure',
                'current_value': peak_pressure,
                'target_range': '8.5-9.5 bar'
            })
        
        # Check flow stability
        flow_stability = self.shot.get('flow_stability', 0)
        if flow_stability < 70:
            recommendations.append({
                'type': 'flow',
                'priority': 'medium',
                'message': f'Flow stability is {flow_stability:.1f}% (target: >80%). Check grind consistency and distribution.',
                'metric': 'flow_stability',
                'current_value': flow_stability,
                'target_range': '>80%'
            })
        
        return recommendations
    
    def _calculate_trends(self) -> Dict:
        """Calculate trend indicators (requires historical data)"""
        # This would compare with previous shots
        # For now, return basic structure
        return {
            'trend_available': False,
            'message': 'Trend analysis requires multiple shots for comparison'
        }
    
    def _calculate_comparison_metrics(self) -> Dict:
        """Calculate metrics useful for comparison"""
        return {
            'key_metrics': {
                'extraction_yield_percent': self._calculate_extraction_metrics().get('extraction_yield_percent', 0),
                'total_time': self.shot.get('total_time', 0),
                'total_weight': self.shot.get('total_weight', 0),
                'peak_pressure': self.shot.get('peak_pressure', 0),
                'average_flow': self.shot.get('average_flow', 0),
                'quality_score': self._calculate_quality_score().get('overall_score', 0)
            }
        }


def calculate_shot_analytics(shot_data: Dict) -> Dict:
    """Main function to calculate all analytics for a shot"""
    try:
        analytics_engine = ShotAnalytics(shot_data)
        return analytics_engine.calculate_all_analytics()
    except Exception as e:
        logger.error(f"Error calculating analytics: {e}")
        return {'error': str(e)}


def compare_shots(shots: List[Dict]) -> Dict:
    """Compare multiple shots and generate comparison metrics"""
    if len(shots) < 2:
        return {'error': 'Need at least 2 shots to compare'}
    
    try:
        # Calculate analytics for each shot
        shot_analytics = []
        for shot in shots:
            analytics = calculate_shot_analytics(shot)
            shot_analytics.append({
                'shot_id': shot.get('id'),
                'shot_number': shot.get('shot_number'),
                'analytics': analytics
            })
        
        # Extract key metrics for comparison
        metrics_to_compare = [
            'extraction_yield_percent',
            'total_time',
            'total_weight',
            'peak_pressure',
            'average_flow',
            'quality_score'
        ]
        
        comparison = {
            'shots': shot_analytics,
            'differences': {},
            'averages': {},
            'ranges': {}
        }
        
        # Calculate differences and averages
        for metric in metrics_to_compare:
            values = []
            for sa in shot_analytics:
                value = sa['analytics'].get('comparison', {}).get('key_metrics', {}).get(metric)
                if value is not None:
                    values.append(value)
            
            if values:
                comparison['averages'][metric] = statistics.mean(values)
                comparison['ranges'][metric] = {
                    'min': min(values),
                    'max': max(values),
                    'range': max(values) - min(values)
                }
                
                # Calculate differences between shots
                if len(values) == 2:
                    comparison['differences'][metric] = abs(values[0] - values[1])
        
        return comparison
    except Exception as e:
        logger.error(f"Error comparing shots: {e}")
        return {'error': str(e)}

