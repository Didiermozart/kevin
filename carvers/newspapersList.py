import re
from bs4 import BeautifulSoup

from datetime import datetime
from urllib.parse import urlparse, urlunparse, quote, unquote


from scraperProxy import *
from newsreader import *

class urls():
    

    YEAR = datetime.now().strftime("%Y")
    MONTH = datetime.now().strftime("%m")

    def __init__(self) -> None:
        articles = list()
        
    web = {
        "interpol" : {
        "interpol notices rouges ":"https://www.interpol.int/fr/Notre-action/Notices/Notices-rouges/Voir-les-notices-rouges",
        },
        "france":{
            "FranceBleu": "https://www.francebleu.fr/infos",
            "FranceInfo": "https://francetvinfo.fr",
            "CERT-FR": "https://www.cert.ssi.gouv.fr/avis/",
            "Le Monde": "https://www.lemonde.fr/pixels/",
            "Parquet de Paris": "https://www.linkedin.com/posts"
        },
        "US":{
            "Cybersecurity Insiders":"https://www.cybersecurity-insiders.com",
        },
        "monde":{
            "TheRecord": "https://www.therecord.media",
        },
        "europe":{
            "Politico CyberSecurity":"https://www.politico.eu/?s=Cybedefense",
        },
        "Cyber":{
            "ASEC":"https://asec.ahnlab.com/en/",
            "HarfangLab":"https://harfanglabs.io/insidethelab/",
            "Zimperium.com": "http://www.zimperium.com/blog/",
            "Tenable":"https://www.tenable.com/security/",
            "Eva":"https://www.evasec.io",
            "fortra":"https://www.fortra.com/security",
            "Help Net Security":"https://helpnetsecurity.com/{YEAR}/{MONTH}/",
            "Computing":"https://www.computing.co.uk",
            "Qualys": "https://blog.qualys.com/",
            "BleepingComputer": "https://www.bleepingcomputer.com/news/security/",
            "Sansec": "https://sansec.io/research/",
            "Promon": "https://promon.co/app-threat-reports/",
            "Dark Reading": "https://www.darkreading.com/",
            "Cado Security": "https://www.cadosecurity.com/blog/",
            "The Hacker News": f"https://thehackernews.com/{YEAR}/{MONTH}/",
            "Cleafy": "https://www.cleafy.com/cleafy-labs/",
            "Google Project Zero": f"https://googleprojectzero.blogspot.com/{YEAR}/{MONTH}/",
            "SC Magazine": "https://www.scmagazine.com/news/",
            "Google Chrome": f"https://chromereleases.googleblog.com/{YEAR}/{MONTH}/",
            "Wordpress": "https://wordpress.org/support/topic/",
            "Wordfence": f"https://www.wordfence.com/blog/{YEAR}/{MONTH}/",
            "GB Hackers": "https://gbhackers.com/",
            "Progress Community": "https://community.progress.com/s/",
            "SentinelOne": "https://www.sentinelone.com/labs/",
            "AnyRun": "https://any.run/cybersecurity-blog/",
            "Mandiant": "https://cloud.google.com/blog/topics/threat-intelligence/?hl=en",
            "CVE News": "https://www.cve.org/Media/News/AllNews",
            "OpenSource Vuln Database": "http://osv.dev/blog/"
        },
        "blogs":{
            "Krebs on Security": "https://krebsonsecurity.com/",
            "Schneier on Security": "https://www.schneier.com/",
            "The Hacker News": "https://thehackernews.com/",
            "Graham Cluley": "https://grahamcluley.com/",
            "CSO Online": "https://www.csoonline.com/",
            "We Live Security": "https://www.welivesecurity.com/",
            "Infosecurity Magazine": "https://www.infosecurity-magazine.com/",
            "Threatpost": "https://threatpost.com/",
            "Troy Hunt": "https://www.troyhunt.com/",
            "Security Affairs": "https://securityaffairs.com/",
            "CyberScoop": "https://www.cyberscoop.com/",
            "Naked Security": "https://nakedsecurity.sophos.com/",
            "The Last Watchdog": "https://www.lastwatchdog.com/",
            "ZDNet Security": "https://www.zdnet.com/topic/security/",
            "Malwarebytes Labs": "https://blog.malwarebytes.com/",
            "Bleeping Computer": "https://www.bleepingcomputer.com/",
            "Cyber Security Review": "https://www.cybersecurity-review.com/",
            "IT Security Guru": "https://www.itsecurityguru.org/",
            "Security Week": "https://www.securityweek.com/",
            "Virus Bulletin": "https://www.virusbulletin.com/",
            "Malware Traffic Analysis": "https://www.malware-traffic-analysis.net/",
            "Malware Analysis Tutorials": "https://fumalwareanalysis.blogspot.com/",
            "Malware Analysis For Hedgehogs": "https://www.malwareanalysisforhedgehogs.com/",
            "Malware Unicorn": "https://malwareunicorn.org/",
            "Hybrid Analysis": "https://www.hybrid-analysis.com/",
            "Any.Run": "https://any.run/",
            "VirusTotal Blog": "https://blog.virustotal.com/",
            "Zeltser Security": "https://zeltser.com/",
            "SANS Internet Storm Center": "https://isc.sans.edu/",
            "Talos Intelligence": "https://blog.talosintelligence.com/",
            "Kaspersky Securelist": "https://securelist.com/",
            "FireEye Threat Research": "https://www.fireeye.com/blog/threat-research.html",
            "Palo Alto Networks Unit 42": "https://unit42.paloaltonetworks.com/",
            "Recorded Future Blog": "https://www.recordedfuture.com/blog/",
            "Cybereason Blog": "https://www.cybereason.com/blog",
            "McAfee Labs Blog": "https://www.mcafee.com/blogs/",
            "Trend Micro Research": "https://www.trendmicro.com/en_us/research.html",
            "Crowdstrike Blog": "https://www.crowdstrike.com/blog/"
            },
    }

    def canonicalize_url(self, url: str) -> str:
        # Parse the URL into components
        parsed_url = urlparse(url)

        # Convert the hostname to lowercase
        netloc = parsed_url.netloc.lower()

        # Remove the default port for HTTP and HTTPS
        if netloc.endswith(':80') and parsed_url.scheme == 'http':
            netloc = netloc[:-3]
        elif netloc.endswith(':443') and parsed_url.scheme == 'https':
            netloc = netloc[:-4]

        # Normalize the path by unquoting and quoting again to remove unnecessary escapes
        path = quote(unquote(parsed_url.path))

        # Remove the trailing slash from the path, unless it's the root path
        if path != '/' and path.endswith('/'):
            path = path[:-1]

        # Reassemble the URL with the normalized components
        canonical_url = urlunparse((
            parsed_url.scheme,
            netloc,
            path,
            parsed_url.params,
            parsed_url.query,
            parsed_url.fragment
        ))

        return canonical_url


    def downlowd_rootpage(self):
        proxy = Proxy()
        for category in urls.web:
            for site in urls.web[category]:
                url = self.canonicalize_url(urls.web[category][site])
                proxy.get(url)
    
    def get_articles(self):
        for category in urls.web:
            for site in urls.web[category]:
                print("URL :", site)
                url = self.canonicalize_url(urls.web[category][site])
                s = newspaper.build(url)
                for article in s.articles:
                    try:
                        html = proxy.get(article.url)
                        if html is None:
                            raise Exception
                        
                        article.download(input_html=html)
                        print(article.url)
                        article.parse()
                        article.nlp()
                        urls = self.get_articles_urls(html)
                        hashes = self.get_article_hashes(html)
                        article_data = {
                            'url': article.url,
                            'publish_date': str(article.publish_date),  # Convert to string if not None
                            'authors': article.authors,      
                            # 'text': article.text,
                            'top_image': article.top_image,
                            'movies': article.movies,
                            'title': article.title,
                            'summary': article.summary,
                            'keywords': article.keywords,
                            'urls': urls,
                            'hashes': hashes
                        }
                        logger.info(f" {article.publish_date} article keywords {article.keywords}")
                    except:
                        logger.warning(f"error downloading url {article.url}")
                    

    def get_articles_urls(self, html) -> list:
        url_list = list()
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a', attrs={'href': re.compile("^https://")}): 
            url_list.append(link.get('href')) 
        return url_list

    def get_article_CVE(self, text):
        cve_pattern = r'CVE-\d{4}-\d{4,7}'
        cves = re.findall(cve_pattern, text)
        cves = list(dict.fromkeys(cves))
        return cves
    
    def get_article_hashes(text):
        md5_regex = r'\b[a-fA-F0-9]{32}\b'
        sha1_regex = r'\b[a-fA-F0-9]{40}\b'
        sha256_regex = r'\b[a-fA-F0-9]{64}\b'
        
        # Finding all matches
        md5_hashes = re.findall(md5_regex, text)
        sha1_hashes = re.findall(sha1_regex, text)
        sha256_hashes = re.findall(sha256_regex, text)
        
        # Getting distinct hashes
        distinct_md5_hashes = set(md5_hashes)
        distinct_sha1_hashes = set(sha1_hashes)
        distinct_sha256_hashes = set(sha256_hashes)
        
        return {"md5":distinct_md5_hashes, "sha1": distinct_sha1_hashes, "sha256":distinct_sha256_hashes}


# catalog = urls()
# catalog.downlowd_rootpage()
# catalog.get_articles()
