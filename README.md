# Trade Agent

An AI-powered tool for generating Rust cryptocurrency trading algorithms with RAG (Retrieval-Augmented Generation) capabilities and Docker containerization support. Part of the AW-Trade algorithmic trading system.

## Features

- **AI-Powered Algorithm Generation**: Generate complete Rust cryptocurrency trading algorithms from natural language descriptions
- **RAG Knowledge Base**: Search and expand a knowledge base of trading strategies and concepts using ChromaDB
- **Docker Integration**: Automatically containerize generated algorithms for easy deployment
- **Interactive CLI**: Terminal-based chat interface for seamless interaction
- **Template System**: Flexible templating engine with intelligent default value generation
- **Integration Ready**: Designed to work with the broader AW-Trade microservices ecosystem

## Prerequisites

- Python 3.8+
- Google AI API key (Gemini)
- Rust (for local algorithm development)
- Docker (for containerization)

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

## Usage

### Start the Interactive CLI

```bash
python main.py
```

The CLI provides an interactive chat interface where you can:

- Generate crypto trading algorithms
- Search the knowledge base for trading strategies
- Add new information to the knowledge base
- Ask general finance and crypto questions

### Example Interactions

```bash
You: Generate a RSI momentum trading algorithm for Bitcoin

You: Search for information about order book imbalance strategies

You: Add information about Bollinger Bands to the knowledge base

You: Create a mean reversion strategy with 20-period moving average
```

### CLI Commands

- `exit` - Quit the application
- `history` - Display chat history
- Regular messages - Process queries through the AI agent

## Architecture

### Core Components

- **`finance_agent.py`** - Main LangChain-based AI agent with tool integration
- **`cli.py`** - Terminal-based chat interface
- **`trading_tools.py`** - Rust algorithm generation and Docker build tools
- **`rag_tools.py`** - ChromaDB integration for knowledge base operations
- **`project_generator.py`** - Template management and project generation
- **`rust_template.rs`** - Base Rust template for generated algorithms

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