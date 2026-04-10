import os

KHELOMORE_URL = "https://ops.khelomore.com/office/graphql"
# KM_KEY = "Bearer eyJhbGciOiJIUzUxMiJ9.eyJleHAiOjE3NTY2NzQwNzMsInV1aWQiOiJkNzNkMWU2Zi0yNGI1LTQ4MjEtOWYxOS03YmZkYmM4ZTkzMzIiLCJpYXQiOjE3NTQwNDYwNzN9.-hb-vc2HlFGHyGB1ehhOOTmee3a4m0Q_WJ81R3oErurEJTLwQ8bU8ylzda5TwPID2qDr4YXqtalXxpD-x_6sIA"
# KM_COOKIE = "WZRK_G=c67204cae6bb4b019c9a9c42ae9a3bbf; ajs_anonymous_id=1852c5ab-9a94-469b-ba4d-ce0f2ae8b942; mp_2d815128587eeadc1eb7036fbf08a5d3_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A19707a4c7cd249-0e789d026da37b-4c657b58-144000-19707a4c7cd249%22%2C%22%24device_id%22%3A%20%2219707a4c7cd249-0e789d026da37b-4c657b58-144000-19707a4c7cd249%22%2C%22%24search_engine%22%3A%20%22bing%22%2C%22%24initial_referrer%22%3A%20%22https%3A%2F%2Fwww.bing.com%2F%22%2C%22%24initial_referring_domain%22%3A%20%22www.bing.com%22%7D; WZRK_S_TEST-5W7-R5K-Z95Z=%7B%22p%22%3A2%2C%22s%22%3A1754046050%2C%22t%22%3A1754046050%7D"


KM_KEY = os.getenv("KM_KEY", "")
KM_COOKIE = os.getenv("KM_COOKIE", "")

KM_COOKIE="WZRK_G=c67204cae6bb4b019c9a9c42ae9a3bbf; ajs_anonymous_id=1852c5ab-9a94-469b-ba4d-ce0f2ae8b942; mp_2d815128587eeadc1eb7036fbf08a5d3_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A19707a4c7cd249-0e789d026da37b-4c657b58-144000-19707a4c7cd249%22%2C%22%24device_id%22%3A%20%2219707a4c7cd249-0e789d026da37b-4c657b58-144000-19707a4c7cd249%22%2C%22%24search_engine%22%3A%20%22bing%22%2C%22%24initial_referrer%22%3A%20%22https%3A%2F%2Fwww.bing.com%2F%22%2C%22%24initial_referring_domain%22%3A%20%22www.bing.com%22%7D; WZRK_S_4W7-R5K-Z95Z=%7B%22p%22%3A2%7D"
KM_KEY="Bearer eyJhbGciOiJIUzUxMiJ9.eyJleHAiOjE3Nzg0NTAxNDQsInV1aWQiOiIzZTMxYzUyNy1jNzI4LTQyOWUtODMzYS1hYWRkNzRiMGZkNzUiLCJpYXQiOjE3NzU4MjIxNDR9.vdshWnPsqM61W0UOw8ueHZ71EmaSkOuA0DjdBFmV-48sCY7wjFTY9e0aQxjUxZVAI41XMvUSSYunQBp-ocb2tw"



KHELOMORE_HEADERS = {
    "Host": "ops.khelomore.com",
    "Connection": "keep-alive",
    "Content-Length": "1659",
    "sec-ch-ua-platform": "\"Windows\"",
    "authorization": KM_KEY,
    "x-xsrf-token": "null",
    "sec-ch-ua": "\"Microsoft Edge\";v=\"137\", \"Chromium\";v=\"137\", \"Not/A)Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
    "accept": "*/*",
    "content-type": "application/json",
    "Origin": "https://ops.khelomore.com",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://ops.khelomore.com/admin/booking",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
    "Cookie": KM_COOKIE
}

PLAYO_BOOKING_URL = "https://api.playo.io/controller/ppc/booking"
PLAYO_ADD_URL = "https://api.playo.io/controller/ppc/carting/slot/add"
PLAYO_URL = "https://api.playo.io/controller/ppc/availability"
PLAYO_AVAILABILITY = "https://api.playo.io/controller/ppc/availability"
PLAYO_CANCEL_URL = "https://api.playo.io/controller/ppc/booking/cancellation"


# PLAYO_KEY = "4e63d650-7155-11f0-976e-015d6501f000:c3288502-004d-4315-b174-c9d7e1b1efa6"
# PLAYO_COOKIE = "AWSALBAPP-0=_remove_; AWSALBAPP-1=_remove_; AWSALBAPP-2=_remove_; AWSALBAPP-3=_remove_; connect.sid=s%3Ajgh4ZqCmNukXOdjZ4mZy7KIp84EeRpkO.w3vSHFamhuFaoqD9gQ26%2BJSnG6nf6hofGH8HJvneZAA"

PLAYO_KEY = os.getenv("PLAYO_KEY", "")
PLAYO_COOKIE = os.getenv("PLAYO_COOKIE", "")
PLAYO_COOKIE="connect.sid=s%3AJxgaodwFUljWcSxVW3kFSDGHo9tZN6TT.2qmnj2KfeAHYfaoU3Tp5z0Aa528kVqZd47ZNT5QiCKs; AWSALBAPP-0=_remove_; AWSALBAPP-1=_remove_; AWSALBAPP-2=_remove_; AWSALBAPP-3=_remove_"
PLAYO_KEY="271df870-34d5-11f1-9531-d7c0a3b21de7:c3288502-004d-4315-b174-c9d7e1b1efa6"
# DATABASE_URL="postgresql://neondb_owner:npg_lXSIMtk05eHv@ep-bold-wave-adctsiey-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"


PLAYO_HEADERS = {
    "Host": "api.playo.io",
    "Connection": "keep-alive",
    "Content-Length": "106",  # Optional, requests will handle this
    "sec-ch-ua-platform": "\"Windows\"",
    "Authorization": PLAYO_KEY,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
    "Accept": "application/json",
    "sec-ch-ua": "\"Microsoft Edge\";v=\"137\", \"Chromium\";v=\"137\", \"Not/A)Brand\";v=\"24\"",
    "Content-Type": "application/json",
    "sec-ch-ua-mobile": "?0",
    "Origin": "https://dashboard.playo.club",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Storage-Access": "active",
    "Referer": "https://dashboard.playo.club/",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
    "Cookie": PLAYO_COOKIE
}
