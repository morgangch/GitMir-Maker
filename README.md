# Python Script for Repository Duplication and Workflow Setup

A simple Python script to:
- Duplicate a repository
- Clone it
- Create a new repository with a custom description
- Set up a mirroring Workflow with Repository variables
- All of this is done automatically using the GitHub API.

## Data Required by This Script

- **SSH_PRIVATE_KEY**: The private SSH key located in your home/user/.ssh folder. Use the 'ssh_key' file, not the 'ssh_key.pub'.
- **GITHUB_API_KEY**: The GitHub API Key which can be generated using the guide below.
- **GITHUB_USERNAME**: Your GitHub username.

## Configuring a GitHub Personal Access Token

### Steps to Create and Configure Your Token

1. **Navigate to the Personal Access Tokens Section**
   - Go to GitHub and navigate to **Settings**.
   - In the sidebar, click **Developer settings**.
   - Click on **Personal access tokens**.
   - Click the **Generate new token** button.
   - You can also click on [this link](https://github.com/settings/tokens) directly.

2. **Configure the Token Settings**
   - **Note:** Give your token a descriptive name to identify its purpose.
   - Set the **Expiration** date according to your needs (e.g., 30 days, 60 days, etc.).

3. **Select the Scopes**
   - In the scopes section, select the following permissions:
     - **repo**
       - `repo:status`
       - `repo_deployment`
       - `public_repo`
       - `repo:invite`
       - `security_events`
     - **workflow**
     - **admin:org**
       - `write:org`
       - `read:org`
       - `manage_runners:org`
     - **admin:public_key**
       - `write:public_key`
       - `read:public_key`
     - **admin:repo_hook**
       - `write:repo_hook`
       - `read:repo_hook`
     - **admin:org_hook**
     - **admin:enterprise**
       - `manage_runners:enterprise`
       - `manage_billing:enterprise`
       - `read:enterprise`
     - **codespace**
       - `codespaces:secrets`
     - **project**
       - `read:project`
     - **admin:gpg_key**
       - `write:gpg_key`
       - `read:gpg_key`
     - **admin:ssh_signing_key**
       - `write:ssh_signing_key`
       - `read:ssh_signing_key`

4. **Generate the Token**
   - After selecting the required scopes, click on the **Generate token** button at the bottom of the page.
   - **Important:** Copy the generated token immediately. You will not be able to see it again.

## Setting Up Your SSH Key for GitHub

### Steps to Create Your SSH Key

1. **Open the Terminal**
   - Open your terminal application on your computer.

2. **Generate the SSH Key**
   - Type the following command and press Enter:
     ```bash
     ssh-keygen
     ```
   - You will be prompted to enter a file name for the key. You can press Enter to accept the default or enter a custom name.

3. **Enter a Passphrase (Optional)**
   - You will be asked to enter a passphrase. This is optional. You can press Enter to skip it.

4. **Confirm the Passphrase (Optional)**
   - If you entered a passphrase, you will be asked to confirm it. Otherwise, you can press Enter to skip this step.

5. **Open the Public Key File**
   - Open the public key file (`.pub` extension) with your preferred text editor (Emacs, Nano, VSCode, etc.). For example, if you used the default name, you can open the file by running:
     ```bash
     nano ~/.ssh/id_rsa.pub
     ```

6. **Copy the Public Key**
   - Copy the entire content of the public key file.

7. **Add the SSH Key to GitHub**
   - Go to GitHub and navigate to **Settings**.
   - In the sidebar, click **SSH and GPG keys**.
   - Click the **New SSH key** button.
   - Enter a title for the key (e.g., "My Laptop Key").
   - Paste the copied public key into the "Key" field.
   - Click the **Add SSH key** button to save it.

8. **Configure SSO and Add Your Organization**
   - If your organization requires SSO (Single Sign-On), make sure to configure it.
   - Allow this key to access your organization's GitHub by adding it to your organization settings.

## Additional Resources
- [GitHub Documentation on SSH](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)
- [Generating a New SSH Key and Adding it to the SSH Agent](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent)

## Using These Data

Once you're done with your SSH key and your GitHub Access Token, you can follow two alternate ways to set this up (both are pretty easy).

### 1. **Create a `.env` File in the Same Folder as This Script**
   - Copy this format, replacing it with the correct values:
     ```env
     SSH_PRIVATE_KEY="X"
     GITHUB_API_KEY=X
     GITHUB_USERNAME=X
     ```
   - **Note:** Formally keep the quotes for `SSH_PRIVATE_KEY`, since it's a multiline format.

### 2. **Execute the Script Once to Initialize Your `.env`**
   - Execute the script (`python3 script.py`) and it will ask for each piece of data.
   - Simply fill in the requested data. For the SSH Key, you only need to give the absolute path (exclude `~/` from your input).
