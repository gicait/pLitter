import requests, tqdm, tarfile

url = "http://f70f5de5f5fe.ngrok.io/taladthai"
target_path = 'talad_thai.tar.xz'

response = requests.get(url, stream=True)

file_size = int(response.headers['Content-Length'])
chunk = 1
chunk_size=1024
num_bars = int(file_size / chunk_size)

if response.status_code == 200:
    with open(target_path, 'wb') as fp:
        for chunk in tqdm.tqdm(
                                    response.iter_content(chunk_size=chunk_size)
                                    , total= num_bars
                                    , unit = 'KB'
                                    , desc = target_path
                                    , leave = True # progressbar stays
                                ):
            fp.write(chunk)
    
    tar = tarfile.open(target_path, "r:xz")
    tar.extractall()
    tar.close()