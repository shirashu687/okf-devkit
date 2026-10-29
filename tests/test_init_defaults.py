"""No-argument initialization starts with the shared defaults."""
from helpers import OkfTestCase
from okf_devkit import cli as okf
from test_init import run_init


class DefaultInitTests(OkfTestCase):
    def test_shared_defaults_and_no_automatic_log(self) -> None:
        run_init()
        bundle = okf.Bundle(self.repo / "okf.yml")
        self.assertEqual(self.repo / "docs", bundle.root)
        self.assertEqual(["shared"], bundle.layers)
        self.assertEqual("project", bundle.cfg["layer_dirs"]["shared"])
        self.assertEqual([], bundle.log_cfg["layers"])
        self.assertEqual("", bundle.log_cfg["baseline"])
        self.assertEqual("log.md", bundle.log_cfg["paths"]["shared"])
        self.assertEqual([("docs/**", "skip"), ("**", "shared")],
                         [(rule["glob"], rule["layer"]) for rule in bundle.cfg["layer_map"]])
