####
# Author: Markus R Pedersen
# Protector Insurance ASA
# Date: 13.09.2022
####

import paramiko
import json
import argparse
import os
parser = argparse.ArgumentParser(description='A script that attempts to gather and dump all docker Swarm secrets that are in use by running containers.\n')
parser.add_argument("-m", "--manager", help="A manager host in the Swarm environment. Required to get necessary environment info.", default="Null", type=str)
parser.add_argument("-u", "--username", help="Username of the local user context. Has to be part of the docker group. Required to get necessary environment info.", default="Null", type=str)
parser.add_argument("-p", "--password", help="Password of the local user context. Has to be part of the docker group. Required to get necessary environment info.", default="Null", type=str)
args = vars(parser.parse_args())

host = args['manager']
username = args['username']
password = args['password']

def validate():
    try:
        if host == "Null" or host == "":
            raise ValueError("Missing input for manager node.")
        if username == "Null" or username == "":
            raise ValueError("Missing input for username.")
        if password == "Null" or username == "":
            raise ValueError("Missing input for password.")
    except ValueError as e:
        print(e)
        exit(1)

def execute_command(_command: str,_client: paramiko.client.SSHClient()):
    try:
        _stdin, _stdout, _stderr = _client.exec_command(_command)
        return _stdout.read().decode().strip()
    except Exception as e:
        print(f"Could not run command {_command}")
        print(e.__class__)

def get_service_top_task_and_host(_servicename: str, _client: paramiko.client.SSHClient()):
    _command = "docker service ps " + _servicename + " --no-trunc --format {{.Name}}.{{.ID}},{{.Node}} | head -n 1"
    return execute_command(_command, _client)


def get_secret_locations(_services: list, _client: paramiko.client.SSHClient()) -> dict:
    print("\n--- Gathering service information and secret locations ---\n")
    try:
        _serviceinfo = {}
        for sn in _services:
            try:
                _serviceinfo[sn] = json.loads(execute_command("docker service inspect " + sn, _client))[0]
            except Exception as e:
                print (f"General error at {sn}.")
                print (e.__class__)
        _worker_commands = {}
        _secrets = {}
        if len(_serviceinfo) < 1:
            raise ValueError("No valid swarm service information.")
        for service in _serviceinfo:
            if 'Secrets' in _serviceinfo[service]['Spec']['TaskTemplate']['ContainerSpec']:
                for secret in _serviceinfo[service]['Spec']['TaskTemplate']['ContainerSpec']['Secrets']:
                    if secret['SecretName'] not in _secrets:
                        print(secret['SecretName'] + " found in " + service + "...")
                        temp_servicetask = get_service_top_task_and_host(service, _client)
                        try:
                            target_host = temp_servicetask.split(',')[1]
                            target_container = temp_servicetask.split(',')[0]
                        except IndexError:
                            print(service + " is not running any containers. Skipping...")
                            continue
                        if target_host not in _worker_commands:
                            _worker_commands[target_host] = {}
                        _worker_commands[target_host][secret['SecretName']] = f"docker exec {target_container} cat /var/run/secrets/{secret['File']['Name']}"
                        _secrets[secret['SecretName']] = service
    except (ValueError) as e:
        print(e)
        exit(1)
    except Exception as e:
        print("General error at get_secret_location.")
        print(e.__class__)
    return _worker_commands


def get_service_list(_client: paramiko.client.SSHClient()) -> list:
    _command = "docker service ls --format {{.Name}}"
    return execute_command(_command, _client).split('\n')

def create_secrets_dir():
    try:
        if not (os.path.isdir('secrets')):
            os.mkdir('secrets')
    except Exception as e:
        print("Could not create secrets subdir: ", e.__class__)
        exit(1)

def main():
    try:
        with paramiko.client.SSHClient() as client:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(host, username=username, password=password)
            servicelist = get_service_list(client)
            if len(servicelist) > 0:
                _worker_commands = {}
                _worker_commands = get_secret_locations(servicelist, client)
            else:
                raise ValueError("Swarm manager node returned empty list of services.")

        create_secrets_dir()
        print("\n--- Gathering secret info from containers ---\n")
        for worker in _worker_commands:
            try:
                with paramiko.client.SSHClient() as client:
                    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    client.connect(worker, username=username, password=password)
                    try:
                        for secret in _worker_commands[worker]:
                            if "ucp-" in secret:
                                raise ValueError("Skipping UCP (MKE) system secrets.")
                            with open(f'secrets/{secret}.txt','w') as file:
                                file.write(execute_command(_worker_commands[worker][secret], client))
                                print(f"{secret}.txt created.")

                    except (FileNotFoundError,FileExistsError, ValueError) as e:
                        print(e)
            except paramiko.ssh_exception.AuthenticationException as e:
                print(f"Authentication error at {worker}: ", e)
                print("Exiting...")
                exit(1)
            except Exception as e:
                print(f"Error at {worker}: ", e.__class__)
    except (TypeError, ValueError, UnboundLocalError) as e:
        print(e)
        exit(1)
    except Exception as e:
        print(f"General error at in main.")
        print(e.__class__)
        exit(1)

validate()
main()