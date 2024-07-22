#
# Copyright 2024 Canonical, Ltd.
# See LICENSE file for licensing details
#

import pytest
from k8s_test_harness.util import docker_util, env_util


@pytest.mark.parametrize("image_version", ("1.28.2", "1.26.1", "1.22.3"))
def test_sanity(image_version):
    rock = env_util.get_build_meta_info_for_rock_version(
        "contour", image_version, "amd64"
    )
    image = rock.image

    entrypoint = "contour"
    process = docker_util.run_in_docker(image, [entrypoint, "--help"], False)
    assert "Contour Kubernetes ingress controller." in process.stderr
