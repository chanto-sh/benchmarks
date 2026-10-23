async def fetch_all(urls, fetch, limit=5, retries=2):
    results = []
    for url in urls:
        last = None
        for _ in range(retries + 1):
            try:
                last = await fetch(url)
                break
            except Exception as e:
                last = e
        results.append(last)
    return results
