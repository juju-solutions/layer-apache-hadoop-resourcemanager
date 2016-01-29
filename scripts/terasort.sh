#!/bin/bash

# Number of mappers and reducers (set to number of slaves in the cluster)
NUM_MAPS=3
NUM_REDS=3

# Number of 100 byte rows, default to 100MB of data to generate and sort
SIZE=1000000

# Location of input/output, relative to the script runner's HDFS dir (defaults to /user/`whoami`)
IN_DIR=tera_demo_in
OUT_DIR=tera_demo_out

# Args to pass to teragen/terasort
TERA_ARGS="-Dmapreduce.map.output.compress=true -Dmapreduce.map.output.compress.codec=org.apache.hadoop.io.compress.SnappyCodec -Dmapreduce.output.fileoutputformat.compress=true -Dmapreduce.output.fileoutputformat.compress.codec=org.apache.hadoop.io.compress.SnappyCodec -Dmapreduce.job.maps=${NUM_MAPS} -Dmapreduce.job.reduces=${NUM_REDS}"

# Clean out previous runs
hadoop fs -rm -f -R -skipTrash ${IN_DIR} || true
hadoop fs -rm -f -R -skipTrash ${OUT_DIR} || true

hadoop jar $HADOOP_HOME/share/hadoop/mapreduce/hadoop-mapreduce-examples*.jar teragen ${TERA_ARGS} ${SIZE} ${IN_DIR}

sleep 20

hadoop jar $HADOOP_HOME/share/hadoop/mapreduce/hadoop-mapreduce-examples*.jar terasort ${TERA_ARGS} ${IN_DIR} ${OUT_DIR}

