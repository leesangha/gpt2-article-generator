import os
import io
import uuid
import shutil
import sys

import json
import tensorflow as tf

from flask import Flask, render_template, flash, send_file, request, jsonify, url_for
import numpy as np
from werkzeug.utils import secure_filename

from queue import Empty,Queue
import threading
import time
from generator import Generator

###################
requests_queue=Queue()
BATCH_SIZE = 1
CHECK_INTERVAL = 0.1
###################
def run(title, initial_content):
    gen=Generator.get_instance()
    result=gen.generate(title,initial_content)
    return result

#Queueing
def handle_requests_by_batch():
    try:
        while True:
            requests_batch=[]
            while not(len(requests_batch) >= BATCH_SIZE):
                try:
                    requests_batch.append(
                        requests_queue.get(timeout=CHECK_INTERVAL)
                    )
                except Empty:
                    continue
        
            batch_outputs=[]

            for request in requests_batch:
                batch_outputs.append(
                 run(request["input"][0],request["input"][1])
                )
            
            for request, output in zip(requests_batch,batch_outputs):
                request["output"]=output

    except Exception as e:
        while not requests_queue.empty():
            requests_queue.get()
        print(e)

#Thread Start
threading.Thread(target=handle_requests_by_batch).start()

app = Flask(__name__, template_folder="templates", static_url_path="/static")

@app.route("/")
def main():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    try:
        if requests_queue.qsize() >=1:
            return jsonify({"message":"Too Many Requests"}),429
        
        text=request.form["message"]
        initial_content=request.form["initial_content"]
        req={"input":[text,initial_content]}
        requests_queue.put(req)

        #Thread output response
        while "output" not in req:
            time.sleep(CHECK_INTERVAL)

        if req["output"] == 500:
            return jsonify({"error": "Error output is something wrong"}), 500
        #status=0
        result=req["output"]
        
        return jsonify({"message": result,"title":text,"subtitle":initial_content}), 200

    except Exception as e:
        print(e)

        return jsonify({"message": e}), 400



@app.route("/health")
def health():
    return res.sendStatus(200)


if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=80)
