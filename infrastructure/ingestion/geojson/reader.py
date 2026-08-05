import json
class GeoJSONSourceReader:
    media_types={"application/geo+json","application/json"}
    def read(self,data:bytes):
        value=json.loads(data.decode("utf-8"))
        if value.get("type")!="FeatureCollection" or not isinstance(value.get("features"),list): raise ValueError("GeoJSON FeatureCollection is required")
        return list(value["features"])
