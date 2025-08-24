# Trade Agent v2.0

An advanced AI-powered trading assistant with unified capabilities for algorithm generation, technical analysis, knowledge base management, and Docker containerization. Features intelligent query routing and real-time market analysis integration.

## 🚀 New Features in v2.0

- **🧠 Intelligent Query Routing**: LangGraph-based system that automatically detects query types and routes to specialized handlers
- **📊 Technical Analysis Integration**: Real-time MFI (Money Flow Index) analysis with buy/sell signals for stocks and crypto
- **🔗 Unified Agent Architecture**: Single agent handling all capabilities with optimized routing
- **📈 Symbol Extraction & Analysis**: Automatic detection and analysis of stock/crypto symbols in queries
- **⚡ Enhanced Performance**: Context-aware responses with specialized tool selection

## Core Features

- **AI-Powered Algorithm Generation**: Generate complete Rust cryptocurrency trading algorithms from natural language descriptions
- **Technical Analysis**: Real-time MFI analysis, overbought/oversold detection, and trading signals
- **RAG Knowledge Base**: Search and expand a knowledge base of trading strategies and concepts using ChromaDB
- **Docker Integration**: Automatically containerize generated algorithms for easy deployment
- **Interactive CLI**: Enhanced terminal interface with routing controls and technical analysis commands
- **Template System**: Flexible templating engine with intelligent default value generation
- **Multi-Symbol Screening**: Screen multiple stocks/crypto for trading opportunities
- **Integration Ready**: Designed to work with the broader AW-Trade microservices ecosystem

## Prerequisites

- Python 3.8+
- Google AI API key (Gemini)
- Rust (for local algorithm development)
- Docker (for containerization)
- **Technical Indicators Finder Service** (for real-time market analysis)

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd trade-agent
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file in the project root:
   ```bash
   GOOGLE_API_KEY=your_google_ai_api_key_here
   ```

4. **Start Technical Indicators Service** (for technical analysis features):
   ```bash
   # In a separate terminal
   cd ../technical-indicators-finder
   python main.py
   ```
   This service runs on port 8000 and provides real-time MFI analysis.

## Usage

### Start the Interactive CLI

```bash
python main.py
```

The CLI provides an intelligent chat interface with advanced routing capabilities:

**🤖 Algorithm Generation:**
- Generate crypto trading algorithms
- Create Docker containers automatically
- Build complete project structures

**📊 Technical Analysis:**
- Real-time MFI analysis for stocks and crypto
- Overbought/oversold detection
- Multi-symbol screening for trading opportunities

**📚 Knowledge Management:**
- Search the knowledge base for trading strategies
- Add new information to the knowledge base
- Cross-reference patterns and examples

**🧠 Intelligent Routing:**
- Automatic query classification and routing
- Optimized responses based on query type
- Context-aware tool selection

### Example Interactions

```bash
# Algorithm Generation
You: Generate a RSI momentum trading algorithm for Bitcoin with Docker

# Technical Analysis
You: Analyze MFI for AAPL - is it overbought?
You: Screen TSLA,MSFT,GOOGL for buy signals
You: What's the current technical analysis for Bitcoin?

# Knowledge Base
You: Search for information about order book imbalance strategies
You: Add information about Bollinger Bands to the knowledge base

# Mixed Queries (automatically routed)
You: Create a mean reversion strategy based on AAPL's MFI signals
You: Find examples of RSI strategies and generate one for Ethereum
```

### CLI Commands

**Basic Commands:**
- `exit` / `quit` - Exit the application
- `history` - Display chat history
- `clear` - Clear chat history
- `stats` - Show system statistics
- `health` - System health check
- `help` - Show comprehensive help

**Routing Commands (New in v2.0):**
- `routing` - Show routing system status
- `routing toggle` - Enable/disable intelligent routing
- `routing enable` - Enable intelligent routing
- `routing disable` - Disable intelligent routing

## Architecture

### Core Components (v2.0)

**Agent System:**
- **`agents/finance_agent.py`** - Unified agent with intelligent routing (LangGraph + LangChain)
- **`cli/interface.py`** - Enhanced terminal interface with routing controls

**Tools & Services:**
- **`tools/trading_tools.py`** - Rust algorithm generation and Docker build tools
- **`tools/rag_tools.py`** - ChromaDB integration for knowledge base operations
- **`tools/technical_indicators_tool.py`** - MFI analysis and trading signals
- **`tools/technical_indicators_client.py`** - REST client for indicators service

**Configuration & Templates:**
- **`config/settings.py`** - Centralized configuration management
- **`templates/`** - Template system for algorithm generation
- **`rust_template.rs`** - Base Rust template for generated algorithms

