import requests  
import os  
from requests.auth import HTTPBasicAuth  
 
 
# Configuration
JFROG_URL = "https://kenvuesd.jfrog.io/artifactory"  # Replace with your JFrog instance URL
REPO_NAMES = ['kenvone', 'sde']  # Replace with your repository name
USERNAME = "sanjay"  # Replace with your JFrog username
PASSWORD = ""  # Replace with your JFrog API key or use password
DOWNLOAD_DIR = "."  # Directory to save downloaded artifacts
 

# Configuration for Nexus Repository

NEXUS_URL = 'http://3.7.45.176:8081'
NEXUS_USERNAME = 'sanjay'
NEXUS_PASSWORD = ''

jfrog_total_downloaded = 0
nexus_total_uploaded = 0

def list_artifacts(REPO_NAME):

    url = f"{JFROG_URL}/api/search/aql"

    aql_query = f'items.find({{"repo": "{REPO_NAME}"}})'

    response = requests.post(url, data=aql_query, auth=HTTPBasicAuth(USERNAME, PASSWORD), headers={'Content-Type': 'text/plain'})
    
    if response.status_code == 200:
        artifacts = response.json()['results']
        print(f"Below is the list of artifacts present in the Jfrog Repository of {REPO_NAME}: ")
        print("------------------------------")
        for artifact in artifacts:
            name = artifact.get('name')
            if name:
                print(name)
        print("------------------------------")
        print(f"Total number of artifacts: {len(artifacts)}")
        print("------------------------------")
        return artifacts

    else:
        print(f"Failed to list artifacts. Status code: {response.status_code}")
        print(response.text)
        return []
    

def download_artifact(artifact, REPO_NAME):

    global jfrog_total_downloaded

    artifact_path = artifact['path']
    artifact_name = artifact['name']



    artifact_path = f"{artifact['path']}/{artifact['name']}"

    url = f"{JFROG_URL}/{REPO_NAME}/{artifact_path}"

    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    if response.status_code == 200:
        file_path = os.path.join(DOWNLOAD_DIR, artifact_name)
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        with open(file_path, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded: {artifact_name}")
        print("------------------------------")
        jfrog_total_downloaded += 1
       
        return file_path
    
    else:
        print(f"Failed to download {artifact_name}. Status code: {response.status_code}")
    



def check_nexus_repo_exists(repo_name):

    print(f"Checking if the repository {repo_name} is already exist or no in Nexus............")
    print("....................................")

    url = f"{NEXUS_URL}/service/rest/v1/repositories/{repo_name}"
    response = requests.get(url, auth=HTTPBasicAuth(NEXUS_USERNAME, NEXUS_PASSWORD))
    
    if response.status_code == 200:
        print(f"Repository {repo_name} already exists in Nexus.")
        print("....................................")
        return True
    elif response.status_code == 404:
        print(f"Repository {repo_name} does not exist in Nexus. Proceeding with creating {repo_name} repository.")
        print("....................................")
        return False
    else:
        print(f"Failed to check repository {repo_name} in Nexus. Status code: {response.status_code}")
        print(response.text)
        return False


def create_nexus_repo(repo_name):
    url = f"{NEXUS_URL}/service/rest/v1/repositories/maven/hosted"
    headers = {
        'Content-Type': 'application/json'
    }
    payload = {
        "name": repo_name,
        "online": True,
        "storage": {
            "blobStoreName": "default",
            "strictContentTypeValidation": True,
            "writePolicy": "allow_once"
        },"maven": {
            "versionPolicy": "release",
            "layoutPolicy": "strict"
        },   
        "cleanup": {
            "policyNames": []
        },
        "component": {
            "proprietaryComponents": True
        }
    }
    
    response = requests.post(url, json=payload, auth=HTTPBasicAuth(NEXUS_USERNAME, NEXUS_PASSWORD), headers=headers)
    
    if response.status_code == 201:
        print(f"Repository {repo_name} created successfully in Nexus. Now proceeding to migrate artifacts from Jfrog to Nexus.")
        print("------------------------------")
    else:
        print(f"Failed to create repository {repo_name} in Nexus. Status code: {response.status_code}")
        print(response.text)


# Function to upload an artifact to Nexus Repository

def upload_artifact_to_nexus(file_path, artifact, REPO_NAME):
    global nexus_total_uploaded

    artifact_path = f"{artifact['path']}/{artifact['name']}"
    
# https://<your-jfrog-domain>/artifactory/<repository-name>/<groupId>/<artifactId>/<version>/<artifactId>-<version>.<extension>

# https://kenvuesd.jfrog.io/artifactory/sde/junit/junit/4.12/junit-4.12.jar

# https://<your-nexus-domain>/repository/<repository-name>/<groupId>/<artifactId>/<version>/<artifactId>-<version>.<extension>

# http://3.7.45.176:8081/repository/sde/sde/junit/4.12/junit-4.12.jar




    url = f"{NEXUS_URL}/repository/{REPO_NAME}/{artifact_path}"

    with open(file_path, 'rb') as f:
        response = requests.put(url, auth=HTTPBasicAuth(NEXUS_USERNAME, NEXUS_PASSWORD), data=f)
    
    if response.status_code == 201:
        print(f"Uploaded: {artifact['name']} to Nexus")
        print("------------------------------")

        nexus_total_uploaded += 1
    else:
        print(f"Failed to upload {artifact_path} to Nexus. Status code: {response.status_code}")
        print(response.text)


def main():
    global jfrog_total_downloaded
    global nexus_total_uploaded

    for REPO_NAME in REPO_NAMES:

        artifacts = list_artifacts(REPO_NAME)

        # Check if Nexus repository exists
        if not check_nexus_repo_exists(REPO_NAME):
            # Create Nexus repository if it does not exist
            create_nexus_repo(REPO_NAME)

        print(f"Downloading artifacts from Jfrog Repository name {REPO_NAME}..........")
        print("------------------------------")

        for artifact in artifacts:
            file_path = download_artifact(artifact,REPO_NAME)
            
        print(f"Uploading artifacts to the Nexus {REPO_NAME} Repository.........")
        print("------------------------------")

        for artifact in artifacts:
            if file_path:
                upload_artifact_to_nexus(file_path, artifact, REPO_NAME)
                
                
        print(f"Total artfacts downloaded from Jfrog Repository {REPO_NAME} : {jfrog_total_downloaded}")
        print(f"Total artifacts uploaded to Nexus Repository {REPO_NAME} : {nexus_total_uploaded}")
        print("------------------------------------------------------------------------------------------")

        nexus_total_uploaded = 0
        jfrog_total_downloaded = 0
    

main()

