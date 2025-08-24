"""Technical indicators tools for the Finance Agent."""

import re
import logging
from typing import List, Dict, Optional
from langchain.tools import tool
from .technical_indicators_client import TechnicalIndicatorsClient

logger = logging.getLogger(__name__)

# Initialize the client
client = TechnicalIndicatorsClient()


@tool
def get_mfi_analysis(symbol: str, period: str = "1y") -> str:
    """
    Get detailed Money Flow Index (MFI) analysis for a stock or cryptocurrency symbol.
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL', 'MSFT', 'BTC-USD')
        period: Time period - '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'
    
    Returns:
        Detailed MFI analysis with trading signals and recommendations
    """
    try:
        if not client.health_check():
            return "❌ Technical indicators service is not available. Please ensure the technical-indicators-finder API is running on localhost:8000."
        
        # Get comprehensive MFI data
        data = client.get_mfi_data(symbol, period=period)
        if not data:
            return f"❌ Could not fetch MFI data for {symbol.upper()}. Symbol may not exist or data may be unavailable."
        
        # Get current signal
        signal_data = client.get_current_signal(symbol)
        if not signal_data:
            return f"❌ Could not generate trading signal for {symbol.upper()}."
        
        # Build detailed analysis
        analysis = []
        analysis.append(f"📊 **MFI Analysis for {symbol.upper()}**")
        analysis.append(f"💰 Current Price: ${signal_data['price']:.2f}")
        analysis.append(f"📈 MFI Value: {signal_data['mfi_value']:.1f}")
        analysis.append(f"🎯 Signal: {signal_data['signal']} ({signal_data['strength']})")
        analysis.append("")
        
        # Add interpretation
        mfi_value = signal_data['mfi_value']
        if mfi_value <= 20:
            analysis.append("🔵 **Oversold Condition**: The asset may be undervalued and could present a buying opportunity.")
            analysis.append("⚡ Consider: Dollar-cost averaging into position if fundamentals support the investment.")
        elif mfi_value >= 80:
            analysis.append("🔴 **Overbought Condition**: The asset may be overvalued and could face selling pressure.")
            analysis.append("⚡ Consider: Taking profits or reducing position size if holding.")
        else:
            analysis.append("🟡 **Normal Range**: MFI indicates balanced buying and selling pressure.")
            analysis.append("⚡ Consider: Wait for clearer signals or focus on other technical indicators.")
        
        analysis.append("")
        analysis.append(f"📅 Analysis Period: {period}")
        analysis.append(f"🔢 Data Points: {data.get('data_points', 'N/A')}")
        
        # Add trend analysis if enough data
        time_series = data.get('time_series', [])
        if len(time_series) >= 5:
            recent_mfi = [point['mfi_value'] for point in time_series[-5:]]
            if len(recent_mfi) >= 2:
                trend = "📈 Rising" if recent_mfi[-1] > recent_mfi[0] else "📉 Falling"
                analysis.append(f"📊 5-Day MFI Trend: {trend}")
        
        return "\n".join(analysis)
        
    except Exception as e:
        logger.error(f"Error in MFI analysis: {e}")
        return f"❌ Error analyzing {symbol}: {str(e)}"


@tool
def validate_stock_symbol(symbol: str) -> str:
    """
    Validate if a stock or cryptocurrency symbol is available for analysis.
    
    Args:
        symbol: Stock symbol to validate (e.g., 'AAPL', 'MSFT', 'BTC-USD')
    
    Returns:
        Validation result with symbol information
    """
    try:
        if not client.health_check():
            return "❌ Technical indicators service is not available."
        
        is_valid = client.validate_symbol(symbol)
        
        if is_valid:
            return f"✅ {symbol.upper()} is a valid symbol and data is available for analysis."
        else:
            return f"❌ {symbol.upper()} is not a valid symbol or data is not available. Please check the symbol spelling."
    
    except Exception as e:
        logger.error(f"Error validating symbol {symbol}: {e}")
        return f"❌ Error validating {symbol}: {str(e)}"


