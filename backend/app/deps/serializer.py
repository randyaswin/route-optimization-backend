def serialize_geojson(data, geometry_field, exclued_fields=[]):
    exclued_fields.append(geometry_field)
    data["longitude"] = data[geometry_field].x
    data["latitude"] = data[geometry_field].y
    return {
        "type": "Feature",
        "geometry": data[geometry_field].__geo_interface__,
        "properties": {k: v for k, v in data.items() if k not in exclued_fields},
    }
