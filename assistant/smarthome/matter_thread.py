"""
Matter/Thread Protocol Support
Implements support for Matter and Thread smart home protocols.
"""

import os
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class DeviceType(Enum):
    LIGHT = "light"
    SWITCH = "switch"
    THERMOSTAT = "thermostat"
    LOCK = "lock"
    SENSOR = "sensor"
    PLUG = "plug"
    BLIND = "blind"
    FAN = "fan"
    OTHER = "other"


class DeviceState(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    UPDATING = "updating"


@dataclass
class MatterDevice:
    device_id: str
    name: str
    device_type: DeviceType
    state: DeviceState
    thread_network_id: str
    fabric_id: str
    endpoint_id: int
    attributes: Dict[str, Any]
    last_seen: str
    created_at: str


@dataclass
class ThreadNetwork:
    network_id: str
    name: str
    pan_id: str
    extended_pan_id: str
    channel: int
    network_key: str
    devices: List[str]
    created_at: str


class MatterThreadManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.smarthome_dir = os.path.join(self.base_dir, "data", "smarthome")
        self.devices_file = os.path.join(self.smarthome_dir, "matter_devices.json")
        self.networks_file = os.path.join(self.smarthome_dir, "thread_networks.json")
        
        os.makedirs(self.smarthome_dir, exist_ok=True)
        
        # Load data
        self.devices = self._load_devices()
        self.networks = self._load_networks()

    def _load_devices(self) -> Dict[str, MatterDevice]:
        """Load Matter devices from disk."""
        if os.path.exists(self.devices_file):
            try:
                with open(self.devices_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {device_id: MatterDevice(**device) for device_id, device in data.items()}
            except Exception:
                pass
        return {}

    def _save_devices(self):
        """Save Matter devices to disk."""
        try:
            data = {device_id: asdict(device) for device_id, device in self.devices.items()}
            with open(self.devices_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[MatterThread] Failed to save devices: {e}")

    def _load_networks(self) -> Dict[str, ThreadNetwork]:
        """Load Thread networks from disk."""
        if os.path.exists(self.networks_file):
            try:
                with open(self.networks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {network_id: ThreadNetwork(**network) for network_id, network in data.items()}
            except Exception:
                pass
        return {}

    def _save_networks(self):
        """Save Thread networks to disk."""
        try:
            data = {network_id: asdict(network) for network_id, network in self.networks.items()}
            with open(self.networks_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[MatterThread] Failed to save networks: {e}")

    def create_thread_network(self, name: str, channel: int = 15) -> ThreadNetwork:
        """
        Create a new Thread network.
        
        Args:
            name: Network name
            channel: WiFi channel (11-26)
            
        Returns:
            ThreadNetwork
        """
        import secrets
        
        network_id = f"network_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        pan_id = secrets.token_hex(4)
        extended_pan_id = secrets.token_hex(16)
        network_key = secrets.token_hex(32)
        
        network = ThreadNetwork(
            network_id=network_id,
            name=name,
            pan_id=pan_id,
            extended_pan_id=extended_pan_id,
            channel=channel,
            network_key=network_key,
            devices=[],
            created_at=datetime.now().isoformat()
        )
        
        self.networks[network_id] = network
        self._save_networks()
        
        return network

    def add_matter_device(self, name: str, device_type: DeviceType, 
                        network_id: str, fabric_id: str = None) -> MatterDevice:
        """
        Add a Matter device to the network.
        
        Args:
            name: Device name
            device_type: Type of device
            network_id: Thread network ID
            fabric_id: Matter fabric ID
            
        Returns:
            MatterDevice
        """
        if network_id not in self.networks:
            raise ValueError(f"Network not found: {network_id}")
        
        import secrets
        
        device_id = f"device_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if not fabric_id:
            fabric_id = secrets.token_hex(8)
        
        device = MatterDevice(
            device_id=device_id,
            name=name,
            device_type=device_type,
            state=DeviceState.ONLINE,
            thread_network_id=network_id,
            fabric_id=fabric_id,
            endpoint_id=1,
            attributes={},
            last_seen=datetime.now().isoformat(),
            created_at=datetime.now().isoformat()
        )
        
        self.devices[device_id] = device
        
        # Add to network
        self.networks[network_id].devices.append(device_id)
        self._save_networks()
        self._save_devices()
        
        return device

    def commission_device(self, device_id: str, qr_code: str = None, 
                       manual_code: str = None) -> Tuple[bool, str]:
        """
        Commission a Matter device.
        
        Args:
            device_id: Device ID
            qr_code: QR code for commissioning
            manual_code: Manual pairing code
            
        Returns:
            (success, message)
        """
        if device_id not in self.devices:
            return False, "Device not found"
        
        device = self.devices[device_id]
        
        # In production, this would use actual Matter commissioning
        # For now, simulate successful commissioning
        device.state = DeviceState.ONLINE
        device.last_seen = datetime.now().isoformat()
        
        self._save_devices()
        
        return True, f"Device {device.name} commissioned successfully"

    def send_command(self, device_id: str, command: str, 
                    parameters: Dict[str, Any] = None) -> Tuple[bool, str]:
        """
        Send a command to a Matter device.
        
        Args:
            device_id: Device ID
            command: Command to send
            parameters: Command parameters
            
        Returns:
            (success, message)
        """
        if device_id not in self.devices:
            return False, "Device not found"
        
        device = self.devices[device_id]
        
        if device.state != DeviceState.ONLINE:
            return False, f"Device is {device.state.value}"
        
        # Update device attributes based on command
        if parameters:
            device.attributes.update(parameters)
        
        device.last_seen = datetime.now().isoformat()
        self._save_devices()
        
        return True, f"Command '{command}' sent to {device.name}"

    def get_device_state(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get current state of a device."""
        if device_id not in self.devices:
            return None
        
        device = self.devices[device_id]
        
        return {
            'device_id': device.device_id,
            'name': device.name,
            'type': device.device_type.value,
            'state': device.state.value,
            'attributes': device.attributes,
            'last_seen': device.last_seen
        }

    def set_device_attribute(self, device_id: str, attribute: str, value: Any) -> bool:
        """Set a device attribute."""
        if device_id not in self.devices:
            return False
        
        self.devices[device_id].attributes[attribute] = value
        self.devices[device_id].last_seen = datetime.now().isoformat()
        self._save_devices()
        
        return True

    def remove_device(self, device_id: str) -> bool:
        """Remove a device from the network."""
        if device_id not in self.devices:
            return False
        
        device = self.devices[device_id]
        
        # Remove from network
        if device.thread_network_id in self.networks:
            network = self.networks[device.thread_network_id]
            if device_id in network.devices:
                network.devices.remove(device_id)
            self._save_networks()
        
        del self.devices[device_id]
        self._save_devices()
        
        return True

    def get_network_devices(self, network_id: str) -> List[MatterDevice]:
        """Get all devices on a network."""
        if network_id not in self.networks:
            return []
        
        network = self.networks[network_id]
        return [self.devices[device_id] for device_id in network.devices if device_id in self.devices]

    def discover_devices(self, network_id: str) -> List[MatterDevice]:
        """
        Discover devices on a Thread network.
        
        Args:
            network_id: Network ID
            
        Returns:
            List of discovered devices
        """
        if network_id not in self.networks:
            return []
        
        # In production, this would perform actual network discovery
        # For now, return existing devices
        return self.get_network_devices(network_id)

    def get_network_status(self, network_id: str) -> Dict[str, Any]:
        """Get status of a Thread network."""
        if network_id not in self.networks:
            return {}
        
        network = self.networks[network_id]
        devices = self.get_network_devices(network_id)
        
        online_devices = sum(1 for d in devices if d.state == DeviceState.ONLINE)
        
        return {
            'network_id': network_id,
            'name': network.name,
            'channel': network.channel,
            'total_devices': len(devices),
            'online_devices': online_devices,
            'offline_devices': len(devices) - online_devices
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get Matter/Thread statistics."""
        total_devices = len(self.devices)
        total_networks = len(self.networks)
        
        # Count by type
        by_type = {}
        for device in self.devices.values():
            dtype = device.device_type.value
            by_type[dtype] = by_type.get(dtype, 0) + 1
        
        # Count by state
        by_state = {}
        for device in self.devices.values():
            state = device.state.value
            by_state[state] = by_state.get(state, 0) + 1
        
        return {
            'total_devices': total_devices,
            'total_networks': total_networks,
            'by_type': by_type,
            'by_state': by_state
        }

    def export_network_config(self, network_id: str, export_path: str) -> Tuple[bool, str]:
        """Export network configuration."""
        if network_id not in self.networks:
            return False, "Network not found"
        
        network = self.networks[network_id]
        
        export_data = {
            'network': asdict(network),
            'devices': [asdict(self.devices[did]) for did in network.devices if did in self.devices],
            'exported_at': datetime.now().isoformat()
        }
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            return True, f"Network config exported to {export_path}"
        except Exception as e:
            return False, f"Export failed: {str(e)}"
