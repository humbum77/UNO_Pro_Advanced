import ast
import hashlib
from pathlib import Path
import unittest


LOCKED_FUNCTIONS = {
    '_env_seconds': '30f406a866cb5d91a5efe3319ed3be4f34bdeb55f8c2a0a747414138a45ec4dd',
    '_env_visual_norm': '4ca9b7cbb2313facbe4101a7047e36117858057485dd407b0055d8d33a924df8',
    '_env_visual_raw': '243509d7d0da906c239668fdb9ff68fdf5854dca040a8e9499addd54104a6aa0',
    '_env_visual_seconds': 'dbcc9e5ca8c83be2ea509d40d9b9dcd8e28e8ef475b0b72830f69baaa65d1eea',
    '_env_geometry': 'df16d45cb5edc13218c72adb453d2c579f7d272a8218034375b1909d1faad43f',
    '_env_level': 'fcf0a327446cbe3b6939376e4019c875374233c3b6defbd819b41fffe6b969ec',
    '_env_is_dynamic': '02cb202a652d66e4327af05c6e4305f379ec1ee1597c43b0533adc35b2151093',
    '_ensure_animation': '3a5e8d7978c76f97f6a9a8ee1515daf9c01110aed9fd47fa72c2010fe297693c',
    '_animation_tick': '204efad8b2438d62fac588ecbf3f607dbee8d941ad82e11a5aa66fd59570591b',
    'env_graph': '70968d269b81585cc5ec3839b3c6f374a52196bec3d651347817cfd1af7afb78',
    '_env_marker_position': '3fc38c41e1ea2e4f3509c4588fb1080dbae91c7f5a52c63785a4bb191553e3cf',
    '_near_env_segment': '7cfb475490b4db801dc01bbf2c861b9f9a47434d51a45480f8b19d44913bc5ed',
    '_drag_env_point': '86ce17f7d6b064d3f6d227b2b33ae8d9f791b103b8d726f53d76fef7b6fde126',
    '_env_note_on': '498b704a0c79f0b6e8b9e0147257212853b6cabdc36e46085ace7f796e70cc60',
    '_env_note_off': 'b25200dbf835619bf29487b4ed2179d37ce6f25b6318fbe9d29ee88715e19df2',
}


class EnvelopeLockTests(unittest.TestCase):
    def test_locked_envelope_implementation_is_unchanged(self):
        source = (Path(__file__).parents[1] / 'app.py').read_text(encoding='utf-8')
        tree = ast.parse(source)
        app_class = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'App')
        functions = {
            node.name: ast.get_source_segment(source, node)
            for node in app_class.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        self.assertEqual(set(LOCKED_FUNCTIONS) - set(functions), set())
        for name, expected in LOCKED_FUNCTIONS.items():
            with self.subTest(function=name):
                digest = hashlib.sha256(functions[name].encode()).hexdigest()
                self.assertEqual(digest, expected)


if __name__ == '__main__':
    unittest.main()
