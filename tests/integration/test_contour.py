#
# Copyright 2024 Canonical, Ltd.
# See LICENSE file for licensing details
#
import json
import logging
import os

# import uuid
from pathlib import Path

from k8s_test_harness import harness
from k8s_test_harness.util import exec_util, k8s_util

pytest_plugins = ["k8s_test_harness.plugin"]

LOG = logging.getLogger(__name__)

# DIR = Path(__file__).absolute().parent
MANIFESTS_DIR = os.path.join(Path(__file__).absolute().parent.parent, "templates")


LOG = logging.getLogger(__name__)


def test_integration_contour(module_instance: harness.Instance):
    image_name_env_variable = "ROCK_CONTOUR"

    image_uri = os.getenv(image_name_env_variable)
    assert image_uri is not None, f"{image_name_env_variable} is not set"

    # This helm chart requires the registry to be separated from the image.
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

    module_instance.exec(helm_command)

    # wait for envoy
    k8s_util.wait_for_daemonset(module_instance, "contour-envoy", "contour")

    # wait for contour
    k8s_util.wait_for_deployment(module_instance, "contour-contour", "contour")

    # deploy for httpbin
    manifest = os.path.join("templates", "httpbin.yaml")
    module_instance.exec(
        ["k8s", "kubectl", "apply", "-f", "-"],
        input=Path(manifest).read_bytes(),
    )

    result = (
        exec_util.stubbornly(retries=5, delay_s=1)
        .on(module_instance)
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
        .on(module_instance)
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
