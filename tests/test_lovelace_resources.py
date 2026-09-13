"""Exercise Lovelace resource registration without importing Home Assistant."""
import ast
import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
import unittest


class LovelaceResourceTest(unittest.TestCase):
    def test_registers_current_sph_resources_and_is_idempotent(self):
        source = Path('custom_components/sph/__init__.py').read_text()
        tree = ast.parse(source)
        nodes = [
            node
            for node in tree.body
            if isinstance(node, ast.AsyncFunctionDef)
            and node.name == '_register_lovelace_resources'
            or isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name)
                and target.id in ('CARD_VERSION', 'CARD_URLS')
                for target in node.targets
            )
        ]
        namespace = {
            'DOMAIN': 'sph',
            'LOVELACE_DATA': 'lovelace',
            'HomeAssistant': object,
        }
        exec(
            compile(
                ast.Module(body=nodes, type_ignores=[]),
                '<resource registration>',
                'exec',
            ),
            namespace,
        )

        manifest = json.loads(
            Path('custom_components/sph/manifest.json').read_text()
        )
        version = namespace['CARD_VERSION']
        self.assertEqual(version, manifest['version'])

        class Resources:
            loaded = True

            def __init__(self):
                self.items = [
                    {
                        'id': 'existing',
                        'url': '/api/sph/static/sph-stundenplan-card.js?v=old',
                        'type': 'module',
                    },
                    {
                        'id': 'other',
                        'url': '/local/custom-card.js',
                        'type': 'module',
                    },
                ]

            def async_items(self):
                return list(self.items)

            async def async_create_item(self, data):
                self.items.append(
                    {
                        **data,
                        'id': str(len(self.items)),
                        'type': data['res_type'],
                    }
                )

            async def async_update_item(self, item_id, data):
                next(item for item in self.items if item['id'] == item_id).update(data)

        resources = Resources()
        hass = SimpleNamespace(
            data={'lovelace': SimpleNamespace(resources=resources)}
        )
        register = namespace['_register_lovelace_resources']

        asyncio.run(register(hass))
        urls = [item['url'] for item in resources.items]

        self.assertEqual(len(urls), 8)
        self.assertIn('/local/custom-card.js', urls)
        self.assertTrue(
            any(
                url == f'/api/sph/static/sph-stundenplan-card.js?v={version}'
                for url in urls
            )
        )
        self.assertTrue(
            any(
                url == f'/api/sph/static/sph-vertretungsplan-card.js?v={version}'
                for url in urls
            )
        )

        asyncio.run(register(hass))
        self.assertEqual([item['url'] for item in resources.items], urls)


if __name__ == '__main__':
    unittest.main()
