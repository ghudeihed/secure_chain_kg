FROM stain/jena-fuseki:latest

# Switch to root to set permissions
USER root

# Copy configuration and data files
COPY config.ttl /fuseki/config.ttl
COPY shiro.ini /fuseki/shiro.ini
COPY data/ /fuseki/data/

# Copy startup script and set executable permissions
COPY load_data.sh /fuseki/load_data.sh
RUN chmod +x /fuseki/load_data.sh

# Ensure /fuseki/databases directory exists and is writable
RUN mkdir -p /fuseki/databases && \
    chown -R fuseki:fuseki /fuseki/databases && \
    chmod -R 777 /fuseki/databases

# Switch back to fuseki user
USER fuseki

# Create volume for persistent data
VOLUME /fuseki/databases

# Expose the Fuseki port
EXPOSE 3030

# Run the startup script
CMD ["/fuseki/load_data.sh"]
