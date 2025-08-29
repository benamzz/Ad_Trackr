FROM python:3.9-slim

WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    openjdk-21-jdk-headless \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Configurer JAVA_HOME (compatible ARM64 et AMD64)
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-*
ENV PATH=$PATH:$JAVA_HOME/bin

COPY ./ /app

ENV PYTHONPATH=/app

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Créer un script d'entrée pour le workflow
RUN echo '#!/bin/bash' > /app/entrypoint.sh && \
    echo 'echo "🎬 MyFlow Container Ready"' >> /app/entrypoint.sh && \
    echo 'echo "Available commands:"' >> /app/entrypoint.sh && \
    echo 'echo "  python examples/youtube_ingestion_workflow.py"' >> /app/entrypoint.sh && \
    echo 'echo "  python run_etl_spark.py"' >> /app/entrypoint.sh && \
    echo 'echo "  python youtube_extractor_to_mongo.py"' >> /app/entrypoint.sh && \
    echo 'echo ""' >> /app/entrypoint.sh && \
    echo 'exec "$@"' >> /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["tail", "-f", "/dev/null"]
