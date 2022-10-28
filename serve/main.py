import os, json
import sqlite3
import uvicorn
from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles

app = FastAPI()

cat_ids = [0,1,2,3,4,5,6]

@app.get("/")
async def index():
    with open('/home/cctv/pLitterCCTV/index.html') as fr:
        data = fr.read()
    return Response(content=data, media_type="text/html")

@app.get("/preds")
async def get():
    try:
        with sqlite3.connect("/home/cctv/pLitterCCTV/test.db", isolation_level=None) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM debris")
            data = cur.fetchall()
            return json.loads(json.dumps(data))
    except:
        return {"Response": "error"}

@app.get("/pie")
async def get():
    try:
        with sqlite3.connect("/home/cctv/pLitterCCTV/test.db", isolation_level=None) as conn:
            cur = conn.cursor()
            cur.execute("SELECT cat_id, count(cat_id) FROM debris group by cat_id")
            data = cur.fetchall()
            return data
    except:
        return {"Response": "error"}

@app.get("/daily")
async def get():
    with sqlite3.connect("/home/cctv/pLitterCCTV/test.db", isolation_level=None) as conn:
        #conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        #cur.execute("SELECT cat_id, im_name, count(im_name) FROM debris group by substr(cat_id, 0, 7), im_name")
        #cur.execute("SELECT cat_id, im_name, count(im_name) FROM debris group by substr(cat_id, 0, 8)")
        #cur.execute("SELECT cat_id, im_name, count(im_name) FROM (SELECT im_name, cat_id from debris group by im_name) group by substr(cat_id, 0, 7)")
        #cur.execute("SELECT cat_id, im_name, count(im_name) FROM debris group by substr(cat_id, 0, 7), im_name order by substr(cat_id, 0, 7)")
        #cur.execute("select cat_id, im_name, count(cat_id) from debris group by cat_id")
        #cur.execute("select im_name, count(substr(im_name, 0, 9)) from debris group by substr(im_name, 0, 9)")
        cur.execute("select substr(im_name, 0, 9), cat_id, count(cat_id) from (select cat_id, im_name from debris) group by cat_id, substr(im_name, 0, 9)")
        
        data = cur.fetchall()
        #dd = {}
        data =  {a[0]: {b[1]: {c[2] for c in [y for y in data if y[:2] == b[:2]]} for b in [x for x in data if x[0] == a[0]]} for a in data}
        return data

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000)
