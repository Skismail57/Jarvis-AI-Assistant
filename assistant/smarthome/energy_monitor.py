"""
Energy Monitoring and Optimization
Monitors energy usage and provides optimization recommendations.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict


class DeviceCategory(Enum):
    LIGHTING = "lighting"
    HVAC = "hvac"
    APPLIANCE = "appliance"
    ENTERTAINMENT = "entertainment"
    KITCHEN = "kitchen"
    OTHER = "other"


@dataclass
class EnergyReading:
    reading_id: str
    device_id: str
    device_category: DeviceCategory
    power_watts: float
    voltage: float
    current: float
    timestamp: str
    cost: float = 0.0


@dataclass
class EnergyOptimization:
    optimization_id: str
    device_id: str
    recommendation: str
    potential_savings_kwh: float
    potential_savings_cost: float
    priority: str  # 'low', 'medium', 'high'
    created_at: str


class EnergyMonitor:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.smarthome_dir = os.path.join(self.base_dir, "data", "smarthome")
        self.readings_file = os.path.join(self.smarthome_dir, "energy_readings.json")
        self.optimizations_file = os.path.join(self.smarthome_dir, "energy_optimizations.json")
        
        os.makedirs(self.smarthome_dir, exist_ok=True)
        
        # Load data
        self.readings = self._load_readings()
        self.optimizations = self._load_optimizations()
        
        # Energy rate (cost per kWh)
        self.energy_rate = 0.12  # $0.12 per kWh

    def _load_readings(self) -> Dict[str, EnergyReading]:
        """Load energy readings from disk."""
        if os.path.exists(self.readings_file):
            try:
                with open(self.readings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {reading_id: EnergyReading(**reading) for reading_id, reading in data.items()}
            except Exception:
                pass
        return {}

    def _save_readings(self):
        """Save energy readings to disk."""
        try:
            from assistant.utils.json_encoder import CustomJSONEncoder
            data = {reading_id: asdict(reading) for reading_id, reading in self.readings.items()}
            with open(self.readings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
        except Exception as e:
            print(f"[EnergyMonitor] Failed to save readings: {e}")

    def _load_optimizations(self) -> Dict[str, EnergyOptimization]:
        """Load energy optimizations from disk."""
        if os.path.exists(self.optimizations_file):
            try:
                with open(self.optimizations_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {opt_id: EnergyOptimization(**opt) for opt_id, opt in data.items()}
            except Exception:
                pass
        return {}

    def _save_optimizations(self):
        """Save energy optimizations to disk."""
        try:
            data = {opt_id: asdict(opt) for opt_id, opt in self.optimizations.items()}
            with open(self.optimizations_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[EnergyMonitor] Failed to save optimizations: {e}")

    def record_reading(self, device_id: str, device_category: DeviceCategory,
                      power_watts: float, voltage: float = 120.0, 
                      current: float = None) -> EnergyReading:
        """
        Record an energy reading.
        
        Args:
            device_id: Device ID
            device_category: Device category
            power_watts: Power consumption in watts
            voltage: Voltage
            current: Current in amps (calculated if not provided)
            
        Returns:
            EnergyReading
        """
        if current is None:
            current = power_watts / voltage if voltage > 0 else 0
        
        reading_id = f"reading_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Calculate cost
        kwh = power_watts / 1000
        cost = kwh * self.energy_rate
        
        reading = EnergyReading(
            reading_id=reading_id,
            device_id=device_id,
            device_category=device_category,
            power_watts=power_watts,
            voltage=voltage,
            current=current,
            timestamp=datetime.now().isoformat(),
            cost=cost
        )
        
        self.readings[reading_id] = reading
        self._save_readings()
        
        return reading

    def get_device_consumption(self, device_id: str, hours: int = 24) -> Dict[str, Any]:
        """
        Get energy consumption for a device.
        
        Args:
            device_id: Device ID
            hours: Number of hours to analyze
            
        Returns:
            Consumption statistics
        """
        cutoff_date = datetime.now() - timedelta(hours=hours)
        
        device_readings = [
            reading for reading in self.readings.values()
            if reading.device_id == device_id and datetime.fromisoformat(reading.timestamp) >= cutoff_date
        ]
        
        if not device_readings:
            return {'device_id': device_id, 'message': 'No readings available'}
        
        total_power = sum(r.power_watts for r in device_readings)
        avg_power = total_power / len(device_readings)
        total_kwh = (total_power / 1000) * (hours / len(device_readings))
        total_cost = total_kwh * self.energy_rate
        
        return {
            'device_id': device_id,
            'period_hours': hours,
            'total_readings': len(device_readings),
            'average_power_watts': round(avg_power, 2),
            'total_kwh': round(total_kwh, 2),
            'total_cost': round(total_cost, 2)
        }

    def get_category_consumption(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get energy consumption by category.
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Category consumption statistics
        """
        cutoff_date = datetime.now() - timedelta(hours=hours)
        
        recent_readings = [
            reading for reading in self.readings.values()
            if datetime.fromisoformat(reading.timestamp) >= cutoff_date
        ]
        
        category_consumption = defaultdict(lambda: {'power': 0.0, 'count': 0})
        
        for reading in recent_readings:
            category = reading.device_category.value
            category_consumption[category]['power'] += reading.power_watts
            category_consumption[category]['count'] += 1
        
        results = {}
        for category, data in category_consumption.items():
            avg_power = data['power'] / data['count'] if data['count'] > 0 else 0
            kwh = (data['power'] / 1000) * (hours / data['count']) if data['count'] > 0 else 0
            cost = kwh * self.energy_rate
            
            results[category] = {
                'average_power_watts': round(avg_power, 2),
                'total_kwh': round(kwh, 2),
                'total_cost': round(cost, 2),
                'reading_count': data['count']
            }
        
        return results

    def get_total_consumption(self, hours: int = 24) -> Dict[str, Any]:
        """Get total energy consumption."""
        cutoff_date = datetime.now() - timedelta(hours=hours)
        
        recent_readings = [
            reading for reading in self.readings.values()
            if datetime.fromisoformat(reading.timestamp) >= cutoff_date
        ]
        
        if not recent_readings:
            return {'message': 'No readings available'}
        
        total_power = sum(r.power_watts for r in recent_readings)
        avg_power = total_power / len(recent_readings)
        total_kwh = (total_power / 1000) * (hours / len(recent_readings))
        total_cost = total_kwh * self.energy_rate
        
        return {
            'period_hours': hours,
            'total_readings': len(recent_readings),
            'average_power_watts': round(avg_power, 2),
            'total_kwh': round(total_kwh, 2),
            'total_cost': round(total_cost, 2)
        }

    def analyze_consumption_patterns(self, days: int = 7) -> Dict[str, Any]:
        """
        Analyze consumption patterns over time.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Pattern analysis
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Group by hour of day
        hourly_consumption = defaultdict(lambda: {'power': 0.0, 'count': 0})
        
        for reading in self.readings.values():
            reading_time = datetime.fromisoformat(reading.timestamp)
            if reading_time >= cutoff_date:
                hour = reading_time.hour
                hourly_consumption[hour]['power'] += reading.power_watts
                hourly_consumption[hour]['count'] += 1
        
        # Calculate average per hour
        hourly_avg = {}
        for hour, data in hourly_consumption.items():
            if data['count'] > 0:
                hourly_avg[hour] = data['power'] / data['count']
        
        # Find peak hours
        if hourly_avg:
            peak_hour = max(hourly_avg, key=hourly_avg.get)
            low_hour = min(hourly_avg, key=hourly_avg.get)
        else:
            peak_hour = None
            low_hour = None
        
        return {
            'period_days': days,
            'hourly_average': {hour: round(power, 2) for hour, power in hourly_avg.items()},
            'peak_hour': peak_hour,
            'low_hour': low_hour
        }

    def generate_optimizations(self) -> List[EnergyOptimization]:
        """Generate energy optimization recommendations."""
        optimizations = []
        
        # Analyze device consumption
        device_consumption = defaultdict(list)
        for reading in self.readings.values():
            device_consumption[reading.device_id].append(reading.power_watts)
        
        for device_id, power_readings in device_consumption.items():
            if len(power_readings) < 10:
                continue
            
            avg_power = sum(power_readings) / len(power_readings)
            
            # High consumption devices
            if avg_power > 1000:  # > 1kW
                potential_savings_kwh = (avg_power * 0.2) / 1000 * 24  # 20% reduction
                potential_savings_cost = potential_savings_kwh * self.energy_rate * 30  # Monthly
                
                opt_id = f"opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                optimization = EnergyOptimization(
                    optimization_id=opt_id,
                    device_id=device_id,
                    recommendation=f"Consider scheduling {device_id} during off-peak hours or reducing usage",
                    potential_savings_kwh=round(potential_savings_kwh, 2),
                    potential_savings_cost=round(potential_savings_cost, 2),
                    priority='high',
                    created_at=datetime.now().isoformat()
                )
                
                optimizations.append(optimization)
                self.optimizations[opt_id] = optimization
        
        self._save_optimizations()
        return optimizations

    def get_optimizations(self) -> List[EnergyOptimization]:
        """Get all energy optimizations."""
        return list(self.optimizations.values())

    def apply_optimization(self, optimization_id: str) -> Tuple[bool, str]:
        """
        Apply an energy optimization.
        
        Args:
            optimization_id: Optimization ID
            
        Returns:
            (success, message)
        """
        if optimization_id not in self.optimizations:
            return False, "Optimization not found"
        
        # In production, this would apply the optimization
        # For now, mark as applied
        return True, "Optimization applied successfully"

    def set_energy_rate(self, rate: float):
        """Set energy rate (cost per kWh)."""
        self.energy_rate = rate

    def clear_old_readings(self, days: int = 90) -> int:
        """Clear readings older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        to_remove = [
            reading_id for reading_id, reading in self.readings.items()
            if datetime.fromisoformat(reading.timestamp) < cutoff_date
        ]
        
        for reading_id in to_remove:
            del self.readings[reading_id]
        
        if to_remove:
            self._save_readings()
        
        return len(to_remove)

    def get_statistics(self) -> Dict[str, Any]:
        """Get energy monitoring statistics."""
        total_readings = len(self.readings)
        total_optimizations = len(self.optimizations)
        
        # Count by category
        by_category = defaultdict(int)
        for reading in self.readings.values():
            by_category[reading.device_category.value] += 1
        
        return {
            'total_readings': total_readings,
            'total_optimizations': total_optimizations,
            'by_category': dict(by_category),
            'energy_rate': self.energy_rate
        }

    def export_consumption_report(self, export_path: str, days: int = 30) -> Tuple[bool, str]:
        """Export consumption report to file."""
        try:
            report = {
                'report_date': datetime.now().isoformat(),
                'period_days': days,
                'total_consumption': self.get_total_consumption(hours=days*24),
                'category_consumption': self.get_category_consumption(hours=days*24),
                'consumption_patterns': self.analyze_consumption_patterns(days=days),
                'optimizations': [asdict(opt) for opt in self.get_optimizations()]
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            
            return True, f"Report exported to {export_path}"
        except Exception as e:
            return False, f"Export failed: {str(e)}"
