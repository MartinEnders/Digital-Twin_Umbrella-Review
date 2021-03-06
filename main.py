import streamlit as st
st.set_page_config(layout='wide',initial_sidebar_state='expanded')

import markdown
from pprint import pprint
from bs4 import BeautifulSoup

import networkx as nx
from networkx.drawing.nx_pydot import write_dot
import io

import collections
import textwrap
import math

#from ipywidgets import interact, interactive, fixed, interact_manual
#import ipywidgets as widgets

def read_markdown_file():
    with open("140.1-Literature-Review-of-Reviews-Systematic.md", 'r', encoding='utf-8') as mdin:
        html_doc = markdown.markdown(mdin.read(), tab_length=2)

    soup = BeautifulSoup(html_doc, 'html.parser')
    return soup

def dictify(ul):
    """Source: https://stackoverflow.com/a/17850788/14631138"""
    result = collections.OrderedDict()
    for li in ul.find_all("li", recursive=False):
        key = next(li.stripped_strings)
        ul = li.find("ul")
        if ul:
            result[key] = dictify(ul)
        else:
            result[key] = None
    return result

def get_review_dict():
    result = {"Digital Twin Umbrella Review" : dictify(read_markdown_file().ul)}
    return result

## MERGED CELLS ### 



def iterdict(d, G, depth=0, pos=0, parent=0, stop_depth=None, show_sources=True, show_selected_branch=None,year_range=[2000,2100]):
    for i, (k,v) in enumerate(d.items()):
        # show only one branch
        # branch is false show everything
        if depth == 1 and len(show_selected_branch) and 'Show All' not in show_selected_branch and k not in show_selected_branch:
            continue
        
        # Create Node-ID
        node_id = f"{parent}-{depth}{pos}{i}"
        
        # Create Labels for Nodes
        label_lines = k.split("\n")
        references_raw = label_lines[1:]
        references = []
        
        # Filter References by year
        for r in references_raw:
            ref_year = int(r[r.find("[")+1 : r.find("]")][-11:-7])
            #print(r, ref_year, year_range, list(range(*year_range)), type(year_range))
            if ref_year in range(*year_range):
                #print("ADD", r)
                references.append(r)
        
        if references and show_sources:
            ref_string = "<br align='left'/>".join(["<br align='left'/>".join(textwrap.wrap(x, subsequent_indent="   ")) for x in references])
            #ref_string = "<br align='left'/>".join(textwrap.wrap(ref_string))
            references_html = f"<font point-size='8'>{ref_string}</font><br align='left'/>"
        elif references and not show_sources:
            references_html = f"<font point-size='7'>[Count: {len(references)}]</font><br align='left'/>"
        else:
            references_html = ""
        
        label = f"<{label_lines[0]} <br align='left'/>{references_html}>"
        #print(label)
                
        # Bulid Tree
        node_color = f"{(pos)/5} {(depth)/10} 0.8"
        node_color = "/set312/{}".format((pos + depth)%12+1)
        G.add_node(node_id, label=label, color=node_color, fillcolor=node_color, style='filled')
        if parent:
            penwidth = 1+int(math.log(1+2*len(references),1.5))
            if references:
                color = 'lightgrey'
            else:
                color = 'black'
            G.add_edge(parent, node_id, color=color, penwidth=penwidth) # "1+" to avoid zero thickness lines and math errors :-)
        if isinstance(v,dict):
            if isinstance(stop_depth, int) and stop_depth == depth:
                pass # stop recursion
            else:
                iterdict(v, G, depth=depth+1, pos=i, parent=node_id, stop_depth=stop_depth, show_sources=show_sources, show_selected_branch=show_selected_branch,year_range=year_range)
    return G        


# @interact(
#     stop_depth=widgets.IntText(min=0, max=30, step=1, value=6, description="Depth"),
#     show_selected_branch=widgets.SelectMultiple(
#         options=['Show All'] + [k for k,v in get_review_dict()['Digital Twin Umbrella Review'].items()],
#         value=['Show All'],
#         rows=17,
#         description='Branches',
#         disabled=False
#     )
# )



def plot_lr_tree(stop_depth=None,renderer=['dot','circo','sfdp', 'neato', 'twopi'],show_sources=True,show_selected_branch=[], year_range=[2000,2100]):
    """
    Based on: https://github.uconn.edu/gist/jet08013/5d008a08da164d7ee67b6be740390c50
    """
    # Add one to include end year
    year_range = (year_range[0], year_range[1] + 1)
    
    G = nx.DiGraph()
    G = iterdict(get_review_dict(), G, stop_depth=stop_depth, show_sources=show_sources, show_selected_branch=show_selected_branch,year_range=year_range)


    G.graph['graph'] = {'rankdir':'LR','nodesep':0.2, 'ranksep':0.2, 'overlap':'false'}
    G.graph['node'] = {'shape':'box',  'fontsize':11, 'margin':0.03, 'width':0, 'height':0, 'fontname': "DejaVu Sans"}

    #A=nx.nx_agraph.to_agraph(G)
    #return A.to_string()

    f = io.StringIO()
    write_dot(G,f)
    f.seek(0)
    return f.read()



st.title("Umbrella Review of Digital Twin Literature Reviews [Work in Progress]")
depth = st.sidebar.slider("Depth of Tree",min_value=0,max_value=10,value=6, step=1)

sources = st.sidebar.checkbox("Show Sources (BibTeX-Keys + comments)")

year_range = list(st.sidebar.slider('Filter Years (show only publications within this time-span)', 2000, 2022, (2000, 2020)))

options = ['Show All'] + [k for k,v in get_review_dict()['Digital Twin Umbrella Review'].items()]
branches = st.sidebar.multiselect("Branches to show", options,default=options[1:4])

st.sidebar.markdown("[Sourcecode at Github](https://github.com/MartinEnders/Digital-Twin_Umbrella-Review)")

#st.write(branches)

st.graphviz_chart(plot_lr_tree(depth, 'dot',sources,branches,year_range))
