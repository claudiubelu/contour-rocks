#
# Copyright 2024 Canonical, Ltd.
# See LICENSE file for licensing details
#
import os

from k8s_test_harness.util import docker_util


def test_sanity():
    image_variable = "ROCK_CONTOUR"
    entrypoint = "contour"
    image = os.getenv(image_variable)
    assert image is not None, f"${image_variable} is not set"

    process = docker_util.run_in_docker(image, [entrypoint, "--help"], False)
    assert "Contour Kubernetes ingress controller." in process.stderr
