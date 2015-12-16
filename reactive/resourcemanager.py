from charms.reactive import when, when_not, set_state, remove_state
from charms.hadoop import get_hadoop_base
from charms.reactive.helpers import data_changed
from jujubigdata.handlers import HDFS, YARN
from jujubigdata import utils
from charmhelpers.core import hookenv, unitdata


@when('hadoop.installed')
@when_not('resourcemanager.started')
def configure_resourcemanager():
    hadoop = get_hadoop_base()
    yarn = YARN(hadoop)
    hdfs = HDFS(hadoop)
    hdfs.configure_client()
    yarn.configure_resourcemanager()
    yarn.configure_jobhistory()
    yarn.register_slaves()
    yarn.start_resourcemanager()
    yarn.start_jobhistory()
    hadoop.open_ports('resourcemanager')
    set_state('resourcemanager.started')


@when('resourcemanager.started')
@when_not('nodemanager.related')
def blocked():
    hookenv.status_set('blocked', 'Waiting for DataNodes')


@when('resourcemanager.started', 'nodemanager.related')
def send_info(nodemanager):
    hadoop = get_hadoop_base()
    resourcemanager_port = hadoop.dist_config.port('resourcemanager')
    hs_http = hadoop.dist_config.port('jh_webapp_http')
    hs_ipc = hadoop.dist_config.port('jobhistory')

    utils.update_kv_hosts({node['ip']: node['hostname'] for node in nodemanager.nodes()})
    utils.manage_etc_hosts()

    nodemanager.send_spec(hadoop.spec())
    nodemanager.send_ports(resourcemanager_port, hs_http, hs_ipc)
    nodemanager.send_ssh_key(utils.get_ssh_key('ubuntu'))
    nodemanager.send_hosts_map(utils.get_kv_hosts())


@when('resourcemanager.started', 'nodemanager.related')
@when_not('nodemanager.registered')
def waiting(nodemanager):
    hookenv.status_set('waiting', 'Waiting for NodeManagers')


@when('resourcemanager.started', 'nodemanager.registered')
def register_nodemanagers(nodemanager):
    hadoop = get_hadoop_base()
    yarn = YARN(hadoop)

    slaves = [node['hostname'] for node in nodemanager.nodes()]
    if data_changed('resourcemanager.slaves', slaves):
        unitdata.kv().set('resourcemanager.slaves', slaves)
        yarn.register_slaves(slaves)

    hookenv.status_set('active', 'Ready ({count} NodeManager{s})'.format(
        count=len(slaves),
        s='s' if len(slaves) > 1 else '',
    ))
    set_state('resourcemanager.ready')
  
  
@when('namenode.related')
@when('nodemanager.ready')
def accept_clients(clients):
    hadoop = get_hadoop_base()
    private_address = hookenv.unit_get('private-address')
    ip_addr = utils.resolve_private_address(private_address)
    resourcemanager_port = hadoop.dist_config.port('resourcemanager')
    hs_http = hadoop.dist_config.port('jh_webapp_http')
    hs_ipc = hadoop.dist_config.port('jobhistory')

    clients.send_spec(hadoop.spec())
    clients.send_ip_addr(ip_addr)
    clients.send_ports(resourcemanager_port, hs_http, hs_ipc)
    clients.send_ready(True)


@when('namenode.related')
@when_not('namenode.ready')
def reject_clients(clients):
    clients.send_ready(False)


@when('resourcemanager.started', 'nodemanager.departing')
def unregister_nodemanager(nodemanager):
    hadoop = get_hadoop_base()
    yarn = YARN(hadoop)
    nodes_leaving = nodemanager.nodes()  # only returns nodes in "leaving" state

    slaves = unitdata.kv().get('nodemanager.slaves')
    slaves_leaving = [node['hostname'] for node in nodes_leaving]
    hookenv.log('Slaves leaving: {}'.format(slaves_leaving))

    slaves_remaining = list(set(slaves) ^ set(slaves_leaving))
    unitdata.kv().set('nodemanager.slaves', slaves_remaining)
    yarn.register_slaves(slaves_remaining)

    utils.remove_kv_hosts({node['ip']: node['hostname'] for node in nodes_leaving})
    utils.manage_etc_hosts()

    if not slaves_remaining:
        hookenv.status_set('blocked', 'Waiting for relation to NodeManagers')
        remove_state('resourcemanager.ready')
