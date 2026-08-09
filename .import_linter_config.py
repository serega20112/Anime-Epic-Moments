"""Import Linter configuration for enforcing clean architecture layers."""

from importlinter.application.app_config import ContractOptions

Contracts = [
    ContractOptions(
        name="Layer Boundaries",
        type="layers",
        layers=[
            "src.backend.delivery",
            "src.backend.use_case",
            "src.backend.domain",
            "src.backend.infrastructure",
            "src.backend.dependencies",
        ],
        contain_objects={"*": "*.py"},
        layer_independence={
            "src.backend.delivery": {
                "can_import": {"src.backend.delivery", "src.backend.use_case", "src.backend.dependencies", "src.backend.infrastructure.web"},
                "can_import_containing_packages": True,
            },
            "src.backend.use_case": {
                "can_import": {"src.backend.use_case", "src.backend.domain", "src.backend.infrastructure"},
                "can_import_containing_packages": True,
            },
            "src.backend.domain": {
                "can_import": {"src.backend.domain"},
                "can_import_containing_packages": True,
            },
            "src.backend.infrastructure": {
                "can_import": {"src.backend.infrastructure", "src.backend.domain", "src.backend.dependencies"},
                "can_import_containing_packages": True,
            },
            "src.backend.dependencies": {
                "can_import": {
                    "src.backend.dependencies",
                    "src.backend.domain",
                    "src.backend.infrastructure",
                    "src.backend.use_case",
                    "src.backend.services",
                },
                "can_import_containing_packages": True,
            },
        },
        layer_output="terminal",
    ),
]
