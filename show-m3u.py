#!/usr/bin/python3

import re
import os
import sys
import json
import argparse
import subprocess

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

COMMAND="mpv"
REFERRER="--referrer={}"
ARGS="--force-window=yes"
SOURCE="{}"

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
        print(val)
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
            subprocess.Popen([COMMAND, ARGS, REFERRER.format(referer), SOURCE.format(location)])
        else:
            subprocess.Popen([COMMAND, ARGS, SOURCE.format(location)])

def itemClicked(event):
    id = treeview.identify_row(event.y)
    printValue(id)

def itemKeypress(event):
    id = treeview.focus()
    printValue(id)
        

treeview.bind("<Button-1>", itemClicked)
treeview.bind("<Key-Return>", itemKeypress)

parser = argparse.ArgumentParser(description='Play M3U File From GUI')

parser.add_argument('-i', '--input', metavar='INFILE', type=str, nargs='+', default='', help='Specify INFILE as M3U input file or files')
parser.add_argument('-l', '--list', metavar='INFILE', type=str, nargs=1, default='', help='Specify INFILE as list of M3U files')
parser.add_argument('-c', '--command', metavar='COMMAND', type=str, nargs=1, default='', help='Specify the program name to use to play the media')
parser.add_argument('-a', '--args', metavar='ARGS', type=str, nargs=1, default='', help='Specify the other arguments needed, as one string')
parser.add_argument('-r', '--referrer', metavar='REFERRER', type=str, nargs=1, default='', help='Specify how to get the player to send the HTTP REFERER header, if needed, as Python format string')
parser.add_argument('-s', '--source', metavar='SOURCE', type=str, nargs=1, default='', help='Specify how to pass the source into the player, as Python format string')

args = parser.parse_args()

if len(args.command) > 0:
    COMMAND = args.command[0]
if len(args.args) > 0:
    ARGS = args.args[0]
if len(args.referrer) > 0:
    REFERRER = args.referrer[0]
if len(args.source) > 0:
    SOURCE = args.source[0]

dumpres = {}

def rightClicked(event):
    id = treeview.identify_row(event.y)
    if id in treeview.get_children():
        root_item = treeview.item(id)
        loc = root_item['text']
        res = {}
        with open(loc, 'r') as inf:
            res = parseM3U(inf)
        for cid in treeview.get_children(id):
            treeview.delete(cid)
        dumpres[loc] = res
        for val in res:
            title = list(val)[0]
            item = treeview.insert(id, "end", text=title)
            items[item] = val

treeview.bind("<Button-2>", rightClicked)
treeview.bind("<Button-3>", rightClicked)

def addPlaylist(fnam):
    res = {}
    with open(fnam, 'r') as inf:
        res = parseM3U(inf)
    root_item = treeview.insert("", "end", text=fnam)
    dumpres[fnam] = res
    for val in res:
        title = list(val)[0]
        item = treeview.insert(root_item, "end", text=title)
        items[item] = val

def openFile():
    fnams = filedialog.askopenfilename(multiple=True, filetypes=[("M3U", "*.m3u")])
    if fnams:
        for fnam in fnams:
            addPlaylist(fnam)

def openList():
    fnam = filedialog.askopenfilename()
    if not fnam:
        return
    with open(fnam, 'r') as inf:
        for ln in inf:
            addPlaylist(ln.rstrip())

def saveList():
    fnam = filedialog.asksaveasfilename()
    if not fnam:
        return
    with open(fnam, 'w', encoding='utf-8') as outf:
        for loc in dumpres.keys():
            outf.write("{}\n".format(loc))

def confPlayer():
    dialog = tk.Toplevel(root)
    dialog.title("Configure Player")
    dialog.transient(root)
    dialog.grab_set()
    tk.Label(dialog, text="Player command:").pack()
    tcmd = tk.StringVar(root, value=COMMAND)
    command = tk.Entry(dialog, textvariable=tcmd)
    command.pack()
    tk.Label(dialog, text="Arguments:").pack()
    targ = tk.StringVar(root, value=ARGS)
    args = tk.Entry(dialog, textvariable=targ)
    args.pack()
    tk.Label(dialog, text="Referrer:").pack()
    tref = tk.StringVar(root, value=REFERRER)
    referrer = tk.Entry(dialog, textvariable=tref)
    referrer.pack()
    tk.Label(dialog, text="Source:").pack()
    tsour = tk.StringVar(root, value=SOURCE)
    source = tk.Entry(dialog, textvariable=tsour)
    source.pack()
    def on_submit():
        global COMMAND, ARGS, REFERRER, SOURCE
        COMMAND = tcmd.get()
        ARGS = targ.get()
        REFERRER = tref.get()
        SOURCE = tsour.get()
        dialog.destroy()
    tk.Button(dialog, text="Submit", command=on_submit).pack()

def dump():
    global dumpres
    fnam = filedialog.asksaveasfilename()
    if fnam:
        with open(fnam, 'w') as outf:
            json.dump(dumpres, outf)

def load():
    global dumpres
    fnam = filedialog.askopenfilename()
    if not fnam:
        return
    with open(fnam, 'r') as inf:
        dumpres = json.load(inf)
    for item in treeview.get_children():
        treeview.delete(item)
    for loc in dumpres.keys():
        root_item = treeview.insert("", "end", text=loc)
        for val in dumpres[loc]:
            title = list(val)[0]
            item = treeview.insert(root_item, "end", text=title)
            items[item] = val

menubar = tk.Menu(root)
filemenu = tk.Menu(menubar, tearoff=0)
filemenu.add_command(label="Open", command=openFile)
filemenu.add_separator()
filemenu.add_command(label="Save List Of M3U Files", command=saveList)
filemenu.add_command(label="Open List Of M3U Files", command=openList)
filemenu.add_separator()
filemenu.add_command(label="Dump All State", command=dump)
filemenu.add_command(label="Load New State", command=load)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=root.quit)
confmenu = tk.Menu(menubar, tearoff=0)
confmenu.add_command(label="Player", command=confPlayer)
menubar.add_cascade(label="File", menu=filemenu)
menubar.add_cascade(label="Configure", menu=confmenu)
root.config(menu=menubar)

if len(args.input) > 0:
    for fnam in args.input:
        addPlaylist(fnam)
if len(args.list) > 0:
    with open(args.list[0], 'r') as inf:
        for ln in inf:
            addPlaylist(ln.rstrip())
    

root.mainloop()
