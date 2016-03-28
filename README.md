## Overview

The Apache Hadoop software library is a framework that allows for the
distributed processing of large data sets across clusters of computers
using a simple programming model.

This charm deploys a node running the ResourceManager component of
[Apache Hadoop 2.4.1](http://hadoop.apache.org/docs/r2.4.1/),
which manages the computation resources and job execution for the platform.


## Usage

This charm is intended to be deployed via one of the
[apache bundles](https://jujucharms.com/u/bigdata-charmers/#bundles).
For example:

    juju quickstart apache-analytics-sql

This will deploy the Apache Hadoop platform with Apache Hive available to
perform SQL-like queries against your data.

You can also manually load and run map-reduce jobs:

    juju scp my-job.jar resourcemanager/0:
    juju ssh resourcemanager/0
    hadoop jar my-job.jar


## Status and Smoke Test

The services provide extended status reporting to indicate when they are ready:

    juju status --format=tabular

This is particularly useful when combined with `watch` to track the on-going
progress of the deployment:

    watch -n 0.5 juju status --format=tabular

The message for each unit will provide information about that unit's state.
Once they all indicate that they are ready, you can perform a "smoke test"
to verify that Yarn is working as expected using the built-in `smoke-test`
action:

    juju action do resourcemanager/0 smoke-test

After a few seconds or so, you can check the results of the smoke test:

    juju action status

You will see `status: completed` if the smoke test was successful, or
`status: failed` if it was not.  You can get more information on why it failed
via:

    juju action fetch <action-id>


## Benchmarking

This charm provides several benchmarks to gauge the performance of your
environment.

The easiest way to run the benchmarks on this service is to relate it to the
[Benchmark GUI][].  You will likely also want to relate it to the
[Benchmark Collector][] to have machine-level information collected during the
benchmark, for a more complete picture of how the machine performed.

[Benchmark GUI]: https://jujucharms.com/benchmark-gui/
[Benchmark Collector]: https://jujucharms.com/benchmark-collector/

However, each benchmark is also an action that can be called manually:

        $ juju action do resourcemanager/0 terasort
        Action queued with id: cbd981e8-3400-4c8f-8df1-c39c55a7eae6
        $ juju action fetch --wait 0 cbd981e8-3400-4c8f-8df1-c39c55a7eae6
        results:
          meta:
            composite:
              direction: asc
              units: ms
              value: "206676"
          results:
            raw: '{"Total vcore-seconds taken by all map tasks": "439783", "Spilled Records":
              "30000000", "WRONG_LENGTH": "0", "Reduce output records": "10000000", "HDFS:
              Number of bytes read": "1000001024", "Total vcore-seconds taken by all reduce
              tasks": "50275", "Reduce input groups": "10000000", "Shuffled Maps ": "8", "FILE:
              Number of bytes written": "3128977482", "Input split bytes": "1024", "Total
              time spent by all reduce tasks (ms)": "50275", "FILE: Number of large read operations":
              "0", "Bytes Read": "1000000000", "Virtual memory (bytes) snapshot": "7688794112",
              "Launched map tasks": "8", "GC time elapsed (ms)": "11656", "Bytes Written":
              "1000000000", "FILE: Number of read operations": "0", "HDFS: Number of write
              operations": "2", "Total megabyte-seconds taken by all reduce tasks": "51481600",
              "Combine output records": "0", "HDFS: Number of bytes written": "1000000000",
              "Total time spent by all map tasks (ms)": "439783", "Map output records": "10000000",
              "Physical memory (bytes) snapshot": "2329722880", "FILE: Number of write operations":
              "0", "Launched reduce tasks": "1", "Reduce input records": "10000000", "Total
              megabyte-seconds taken by all map tasks": "450337792", "WRONG_REDUCE": "0",
              "HDFS: Number of read operations": "27", "Reduce shuffle bytes": "1040000048",
              "Map input records": "10000000", "Map output materialized bytes": "1040000048",
              "CPU time spent (ms)": "195020", "Merged Map outputs": "8", "FILE: Number of
              bytes read": "2080000144", "Failed Shuffles": "0", "Total time spent by all
              maps in occupied slots (ms)": "439783", "WRONG_MAP": "0", "BAD_ID": "0", "Rack-local
              map tasks": "2", "IO_ERROR": "0", "Combine input records": "0", "Map output
              bytes": "1020000000", "CONNECTION": "0", "HDFS: Number of large read operations":
              "0", "Total committed heap usage (bytes)": "1755840512", "Data-local map tasks":
              "6", "Total time spent by all reduces in occupied slots (ms)": "50275"}'
        status: completed
        timing:
          completed: 2015-05-28 20:55:50 +0000 UTC
          enqueued: 2015-05-28 20:53:41 +0000 UTC
          started: 2015-05-28 20:53:44 +0000 UTC



## Monitoring

This charm supports monitoring via Ganglia.  To enable monitoring, you must
do **both** of the following (the order does not matter):

 * Add a relation to the [Ganglia charm][] via the `:master` relation
 * Enable the `ganglia_metrics` config option

For example:

    juju add-relation yarn-master ganglia:master
    juju set yarn-master ganglia_metrics=true

Enabling monitoring will issue restart the ResourceManager and all NodeManager
components on all of the related compute-slaves.  Take care to ensure that there
are no running jobs when enabling monitoring.


## Deploying in Network-Restricted Environments

The Apache Hadoop charms can be deployed in environments with limited network
access. To deploy in this environment, you will need a local mirror to serve
the packages and resources required by these charms.


### Mirroring Packages

You can setup a local mirror for apt packages using squid-deb-proxy.
For instructions on configuring juju to use this, see the
[Juju Proxy Documentation](https://juju.ubuntu.com/docs/howto-proxies.html).


### Mirroring Resources

In addition to apt packages, the Apache Hadoop charms require a few binary
resources, which are normally hosted on Launchpad. If access to Launchpad
is not available, the `jujuresources` library makes it easy to create a mirror
of these resources:

    sudo pip install jujuresources
    juju-resources fetch --all /path/to/resources.yaml -d /tmp/resources
    juju-resources serve -d /tmp/resources

This will fetch all of the resources needed by this charm and serve them via a
simple HTTP server. The output from `juju-resources serve` will give you a
URL that you can set as the `resources_mirror` config option for this charm.
Setting this option will cause all resources required by this charm to be
downloaded from the configured URL.

You can fetch the resources for all of the Apache Hadoop charms
(`apache-hadoop-hdfs-master`, `apache-hadoop-yarn-master`,
`apache-hadoop-hdfs-secondary`, `apache-hadoop-plugin`, etc) into a single
directory and serve them all with a single `juju-resources serve` instance.


## Contact Information

- <bigdata@lists.ubuntu.com>


## Hadoop

- [Apache Hadoop](http://hadoop.apache.org/) home page
- [Apache Hadoop bug trackers](http://hadoop.apache.org/issue_tracking.html)
- [Apache Hadoop mailing lists](http://hadoop.apache.org/mailing_lists.html)
- [Apache Hadoop Juju Charm](http://jujucharms.com/?text=hadoop)


[Ganglia charm]: http://jujucharms.com/ganglia/
