# Multi-stage build for optimized {strategy_name}
FROM messense/rust-musl-cross:x86_64-musl as chef

RUN cargo install cargo-chef
WORKDIR /{base_name}-algo

FROM chef AS planner
# Copy source code
COPY . .
# Generate recipe for dependency caching
RUN cargo chef prepare --recipe-path recipe.json

FROM chef AS builder
COPY --from=planner /{base_name}-algo/recipe.json recipe.json

# Build & cache dependencies
RUN cargo chef cook --release --target x86_64-unknown-linux-musl --recipe-path recipe.json

# Copy source and build application
COPY . .
RUN cargo build --release --target x86_64-unknown-linux-musl

# Runtime stage - minimal image
FROM alpine:latest

# Install CA certificates for HTTPS connections
RUN apk --no-cache add ca-certificates

# Create non-root user for security
RUN addgroup -g 1000 algo && \
    adduser -D -s /bin/sh -u 1000 -G algo algo

# Copy binary from builder stage
COPY --from=builder /{base_name}-algo/target/x86_64-unknown-linux-musl/release/{project_name} /{base_name}-algo

# Change ownership and make executable
RUN chown algo:algo /{base_name}-algo && \
    chmod +x /{base_name}-algo

# Switch to non-root user
USER algo

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD pgrep -x "{base_name}-algo" > /dev/null || exit 1

# Expose port (if needed)
EXPOSE 3000

# Set entrypoint
ENTRYPOINT ["/{base_name}-algo"]

# Labels for better image management
LABEL maintainer="AI Trading Agent"
LABEL description="{strategy_description}"
LABEL version="1.0.0"
LABEL strategy="{strategy_name}"