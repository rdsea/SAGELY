import subprocess

def update_configmap(new_policy):
    # Corrected string interpolation using an f-string
    command = (f"kubectl create configmap opa-policy "
               f"--from-file=policy.rego={new_policy} "
               "--dry-run=client -o yaml | "
               "kubectl replace -f -")
    
    try:
        # Execute the command
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Print the output of the command
        print("Command output:", result.stdout)
        
    except subprocess.CalledProcessError as e:
        # Print the error if the command failed
        print("Command failed with error:", e.stderr)

if __name__ == "__main__":
    update_configmap(new_policy="new_policy.rego")
