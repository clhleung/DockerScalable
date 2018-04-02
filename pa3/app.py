from flask import Flask, request, redirect, abort, jsonify, Response, make_response
import ast
import requests
import os
import socket
import json
import math
import random
import json
import operator
import time

app = Flask(__name__)
tupleList = {}
nodeList = []

'''
@app.route("/")
def hello():
        #try:
        #    visits = redis.incr("counter")
        #except RedisError:
        #    visits = "<i>cannot connect to Redis, counter disabled</i>"

        html = "<h3>Hello {name}!</h3>" \
                     "<b>Hostname:</b> {hostname}<br/>" \
                     "<b>Visits:</b> {visits}"
        return html.format(name=os.getenv("NAME", "world"), hostname=socket.gethostname(), visits=visits)
'''

'''
@app.route("/hello",methods=['GET'])
def hello():
        user = request.args.get('name')
        if request.method== 'GET':
             if user is None:
                 return "Hello user!"
             else:
                 return "Hello " + user + "!"

'''

# Update nodeList with VIEW params at start
@app.before_first_request
def storeNodeIps():
  # First batches of nodes are being created
  if os.environ.get('VIEW') is not None:
    ip = os.environ.get('VIEW').split(',')
    for i in range(len(ip)):
      if ip[i] not in nodeList:
        nodeList.append(ip[i])

### Seach nodes for a key, return response
def sendGetRequest(desiredKey):
    # Forwards GET to all active nodes
    for i in range(len(nodeList)):
      if nodeList[i] != os.environ.get('ip_port'): # Prevents node from redirecting to itself
        req = requests.get("http://" + nodeList[i] + "/kvs", data={'key':desiredKey, 'redirect':1})
        if req.status_code == 200: # Key is found
          resp = make_response(req.text, req.status_code, {'Content-Type':'application/json'})
          return resp, req.status_code, req.json()['owner']
        else:
          theValue = tupleList.get(desiredKey) # Search key in dictionary, return value
          if theValue is not None:
            jsonString = jsonify(msg="success", value=theValue, owner=os.environ.get('ip_port'))
            resp = make_response(jsonString, 200, {'Content-Type':'application/json'})
            return resp, 200, os.environ.get('ip_port')
    return None, None, None

@app.route("/kvs/test")
def test():
    return str(nodeList) + '\n' + str(tupleList) + '\n' + str(os.environ.get('ip_port'))

# Allows existing nodes to send their version of view to newly created node
@app.route("/kvs/send_view", methods = ['PUT'])
def receiveView():
    viewList = ast.literal_eval(request.values.get('view'))
    for i in range(len(viewList)):
      if viewList[i] not in nodeList: nodeList.append(viewList[i])

# Test to see number of nodes each container recognizes
@app.route("/kvs/nodeCounter", methods = ['GET'])
def nodeCnter():
    length = len(nodeList)
    jsonString = jsonify(msg="success", length=length)
    resp = make_response(jsonString, 200, {'Content-Type':'application/json'})
    return resp, 200

# Test to check the nodes that are in each container's nodeList
@app.route("/kvs/nodeRan", methods = ['GET'])
def nodeRand():
    randV = random.choice(nodeList)
    jsonString = jsonify(msg="success", thev=randV)
    resp = make_response(jsonString, 200, {'Content-Type':'application/json'})
    return resp, 200

# Method to update Node lists for a container, given a node ip_port to add
@app.route("/kvs/updateNodeList", methods = ['PUT'])
def updateNodeLists():
    theNode = request.values.get('newNode')
    if theNode not in nodeList:
      nodeList.append(theNode)
    jsonString = jsonify(msg="success", length=length)
    resp = make_response(jsonString, 200, {'Content-Type':'application/json'})
    return resp, 200

# Return 1 random dict entry for a particular container
# & remove it from the container
@app.route("/kvs/return_dictEntries", methods = ['GET'])
def getNodeEntries():
    randK,randV = random.choice(list(tupleList.items()))
    tupleList.pop(randK)
    theLength = len(tupleList)
    jsonString = jsonify(theK=randK,theV=randV, theL = theLength)
    resp = make_response(jsonString, 200, {'Content-Type':'application/json'})
    return resp,200

