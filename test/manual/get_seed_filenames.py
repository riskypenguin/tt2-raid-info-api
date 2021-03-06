from test.utils.make_request import make_request_sync

import requests
from src.model.seed_type import SeedType
from src.stage import Stage

result = make_request_sync(
    method=requests.get,
    path=f"admin/all_seed_filenames/{SeedType.RAW.value}",
    stage=Stage.PRODUCTION)

print("RAW:", result)

result = make_request_sync(
    method=requests.get,
    path=f"admin/all_seed_filenames/{SeedType.ENHANCED.value}",
    stage=Stage.PRODUCTION)

print("ENHANCED:", result)
