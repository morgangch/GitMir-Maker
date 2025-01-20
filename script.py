import os
import base64
import json
import requests
from dotenv import load_dotenv
from nacl import encoding, public
from base64 import b64encode

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

GITHUB_API_KEY = os.getenv('GITHUB_API_KEY')
SSH_PRIVATE_KEY = os.getenv('SSH_PRIVATE_KEY')
USERNAME = os.getenv('GITHUB_USERNAME')  # Assurez-vous que votre nom d'utilisateur GitHub est dans le .env

# Fonction pour créer un nouveau dépôt
def create_repository(repo_name, description):
    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {GITHUB_API_KEY}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "name": repo_name,
        "description": description,
        "private": False,  # Dépôt public
        "default_branch": "main"
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201:
        print(f"Repository '{repo_name}' created successfully.")
    else:
        print(f"Failed to create repository: {response.json()}")


# Fonction pour obtenir la clé publique du dépôt pour chiffrer le secret
def get_public_key(repo_name):
    url = f"https://api.github.com/repos/{USERNAME}/{repo_name}/actions/secrets/public-key"
    headers = {
        "Authorization": f"token {GITHUB_API_KEY}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get public key: {response.json()}")
        return None
    

# Fonction pour chiffrer un secret
def encrypt_secret(public_key, secret_value):
    public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return b64encode(encrypted).decode("utf-8")


# Fonction pour ajouter des secrets au dépôt
def add_secret(repo_name, secret_name, secret_value):
    public_key = get_public_key(repo_name)
    if not public_key:
        return
    
    encrypted_secret = encrypt_secret(public_key["key"], secret_value)
    url = f"https://api.github.com/repos/{USERNAME}/{repo_name}/actions/secrets/{secret_name}"
    headers = {
        "Authorization": f"token {GITHUB_API_KEY}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "encrypted_value": encrypted_secret,
        "key_id": public_key['key_id']
    }

    response = requests.put(url, json=payload, headers=headers)
    if response.status_code == 201:
        print(f"Secret '{secret_name}' added successfully.")
    else:
        print(f"Failed to add secret: {response.json()}")

