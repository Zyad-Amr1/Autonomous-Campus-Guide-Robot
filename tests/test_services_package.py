from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_services_package_can_be_imported():
    import services

    assert services is not None


def test_services_package_has_file_attribute():
    import services

    assert Path(services.__file__).exists()


def test_services_folder_contains_init_file():
    assert (ROOT / "services" / "__init__.py").exists()
