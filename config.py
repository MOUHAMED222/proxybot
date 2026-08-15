import os

BOT_TOKEN = "8749444386:AAE-AGvGC-cr9Uonsab4SXjwutu-77Jbp9A"

OWNER_IDS: list[int] = [6891530912]

MAX_CHANNELS_PER_USER = 0

PROXY_SOURCES = {
    "http": [
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
        "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt",
    ],
    "https": [
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    ],
    "socks4": [
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks4.txt",
        "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/socks4/data.txt",
    ],
    "socks5": [
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt",
        "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/socks5/data.txt",
    ],
}

PROXYSCRAPE_API = (
    "https://api.proxyscrape.com/v3/free-proxy-list/get"
    "?request=display_proxies&protocol={proto}&timeout=10000&country=all&ssl=all&anonymity=all"
)
PROXYSCRAPE_PROTOCOLS = ["http", "socks4", "socks5"]

GITHUB_SEARCH_QUERIES = [
    "socks5.txt in:path",
    "socks4.txt in:path",
    "http.txt proxy in:path",
    "proxy_list.txt in:path",
]
GITHUB_TOKEN = "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"

GENERATOR_COMMON_PORTS = ["80", "8080", "3128", "8081", "8000", "1080", "4145", "5678", "9999"]

CHECK_URL = "http://httpbin.org/ip"
CHECK_TIMEOUT = 3
MAX_CONCURRENT_CHECKS = 300

GEOIP_API = "http://ip-api.com/json/{ip}?fields=status,countryCode"

AUTO_INTERVAL_HOURS = 3
AUTO_LOOP_TICK_MINUTES = 10
PUBLISH_BATCH_AS_FILE_THRESHOLD = 30

DB_PATH = "proxybot.db"
