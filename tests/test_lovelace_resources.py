"""Exercise the resource migration without importing Home Assistant."""
import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
import unittest


class ResourceMigrationTest(unittest.TestCase):
    def test_removes_only_obsolete_sph_resources_and_is_idempotent(self):
        source = Path('custom_components/sph/__init__.py').read_text()
        tree = ast.parse(source)
        nodes = [node for node in tree.body if
                 isinstance(node, ast.AsyncFunctionDef) and node.name == '_register_lovelace_resources'
                 or isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in ('CARD_VERSION', 'CARD_URLS') for t in node.targets)]
        namespace = {'DOMAIN': 'sph', 'LOVELACE_DATA': 'lovelace', 'HomeAssistant': object}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), '<resource migration>', 'exec'), namespace)

        class Resources:
            loaded = True
            def __init__(self):
                self.items = [
                    {'id': 'old', 'url': '/api/sph/static/kfg-stundenplan-card.js?v=old'},
                    {'id': 'compat', 'url': '/api/sph/static/kfg-stundenplan-compat.js'},
                    {'id': 'other', 'url': '/api/kfg_vertretungsplan/static/vertretungsplan-card.js'},
                    {'id': 'local', 'url': '/local/kfg-stundenplan-card.js'},
                ]
            def async_items(self): return list(self.items)
            async def async_delete_item(self, item_id): self.items = [i for i in self.items if i['id'] != item_id]
            async def async_create_item(self, data): self.items.append({**data, 'id': str(len(self.items)), 'type': data['res_type']})
            async def async_update_item(self, item_id, data):
                next(i for i in self.items if i['id'] == item_id).update(data)

        resources = Resources()
        hass = SimpleNamespace(data={'lovelace': SimpleNamespace(resources=resources)})
        register = namespace['_register_lovelace_resources']
        asyncio.run(register(hass))
        urls = [i['url'] for i in resources.items]
        self.assertEqual(len(urls), 8)
        self.assertIn('/local/kfg-stundenplan-card.js', urls)
        self.assertIn('/api/kfg_vertretungsplan/static/vertretungsplan-card.js', urls)
        self.assertFalse(any(url.startswith('/api/sph/static/kfg-') for url in urls))
        asyncio.run(register(hass))
        self.assertEqual([i['url'] for i in resources.items], urls)


if __name__ == '__main__':
    unittest.main()
