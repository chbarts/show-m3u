#!/usr/bin/python3

import re
import os
import sys
import argparse
import subprocess

import tkinter as tk
from tkinter import ttk

def parseM3U(inf):
    res = []
    item = {}
    title = ""
    for line in inf:
        line = line.rstrip()
        if re.match("#EXTM3U", line):
            continue
        elif re.match("#EXTINF.+", line):
            tagarr = re.findall("([-0-9A-Za-z]+)=\"?([^\"]*)\"?", line)
            tags = {}
            if len(tagarr) > 0:
                title = re.split("([-0-9A-Za-z]+)=\"?([^\"]*)\"?", line)[-1]
                for key, value in tagarr:
                    tags[key] = value
            else:
                title = re.split(":\\S+\\s", line)[-1]
            tgrp = re.match(",(.+)", title)
            if tgrp:
                title = tgrp.groups()[0]
            item[title] = {"tags": tags}
        elif re.match("#.+:.+", line):
            tags = item[title]["tags"]
            tagarr = re.findall("([-0-9A-Za-z]+)=\"?([^\"]+)\"?", line)
            for key, value in tagarr:
                tags[key] = value
            item[title]["tags"] = tags
        else:
            item[title]["location"] = line
            res.append(item)
            item = {}
    return res


root = tk.Tk()
root.title("Show M3U")

treeview = ttk.Treeview(root)
treeview.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)

items = {}

def printValue(id):
    if id in items:
        print("Now Playing")
        val = items[id]
        title = list(val)[0]
        location = val[title]["location"]
        print(title)
        print(location)
        referer = ""
        if "http-referrer" in val[title]["tags"].keys():
            referer = val[title]["tags"]["http-referrer"]
        for key, value in val[title]["tags"].items():
            print("{} = {}".format(key, value))
        print("%")
        # subprocess.Popen(["mpv","https://rpn.bozztv.com/gusa/gusa-tvsmystery/index.m3u8"])
        if len(referer) > 0:
            subprocess.Popen(["mpv", "--force-window=yes", "--referrer={}".format(referer), location])
        else:
            subprocess.Popen(["mpv", "--force-window=yes", location])

def itemClicked(event):
    id = treeview.identify_row(event.y)
    printValue(id)

def itemKeypress(event):
    id = treeview.focus()
    printValue(id)

treeview.bind("<Button-1>", itemClicked)
treeview.bind("<Key-Return>", itemKeypress)

parser = argparse.ArgumentParser(description='Play M3U File From GUI')

parser.add_argument('-i', '--input', metavar='INFILE', type=str, nargs='+', default='', help='Specify INFILE as M3U input file or files, defaults to one playlist on stdin')

args = parser.parse_args()

def addPlaylist(fnam):
    res = {}
    with open(fnam, 'r') as inf:
        res = parseM3U(inf)
    root_item = treeview.insert("", "end", text=fnam)
    for val in res:
        title = list(val)[0]
        item = treeview.insert(root_item, "end", text=title)
        items[item] = val

if len(args.input) > 0:
    for fnam in args.input:
        addPlaylist(fnam)
else:
    res = parseM3U(sys.stdin)
    root_item = treeview.insert("", "end", text="stdin")
    for val in res:
        title = list(val)[0]
        item = treeview.insert(root_item, "end", text=title)
        items[item] = val


root.mainloop()
