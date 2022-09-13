# swarm-secret-gatherer script
The script will gather all secret info and dump all secrets in a folder relative to where the current workdir is.
<br/>Requirements for the script to work:
- python
- pip install -r requirements.txt has been run.
- the script has to be run from a server/computer that has ssh access to all nodes that host containers.
- a user with ssh access to all of the worker nodes in the swarm cluster, as well as the target manager node.
- the user that the script is being run as will need to be part of the local docker group on all servers.

----

<b>Usage:</b>
<br/>

Run the following command:
<br/>
python swarm-secret-gatherer.py -m "managerhostname" -u "username" -p "secretpassword"