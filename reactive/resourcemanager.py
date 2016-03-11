# pylint: disable=unused-argument
from charms.reactive import when, when_not, set_state, remove_state, when_none
from charms.layer.hadoop_base import get_hadoop_base
from charms.reactive.helpers import data_changed
from jujubigdata.handlers import YARN
from jujubigdata import utils
from charmhelpers.core import hookenv, unitdata


@when('hadoop.installed')
@when_not('resourcemanager.configured')
def configure_resourcemanager():
    local_hostname = hookenv.local_unit().replace('/', '-')
    private_address = hookenv.unit_get('private-address')
    ip_addr = utils.resolve_private_address(private_address)
    hadoop = get_hadoop_base()
    yarn = YARN(hadoop)
    yarn.configure_resourcemanager()
    yarn.configure_jobhistory()
    utils.update_kv_hosts({ip_addr: local_hostname})
    set_state('resourcemanager.configured')


@when('resourcemanager.configured')
@when('namenode.joined')
@when_not('nodemanager.joined')
def blockednodemanager(hdfs):
    hookenv.status_set('blocked', 'Waiting for relation to NodeManager')


@when('resourcemanager.configured')
@when('nodemanager.joined')
@when_not('namenode.joined')
def blockedhdfs(hdfs):
    hookenv.status_set('blocked', 'Waiting for relation to HDFS')


@when('resourcemanager.configured')
@when_none('nodemanager.joined', 'namenode.joined')
def blockedboth():
    hookenv.status_set('blocked',
                       'Waiting for relation to NodeManager and HDFS')


@when('resourcemanager.configured')
@when('nodemanager.joined', 'namenode.joined')
@when_not('namenode.ready')
def waitinghdfs(nodemanager, hdfs):
    hookenv.status_set('waiting', 'Waiting for HDFS')


@when('resourcemanager.started', 'nodemanager.joined')
def send_info(nodemanager):
    hadoop = get_hadoop_base()
    yarn = YARN(hadoop)
    local_hostname = hookenv.local_unit().replace('/', '-')
    port = hadoop.dist_config.port('resourcemanager')
    hs_http = hadoop.dist_config.port('jh_webapp_http')
    hs_ipc = hadoop.dist_config.port('jobhistory')

    utils.update_kv_hosts({node['ip']: node['host']
                           for node in nodemanager.nodes()})
    utils.manage_etc_hosts()

    nodemanager.send_spec(hadoop.spec())
    nodemanager.send_resourcemanagers([local_hostname])
    nodemanager.send_ports(port, hs_http, hs_ipc)
    nodemanager.send_ssh_key(utils.get_ssh_key('hdfs'))
    nodemanager.send_hosts_map(utils.get_kv_hosts())

    slaves = [node['host'] for node in nodemanager.nodes()]
    if data_changed('resourcemanager.slaves', slaves):
        unitdata.kv().set('resourcemanager.slaves', slaves)
        yarn.register_slaves(slaves)

    hookenv.status_set('active', 'Ready ({count} NodeManager{s})'.format(
        count=len(slaves),
        s='s' if len(slaves) > 1 else '',
    ))
    set_state('resourcemanager.ready')


@when('resourcemanager.clients', 'resourcemanager.ready')
def accept_clients(clients):
    hadoop = get_hadoop_base()
    local_hostname = hookenv.local_unit().replace('/', '-')
    port = hadoop.dist_config.port('resourcemanager')
    hs_http = hadoop.dist_config.port('jh_webapp_http')
    hs_ipc = hadoop.dist_config.port('jobhistory')

    clients.send_spec(hadoop.spec())
    clients.send_resourcemanagers([local_hostname])
    clients.send_ports(port, hs_http, hs_ipc)
    clients.send_hosts_map(utils.get_kv_hosts())
    clients.send_ready(True)


@when('resourcemanager.clients')
@when_not('resourcemanager.ready')
def reject_clients(clients):
    clients.send_ready(False)


@when('namenode.ready', 'hadoop.hdfs.configured')
@when('resourcemanager.configured')
@when_not('resourcemanager.started')
def configure_hdfs(hdfs_rel):
    hadoop = get_hadoop_base()
    yarn = YARN(hadoop)
    yarn.start_resourcemanager()
    yarn.start_jobhistory()
    hadoop.open_ports('resourcemanager')
    set_state('resourcemanager.started')


@when('resourcemanager.started')
@when_not('namenode.ready')
def hdfs_departed():
    hadoop = get_hadoop_base()
    yarn = YARN(hadoop)
    hadoop.close_ports('resourcemanager')
    yarn.stop_jobhistory()
    yarn.stop_resourcemanager()
    remove_state('resourcemanager.started')
    remove_state('resourcemanager.ready')


@when('resourcemanager.started', 'nodemanager.departing')
def unregister_nodemanager(nodemanager):
    hadoop = get_hadoop_base()
    yarn = YARN(hadoop)
    nodes_leaving = nodemanager.nodes()

    slaves = unitdata.kv().get('resourcemanager.slaves', [])
    slaves_leaving = [node['host'] for node in nodes_leaving]
    hookenv.log('Slaves leaving: {}'.format(slaves_leaving))

    slaves_remaining = list(set(slaves) - set(slaves_leaving))
    unitdata.kv().set('resourcemanager.slaves', slaves_remaining)
    yarn.register_slaves(slaves_remaining)

    utils.remove_kv_hosts(slaves_leaving)
    utils.manage_etc_hosts()

    if not slaves_remaining:
        remove_state('resourcemanager.ready')

    nodemanager.dismiss()


@when('benchmark.joined')
def register_benchmarks(benchmark):
    benchmark.register('teragen', 'terasort')
