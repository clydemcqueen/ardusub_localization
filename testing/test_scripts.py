# Run tests:
# python -m pytest

# Run tests and show captured stdout:
# python -m pytest -rP

# Run a particular test:
# python -m pytest -rP testing/test_scripts.py::TestScripts::test_param_parsing

import pytest

import param


class TestScripts:

    def test_param_parsing(self):
        lutris_params = param.parse_params('params/lutris.params')
        assert len(lutris_params) == 21

        fusion_params = param.parse_params('params/fusion.params')
        assert len(fusion_params) == 21