# Fonction pour ajouter une variable publique
def add_variable(repo_name, var_name, var_value):
    url = f"https://api.github.com/repos/{USERNAME}/{repo_name}/actions/variables"
    headers = {
        "Authorization": f"token {GITHUB_API_KEY}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "name": var_name,
        "value": var_value
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201:
        print(f"Variable '{var_name}' added successfully.")
    else:
        print(f"Failed to add variable: {response.json()}")

# Fonction pour créer le fichier workflow
def create_workflow(repo_name, mirror_url, old_repo_url):
    # Cloner le vieux repository localement
    old_repo_path = f"/tmp/{repo_name}_old"
    print(f"Cloning old repository at {old_repo_path} with url {mirror_url}")
    os.system(f"git clone {mirror_url} {old_repo_path}")

    # Copier le contenu du vieux repository dans le nouveau repository
    new_repo_path = f"/tmp/{repo_name}_new"
    os.makedirs(new_repo_path, exist_ok=True)
    os.system(f"cp -r {old_repo_path}/* {new_repo_path}/")

    # Créer le fichier workflow localement dans le nouveau repository
    workflow_content = f"""
name: {repo_name}

on:
  push:
    branches-ignore:
      - 'ga-ignore-*'
  pull_request:
    branches-ignore:
      - 'ga-ignore-*'

jobs:
  check_coding_style:
    name: "Use coding_style_checker"
    runs-on: ubuntu-latest

    steps:
      # Checkout repository code
      - name: Checkout code
        uses: actions/checkout@v4

      # Set up environment variables for directories
      - name: Set environment variables
        run: |
          echo "DELIVERY_DIR=$(pwd)" >> $GITHUB_ENV
          echo "REPORTS_DIR=$(pwd)/reports" >> $GITHUB_ENV

      # Create the reports directory
      - name: Create reports directory
        run: mkdir -p ${{ env.REPORTS_DIR }}

      # Run the coding style checker in the container
      - name: Run coding style checker
        run: |
          docker pull ghcr.io/epitech/coding-style-checker:latest
          docker run --rm \
            --security-opt "label:disable" \
            -v ${{ env.DELIVERY_DIR }}:/mnt/delivery \
            -v ${{ env.REPORTS_DIR }}:/mnt/reports \
            ghcr.io/epitech/coding-style-checker:latest \
            /mnt/delivery /mnt/reports
""" + """
      # Display coding style errors
      - name: Analyze coding style reports
        run: |
          REPORT_FILE="${{ env.REPORTS_DIR }}/coding-style-reports.log"
          if [[ -s "$REPORT_FILE" ]]; then
            echo "Coding style errors detected:"
            cat "$REPORT_FILE"
            CODING_STYLE_ERRORS=$(cat "$REPORT_FILE")
            for ERRORS in $CODING_STYLE_ERRORS; do
              array=(`echo $ERRORS | sed 's/:/\n/g'`)
              echo "::error file=${array[1]#./},title=${array[3]#./} coding style errors detected: ${array[2]#./}::${array[4]#./}"
            done
            exit 1
          else
            echo "No coding style errors detected"
          fi
""" + """
  check_repo:
    if: ${{{{ github.repository == 'morgangch/{repo_name}' }}}}
    name: "Checks if the repository is clean and void of any unwanted files (temp files, binary files, etc.)"
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - id: check_repo
        run: |
          UNWANTED_FILES=$(find . -type f -not -path "./git/*" -wholename "*tmp/*" -or -name "*~" -or -name "*.o" -or -name "*.so" -or -name "*.gcno" -or -name "*.gcda" -or -name "*#" -or -name "#*" -or -name "*.gcov")
          for FILES in $UNWANTED_FILES; do
            echo "::error file=${{FILES#./}},title=Unwanted file detected::${{FILES#./}}"
          done
          if [[ -n $UNWANTED_FILES ]]
          then
            exit 1
          else
            echo No unwanted files detected
          fi

  check_program_compilation:
    needs: [check_repo]
    name: "Checks if make compil and test all binary listed in the ARGUMENTS variable"
    runs-on: ubuntu-latest
    container:
      image: epitechcontent/epitest-docker:latest
    steps:
      - uses: actions/checkout@v4
      - name: Check for Makefile and compile
        run: |
          if [ -f Makefile ]; then
            for target in all clean fclean re; do
              make $target
              if [ make_exit_code -ne 0 ]; then
                echo "Error: make $target failed with exit code $?"
                exit 1
              fi
            done
          else
            echo "Makefile not found, skipping compilation and testing."
          fi
        timeout-minutes: 2

  run_tests:
    needs: [check_program_compilation]
    name: "Runs tests with criterion"
    runs-on: ubuntu-latest
    container:
      image: epitechcontent/epitest-docker:latest

    steps:
      - uses: actions/checkout@v4
      - name: Check if tests_run rule exists
        run: |
          if [ -f Makefile ]; then
            if cat Makefile | grep -q "tests_run"; then
              make tests_run
              if [ $? -eq 0 ]; then
                echo "Tests run successfully"
              else
                echo "Error: make tests_run failed"
                exit 1
              fi
            else
              echo "tests_run rule not found, skipping tests."
            fi
          else
            echo "Makefile not found, skipping tests."
          fi
        timeout-minutes: 2

  push_to_mirror:
    needs: [check_coding_style, run_tests, check_repo, check_program_compilation]
    if: ${{{{ github.event_name == 'push' && github.actor != 'github-actions[bot]' }}}}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: pixta-dev/repository-mirroring-action@v1
        with:
          target_repo_url: ${{{{ vars.MIRROR_URL }}}}
          ssh_private_key: ${{{{ secrets.SSH_PRIVATE_KEY }}}}
"""
    workflow_path = f"{new_repo_path}/.github/workflows/mirror.yml"
    os.makedirs(os.path.dirname(workflow_path), exist_ok=True)
    with open(workflow_path, 'w') as file:
        file.write(workflow_content)
    print(f"Workflow created at {workflow_path}")

    # Initialiser un nouveau dépôt git dans le nouveau repository local
    os.system(f"cd {new_repo_path} && git init")
    os.system(f"cd {new_repo_path} && git remote add origin git@github.com:{USERNAME}/{repo_name}.git")
    os.system(f"cd {new_repo_path} && git add .")
    os.system(f"cd {new_repo_path} && git commit -m 'Initial commit with workflow and old repository content'")
    os.system(f"cd {new_repo_path} && git branch -M main")
    os.system(f"cd {new_repo_path} && git push -u origin main --force")

def build_dotenv():
    ssh_path = input("Enter your SSH private key absolute path (dont forget to configure SSO access if needed) : ")
    GITHUB_API_KEY = input("Enter your GitHub API key (must have admin accesses) : ")
    USERNAME = input("Enter your GitHub username : ")
    with open(ssh_path, 'r') as file:
        SSH_PRIVATE_KEY = file.read()
    with open('.env', 'w') as file:
        file.write(f'SSH_PRIVATE_KEY="{SSH_PRIVATE_KEY}"\n')
        file.write(f'GITHUB_API_KEY={GITHUB_API_KEY}\n')
        file.write(f"GITHUB_USERNAME={USERNAME}\n")

# Main script
def main():
    if not os.path.exists('.env') or not SSH_PRIVATE_KEY or not GITHUB_API_KEY or not USERNAME:
        build_dotenv()
        load_dotenv()
    if len(os.sys.argv) > 1:
        org_repo_url = os.sys.argv[1]
    else:
        org_repo_url = input("Enter the organization repository URL (HTTPS URL): ")
    old_repo_name = org_repo_url.split('/')[-1]
    old_repo_name = old_repo_name.replace('.git', '')
    repo_name = old_repo_name.split('-')[-2]
    if input(f"Do you want to name the new repo '{repo_name}' ? (y/n): ").lower() not in ['y', ' ']:
        repo_name = input("Enter the correct repository name: ")
    ssh_repo_url = f"git@{org_repo_url[8:].replace('github.com/', 'github.com:')}"
    print(f"Repository SSH URL: {ssh_repo_url}")
    description = input("Enter a description for the new repository: ")

    create_repository(repo_name, description)
    add_secret(repo_name, "SSH_PRIVATE_KEY", SSH_PRIVATE_KEY)
    add_variable(repo_name, "MIRROR_URL", ssh_repo_url)
    create_workflow(repo_name, ssh_repo_url, org_repo_url)

if __name__ == "__main__":
    main()
