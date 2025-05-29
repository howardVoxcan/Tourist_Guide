import json
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourist_Guide.settings")
django.setup()

from location.models import BusStop, BusRoute, RouteStop

json_path = 'bus_data.json'

with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

elements = data.get('elements', [])

print("🚏 Importing BusStop nodes...")
inserted_count = 0
for elem in elements:
    if elem.get('type') == 'node':
        osm_id = elem['id']
        lat = elem.get('lat')
        lon = elem.get('lon')
        if lat is None or lon is None:
            continue
        
        name = elem.get('tags', {}).get('name', '').strip()

        if not name:
            continue

        obj, created = BusStop.objects.update_or_create(
            osm_id=osm_id,
            defaults={
                'name': name,
                'latitude': lat,
                'longitude': lon,
            }
        )

        if created:
            inserted_count += 1
            print(f"✅ Inserted BusStop {osm_id} - '{name}' at ({lat}, {lon})")
        else:
            print(f"🔄 Updated BusStop {osm_id} - '{name}'")

print(f"\n✅ Finished inserting {inserted_count} new BusStops.\n")

print("🚌 Importing BusRoutes and assigning stops...")
for elem in elements:
    if elem.get('type') == 'relation' and elem.get('tags', {}).get('route') == 'bus':
        osm_id   = elem['id']
        tags     = elem.get('tags', {})
        ref      = tags.get('ref', '').strip()
        name     = tags.get('name', '').strip()
        operator = tags.get('operator', '').strip()

        route, created = BusRoute.objects.update_or_create(
            osm_id=osm_id,
            defaults={ 'ref': ref, 'name': name, 'operator': operator }
        )
        print(f"{'🆕 Created' if created else '🔄 Updated'} BusRoute {ref or osm_id} - {name}")

        RouteStop.objects.filter(route=route).delete()

        seq = 0
        for member in elem.get('members', []):
            if member.get('type') == 'node' and member.get('role') in ('stop', 'platform'):
                stop_id = member['ref']
                stop = BusStop.objects.filter(osm_id=stop_id).first()
                if not stop:
                    print(f"⚠️  Missing BusStop {stop_id}, skipping")
                    continue
                seq += 1
                RouteStop.objects.create(route=route, stop=stop, sequence=seq)
        print(f"   🔗 Linked {seq} stops to route {ref or osm_id}")

print("\n✅ Bus data import complete.")