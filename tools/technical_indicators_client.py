"""Technical Indicators Client for connecting to the technical-indicators-finder API."""

import requests
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class TechnicalIndicatorsClient:
    """Client for interacting with the technical-indicators-finder API."""
    
    def __init__(self, base_url: str = "http://localhost:8005"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def health_check(self) -> bool:
        """Check if the technical indicators service is running"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def get_mfi_data(
        self, 
        symbol: str, 
        period: str = "1y", 
        interval: str = "1d", 
        mfi_period: int = 14
    ) -> Optional[Dict[str, Any]]:
        """
        Get Money Flow Index data for a symbol
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            period: Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            interval: Data interval ('1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo')
            mfi_period: MFI calculation period (1-50)
        
        Returns:
            MFI response data or None if error
        """
        try:
            params = {
                "symbol": symbol.upper(),
                "period": period,
                "interval": interval,
                "mfi_period": mfi_period
            }
            
            response = self.session.get(f"{self.base_url}/indicators/mfi", params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 400:
                logger.error(f"Invalid symbol or parameters: {response.json()}")
                return None
            elif response.status_code == 404:
                logger.error(f"No data found for symbol {symbol}: {response.json()}")
                return None
            elif response.status_code == 422:
                logger.error(f"Insufficient data to calculate MFI: {response.json()}")
                return None
            else:
                logger.error(f"API error {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.ConnectionError:
            logger.error(f"Unable to connect to indicators service at {self.base_url}")
            return None
        except requests.exceptions.Timeout:
            logger.error(f"Timeout connecting to indicators service at {self.base_url}")
            return None
        except Exception as e:
            logger.error(f"Error fetching MFI data for {symbol}: {e}")
            return None
    
    def get_latest_mfi_value(self, symbol: str, period: str = "1mo") -> Optional[float]:
        """Get just the latest MFI value for quick checks"""
        data = self.get_mfi_data(symbol, period=period)
        if data and data.get("time_series"):
            return data["time_series"][-1]["mfi_value"]
        return None
    
    def get_current_signal(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current trading signal based on MFI"""
        data = self.get_mfi_data(symbol, period="3mo")
        if not data or not data.get("time_series"):
            return None
            
        latest = data["time_series"][-1]
        mfi = latest["mfi_value"]
        
        # Basic signal logic based on common MFI thresholds
        if mfi <= 20:
            signal = "BUY"
            strength = "STRONG" if mfi <= 10 else "MODERATE"
        elif mfi >= 80:
            signal = "SELL" 
            strength = "STRONG" if mfi >= 90 else "MODERATE"
        else:
            signal = "HOLD"
            strength = "WEAK"
        
        return {
            "symbol": symbol.upper(),
            "signal": signal,
            "strength": strength,
            "mfi_value": mfi,
            "price": latest["close_price"],
            "timestamp": latest["timestamp"]
        }
    
    def screen_symbols(self, symbols: List[str], signal_type: str = "BUY") -> List[Dict[str, Any]]:
        """Screen multiple symbols for specific signals"""
        results = []
        
        for symbol in symbols:
            signal_data = self.get_current_signal(symbol)
            if signal_data and signal_data["signal"] == signal_type:
                results.append(signal_data)
        
        # Sort by MFI value (lowest first for BUY signals, highest for SELL)
        if signal_type == "BUY":
            results.sort(key=lambda x: x["mfi_value"])
        else:
            results.sort(key=lambda x: x["mfi_value"], reverse=True)
            
        return results

    def validate_symbol(self, symbol: str) -> bool:
        """Validate if a symbol exists by attempting to fetch basic data"""
        try:
            data = self.get_mfi_data(symbol, period="5d")
            return data is not None
        except Exception:
            return False