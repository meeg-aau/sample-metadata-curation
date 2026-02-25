from typing import Any, Dict, List, Optional

from sample_metadata_curation.sample_parser import normalize_key


class BiomeCurator:
    def __init__(self, biome_keys: Optional[List[str]] = None):
        self.biome_keys = [normalize_key(k) for k in biome_keys] if biome_keys else []

    def curate_biome(self, cleaned_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract biome information from cleaned dictionary based on biome_keys.
        """
        result = {}
        if self.biome_keys:
            biome_values = []
            for bk in self.biome_keys:
                if bk in cleaned_dict:
                    val = cleaned_dict.get(bk)
                    if val:
                        biome_values.append(str(val))
            if biome_values:
                result["biome"] = ";".join(biome_values)
        return result
