# Airflow with Spark superpowers:
#  - a headless JRE + pyspark, so spark-submit exists inside the container
#  - the Spark provider, so SparkSubmitOperator works out of the box
FROM apache/airflow:2.9.2-python3.11

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends default-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# JAVA_HOME for spark-submit (Debian bookworm JRE path)
ENV JAVA_HOME=/usr/lib/jvm/default-java

USER airflow
RUN pip install --no-cache-dir \
    pyspark==3.5.1 \
    apache-airflow-providers-apache-spark==4.8.1
