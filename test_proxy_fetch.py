import urllib.request, json, sys, requests
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def test_proxies():
    print("Fetching free proxy list from GitHub...")
    # Pull fresh proxies from verified raw list
    url = "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        proxy_list = urllib.request.urlopen(req, timeout=10).read().decode("utf-8").splitlines()
        print(f"Retrieved {len(proxy_list)} candidate HTTP proxies.")
    except Exception as e:
        print(f"Failed to fetch proxy list: {e}")
        return

    v_id = "U03YoHWfJi8"

    for p in proxy_list[:20]:
        p = p.strip()
        if not p: continue
        print(f"Testing proxy {p} ...")
        try:
            proxy_cfg = GenericProxyConfig(http_url=f"http://{p}", https_url=f"http://{p}")
            ytt = YouTubeTranscriptApi(proxy_config=proxy_cfg)
            t = ytt.fetch(v_id)
            text = " ".join([entry.text for entry in t])
            print(f"\n>>> [SUCCESS WITH PROXY {p}!] Fetched {len(text.split())} words! <<<\n")
            return p
        except Exception as e:
            err = str(e).splitlines()[0] if str(e) else type(e).__name__
            print(f"  [Failed]: {err[:65]}")
            
    print("Batch test completed.")

test_proxies()