# Created my own insertion method, because the already existing
# one was preventing my code from inserting into the newly inserted node
@app.route("/kvs/insertBalance", methods = ['PUT'])
def insertBalance():
    k = str(request.values.get('key'))
    v = str(request.values.get('value'))
    tupleList.update({k:v})
    jsonString = jsonify(msg="success")
    resp = make_response(jsonString, 200, {'Content-Type':'application/json'})
    return resp,200

# Endpoint for view updates for Node insertions & deletions
@app.route("/kvs/view_update", methods = ['PUT'])
def getInsertDelete():
    def deleteRebalance():
      # Get counts all nodes & take special note of the key count in node to be deleted
      # Take average of all node counts (minus the 1 node container).
      # Redistribute random keys until no keys remain in node about to be deleted
      # Continually add to same node with lowest key until it has at least avg key count
      # If keys still remaining in node to be deleted, continually add to node with next lowest key count
      # keyList = list(tupleList.keys())
      # valueList = list(tupleList.values())
      # for i in range(len(tupleList)):
      #   index = i % len(nodeList)
      #   req = requests.put("http://" + nodeList[index] + "/kvs", data={'key':keyList[i], 'value':valueList[i], 'redirect':1})
      return

    def insertRebalance(desiredPort):
      nodeCnt = {}
      if desiredPort not in nodeList:
        nodeList.append(desiredPort)
      # update nodeList of newly inserted node in kvs
      for i in range(len(nodeList)):
        forwardTo = "http://" + desiredPort + "/kvs/updateNodeLists"
        req = requests.put(forwardTo, data={'newNode':nodeList[i]})
      # update nodeList of every other nodes besides newly inserted node
      for i in range (len(nodeList)):
        if nodeList[i] != os.environ.get('ip_port') and nodeList[i] != desiredPort:
          forwardTo = "http://" + nodeList[i] + "/kvs/updateNodeLists"
          req = requests.put(forwardTo, data={'newNode':desiredPort})
      # Get counts of all nodes and store into dict
      for i in range(len(nodeList)):
       # Ping other containers for their key count
       if nodeList[i] != os.environ.get('ip_port'):
        forwardTo = "http://" + nodeList[i] + "/kvs/get_number_of_keys"
        req = requests.get(forwardTo, data={'redirect':1})
        keyCounter = int(req.json()['count'])
        nodeCnt.update({nodeList[i]:keyCounter})
       else:
        # Record the key count of the node container you're on
        yourIp = os.environ.get('ip_port')
        tupleLength = len(tupleList)
        nodeCnt.update({yourIp:tupleLength})

      # Get average count for nodes
      avgNodes = 0
      for i in range (len(nodeList)):
        avgNodes += nodeCnt.get(nodeList[i] ,0)
      avgNodes = math.floor(avgNodes / len(nodeList))

      # Redistribute nodes until new node has at least avgNodes keys
      newNodeKeys = 0
      # Working up to this point
      while (newNodeKeys < avgNodes) and bool(nodeCnt) != False:
        # Get node with highest key count (choose random, if tied)
        insertKey = max(nodeCnt.iteritems(), key=operator.itemgetter(1))[0]
        # Case where node is not the node you want to insert keys into
        # and is not the node you're currently on
        if insertKey != desiredPort and insertKey != os.environ.get('ip_port'):
          ipp = desiredPort
          numOfNodes = nodeCnt.get(insertKey, 0)
          diffCount = numOfNodes - avgNodes
          theLength = 0
          if diffCount > 0:
            theLength = diffCount
          # Check if we need to transfer nodes for chosen container
          while diffCount > 0:
            forwardTo = "http://" + insertKey + "/kvs/return_dictEntries"
            req = requests.get(forwardTo, data={'avgKeys':avgNodes})
            returnKey = str(req.json()['theK'])
            returnVal = str(req.json()['theV'])
            returnCount = str(req.json()['theL'])
            putKeysAt = "http://" + desiredPort + "/kvs/insertBalance"
            putReq = requests.put(putKeysAt, data={'key':returnKey,'value':returnVal})
            newNodeKeys  += 1
            diffCount -= 1

        # Case where we have to transfer keys to new node from the node
        # we are currently on. No need to ping other nodes
        # & use this container's tupleList
        if insertKey != desiredPort and insertKey == os.environ.get('ip_port'):
          ipp = desiredPort
          numOfNodes = nodeCnt.get(insertKey, 0)
          diffCount = numOfNodes - avgNodes
          theLength = 0
          if diffCount > 0:
            theLength = diffCount
          while diffCount > 0:
            returnK,returnV = random.choice(list(tupleList.items()))
            tupleList.pop(returnK)
            putKeysAt = "http://" + desiredPort + "/kvs/insertBalance"
            putReq = requests.put(putKeysAt, data={'key':returnK,'value':returnV})
            newNodeKeys  += 1
            diffCount -= 1
        # Remove container so we don't have to take away keys from again
        # Also means that container has the average calculated amt of keys
        # or less
        nodeCnt.pop(insertKey)
        # If new nodes needs more keys, we iterate to the node with next highest keyCount
        # within the while loop above, repeat the same process above in while loop
      # Return successfult JSON response
      jsonString = jsonify(msg="success")
      resp = make_response(jsonString, 200, {'Content-Type':'application/json'})
      return resp, 200


    desiredPort = str(request.values.get('ip_port'))
    desiredType = str(request.values.get('type'))
    # If request was a redirect, add / delete
    if request.values.get('redirect') is not None:
      if desiredType == 'add' and desiredPort not in nodeList:
        # Add new node to lists of already existing ports
        nodeList.append(desiredPort)
      elif desiredType == 'remove' and desiredPort in nodeList:
        nodeList.remove(desiredPort)
    # If request was not a redirect, broadcast request to every node
    else:
      for i in range(len(nodeList)):
        if nodeList[i] != os.environ.get('ip_port'):
          forwardTo = "http://" + nodeList[i] + "/kvs/view_update"
          req = requests.put(forwardTo, data={'ip_port':desiredPort, 'type':desiredType, 'redirect':1})
      if desiredType == 'add' and desiredPort not in nodeList:
        nodeList.append(desiredPort)
        req = requests.put("http://" + desiredPort + "/kvs/send_view", data={'view':str(nodeList)})
      elif desiredType == 'remove' and desiredPort in nodeList:
        nodeList.remove(desiredPort)
    # Start of node insertion rebalancing method
    if request.values.get('redirect') is None and desiredType == 'add':
      insertRebalance( desiredPort)
    #if request.values.get('redirect') is not None and desiredType == 'remove':
      #deleteRebalance(os.environ.get('ip_port'))
    jsonString = jsonify(msg="success")
    resp = make_response(jsonString, 200, {'Content-Type':'application/json'})
    return resp, 200

