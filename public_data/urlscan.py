import sys
import requests
import time
import argparse
import logging

logging.basicConfig(level=logging.INFO)

# requests session
session = requests.Session()

 # urlscan.io
URLSCAN_IO_KEY = 'bee574bb-e575-44e5-9667-ceaf9e59c4b0'

# urlscan.io
def urlscan_sumbit(domain):
    is_public = True
    headers = {
        'Content-Type': 'application/json',
        'API-Key': URLSCAN_IO_KEY,
    }

    if not is_public:
        scan_data = '{"url": "%s"}' % domain
    else:
        scan_data = '{"url": "%s", "public": "on"}' % domain 

    response = session.post('https://urlscan.io/api/v1/scan/', headers=headers, data=scan_data)

    ## end POST request
    r = response.content.decode("utf-8")
    target_uuid = response.json().get('uuid')

    print('[***] urlscan.io: successfully submitted request to the server.[***]')
    time.sleep(5)

    return target_uuid

# print url scan summary
def print_summary(data, target_uuid):
    print('[***] urlscan.io: retrieving the results from the server [***]')
    response = None
    cnt = 0
    while True:
        response = session.get("https://urlscan.io/api/v1/result/%s/" % target_uuid)
        null_response_string = '"status": 404'

        r = response.content.decode("utf-8")
        
        run_success = False
        cnt += 1
        if null_response_string in r:
            logging.warning('urlscan.io: Results not processed. Please check again later.')
            time.sleep(6)
        elif cnt > 3:
            break

    ### relevant aggregate data
    if response:
        content = response.json()
        request_info = content.get("data").get("requests")
        meta_info = content.get("meta")
        verdict_info = content.get("verdicts")
        list_info = content.get("lists")
        stats_info = content.get("stats")
        page_info = content.get("page")
        
        ### more specific data
        geoip_info = meta_info.get("processors").get("geoip") 
        web_apps_info = meta_info.get("processors").get("wappa")
        resource_info = stats_info.get("resourceStats")
        protocol_info = stats_info.get("protocolStats")
        ip_info = stats_info.get("ipStats")

        ### enumerate countries 
        countries = []
        for item in resource_info:
            country_list = item.get("countries")
            for country in country_list:
                if country not in countries:
                    countries.append(country)

        ### enumerate web apps
        web_apps = []
        for app in web_apps_info.get("data"):
            web_apps.append(app.get("app"))
        
        ### enumerate domains pointing to ip
        pointed_domains = []
        for ip in ip_info:
            domain_list = ip.get("domains")
            for domain in domain_list:
                if domain not in pointed_domains:
                    pointed_domains.append(domain)


        ### data for summary
        page_domain = page_info.get("domain")
        page_ip = page_info.get("ip")
        page_country = page_info.get("country")
        page_server = page_info.get("server")
        ads_blocked = stats_info.get("adBlocked")
        https_percentage = stats_info.get("securePercentage")
        ipv6_percentage = stats_info.get("IPv6Percentage")
        country_count = stats_info.get("uniqCountries")
        num_requests = len(request_info)
        is_malicious = verdict_info.get("overall").get("malicious")
        malicious_total = verdict_info.get("engines").get("maliciousTotal")
        ip_addresses = list_info.get("ips")
        urls = list_info.get("urls")

        data['urlscan_domain'] = page_domain
        data['urlscan_ip_address'] = page_ip
        data['urlscan_country'] = page_country
        data['urlscan_server'] = page_server
        data['urlscan_web_apps'] = ';'.join(web_apps)
        data['urlscan_number_of_requests'] = num_requests
        data['urlscan_ads_blocked'] = ads_blocked
        data['urlscan_http_requests'] = str(https_percentage) + "%"
        data['urlscan_ipv6'] = str(ipv6_percentage) + "%"
        data['urlscan_unique_country'] = country_count
        data['urlscan_malicious'] = str(is_malicious)
        data['urlscan_malicious_requests'] = str(malicious_total)
        data['urlscan_pointed_domains'] = ';'.join(pointed_domains)

        
        ### print data
        print("[++] urlscan.io result [++]")
        print("Domain: " + page_domain)
        print("IP Address: " + page_ip)
        print("Country: " + page_country)
        print("Server: " + page_server)
        print("Web Apps: " + str(web_apps))
        print("Number of Requests: " + str(num_requests))
        print("Ads Blocked: " + str(ads_blocked))
        print("HTTPS Requests: " + str(https_percentage) + "%")
        print("IPv6: " + str(ipv6_percentage) + "%")
        print("Unique Country Count: " + str(country_count))
        print("Malicious: " + str(is_malicious))
        print("Malicious Requests: " + str(malicious_total))
        print("Pointed Domains: " + str(pointed_domains))

    return data

def _run_urlscan(domain, data):
    print('[=] urlscan.io [=]')

    target_uuid = urlscan_sumbit(domain)

    data = print_summary(data, target_uuid)

    return data

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--uuid', type=str, required=True, help="Target uuid.")

    uuid = parser.parse_args().uuid
    print_summary({}, uuid)
