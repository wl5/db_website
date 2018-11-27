import csv
import pdb
import pandas as pd

all_nodes = []
with open('static/node.csv') as node_file:
	node_reader = csv.reader(node_file, delimiter=',')
	next(node_reader)
	for node in node_reader:
		all_nodes.append(node)

all_edges = []
with open('static/edge.csv') as edge_file:
        edge_reader = csv.reader(edge_file, delimiter=',')
        next(edge_reader)
        for edge in edge_reader:
                all_edges.append(edge)

nodes_idx = [n[0] for n in all_nodes]

modified_edges = []
for e in all_edges:
	id1 = nodes_idx.index(e[0])
	id2 = nodes_idx.index(e[1])
	e[0] = str(id1)
	e[1] = str(id2)
	print(e)
	modified_edges.append(e)

df = pd.DataFrame(all_nodes)
df.columns = ["ID"]
df.to_csv("static/node_.csv", header = True, index = False)

df = pd.DataFrame(all_edges)
df.columns = ["source", "target"]
df.to_csv("static/edge_.csv", header = True, index = False)
