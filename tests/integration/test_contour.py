#
# Copyright 2024 Canonical, Ltd.
# See LICENSE file for licensing details
#
import json
import logging
import os

# import uuid
from pathlib import Path

import pytest
from k8s_test_harness import harness
from k8s_test_harness.util import env_util, exec_util, k8s_util

pytest_plugins = ["k8s_test_harness.plugin"]

LOG = logging.getLogger(__name__)

# DIR = Path(__file__).absolute().parent
MANIFESTS_DIR = os.path.join(Path(__file__).absolute().parent.parent, "templates")


LOG = logging.getLogger(__name__)


@pytest.mark.parametrize("image_version", ("1.28.2", "1.26.1", "1.22.3"))
def test_integration_contour(function_instance: harness.Instance, image_version: str):
    contour_rock = env_util.get_build_meta_info_for_rock_version(
        "contour", image_version, "amd64"
    )

    # This helm chart requires the registry to be separated from the image.
    image_uri = contour_rock.image
    registry = "docker.io"
    parts = image_uri.split("/")
    if len(parts) > 1:
        registry = parts[0]
        image_uri = "/".join(parts[1:])

    helm_command = k8s_util.get_helm_install_command(
        "contour",
        "contour",
        namespace="contour",
        repository="https://charts.bitnami.com/bitnami",
        images=[k8s_util.HelmImage(image_uri)],
        chart_version="17.0.4",  # chart version with 1.28.2 app
        set_configs=[f"image.registry={registry}"],
    )

    function_instance.exec(helm_command)

    # wait for envoy
    k8s_util.wait_for_daemonset(function_instance, "contour-envoy", "contour")

    # wait for contour
    k8s_util.wait_for_deployment(function_instance, "contour-contour", "contour")

    # deploy for httpbin
    manifest = os.path.join("templates", "httpbin.yaml")
    function_instance.exec(
        ["k8s", "kubectl", "apply", "-f", "-"],
        input=Path(manifest).read_bytes(),
    )

    result = (
        exec_util.stubbornly(retries=5, delay_s=1)
        .on(function_instance)
        .exec(
            ["k8s", "kubectl", "get", "svc", "httpbin", "-o", "json"],
            capture_output=True,
        )
    )
    assert result.returncode == 0, "Failed to get httpbin service"
    qwe = json.loads(result.stdout.decode())
    awd = qwe["spec"]["clusterIP"]
    resp = (
        exec_util.stubbornly(retries=15, delay_s=5)
        .on(function_instance)
        .exec(
            [
                "curl",
                f"{awd}:8888",
            ],
            capture_output=True,
        )
    )

    out = resp.stdout.decode()
    assert "<title>httpbin.org</title>" in out