# Endpoint to get number of keys in 1 instance
@app.route("/kvs/get_number_of_keys", methods = ['GET'])
def routeCount():
    # desiredKey = str(request.values.get('key'))
    # if request.method == 'GET' and service == 'get_number_of_keys':
    countNodes = len(tupleList)
    jsonString = jsonify(count=countNodes)
    resp = make_response(jsonString, 200, {'Content-Type':'application/json'})
    return resp, 200

@app.route("/kvs", methods = ['GET', 'PUT', 'DELETE'])
def keyValue():
    # To account for cases where key parameter is passed via url for GET/DEL as
    # specified in the docs
    desiredKey = str(request.values.get('key'))
    desiredValue = str(request.values.get('value'))
    # If given a key parameter via url, we need to check its length so it doesn't exceeed 250
    # char length
    if desiredKey is not None:
      if len(desiredKey) > 250:
        jsonString = jsonify(msg="error", error="key too long")
        resp = make_response(jsonString, 404, {'Content-Type':'application/json'})
        return resp, 404
    theValue = None
    if request.method == 'GET':
      # If request is a redirect from another node, GET key value pair
      if request.values.get('redirect') is not None:
        theValue = tupleList.get(desiredKey) # Search key in dictionary, return value
        if theValue is not None:
          jsonString = jsonify(msg="success", value=theValue, owner=os.environ.get('ip_port'))
          resp = make_response(jsonString, 200, {'Content-Type':'application/json'})
          return resp, 200
      # If request is from a client, redirect request to nodes, return 'success' if some active node has value
      else:
        resp, statusCode, owner = sendGetRequest(desiredKey)
        if statusCode is not None: # Key is found
          return resp, statusCode
      # No keys are found
      jsonString = jsonify(msg="error", error="key does not exist")
      resp = make_response(jsonString, 404, {'Content-Type':'application/json'})
      return resp, 404
    elif request.method == 'PUT':
      # If value does not exist in key value pair
      if desiredValue is None:
        jsonString = jsonify(msg="error")
        resp = make_response(jsonString, 404, {'Content-Type':'application/json'})
        return resp, 404
      # Check if remaining active nodes has key, by sending a GET request to each node
      if request.values.get('redirect') is None: # Prevents deadlocks
        resp, statusCode, owner = sendGetRequest(desiredKey)
        if owner is not None:
          if owner == os.environ.get('ip_port'):
            tupleList.update({desiredKey:desiredValue})
          else:
            req = requests.put("http://" + owner + "/kvs", data={'key':desiredKey, 'value':desiredValue, 'redirect':1})
          jsonString = jsonify(replaced=1, msg="success", owner=owner)
          resp = make_response(jsonString, 200, {'Content-Type':'application/json'})
          return resp, 200
      # If request is a redirect, store key/value pair
      if request.values.get('redirect') is not None: # To prevent deadlocks
        tupleList.update({desiredKey:desiredValue})
        owner = os.environ.get('ip_port')
      # If request is not redirect, query node key count from all nodes, then redirect PUT request
      # to node with lowest key count
      else:
        # Broadcast query to all nodes for their key count
        keyCnt = [] # Store key count of all nodes
        for i in range(len(nodeList)):
          if nodeList[i] != os.environ.get('ip_port'): # Prevents node from redirecting to itself
            req = requests.get("http://" + nodeList[i] + "/kvs/get_number_of_keys")
            keyCnt.append(int(req.json()['count']))
          else:
              keyCnt.append(len(tupleList))
        owner = nodeList[keyCnt.index(min(keyCnt))] # Node that has min
        # If lowest is current node add/update dictionary, otherwise redirect to lowest key count node
        if owner == os.environ.get('ip_port'):
          tupleList.update({desiredKey:desiredValue})
        else:
          req = requests.put("http://" + owner + "/kvs", data={'key':desiredKey, 'value':desiredValue, 'redirect':1})
          resp = make_response(req.text, req.status_code, {'Content-Type':'application/json'})
          return resp, req.status_code
      jsonString = jsonify(replaced=0, msg="success", owner=owner)
      resp = make_response(jsonString, 201, {'Content-Type':'application/json'})
      return resp, 201
    else:
        # If we reach this point, it means user is doing a DELETE request
        # theValue = tupleList.get(desiredKey)
        # Check to make sure we can actually delete something
        # if theValue is not None:
            # tupleList.pop(desiredKey, None)
            # jsonString = jsonify(msg="success")
            # resp = make_response(jsonString, 200)
            # resp.mimetype = "application/json"
            # return resp, 200
        # else:
            # jsonString = jsonify(msg="error", error="key does not exist")
            # resp = make_response(jsonString, 404, {'Content-Type':'application/json'})
            # return resp, 404

        # DELETE DELETE DELETE DELETE DELETE DELETE DELETE Request Requestssssssssssssssssssssssssssssssssssssss
        # Check to make sure we are provided a key to delete
        if desiredKey is None:
          jsonString = jsonify(msg="error")
          resp = make_response(jsonString, 404, {'Content-Type':'application/json'})
          return resp, 404
        # Check if remaining active nodes has key, by sending a GET request to each node
        if request.values.get('redirect') is None: # Prevents deadlocks
          resp, statusCode, owner = sendGetRequest(desiredKey)
          if owner is not None:
            if owner == os.environ.get('ip_port'):
              tupleList.pop(desiredKey, None)
            else:
              req = requests.delete("http://" + owner + "/kvs", data={'key':desiredKey, 'value':desiredValue, 'redirect':1})
            jsonString = jsonify( msg="success", owner=owner)
            resp = make_response(jsonString, 200, {'Content-Type':'application/json'})
            return resp, 200
          else:
            jsonString = jsonify(msg="error",error="key does not exist")
            resp = make_response(jsonString, 404, {'Content-Type':'application/json'})
            return resp, 404
        # If request is a redirect, store key/value pair
        if request.values.get('redirect') is not None: # To prevent deadlocks
          tupleList.pop(desiredKey, None)
          owner = os.environ.get('ip_port')

    jsonString = jsonify( msg="success", owner=owner)
    resp = make_response(jsonString, 201, {'Content-Type':'application/json'})
    return resp, 201

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0', port=8080)
    app.config['JSON_AS_ASCII'] = False
