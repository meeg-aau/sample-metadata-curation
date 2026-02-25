import os
import sys

from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install


def run_install_resources():
    import subprocess

    print("Running geographical mapping setup...")

    # Try to find the script
    script_path = os.path.join("sample_metadata_curation", "install_resources.py")
    if os.path.exists(script_path):
        env = os.environ.copy()
        env["PYTHONPATH"] = os.getcwd() + (
            os.pathsep + env["PYTHONPATH"] if "PYTHONPATH" in env else ""
        )
        subprocess.check_call([sys.executable, script_path], env=env)
    else:
        # Try running it as a module
        try:
            subprocess.check_call(
                [sys.executable, "-m", "sample_metadata_curation.install_resources"]
            )
        except subprocess.CalledProcessError:
            print(
                f"Warning: {script_path} not found and failed to run as module. "
                "Skipping resource installation."
            )


class PostInstallCommand(install):
    """Post-installation for installation mode."""

    def run(self):
        install.run(self)
        run_install_resources()


class PostDevelopCommand(develop):
    """Post-installation for development mode."""

    def run(self):
        develop.run(self)
        run_install_resources()


setup(
    cmdclass={
        "install": PostInstallCommand,
        "develop": PostDevelopCommand,
    },
)
