import os
import yaml
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import PreservedScalarString
yaml = YAML()
secretfolder = "secrets"
k8ssecretfolder = "k8s-secrets"


def validate(_folder: str):
    try:
        _, _, filenames = next(os.walk(_folder), (None, None, []))
        if len(filenames) < 1:
            raise ValueError(f"Directory {_folder} is empty.")
    except ValueError as e:
        print(e)
        exit(1)
    except Exception as e:
        print("Unhandled validation error.")
        print(e.__class__)
        exit(1)

def get_all_secret_files(_folder: str) -> list:
    _, _, filenames = next(os.walk(_folder), (None, None, []))
    return filenames

def read_file_content(_filepath: str):
    try:
        with open(_filepath,'r') as file:
            content = file.read()
            if content == '':
                raise ValueError(f"{_filepath} does not have any content.")
    except ValueError as e:
        print(e)
    except Exception as e:
        print(e.__class__)
    return content

def create_k8s_secrets_dir(_folder: str):
    try:
        if not (os.path.isdir(_folder)):
            os.mkdir(_folder)
    except Exception as e:
        print("Could not create secrets subdir: ", e.__class__)
        exit(1)

def create_secrets_dict(files_list: list) -> dict:
    temp = {}
    for file in files_list:
        k8scompliantsecretname = file.lower().split('.')[0].replace('_', '-')
        temp[k8scompliantsecretname] = read_file_content(f"{secretfolder}/{file}")
    return temp

def write_to_yml_file(_filepath: str, _content: dict):
    try:
        with open(_filepath,"w") as file:
            print(f"Creating {_filepath}...")

            yaml.dump(_content,file)
    except (PermissionError, TypeError) as e:
        print(e)
    except Exception as e:
        print("Unhandled error at writing to file.")
        print(e.__class__)

def k8s_secret_format(_name: str,_content):
        return {'apiVersion': 'v1',
                 'kind': 'Secret',
                 'metadata':
                     {'name': _name},
                 'type': 'Opaque',
                 'stringData':
                     {'content': PreservedScalarString(_content)}
                 }

def create_k8s_secrets(_secretdict: dict, _k8ssecretfolderpath: str):
    try:
        for secret in _secretdict:
            write_to_yml_file(f"{_k8ssecretfolderpath}/{secret}.yml", k8s_secret_format(secret, _secretdict[secret]))
    except Exception as e:
        print("Unhandled error at create_k8s_secrets")
        print(e.__class__)

def main():
    validate(secretfolder)
    filecontent = {}
    filecontent = create_secrets_dict(get_all_secret_files(secretfolder))
    create_k8s_secrets_dir(k8ssecretfolder)
    create_k8s_secrets(filecontent, k8ssecretfolder)

main()