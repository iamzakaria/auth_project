import pytest

def pytest_configure(config):
    config.option.headed = False  # Enable headed mode for all tests