from django.http import HttpResponse,HttpRequest
from django.shortcuts import redirect
import sys
import os
import random
os.environ["PYWPS_PROCESSES"]=os.path.realpath(os.path.join(os.path.dirname(__file__),"..","processes"))
import pywps
import glob
import threading
import subprocess

def process_status(nm):
    f=open(nm)
    st=f.read()
    iok = st.find("[processsucceeded]")
    istart = st.rfind("Status [processstarted]")
    ifailed = st.rfind("Status [processfailed]")
    if istart>-1:
        line = st[24+istart:].split("\n")[0]
        p = line.split("]")[0]
    else:
        p=0
    if iok>-1:
        return "Done",100.,st
    elif ifailed>-1:
        return "Failed",p,st[ifailed+23:].strip()
    elif istart>-1:
        msg = ":".join(line.split(":")[1:])
        return "Running",p,msg
    else:
        return "Unknown",-1,"???"

def status(request):
    processes = glob.glob("err*.txt")
    done =[]
    running=[]
    unknown = []
    failed=[]
    for nm in sorted(processes):
        id = nm[4:-4]
        status,p,msg = process_status(nm)
        if status == "Done":
            done.append(id)
        elif status == "Failed":
            failed.append([id,p,msg])
        elif status == "Running":
            running.append([id,p,msg])
        else:
            unknown.append(id)
    st="""<h1>Finished Processes</h1>
    <ul>"""
    host = request.get_host()
    for d in done:
        st+="<li><a href='http://%s/view/%s'>%s</a> <a href='http://%s/clear/%s'>clear</a></li>" % (host,d,d,host,d)
    st+="</ul><h1>Runnning Processes</h1><ul>"
    for r in running:
        st+="<li>%s - %s - %s</li>" % (r[0],r[1],r[2])
    st+="</ul><h1>Failed Processes</h1><ul>"
    for f in failed:
        st+="<li>%s (%s %%) -%s<a href='http://%s/clear/%s'>clear</a></li>" % (f[0],f[1],f[2],host,f[0])
    st+="</ul>%s " % processes

    return HttpResponse(st)

def view_process(request,id):
    nm = "out_%s.txt" % id
    if os.path.exists(nm):
        f=open(nm)
        msg = f.read()
    else:
        msg = "Unknown process"
    return HttpResponse(msg)

def clear_process(request,id):
    os.remove("out_%i.txt" % int(id))
    os.remove("err_%i.txt" % int(id))
    return redirect("/status")

def wps(request):
  rndm = random.randint(0,100000000000)
  out = open("out_%i.txt" % rndm, "w")
  err = open("err_%i.txt" % rndm, "w")
  T=threading.Thread(target=run_wps,args=(request,out,err,rndm))
  T.start()
  if request.META["QUERY_STRING"].find("request=Execute")>-1:
      return HttpResponse("Started Request Process id: <a href='%s/view/%i'>%i</a>" % (request.get_host(),rndm,rndm))
  else:
      T.join()
      out = open("out_%i.txt" % rndm)
      st = out.read()
      out.close()
      os.remove("out_%i.txt" % rndm)
      os.remove("err_%i.txt" % rndm)
      return HttpResponse(st)

def run_wps(request,out,err,rndm):

  inputQuery = request.META["QUERY_STRING"]
  P=subprocess.Popen(["wps.py",inputQuery],bufsize=0,stdin=None,stdout=out,stderr=err)
  P.wait()
  out.close()
  err.close()
