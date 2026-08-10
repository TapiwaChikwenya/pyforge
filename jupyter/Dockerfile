# JupyterLab with Spark (base image) + the database clients and DS/AI libraries
# used across the PyForge curriculum — so notebooks never need manual installs.
FROM quay.io/jupyter/pyspark-notebook:spark-3.5.0

RUN pip install --no-cache-dir \
    psycopg2-binary==2.9.9 \
    pymongo==4.7.3 \
    redis==5.0.6 \
    duckdb==1.0.0 \
    scikit-learn==1.5.1 \
    sqlalchemy==2.0.31

# Postgres JDBC driver so Spark can read/write the warehouse (Lakehouse Lite).
# Dropped into Spark's own jars directory, where it is picked up automatically —
# no PYSPARK_SUBMIT_ARGS to remember, and nothing breaks if it is absent.
# The download is deliberately non-fatal: a blocked or flaky network must not
# fail the whole stack build, since only one project needs this driver.
USER root
RUN wget -q --tries=3 --timeout=20 \
      https://jdbc.postgresql.org/download/postgresql-42.7.3.jar \
      -O "${SPARK_HOME}/jars/postgresql-42.7.3.jar" \
    && chown ${NB_UID}:${NB_GID} "${SPARK_HOME}/jars/postgresql-42.7.3.jar" \
    || { rm -f "${SPARK_HOME}/jars/postgresql-42.7.3.jar"; \
         echo "WARNING: Postgres JDBC driver download failed. Everything works except"; \
         echo "         Spark<->warehouse writes in Lakehouse Lite - see RUNBOOK troubleshooting."; }
USER ${NB_UID}
