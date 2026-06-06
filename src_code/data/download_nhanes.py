import urllib.request
import os
import pandas as pd

CDC_BASE_URL_J = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/"

FILES_J = [
    "DEMO_J.xpt", "BMX_J.xpt", "GLU_J.xpt", "INS_J.xpt", 
    "TRIGLY_J.xpt", "HDL_J.xpt", "BIOPRO_J.xpt", "CBC_J.xpt", 
    "LUX_J.xpt", "DXX_J.xpt"
]

ADDITIONAL_CYCLES = {
    "LUX_K.XPT": "https://wwwn.cdc.gov/nchs/nhanes/2019-2020/LUX_K.XPT",
    "DEMO_K.XPT": "https://wwwn.cdc.gov/nchs/nhanes/2019-2020/DEMO_K.XPT",
    "BMX_K.XPT":  "https://wwwn.cdc.gov/nchs/nhanes/2019-2020/BMX_K.XPT",
    "BIOPRO_K.XPT": "https://wwwn.cdc.gov/nchs/nhanes/2019-2020/BIOPRO_K.XPT",
    "GLU_K.XPT":  "https://wwwn.cdc.gov/nchs/nhanes/2019-2020/GLU_K.XPT",
    "INS_K.XPT":  "https://wwwn.cdc.gov/nchs/nhanes/2019-2020/INS_K.XPT",
    "TRIGLY_K.XPT": "https://wwwn.cdc.gov/nchs/nhanes/2019-2020/TRIGLY_K.XPT",
    "HDL_K.XPT":  "https://wwwn.cdc.gov/nchs/nhanes/2019-2020/HDL_K.XPT",
    "DXX_K.XPT": "https://wwwn.cdc.gov/nchs/nhanes/2019-2020/DXX_K.XPT"
}

def download_and_merge(output_path="raw_nhanes_merged.csv"):
    raw_dir = os.path.join(os.path.dirname(__file__), "raw_data")
    os.makedirs(raw_dir, exist_ok=True)
    
    # Process J Cycle
    df_merged_j = None
    for filename in FILES_J:
        url = CDC_BASE_URL_J + filename
        local_path = os.path.join(raw_dir, filename)
        if not os.path.exists(local_path):
            print(f"Downloading {url}...")
            # Use requests if urllib fails due to user agent, but urllib usually works for actual files on CDC
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response, open(local_path, 'wb') as out_file:
                out_file.write(response.read())
            
        print(f"Reading {local_path}...")
        df_temp = pd.read_sas(local_path)
        if df_merged_j is None:
            df_merged_j = df_temp
        else:
            df_merged_j = pd.merge(df_merged_j, df_temp, on="SEQN", how="outer")
            
    df_merged_j['cycle'] = 'J'

    # Process K Cycle
    df_merged_k = None
    for filename, url in ADDITIONAL_CYCLES.items():
        local_path = os.path.join(raw_dir, filename)
        if not os.path.exists(local_path):
            print(f"Downloading {url}...")
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response, open(local_path, 'wb') as out_file:
                    out_file.write(response.read())
            except Exception as e:
                print(f"Failed to download {filename}: {e}")
                continue
                
        if os.path.exists(local_path):
            print(f"Reading {local_path}...")
            df_temp = pd.read_sas(local_path)
            if df_merged_k is None:
                df_merged_k = df_temp
            else:
                df_merged_k = pd.merge(df_merged_k, df_temp, on="SEQN", how="outer")

    if df_merged_k is not None:
        df_merged_k['cycle'] = 'K'
        df_merged = pd.concat([df_merged_j, df_merged_k], ignore_index=True)
    else:
        df_merged = df_merged_j

    output_full = os.path.join(os.path.dirname(__file__), output_path)
    print(f"Saving merged dataset to {output_full}...")
    df_merged.to_csv(output_full, index=False)
    print("Done!")

if __name__ == "__main__":
    download_and_merge()
