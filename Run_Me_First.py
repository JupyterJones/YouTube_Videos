import os
import subprocess

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print("Created directory: {}".format(path))
    else:
        print("Directory already exists: {}".format(path))

def create_virtualenv(venv_name):
    subprocess.call(["virtualenv", "--python=python3.8", venv_name])
    print("Virtual environment '{}' created.".format(venv_name))

def activate_virtualenv(venv_name):
    activate_script = os.path.join(venv_name, "bin", "activate")
    os.chmod(activate_script, 0o755)  # Change permissions to make it executable
    subprocess.call(["bash", "-c", "source {}".format(activate_script)])
    print("Activated virtual environment '{}'.".format(venv_name))

def install_requirements(venv_name):
    activate_virtualenv(venv_name)
    subprocess.call([os.path.join(venv_name, "bin", "pip"), "install", "-r", "requirements.txt"])
    print("Requirements installed.")

if __name__ == "__main__":
    # Define directory paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(base_dir, "static")
    templates_dir = os.path.join("templates")
    css_dir = os.path.join(static_dir, "css")
    videos_dir = os.path.join(static_dir, "videos")
    images_dir = os.path.join(static_dir, "images")
    text_dir = os.path.join(static_dir, "text")

    # Create directories
    create_directory(static_dir)
    create_directory(templates_dir)
    create_directory(css_dir)
    create_directory(videos_dir)
    create_directory(images_dir)
    create_directory(text_dir)

    # Create and activate virtual environment
    venv_name = "flask_env"
    create_virtualenv(venv_name)
    install_requirements(venv_name)
    subprocess.call([os.path.join(venv_name, "bin", "pip"), "freeze"])
