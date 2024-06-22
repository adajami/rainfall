import json
import sys
import xarray as xr

def load_json(file_path):
    """Load JSON file."""
    with open(file_path) as f:
        return json.load(f)

def main():
    # Load STAC metadata for rainfall
    rainfall_stac_metadata = load_json("rfb_blended_moz_dekad.json")

    # Extract the asset URL for rfb band if it exists
    assets = rainfall_stac_metadata.get('assets', {})
    rfb_info = assets.get('rfb', None)

    if rfb_info is None:
        print("Error: 'rfb' asset information not found in metadata.", file=sys.stderr)
        sys.exit(1)

    rfb_url = rfb_info.get('href', None)

    if rfb_url is None:
        print("Error: 'href' information not found for 'rfb' asset.", file=sys.stderr)
        sys.exit(1)

    try:
        # Load blended rainfall data using the rfb URL
        rainfall_ds = xr.open_rasterio(rfb_url)
        print("Successfully loaded rainfall data.")
        print("Dataset details:")
        print(rainfall_ds)
    except Exception as e:
        print(f"Error loading rainfall data from {rfb_url}: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
