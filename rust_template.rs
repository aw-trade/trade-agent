use std::collections::HashMap;
use std::net::{{UdpSocket, SocketAddr, ToSocketAddrs}};
use std::sync::{{Arc, Mutex}};
use std::thread;
use std::time::{{Duration, Instant}};
use serde::{{Deserialize, Serialize}};
use std::env;

// ============================================
// SIGNAL OUTPUT UDP CONFIGURATION
// ============================================
const SIGNAL_OUTPUT_PORT: u16 = 9999;
const SIGNAL_OUTPUT_BIND_IP: &str = "0.0.0.0";

// Configuration for the trading strategy
#[derive(Clone, Debug)]
pub struct StrategyConfig {{
    pub imbalance_threshold: f64,
    pub min_volume_threshold: f64,
    pub lookback_periods: usize,
    pub signal_cooldown_ms: u64,
}}

impl Default for StrategyConfig {{
    fn default() -> Self {{
        Self {{
            imbalance_threshold: {imbalance_threshold},
            min_volume_threshold: {min_volume_threshold},
            lookback_periods: {lookback_periods},
            signal_cooldown_ms: {signal_cooldown_ms},
        }}
    }}
}}

impl StrategyConfig {{
    pub fn from_env() -> Result<Self, Box<dyn std::error::Error>> {{
        let imbalance_threshold = env::var("IMBALANCE_THRESHOLD")
            .map(|s| s.parse::<f64>())
            .unwrap_or(Ok({imbalance_threshold}))?;
        
        let min_volume_threshold = env::var("MIN_VOLUME_THRESHOLD")
            .map(|s| s.parse::<f64>())
            .unwrap_or(Ok({min_volume_threshold}))?;
        
        let lookback_periods = env::var("LOOKBACK_PERIODS")
            .map(|s| s.parse::<usize>())
            .unwrap_or(Ok({lookback_periods}))?;
        
        let signal_cooldown_ms = env::var("SIGNAL_COOLDOWN_MS")
            .map(|s| s.parse::<u64>())
            .unwrap_or(Ok({signal_cooldown_ms}))?;
        
        Ok(Self {{
            imbalance_threshold,
            min_volume_threshold,
            lookback_periods,
            signal_cooldown_ms,
        }})
    }}
}}

// Market data structure from UDP feed
#[derive(Debug, Clone, Deserialize)]
pub struct MarketData {{
    pub symbol: String,
    pub price: f64,
    pub volume: f64,
    pub bid: f64,
    pub ask: f64,
    pub timestamp: u64,
    pub exchange: String,
}}

// Trading signal output
#[derive(Debug, Clone, Serialize)]
#[serde(tag = "type", rename_all = "PascalCase")]
pub enum Signal {{
    Buy {{
        symbol: String,
        timestamp: u64,
        confidence: f64,
        imbalance_ratio: f64,
        mid_price: f64,
    }},
    Sell {{
        symbol: String,
        timestamp: u64,
        confidence: f64,
        imbalance_ratio: f64,
        mid_price: f64,
    }},
}}

// Strategy name: {strategy_name}
// Description: {strategy_description}

// Main strategy implementation
pub struct {strategy_class_name} {{
    config: StrategyConfig,
    metrics_history: HashMap<String, Vec<ImbalanceMetrics>>,
    last_signal_time: HashMap<String, Instant>,
    signal_sender: crossbeam_channel::Sender<Signal>,
}}

// Order book imbalance metrics
#[derive(Debug, Clone)]
struct ImbalanceMetrics {{
    bid_volume: f64,
    ask_volume: f64,
    total_volume: f64,
    imbalance_ratio: f64,
    timestamp: u64,
}}

impl ImbalanceMetrics {{
    fn new(bid: f64, ask: f64, volume: f64, timestamp: u64) -> Self {{
        let spread = ask - bid;
        let mid_price = (bid + ask) / 2.0;
        
        let total_volume = volume;
        let imbalance_ratio = if spread > 0.0 {{
            (bid - mid_price) / (spread / 2.0)
        }} else {{
            0.0
        }};

        Self {{
            bid_volume: volume / 2.0,
            ask_volume: volume / 2.0,
            total_volume,
            imbalance_ratio,
            timestamp,
        }}
    }}
}}