@tool
def get_technical_indicators(symbols: str, signal_type: str = "BUY") -> str:
    """
    Screen multiple symbols for trading opportunities based on MFI signals.
    
    Args:
        symbols: Comma-separated list of symbols (e.g., 'AAPL,MSFT,GOOGL')
        signal_type: Type of signal to look for - 'BUY', 'SELL', or 'HOLD'
    
    Returns:
        List of symbols matching the signal criteria with analysis
    """
    try:
        if not client.health_check():
            return "❌ Technical indicators service is not available."
        
        # Parse symbols
        symbol_list = [s.strip().upper() for s in symbols.split(',')]
        if len(symbol_list) > 10:
            return "❌ Maximum 10 symbols allowed for screening."
        
        results = client.screen_symbols(symbol_list, signal_type.upper())
        
        if not results:
            return f"📊 No symbols found with {signal_type} signals among: {', '.join(symbol_list)}"
        
        analysis = []
        analysis.append(f"📊 **{signal_type} Signal Screening Results**")
        analysis.append("")
        
        for result in results:
            symbol = result['symbol']
            mfi = result['mfi_value']
            price = result['price']
            strength = result['strength']
            
            analysis.append(f"🎯 **{symbol}** - ${price:.2f}")
            analysis.append(f"   📈 MFI: {mfi:.1f} | Signal: {signal_type} ({strength})")
            
            # Add quick interpretation
            if signal_type == "BUY" and mfi <= 10:
                analysis.append("   🔥 Strong oversold condition - high conviction buy signal")
            elif signal_type == "SELL" and mfi >= 90:
                analysis.append("   🔥 Strong overbought condition - high conviction sell signal")
            
            analysis.append("")
        
        return "\n".join(analysis)
        
    except Exception as e:
        logger.error(f"Error in technical screening: {e}")
        return f"❌ Error screening symbols: {str(e)}"


def extract_symbols_from_text(text: str) -> List[str]:
    """Extract stock symbols from text using regex patterns."""
    # Common stock symbol patterns
    symbol_pattern = r'\b([A-Z]{1,5}(?:-[A-Z]{1,3})?)\b'
    potential_symbols = re.findall(symbol_pattern, text.upper())
    
    # Filter out common English words that might match the pattern
    common_words = {
        'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 
        'WAS', 'ONE', 'OUR', 'OUT', 'DAY', 'GET', 'HAS', 'HIM', 'HIS', 'HOW',
        'NEW', 'NOW', 'OLD', 'SEE', 'TWO', 'WHO', 'BOY', 'DID', 'ITS', 'LET',
        'PUT', 'SAY', 'SHE', 'TOO', 'USE', 'USD', 'API', 'URL', 'HTTP', 'JSON'
    }
    
    symbols = [s for s in potential_symbols if s not in common_words and len(s) >= 2]
    return list(set(symbols))  # Remove duplicates


def build_indicators_context(symbols: List[str]) -> str:
    """Build technical indicators context for multiple symbols."""
    if not client.health_check():
        return "\nNote: Technical indicators service is currently unavailable."
    
    if not symbols:
        return ""
    
    context_parts = []
    context_parts.append("\n**📊 Technical Analysis:**")
    
    for symbol in symbols[:3]:  # Limit to 3 symbols for context
        try:
            signal_data = client.get_current_signal(symbol)
            if signal_data:
                context_parts.append(f"\n**{symbol}** (${signal_data['price']:.2f}):")
                context_parts.append(f"- MFI: {signal_data['mfi_value']:.1f}")
                context_parts.append(f"- Signal: {signal_data['signal']} ({signal_data['strength']})")
                
                # Add interpretation
                mfi = signal_data['mfi_value']
                if mfi >= 80:
                    context_parts.append(f"- Status: Potentially overbought")
                elif mfi <= 20:
                    context_parts.append(f"- Status: Potentially oversold")
                else:
                    context_parts.append(f"- Status: Normal trading range")
            else:
                context_parts.append(f"\n**{symbol}**: No data available")
        except Exception as e:
            logger.error(f"Error building context for {symbol}: {e}")
            continue
    
    return "".join(context_parts) if context_parts else ""