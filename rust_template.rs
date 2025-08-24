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
const SIGNAL_OUTPUT_PORT: u16 = 9999;              // Port to stream signals on
const SIGNAL_OUTPUT_BIND_IP: &str = "0.0.0.0";     // IP to bind signal output to

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

// Subscription request structure (matches market-streamer)
#[derive(Debug, Serialize)]
pub struct SubscriptionRequest {{
    pub action: String,  // "start" or "stop"
    pub symbol: String,
}}

// Market data structure from UDP feed - matches market-streamer output
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
        
        println!("📊 {{}}: ${{:.4}} | Vol: {{:.2}} | Bid: ${{:.4}} | Ask: ${{:.4}}", 
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

// UDP client that subscribes to market-streamer
pub struct UdpMarketDataConsumer {{
    socket: UdpSocket,
    strategy: Arc<Mutex<{strategy_class_name}>>,
    server_addr: SocketAddr,
    subscribed_symbols: Vec<String>,
}}

impl UdpMarketDataConsumer {{
    pub fn new_with_config(
        strategy: {strategy_class_name},
        streaming_ip: &str,
        streaming_port: u16,
    ) -> Result<Self, Box<dyn std::error::Error>> {{
        let socket = UdpSocket::bind("0.0.0.0:0")?;
        let local_addr = socket.local_addr()?;
        
        println!("✓ Client socket bound to: {{}}", local_addr);
        
        let mut server_addrs = format!("{{}}:{{}}", streaming_ip, streaming_port).to_socket_addrs()?;
        let server_addr = server_addrs.next().ok_or("Failed to resolve server address")?;

        println!("✓ Streaming server address: {{}}", server_addr);
        
        socket.set_read_timeout(Some(Duration::from_millis(1000)))?;
        
        Ok(Self {{
            socket,
            strategy: Arc::new(Mutex::new(strategy)),
            server_addr,
            subscribed_symbols: Vec::new(),
        }})
    }}

    pub fn subscribe(&mut self, symbol: &str) -> Result<(), Box<dyn std::error::Error>> {{
        let request = SubscriptionRequest {{
            action: "start".to_string(),
            symbol: symbol.to_uppercase(),
        }};
        
        let json_data = serde_json::to_string(&request)?;
        
        match self.socket.send_to(json_data.as_bytes(), &self.server_addr) {{
            Ok(_) => {{
                println!("✓ Subscribed to {{}}", symbol.to_uppercase());
                if !self.subscribed_symbols.contains(&symbol.to_uppercase()) {{
                    self.subscribed_symbols.push(symbol.to_uppercase());
                }}
                Ok(())
            }}
            Err(e) => {{
                println!("❌ Failed to subscribe to {{}}: {{}}", symbol, e);
                Err(Box::new(e))
            }}
        }}
    }}

    pub fn start_consuming(&mut self) -> Result<(), Box<dyn std::error::Error>> {{
        println!("🚀 Starting UDP consumption loop...");
        println!("📡 Listening for data from server: {{}}", self.server_addr);
        
        let mut buffer = [0u8; 4096];
        
        loop {{
            match self.socket.recv_from(&mut buffer) {{
                Ok((size, addr)) => {{
                    let data_str = String::from_utf8_lossy(&buffer[..size]);
                    
                    match serde_json::from_str::<MarketData>(&data_str) {{
                        Ok(market_data) => {{
                            if let Ok(mut strategy) = self.strategy.lock() {{
                                strategy.process_market_data(market_data);
                            }}
                        }}
                        Err(e) => {{
                            println!("❌ Failed to parse market data: {{}}", e);
                        }}
                    }}
                }}
                Err(ref e) if e.kind() == std::io::ErrorKind::WouldBlock || e.kind() == std::io::ErrorKind::TimedOut => {{
                    continue;
                }}
                Err(e) => {{
                    eprintln!("❌ UDP receive error: {{}}", e);
                    thread::sleep(Duration::from_millis(100));
                }}
            }}
        }}
    }}

    pub fn shutdown(&mut self) -> Result<(), Box<dyn std::error::Error>> {{
        println!("🛑 Shutting down client...");
        
        for symbol in self.subscribed_symbols.clone() {{
            let request = SubscriptionRequest {{
                action: "stop".to_string(),
                symbol: symbol.clone(),
            }};
            
            let json_data = serde_json::to_string(&request)?;
            let _ = self.socket.send_to(json_data.as_bytes(), &self.server_addr);
        }}
        
        Ok(())
    }}
}}

// UDP Signal Broadcaster - sends signals to trade-simulator
pub struct UdpSignalBroadcaster {{
    socket: Arc<UdpSocket>,
    clients: Arc<Mutex<Vec<SocketAddr>>>,
}}

impl UdpSignalBroadcaster {{
    pub fn new() -> Result<Self, Box<dyn std::error::Error>> {{
        let bind_addr = format!("{{}}:{{}}", SIGNAL_OUTPUT_BIND_IP, SIGNAL_OUTPUT_PORT);
        let socket = UdpSocket::bind(&bind_addr)?;
        
        println!("🎯 Signal UDP broadcaster bound to: {{}}", bind_addr);
        
        socket.set_nonblocking(true)?;
        
        Ok(Self {{
            socket: Arc::new(socket),
            clients: Arc::new(Mutex::new(Vec::new())),
        }})
    }}
    
    pub fn start_client_listener(&self) -> Result<(), Box<dyn std::error::Error>> {{
        let socket_clone = self.socket.clone();
        let clients_clone = self.clients.clone();
        
        thread::spawn(move || {{
            let mut buffer = [0u8; 1024];
            
            loop {{
                match socket_clone.recv_from(&mut buffer) {{
                    Ok((size, addr)) => {{
                        let message = String::from_utf8_lossy(&buffer[..size]);
                        println!("📞 Client registration from {{}}: {{}}", addr, message.trim());
                        
                        if let Ok(mut clients) = clients_clone.lock() {{
                            if !clients.contains(&addr) {{
                                clients.push(addr);
                                println!("✅ Added client: {{}} (total: {{}})", addr, clients.len());
                                
                                let ack = "CONNECTED";
                                let _ = socket_clone.send_to(ack.as_bytes(), addr);
                            }}
                        }}
                    }}
                    Err(ref e) if e.kind() == std::io::ErrorKind::WouldBlock => {{
                        thread::sleep(Duration::from_millis(10));
                        continue;
                    }}
                    Err(e) => {{
                        eprintln!("❌ Client listener error: {{}}", e);
                        thread::sleep(Duration::from_millis(100));
                    }}
                }}
            }}
        }});
        
        Ok(())
    }}
    
    pub fn broadcast_signal(&self, signal: &Signal) -> Result<(), Box<dyn std::error::Error>> {{
        let json_signal = serde_json::to_string(signal)?;
        
        if let Ok(mut clients) = self.clients.lock() {{
            if clients.is_empty() {{
                println!("🚨 SIGNAL (no UDP clients): {{}}", json_signal);
                return Ok(());
            }}
            
            println!("📡 Broadcasting signal to {{}} clients: {{}}", clients.len(), json_signal);
            
            let mut failed_clients = Vec::new();
            
            for &client_addr in clients.iter() {{
                match self.socket.send_to(json_signal.as_bytes(), client_addr) {{
                    Ok(_) => {{}}
                    Err(e) => {{
                        println!("❌ Failed to send to {{}}: {{}}", client_addr, e);
                        failed_clients.push(client_addr);
                    }}
                }}
            }}
            
            for failed_addr in failed_clients {{
                clients.retain(|&addr| addr != failed_addr);
            }}
        }}
        
        Ok(())
    }}
}}

// Signal output handler with UDP broadcasting
pub struct SignalOutput {{
    receiver: crossbeam_channel::Receiver<Signal>,
    udp_broadcaster: UdpSignalBroadcaster,
}}

impl SignalOutput {{
    pub fn new(receiver: crossbeam_channel::Receiver<Signal>) -> Result<Self, Box<dyn std::error::Error>> {{
        let udp_broadcaster = UdpSignalBroadcaster::new()?;
        
        Ok(Self {{ 
            receiver,
            udp_broadcaster,
        }})
    }}

    pub fn start_output_stream(&self) -> Result<(), Box<dyn std::error::Error>> {{
        self.udp_broadcaster.start_client_listener()?;
        
        let receiver = self.receiver.clone();
        let socket = self.udp_broadcaster.socket.clone();
        let clients = self.udp_broadcaster.clients.clone();
        
        thread::spawn(move || {{
            loop {{
                match receiver.recv() {{
                    Ok(signal) => {{
                        match serde_json::to_string(&signal) {{
                            Ok(json_signal) => {{
                                if let Ok(mut client_list) = clients.lock() {{
                                    if client_list.is_empty() {{
                                        println!("🚨 SIGNAL (no UDP clients): {{}}", json_signal);
                                    }} else {{
                                        let mut failed_clients = Vec::new();
                                        
                                        for &client_addr in client_list.iter() {{
                                            match socket.send_to(json_signal.as_bytes(), client_addr) {{
                                                Ok(_) => {{}}
                                                Err(_) => {{
                                                    failed_clients.push(client_addr);
                                                }}
                                            }}
                                        }}
                                        
                                        for failed_addr in failed_clients {{
                                            client_list.retain(|&addr| addr != failed_addr);
                                        }}
                                    }}
                                }}
                            }}
                            Err(e) => {{
                                eprintln!("❌ Failed to serialize signal: {{}}", e);
                            }}
                        }}
                    }}
                    Err(_) => {{
                        break;
                    }}
                }}
            }}
        }});
        
        Ok(())
    }}
}}

// Configuration structure for environment variables
#[derive(Debug)]
struct AppConfig {{
    streaming_source_ip: String,
    streaming_source_port: u16,
}}

impl AppConfig {{
    fn from_env() -> Result<Self, Box<dyn std::error::Error>> {{
        let streaming_source_ip = env::var("STREAMING_SOURCE_IP")
            .unwrap_or_else(|_| "127.0.0.1".to_string());
        
        let streaming_source_port: u16 = env::var("STREAMING_SOURCE_PORT")
            .unwrap_or_else(|_| "8888".to_string())
            .parse()
            .map_err(|e| format!("Invalid STREAMING_SOURCE_PORT: {{}}", e))?;
        
        Ok(Self {{
            streaming_source_ip,
            streaming_source_port,
        }})
    }}
}}

// Main application
fn main() -> Result<(), Box<dyn std::error::Error>> {{
    let config = AppConfig::from_env()?;
    
    println!("🎯 Starting {strategy_name}...");
    println!("🌐 Remote streaming server: {{}}:{{}}", config.streaming_source_ip, config.streaming_source_port);
    println!("📡 Signal UDP output: {{}}:{{}}", SIGNAL_OUTPUT_BIND_IP, SIGNAL_OUTPUT_PORT);
    
    let strategy_config = StrategyConfig::from_env()?;
    let (strategy, signal_receiver) = {strategy_class_name}::new(strategy_config.clone());
    
    let mut consumer = UdpMarketDataConsumer::new_with_config(
        strategy, 
        &config.streaming_source_ip, 
        config.streaming_source_port
    )?;
    
    let signal_output = SignalOutput::new(signal_receiver)?;
    signal_output.start_output_stream()?;
    
    let symbols = ["BTC", "ETH", "ADA", "SOL"];
    for symbol in &symbols {{
        consumer.subscribe(symbol)?;
        thread::sleep(Duration::from_millis(100));
    }}
    
    println!("✅ {strategy_name} initialized successfully!");
    println!("📡 Listening for data from {{}} symbols...", symbols.len());
    println!("🎯 Broadcasting signals via UDP on port {{}}", SIGNAL_OUTPUT_PORT);
    println!("Press Ctrl+C to stop");
    
    let consumer = Arc::new(Mutex::new(consumer));
    let consumer_clone = consumer.clone();
    
    ctrlc::set_handler(move || {{
        println!("\n👋 Received Ctrl+C, shutting down...");
        if let Ok(mut consumer) = consumer_clone.lock() {{
            let _ = consumer.shutdown();
        }}
        std::process::exit(0);
    }})?;
    
    if let Ok(mut consumer) = consumer.lock() {{
        consumer.start_consuming()?;
    }}
    
    Ok(())
}}