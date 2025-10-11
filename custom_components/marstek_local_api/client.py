"""Marstek UDP client for battery communication."""
from __future__ import annotations

import asyncio
import json
import logging
import random
import socket
from typing import Any

from .const import UDP_TIMEOUT, MAX_RETRIES, METHOD_BAT_STATUS, METHOD_ES_STATUS

_LOGGER = logging.getLogger(__name__)

class MarstekDevice:
    """Represents a Marstek battery device."""
    
    def __init__(self, name: str, ip_address: str, destination_port: int) -> None:
        """Initialize the device."""
        self.name = name
        self.ip_address = ip_address
        self.destination_port = destination_port
        self.identifier: str | None = None
        self._pending_requests: dict[int, asyncio.Future] = {}
    
    def __str__(self) -> str:
        """Return string representation."""
        return f"MarstekDevice({self.name}@{self.ip_address}:{self.destination_port})"


class MarstekUDPClient:
    """UDP client for Marstek battery communication."""
    
    def __init__(self, source_port: int) -> None:
        """Initialize the UDP client."""
        self.source_port = source_port
        self._socket: socket.socket | None = None
        self._transport: asyncio.DatagramTransport | None = None
        self._protocol: MarstekUDPProtocol | None = None
        self._devices: list[MarstekDevice] = []
        self._pending_requests: dict[int, tuple[MarstekDevice, asyncio.Future]] = {}
        self._last_request_id: int = 0
        self._id_lock = asyncio.Lock()
    
    async def start(self) -> None:
        """Start the UDP client."""
        try:
            loop = asyncio.get_event_loop()
            
            # Create the datagram endpoint
            self._transport, self._protocol = await loop.create_datagram_endpoint(
                lambda: MarstekUDPProtocol(self._handle_response),
                local_addr=("0.0.0.0", self.source_port)
            )
            
            _LOGGER.info("UDP client started on port %s", self.source_port)
            
        except Exception as e:
            _LOGGER.error("Failed to start UDP client: %s", e)
            raise
    
    async def stop(self) -> None:
        """Stop the UDP client."""
        if self._transport:
            self._transport.close()
            self._transport = None
        
        # Cancel all pending requests
        for request_id, (device, future) in self._pending_requests.items():
            if not future.done():
                future.cancel()
        
        self._pending_requests.clear()
        _LOGGER.info("UDP client stopped")
    
    def add_device(self, name: str, ip_address: str, destination_port: int) -> MarstekDevice:
        """Add a device to monitor."""
        device = MarstekDevice(name, ip_address, destination_port)
        self._devices.append(device)
        _LOGGER.info("Added device: %s", device)
        return device
    
    async def _get_next_request_id(self) -> int:
        """Get the next unique request ID with thread safety."""
        async with self._id_lock:
            self._last_request_id += 1
            # Keep within smallint range (1-32767)
            if self._last_request_id > 32767:
                self._last_request_id = 1
            return self._last_request_id
    
    async def get_battery_status(self, device: MarstekDevice) -> dict[str, Any] | None:
        """Get battery status from a device."""
        return await self._send_request(device, METHOD_BAT_STATUS)
    
    async def get_energy_system_status(self, device: MarstekDevice) -> dict[str, Any] | None:
        """Get energy system status from a device."""
        return await self._send_request(device, METHOD_ES_STATUS)
    
    async def _send_request(
        self, device: MarstekDevice, method: str, retries: int = 0
    ) -> dict[str, Any] | None:
        """Send a request to a device."""
        if not self._transport or not self._protocol:
            _LOGGER.error("UDP client not started")
            return None
        
        # Create unique request ID
        request_id = await self._get_next_request_id()
        
        # Build JSON-RPC request
        request = {
            "id": request_id,
            "method": method,
            "params": {"id": request_id}
        }
        
        try:
            # Create future for response tracking
            future: asyncio.Future[dict[str, Any]] = asyncio.Future()
            self._pending_requests[request_id] = (device, future)
            
            # Send JSON-RPC request via UDP
            message = json.dumps(request, separators=(',', ':')).encode('utf-8')
            self._transport.sendto(message, (device.ip_address, device.destination_port))
            
            # Wait for response with timeout and retry logic
            try:
                response = await asyncio.wait_for(future, timeout=UDP_TIMEOUT)
                return response
                
            except asyncio.TimeoutError:
                _LOGGER.warning("Timeout waiting for response from %s", device)
                if retries < MAX_RETRIES:
                    _LOGGER.info("Retrying request to %s (attempt %d/%d)", device, retries + 1, MAX_RETRIES)
                    return await self._send_request(device, method, retries + 1)
                return None
                
        except Exception as e:
            _LOGGER.error("Error sending request to %s: %s", device, e)
            return None
            
        finally:
            # Clean up pending request tracking
            self._pending_requests.pop(request_id, None)
    
    def _handle_response(self, data: bytes, addr: tuple[str, int]) -> None:
        """Handle incoming UDP response."""
        try:
            response = json.loads(data.decode('utf-8'))
            
            request_id = response.get("id")
            
            if request_id is None:
                _LOGGER.warning("Received response without ID from %s", addr)
                return
            
            if request_id not in self._pending_requests:
                _LOGGER.warning("Received response for unknown request ID %s from %s", request_id, addr)
                return
            
            device, future = self._pending_requests[request_id]
            
            # Store device identifier if received
            if "src" in response and device.identifier is None:
                device.identifier = response["src"]
                _LOGGER.info("Device %s identified as %s", device, device.identifier)
            
            # Complete the response future
            if not future.done():
                future.set_result(response)
                
        except json.JSONDecodeError as e:
            # For JSON decode errors, show the raw data since it's malformed
            raw_data = data.decode('utf-8', errors='replace')
            _LOGGER.error("Failed to decode JSON response from %s: %s. Raw data: %s", addr, e, raw_data)
        except Exception as e:
            _LOGGER.error("Error handling response from %s: %s", addr, e)


class MarstekUDPProtocol(asyncio.DatagramProtocol):
    """UDP protocol for Marstek communication."""
    
    def __init__(self, response_handler) -> None:
        """Initialize the protocol."""
        self.response_handler = response_handler
    
    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        """Handle received datagram."""
        self.response_handler(data, addr)
    
    def error_received(self, exc: Exception) -> None:
        """Handle error."""
        _LOGGER.error("UDP protocol error: %s", exc)