import os
import sys

from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install


def run_install_resources():
    import subprocess

    print("Running geographical mapping setup...")
    # We need to make sure the package is in sys.path if we want to run
    # the script via python -m
    # Or we can just run the script directly if we know where it is.
    # During install, the files are being copied.

    # Try to find the script
    script_path = os.path.join(
        "sample_metadata_curation", "bin", "install_resources.py"
    )
    if os.path.exists(script_path):
        subprocess.check_call([sys.executable, script_path])
    else:
        # If not in current dir, maybe it's already installed?
        # But we want to run it during installation to generate files
        # that SHOULD be packaged.
        # Actually, if we run it now, it generates files in resources/
        # which will then be picked up by setuptools if they are
        # included in package_data.
        print(f"Warning: {script_path} not found. Skipping resource installation.")


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
