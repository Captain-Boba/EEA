"""Protect the pip entry point used by Railway's Python provider."""
from pathlib import Path
import tomllib
import unittest


class DeploymentDependencyTests(unittest.TestCase):
    def test_railpack_requirements_match_project_runtime_dependencies(self):
        root = Path(__file__).resolve().parents[1]
        project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
        requirements = [line.strip() for line in (root / "requirements.txt").read_text(encoding="utf-8").splitlines()
                        if line.strip() and not line.lstrip().startswith("#")]
        self.assertCountEqual(requirements, project["project"]["dependencies"])
        self.assertTrue(any(item.startswith("playwright") for item in requirements))


if __name__ == "__main__":
    unittest.main()
