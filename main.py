from typing import Optional
from pydantic import BaseModel

from fastapi import FastAPI, Request,Form,HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse,JSONResponse
from fastapi.staticfiles import StaticFiles


import pymongo 


app = FastAPI()


myclient = pymongo.MongoClient("YOUR_MONGO_DB_URI")
db = myclient['bbs']

# exception class
class UnicornException(Exception):
    def __init__(self, name: str):
        self.name = name

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")


# exception
@app.exception_handler(UnicornException)
async def unicorn_exception_handler(request: Request, exc: UnicornException):
    return JSONResponse(
        status_code=404,
        content={"message": f"Oops! {exc.name} did something. There goes a rainbow...",},
    )



@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/allcus", response_class=HTMLResponse)
async def allcus(request: Request):
    col = db['bbsclients']
    data=list(col.find())
    return templates.TemplateResponse("customer.html", {"request": request,'data':data})


@app.post('/trans',response_class = HTMLResponse)
async def trans(request:Request,sname: str = Form(...), rname: str = Form(...),amnt: int = Form(...)):
    col = db['bbsclients']
    holder = col.find_one({'name':sname})

    # insufficient bal
    if amnt>int(holder['balance']):
        data=list(col.find())
        message = {
        'mess':'Insufficiant balance in holder Acc.',
        'status' : 'danger',
        'label' : 'Danger',
        'ref' : '#exclamation-triangle-fill'
        }
        return templates.TemplateResponse("customer.html", {"request": request,'data':data,'message':message})

    # success transaction
    message = {
        'mess':'Successfully transfered',
        'status' : 'success',
        'label' : 'Success',
        'ref' : '#check-circle-fill'
        }
    # update sender bal
    query = {'name':sname}
    updatebal = { "$set": { "balance": int(holder['balance'])-amnt } }
    col.update_one(query,updatebal)

    # reciver balance update
    query = {'id':rname}
    reciver = col.find_one(query)
    print(rname,reciver)
    updatebal = { "$set": { "balance": int(reciver['balance'])+amnt } }
    col.update_one(query,updatebal)

    # grab updated bal
    data=list(col.find())

    # save transaction history in bbstrans
    col = db['bbstrans']
    trans =  {'sender':sname, 'reciver':reciver['name'],'amnt':amnt}
    col.insert_one(trans)
    return templates.TemplateResponse("customer.html", {"request": request,'data':data,'message':message})

@app.get("/trans/{cid}", response_class=HTMLResponse)
async def trans(request: Request,cid:str):
    col = db['bbsclients']
    data=list(col.find({'id':{'$ne':cid}}))
    holder = col.find_one({'id':cid})
    return templates.TemplateResponse("trans.html", {"request": request,'data':data,'holder' : holder})


# transaction History

@app.get("/trans-his", response_class=HTMLResponse)
async def his(request: Request):
    col = db['bbstrans']
    data=list(col.find())
    return templates.TemplateResponse("tranhis.html", {"request": request,'data':data})