impl {strategy_class_name} {{
    pub fn new(config: StrategyConfig) -> (Self, crossbeam_channel::Receiver<Signal>) {{
        let (tx, rx) = crossbeam_channel::unbounded();
        
        let strategy = Self {{
            config,
            metrics_history: HashMap::new(),
            last_signal_time: HashMap::new(),
            signal_sender: tx,
        }};
        
        (strategy, rx)
    }}

    pub fn process_market_data(&mut self, data: MarketData) {{
        let metrics = ImbalanceMetrics::new(
            data.bid,
            data.ask,
            data.volume,
            data.timestamp,
        );
        
        println!("📊 {{}}: ${{{{:.4}}}} | Vol: {{{{:.2}}}} | Bid: ${{{{:.4}}}} | Ask: ${{{{:.4}}}}", 
                 data.symbol, data.price, data.volume, data.bid, data.ask);
        
        let history = self.metrics_history
            .entry(data.symbol.clone())
            .or_insert_with(Vec::new);
        
        history.push(metrics.clone());
        
        if history.len() > self.config.lookback_periods {{
            history.remove(0);
        }}

        if let Some(signal) = self.evaluate_signal(&data.symbol, &data, &metrics) {{
            if self.should_emit_signal(&data.symbol) {{
                self.last_signal_time.insert(data.symbol.clone(), Instant::now());
                let _ = self.signal_sender.send(signal);
            }}
        }}
    }}

    fn evaluate_signal(&self, symbol: &str, data: &MarketData, current_metrics: &ImbalanceMetrics) -> Option<Signal> {{
        if current_metrics.total_volume < self.config.min_volume_threshold {{
            return None;
        }}

        let history = self.metrics_history.get(symbol)?;
        if history.len() < 2 {{
            return None;
        }}

        let avg_imbalance = history.iter()
            .map(|m| m.imbalance_ratio)
            .sum::<f64>() / history.len() as f64;

        let imbalance_consistency = self.calculate_consistency(history);
        let magnitude_factor = current_metrics.imbalance_ratio.abs();
        let confidence = (imbalance_consistency * magnitude_factor).min(1.0);

        let mid_price = (data.bid + data.ask) / 2.0;

        if avg_imbalance > self.config.imbalance_threshold {{
            Some(Signal::Buy {{
                symbol: symbol.to_string(),
                timestamp: data.timestamp,
                confidence,
                imbalance_ratio: avg_imbalance,
                mid_price,
            }})
        }} else if avg_imbalance < -self.config.imbalance_threshold {{
            Some(Signal::Sell {{
                symbol: symbol.to_string(),
                timestamp: data.timestamp,
                confidence,
                imbalance_ratio: avg_imbalance,
                mid_price,
            }})
        }} else {{
            None
        }}
    }}

    fn calculate_consistency(&self, history: &[ImbalanceMetrics]) -> f64 {{
        if history.len() < 2 {{
            return 0.0;
        }}

        let ratios: Vec<f64> = history.iter().map(|m| m.imbalance_ratio).collect();
        let mean = ratios.iter().sum::<f64>() / ratios.len() as f64;
        
        let variance = ratios.iter()
            .map(|r| (r - mean).powi(2))
            .sum::<f64>() / ratios.len() as f64;
        
        let std_dev = variance.sqrt();
        
        if mean.abs() < f64::EPSILON {{
            return 0.0;
        }}
        
        let cv = std_dev / mean.abs();
        (1.0 / (1.0 + cv)).min(1.0)
    }}

    fn should_emit_signal(&self, symbol: &str) -> bool {{
        if let Some(last_time) = self.last_signal_time.get(symbol) {{
            last_time.elapsed().as_millis() as u64 >= self.config.signal_cooldown_ms
        }} else {{
            true
        }}
    }}
}}

fn main() -> Result<(), Box<dyn std::error::Error>> {{
    println!("🎯 Starting {strategy_name}...");
    
    let strategy_config = StrategyConfig::from_env()?;
    let (strategy, signal_receiver) = {strategy_class_name}::new(strategy_config);
    
    println!("✅ {strategy_name} initialized successfully!");
    println!("📡 Strategy ready for market data...");
    
    Ok(())
}}