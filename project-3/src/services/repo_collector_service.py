import requests
import time
from src.constants.config_constant import HEADERS
from src.constants.url_constant import URL_GIT_HUB_API
from src.constants.limits_constant import MIN_PRS, MAX_REPOS

def get_with_retry(url, headers, retries=10, delay=5, timeout=(20, 60)):
    attempt = 0
    while attempt < retries:
        try:
            res = requests.get(url, headers=headers, timeout=timeout)
            return res
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Tentativa {attempt+1} falhou para URL: {url} ({str(e)}). Retentando em {delay} segundos...")
        attempt += 1
        time.sleep(delay)
    raise Exception(f"Erro: Falha na conexão após {retries} tentativas para URL: {url}")

def get_top_repositories():
    repos_validos = []
    page = 1

    while len(repos_validos) < MAX_REPOS:
        print(f"🔎 Buscando página {page} de repositórios populares...")
        url = f"{URL_GIT_HUB_API}/search/repositories?q=stars:>10000&sort=stars&order=desc&per_page=50&page={page}"
        res = get_with_retry(url, headers=HEADERS)

        if res.status_code != 200:
            print("Erro ao buscar repositórios.")
            break

        items = res.json().get("items", [])
        for repo in items:
            full_name = repo["full_name"]
            if repo_tem_100_prs(full_name):
                print(f"✔️  {full_name} adicionado")
                repos_validos.append(full_name)
            if len(repos_validos) >= MAX_REPOS:
                break

        page += 1
        time.sleep(2)

    return repos_validos

def repo_tem_100_prs(full_name):
    # Limitamos a 1 PR por página para minimizar o payload e evitar timeouts
    url = f"{URL_GIT_HUB_API}/repos/{full_name}/pulls?state=all&per_page=1"
    res = get_with_retry(url, headers=HEADERS, timeout=(30, 60))
    if 'Link' in res.headers:
        links = res.headers['Link'].split(',')
        for link in links:
            if 'rel="last"' in link:
                last_url = link.split(';')[0].strip()[1:-1]
                last_page = int(last_url.split('page=')[-1])
                return last_page >= MIN_PRS  
    return False
