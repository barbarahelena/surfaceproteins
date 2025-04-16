FROM mambaorg/micromamba:2.0.3-ubuntu24.04

# Install required system dependencies (e.g., procps for Nextflow compatibility)
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends apt-utils procps && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/*

# Switch back to micromamba user
USER $MAMBA_USER

# Copy environment file
COPY --chown=$MAMBA_USER:$MAMBA_USER env.yaml /tmp/env.yaml

# (Optional) Copy local package if it's not available online
COPY --chown=$MAMBA_USER:$MAMBA_USER signalp-6-package/ /tmp/signalp-6-package/

# Install Conda environment and Python dependencies
RUN micromamba install -y -n base -f /tmp/env.yaml && \
    micromamba clean --all --yes

# Install the package if it's copied
RUN [ -d "/tmp/signalp-6-package" ] && micromamba run -n base pip install /tmp/signalp-6-package/ || echo "Skipping local package installation"

# Find the SignalP installation path and copy model weights
RUN SIGNALP_DIR=$(micromamba run -n base python3 -c "import signalp; import os; print(os.path.dirname(signalp.__file__))") && \
    mkdir -p $SIGNALP_DIR/model_weights && \
    cp -r /tmp/signalp-6-package/models/* $SIGNALP_DIR/model_weights/

# Ensure correct environment activation for Singularity
ENV PATH="$MAMBA_ROOT_PREFIX/bin:$PATH"
