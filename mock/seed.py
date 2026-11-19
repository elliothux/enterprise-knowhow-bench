"""Load frozen finance requests and documents into local ownCloud and Rocket.Chat."""
import argparse
import base64
import hashlib
import json
import os
import re
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

FIXTURES = Path(__file__).resolve().parent / 'finance'


def request(url, method='GET', data=None, headers=None, allowed=()):
    try:
        with urlopen(Request(url, method=method, data=data, headers=headers or {}), timeout=30) as response:
            return response.status, response.read()
    except HTTPError as exc:
        if exc.code in allowed:
            return exc.code, exc.read()
        raise RuntimeError(f'{method} {url} returned HTTP {exc.code}') from exc


def chat(server, endpoint, payload=None, headers=None, allowed=()):
    status, body = request(server+'/api/v1/'+endpoint, 'GET' if payload is None else 'POST',
                           None if payload is None else json.dumps(payload).encode(),
                           {'Content-Type':'application/json', **(headers or {})}, allowed)
    return status, json.loads(body)


def login(server):
    user = os.getenv('BENCH_USER', 'theagentcompany')
    password = os.getenv('BENCH_PASSWORD', 'theagentcompany')
    _, result = chat(server, 'login', {'user':user, 'password':password})
    return {'X-User-Id':result['data']['userId'], 'X-Auth-Token':result['data']['authToken']}


def seed(args, fixtures=None):
    user = os.getenv('BENCH_USER', 'theagentcompany')
    password = os.getenv('BENCH_PASSWORD', 'theagentcompany')
    auth = {'Authorization':'Basic '+base64.b64encode(f'{user}:{password}'.encode()).decode()}
    token = login(args.chat)
    records = []
    folder_prefix = 'Enterprise review ' if not args.namespace else args.namespace+' '
    room_prefix = args.namespace or 'finance-review'
    base = args.cloud+'/remote.php/dav/files/'+quote(user, safe='')+'/Documents'
    request(base, 'MKCOL', headers=auth, allowed=(405,))
    for fixture in (sorted(FIXTURES.iterdir()) if fixtures is None else fixtures):
        if args.case and fixture.name!=args.case:continue
        folder=base+'/'+quote(folder_prefix+fixture.name)
        request(folder, 'MKCOL', headers=auth, allowed=(405,))
        for pdf in sorted(fixture.glob('*.pdf')):
            url=folder+'/'+quote(pdf.name)
            content=pdf.read_bytes()
            status, old=request(url, headers=auth, allowed=(404,))
            if status==404:
                request(url,'PUT',content,{**auth,'If-None-Match':'*','Content-Type':'application/pdf'},(412,))
                _,old=request(url, headers=auth)
            if old!=content:raise ValueError(f'Document differs from frozen fixture: {pdf.name}')
        room=room_prefix+'-'+fixture.name.lower()
        status, info=chat(args.chat, 'groups.info?'+urlencode({'roomName':room}), headers=token, allowed=(400,404))
        if status!=200:
            _,info=chat(args.chat, 'groups.create',{'name':room},token)
        rid=info['group']['_id']
        message=(fixture/'incoming.txt').read_text()
        mid=hashlib.sha256((room+'\n'+message).encode()).hexdigest()[:24]
        status, prior=chat(args.chat, 'chat.getMessage?'+urlencode({'msgId':mid}),headers=token,allowed=(400,404))
        if status!=200:
            _,prior=chat(args.chat, 'chat.sendMessage',{'message':{'_id':mid,'rid':rid,'msg':message}},token)
        if prior['message']['msg']!=message or prior['message']['rid']!=rid:
            raise ValueError(f'Request differs from frozen fixture: {room}')
        records.append(dict(room_id=rid, room=room, seed_id=mid, operator_id=token['X-User-Id'],
                            folder='Documents/'+folder_prefix+fixture.name))
        print(f'{fixture.name}  Documents/{folder_prefix}{fixture.name}  {room}')

    return records


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case',choices=sorted(f.name for f in FIXTURES.iterdir()))
    p.add_argument('--namespace',default='',help='optional separate folder and room prefix')
    p.add_argument('--cloud',default='http://localhost:8092')
    p.add_argument('--chat',default='http://localhost:13000')
    args=p.parse_args()
    if args.namespace and not re.fullmatch(r'[a-z0-9-]{1,35}',args.namespace):p.error('invalid namespace')
    seed(args)
