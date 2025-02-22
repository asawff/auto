from http.server import BaseHTTPRequestHandler, HTTPServer , SimpleHTTPRequestHandler
from urllib.parse import urlparse,parse_qs
import json
import urllib
import urllib.parse
import urllib.request
import requests
import threading

######## http server #######
class HttpBaseHandler(BaseHTTPRequestHandler):
    regist_handler = {"/":lambda x:{"msg":"This is HttpBaseHandler,please inheritance it and override regist_handler"}}
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # GET
    def do_GET(self):
        content = '{}'
        ret_code = 404
        querypath = urlparse(self.path)
        if querypath.path  in self.regist_handler.keys():
            query_args = parse_qs(querypath.query)
            hand_args = {}
            for key in query_args.keys():
                hand_args[key] = query_args.get(key)[0]
            resp = self.regist_handler[querypath.path](hand_args)
            content = json.dumps(resp)
            ret_code = 200

        content = content.encode("utf-8")
        self.send_response(ret_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(content)



def __start_http(my_handler,port):
    print('starting server, port', port)
    # Server settings
    server_address = ('', port)
    httpd = HTTPServer(server_address, my_handler)
    print('running server...')
    httpd.serve_forever()

def start_http_server(my_handler = HttpBaseHandler,port = 8000):
    thd = threading.Thread(target=__start_http,args=[my_handler,port])
    thd.start()
    return thd



######## http client #######
def http_get(url, params=None, add_to_headers=None):
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36',
    }
    if add_to_headers:
        headers.update(add_to_headers)
    if type(params) != type(None):
        postdata = urllib.parse.urlencode(params)
    else:
        postdata = ""
    response = requests.get(url, postdata, headers=headers, timeout=5)
    try:

        if response.status_code == 200:
            return response.json()
        else:
            return
    except BaseException as e:
        print("httpGet failed, detail is:%s,%s" % (response.text, e))
        return



def http_post(url, params, add_to_headers=None):
    headers = {
        'Content-Type': 'application/json'
    }
    if add_to_headers:
        headers.update(add_to_headers)
    postdata = json.dumps(params)
    response = requests.post(url, postdata, headers=headers, timeout=10)
    try:

        if response.status_code == 200:
            return response.json()
        else:
            return
    except BaseException as e:
        print("httpPost failed, detail is:%s,%s" % (response.text, e))
        return