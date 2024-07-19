#
# Copyright 2024 Canonical, Ltd.
# See LICENSE file for licensing details
#
import os
import subprocess


def test_sanity():
    image_variable = "ROCK_CONTOUR"
    entrypoint = "contour"
    image = os.getenv(image_variable)
    assert image is not None, f"${image_variable} is not set"

    docker_run = subprocess.run(
        ["docker", "run", "--rm", "--entrypoint", entrypoint, image, "--help"],
        capture_output=True,
        text=True,
    )
    assert "Contour Kubernetes ingress controller." in docker_run.stderr