**Services Integration:**
- **`services/docker_service.py`** - Docker operations and container management
- **`services/rag_service.py`** - Vector database operations
- **`services/project_service.py`** - Project lifecycle management

### Intelligent Routing System

The v2.0 agent uses LangGraph to implement intelligent query routing:

```
User Query → Preparation → Classification → Specialized Handler → Response
              ↓              ↓                ↓
        Symbol Extraction  Route Detection   Optimized Tools
```

**Route Types:**
- **`algorithm_generation`** - Code generation, Docker operations
- **`technical_analysis`** - MFI analysis, trading signals
- **`rag_search`** - Knowledge base searches
- **`mixed_analysis`** - Combined technical + algorithm/search
- **`general_agent`** - General trading questions

### Integration with AW-Trade

The Trade Agent generates algorithms that integrate seamlessly with the AW-Trade ecosystem:

- **Market Data**: Algorithms consume UDP streams from `market-streamer` (port 8888)
- **Signal Output**: Generated algorithms output signals to `trade-simulator` (port 9999)
- **Configuration**: Environment-based configuration compatible with AW-Trade components
- **Docker Ready**: Generated algorithms include Docker configurations for orchestration

## Generated Algorithm Structure

When you generate an algorithm, the tool creates:

```
generated_algorithms/
└── [algorithm-name]_[timestamp]/
    ├── src/
    │   └── main.rs          # Complete Rust implementation
    ├── Cargo.toml           # Project dependencies and metadata
    ├── Dockerfile           # Multi-stage Docker build
    ├── .dockerignore        # Docker build optimizations
    └── README.md           # Algorithm-specific documentation
```

### Algorithm Features

- **UDP Communication**: Receives market data and sends trading signals
- **Environment Configuration**: Customizable via environment variables
- **Signal Structure**: Compatible with AW-Trade signal format
- **Error Handling**: Robust error handling and logging
- **Docker Optimized**: Alpine-based images with security best practices

## Configuration

### Environment Variables

- `GOOGLE_API_KEY` - Required for AI functionality
- `IMBALANCE_THRESHOLD` - Default: 0.6 (used in generated algorithms)
- `MIN_VOLUME_THRESHOLD` - Default: 10.0
- `LOOKBACK_PERIODS` - Default: 5
- `SIGNAL_COOLDOWN_MS` - Default: 100

### Knowledge Base

The RAG system uses ChromaDB stored in `algorithm_chromadb/` directory. The knowledge base automatically expands as you add information and can be queried for trading concepts, strategies, and technical analysis.

## Development

### Project Structure

```
trade-agent/
├── algorithm_chromadb/     # ChromaDB vector database
├── generated_algorithms/   # Output directory for generated algorithms
├── cli.py                 # Command line interface
├── finance_agent.py       # Main AI agent
├── main.py               # Entry point
├── project_generator.py   # Template management
├── rag_tools.py          # Knowledge base tools
├── trading_tools.py      # Algorithm generation tools
├── rust_template.rs      # Rust code template
├── dockerfile_template.dockerfile  # Docker template
└── requirements.txt      # Python dependencies
```

### Adding New Templates

To add new algorithm templates:

1. Create template files with `{variable}` placeholders
2. Update `project_generator.py` with new template variables
3. Add default values to `TemplateManager.default_values`

### Extending Tools

The agent uses LangChain tools defined in:
- `trading_tools.py` - Algorithm generation and Docker operations
- `rag_tools.py` - Knowledge base search and updates

## Examples

### Generate a Simple RSI Strategy
```
You: Create a RSI trading algorithm with 14-period RSI, buy when oversold below 30, sell when overbought above 70
```

### Search Knowledge Base
```
You: What do you know about momentum trading strategies?
```

### Add Domain Knowledge
```
You: Add information: MACD crossover signals occur when the MACD line crosses above or below the signal line, indicating potential trend changes
```

## Integration with AW-Trade System

Generated algorithms are designed to work within the AW-Trade microservices architecture:

- **Data Source**: Connect to `market-streamer` for real-time Coinbase Pro data
- **Signal Destination**: Send trading signals to `trade-simulator`
- **Orchestration**: Compatible with `orch-api` Docker Compose management
- **Monitoring**: Integrate with Redis pub/sub for real-time statistics

## Contributing

1. Follow existing code style and patterns
2. Test generated algorithms for compatibility with AW-Trade components
3. Update documentation for new features
4. Ensure Docker images build successfully

## License

Part of the AW-Trade algorithmic trading system.