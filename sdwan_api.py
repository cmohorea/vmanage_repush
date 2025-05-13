import requests, getpass, os, time 

class sdwan_api:
  def __init__ (self):

    manager = os.environ.get("MANAGER_ADDR")  # or "manager.bell.ca"
    username = os.environ.get("MANAGER_USER") # or input ("Username: ")
    password = os.environ.get("MANAGER_PASS") # or getpass.getpass('Password: ')

    if not (manager or username or password):
      raise SystemExit (f'vManage credentials not provided')

    self.base_url = f"https://{manager}"
    self.base_api_url = self.base_url + "/dataservice"
    self.session = requests.Session ()

    # Disable TLS certificate warnings: do it for testing only
    requests.packages.urllib3.disable_warnings()
    self.session.verify = False

    if not self.login (username, password):
      raise SystemExit (f'Login to {self.base_url} failed, exiting...')

# --------------------------------------------------------------------------------------
  def get_name (self):
    return self.fabric_name

# --------------------------------------------------------------------------------------
  def login (self, username, password):
    login_url = self.base_url + "/j_security_check"
    token_url = self.base_api_url + "/client/token?json=true"
    login_data = {"j_username": username, "j_password": password}

    try:
      response = self.session.post(url=login_url, data=login_data, timeout=10, verify=False)

      # If authenticated, the response code is 200 and body is empty. 
      # If not, the response body contains a html login page
      if response.status_code != 200 or response.text:
        print ("Erorr: Authentication Error")
        return False
    except Exception as e:
      print(f"Error: Authentication network error: {e}")
      return False


    # session object contains the JSESSIONID cookie
    response = self.session.get(url=token_url, verify=False)
    response.raise_for_status ()

    try:
      self.session.headers['X-XSRF-TOKEN'] = response.json()['token']
      return True
    except:
      print ("Error obtaining XSRF Token")
      return False

    # session object contains the JSESSIONID cookie
    try:
      response = self.session.get(url=token_url, timeout=10, verify=False)
      if response.status_code != 200:
          print(f"HTTP {response.status_code} obtaining XSRF Token")
          return False

      self.session.headers['X-XSRF-TOKEN'] = response.json()['token']
      return True

    except: # exception on API call OR on .json()['token']
      print ("Error: Unable to obtain the Auth Token")
      return False

# --------------------------------------------------------------------------------------
  def logout (self):
    url = self.base_url + "/logout"

    # use "GET" action in versions <20.12, "POST" in 20.12+
    # response = self.session.get (url)
    response = self.session.post (url, {'nocache': str(time.time_ns())} )
    response.raise_for_status()

# --------------------------- Actual API call ------------------------------------------
  def api_action (self, method, url, payload = {}):
    """ Suitable only for API calls that return JSON structures """

    try:
        response = self.session.request(method=method, url=url, json=payload, timeout=10, verify=False)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"SD-WAN API: {method} request failed for {url} - {e}")
        return False

# --------------------------------------------------------------------------------------
  def api_GET (self, path):
    response = self.api_action ("GET", self.base_api_url + path)
    return response

  def api_POST (self, path, payload):
    response = self.api_action ("POST", self.base_api_url+path, payload)
    return response

  def api_PUT (self, path, payload):
    response = self.api_action ("PUT", self.base_api_url+path, payload)
    return response

  def api_DELETE (self, path):
    response = self.api_action ("DELETE", self.base_api_url + path)
    return response
  