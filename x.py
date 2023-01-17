def generate_zip_walkbacks(url):

    prefix = ""
    # Temporarily remove http* prefix to avoid interfering with logic that splits on /.
    if url.startswith("https://"):
        prefix = "https://"
        url = url.replace(prefix, "")
    elif url.startswith("http://"):
        prefix = "http://"
        url = url.replace(prefix, "")
        url = url.rstrip("/")

    targets = []

    while True:
        print("URL AT LOOP START=" + url)
        chunks = url.rsplit('/', 1)
        remaining = url.split('/')

        targets.append(url.rstrip("/") + "/")
        targets.append(url + ".zip")

        # Exit loop when there are no more url endpoints or if there are more than 15, to reduce the impact of timeout bombing. 
        if len(remaining) == 1 or len(remaining) > 15:
            break

        if url.endswith("php"):
            temp = url.rstrip("php")
            temp = temp + "zip"
            targets.append(temp)
            
        url = chunks[0]

    # Add http* prefix back to each target.
    for i in range(len(targets)):
        targets[i] = prefix + targets[i]

    return targets

url = "http://ecmglkj-iub-4.ml/login.adobe.com/"

targets = generate_zip_walkbacks(url)

print(targets)