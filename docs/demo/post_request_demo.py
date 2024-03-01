import json
from pathlib import Path
from pprint import pprint

import requests

# Note you have to change url if you change any default settings.
url = "http://localhost:8000"

if __name__ == "__main__":
    settings_main = {"skip_extracted_files": False, "store_to_file": False}

    input_folder = Path(__file__).resolve().parent / "input"
    output_folder = Path(__file__).resolve().parent / "output"

    real_file = False
    input_file_path_main = None
    while not real_file:
        file_name = input(f"What is the file name you want to extract? (Folder is {input_folder})")
        input_file_path_main = input_folder / file_name
        real_file = input_file_path_main.is_file()
        if not real_file:
            print("The input file can't be found. Please recheck and enter a valid file.")

    if real_file and input_file_path_main is not None:
        output_file_path_main = output_folder / input_file_path_main.with_suffix(".json").name

        server_live_check = requests.get(f"{url}/liveness", proxies={"http": "", "https": ""})
        if server_live_check.status_code == 200:
            file = {"file": open(str(input_file_path_main), "rb")}
            response = requests.post(f"{url}/extract", files=file, proxies={"http": "", "https": ""})
            if response.status_code == 200:
                response_dict = json.loads(response.content)
                extraction_dict = response_dict["dictionary"]
                print(f"We store output to {output_file_path_main}.")
                pprint(extraction_dict)
                with open(str(output_file_path_main), "w") as f:
                    json.dump(extraction_dict, f)
