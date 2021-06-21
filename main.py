import time
from flask import Flask, request, jsonify, json
import requests, requests_cache
from threading import Thread

app = Flask(__name__)

api_uri = 'https://api.hatchways.io/assessment/blog/posts'
requests_cache.install_cache('api_cache', backend='sqlite', expire_after=100)  # cache all request within 100 seconds

@app.route("/api/ping",methods=['GET'])
def route_1():
    return {"success": True}, 200


@app.route("/api/posts", methods=['GET'])
def route_2():
    tags = request.args.get('tags')
    sortBy = request.args.get('sortBy')
    direction = request.args.get('direction')
    if tags is None:
        return jsonify({"error": "Tags parameter is required"}), 400
    else:
        tags = tags.split(',')  # split string into list
        for i in range(len(tags)):  # remove trailing and preceeding spaces
            tags[i].strip()
            tags[i] = tags[i].lower()

    if sortBy is None:
        sortBy = 'id'
    elif sortBy.lower() not in ['id', 'reads','likes', 'popularity']:
        return jsonify({"error": "sortBy parameter is invalid"}), 400
    else:
        sortBy = sortBy.lower()

    if direction is None:
        direction = 'asc'
    elif direction.lower() not in ['desc','asc']:
        return jsonify({"error": "direction parameter is invalid"}), 400
    else:
        direction = direction.lower()

    result = {}
    json_data = {'posts': []}

    thread_list = []
    for i in range(len(tags)):
        try:
            temp = Thread(target=make_a_api_request,args=(tags[i],json_data,))
            thread_list.append(temp)
        except Exception as e:
            print(e)
            return jsonify({'error': "failed to fetch from api"})

    for thread in thread_list:
        thread.start()
    for thread in thread_list:
        thread.join()

    authorId_set = set()
    id_set = set()
    data_iter = json_data['posts']
    i = 0
    while i< len(data_iter):
        id_checker = data_iter[i]['id']
        authorId_checker = data_iter[i]['authorId']
        if id_checker in id_set and authorId_checker in authorId_set:  # check for duplications and remove them
            data_iter.pop(i)
        else:
            id_set.add(id_checker)
            authorId_set.add(authorId_checker)
            i += 1

    rev = False
    if direction == 'desc':
        rev = True
    data_iter.sort(key=lambda x: x[sortBy], reverse=rev)  # sort the list by sortBy and direction order

    result['posts'] = data_iter

    return jsonify(result), 200


def make_a_api_request(tag, json_data):
    try:
        req = requests.get(api_uri + "?tag=" + tag)
        # checking if requests-cache in used by using from_cache attribute
        now = time.ctime(int(time.time()))
        print("Time: {0} / Used Cache: {1}".format(now, req.from_cache))

        result = json.loads(req.content)
        json_data['posts'] += result['posts']
    except Exception as e:
        print(e)
        return Exception




if __name__ == "__main__":
    app.run(debug=True)