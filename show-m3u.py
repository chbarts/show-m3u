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
from tkinter import N, S, E, W

from configparser import ConfigParser

from pathlib import Path

COMMAND="mpv"
REFERRER="--referrer={}"
ARGS="--force-window=yes"
SOURCE="{}"

def parseM3U(inf):
    resarr = []
    res = {}
    item = {}
    title = ""
    res["title"] = None
    for line in inf:
        line = line.rstrip()
        if re.match("#EXTM3U", line):
            continue
        elif re.match("#PLAYLIST:.+", line):
            grp = re.match("#PLAYLIST:(.+)", line)
            res["title"] = grp.groups()[0]
        elif re.match("#EXTINF.+", line):
            tagarr = re.findall("([-0-9A-Za-z]+)=\"?([^\"]*)\"?", line)
            tags = {}
            if len(tagarr) > 0:
                title = re.split("([-0-9A-Za-z]+)=\"?([^\"]*)\"?", line)[-1]
                for key, value in tagarr:
                    tags[key] = value
            else:
                title = re.split(":-?\\d+,\\s?", line)[-1]
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
            if title in item:
                item[title]["location"] = line
                resarr.append(item)
                item = {}
            else:
                resarr.append({line: {"location": line}})
    res["array"] = resarr
    return res

root = tk.Tk()
root.title("Show M3U")

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

tk.Grid.rowconfigure(root, 0, weight=1)
tk.Grid.columnconfigure(root, 0, weight=1)

pane = ttk.PanedWindow(root, orient=tk.VERTICAL)
pane.grid(row=0, column=0, sticky=N+S+E+W)
pane.grid_columnconfigure(0, weight=1)
pane.grid_columnconfigure(1, weight=1)
pane.grid_columnconfigure(2, weight=1)
pane.grid_rowconfigure(0, weight=1)
pane.grid_rowconfigure(1, weight=1)
pane.grid_rowconfigure(2, weight=1)

searchframe = ttk.Frame(pane)
searchframe.grid(row=0, column=0, sticky=N+S+E+W)
searchframe.grid_columnconfigure(0, weight=1)
searchframe.grid_columnconfigure(1, weight=1)
searchframe.grid_columnconfigure(2, weight=1)
label = ttk.Label(searchframe, text='Enter regular expression, blank to reset:')
label.grid(column=0, row=0, sticky=N+S+E+W)
searchterm = ttk.Entry(searchframe)
searchterm.grid(column=1, row=0, sticky=E+W)
searchbutton = ttk.Button(searchframe, text='Search/Reset')
searchbutton.grid(column=2, row=0, sticky=N+S+E+W)

treeframe = ttk.Frame(pane)
treeframe.grid(row=1, column=0, sticky=N+S+E+W)
treeframe.grid_columnconfigure(0, weight=1)
treeframe.grid_rowconfigure(0, weight=1)

treeview = ttk.Treeview(treeframe)
treeview.grid(column=0, row=0, sticky=N+S+E+W)

scrollbar = ttk.Scrollbar(treeframe)
scrollbar.grid(column=1, row=0, sticky=N+S)

treeview['yscrollcommand'] = scrollbar.set
scrollbar.config(command=treeview.yview)

procs = ttk.Treeview(root, columns=('args'), height=2)
# procs.insert('', 'end', text='mpv', values=('running'))

pane.add(searchframe, weight=0)
pane.add(treeframe, weight=6)
pane.add(procs, weight=1)

items = {}
procdct = {}

def checker():
    dead = []
    for id in list(procdct):
        proc = procdct[id]
        if proc.poll() is not None: # If process is dead
            procs.delete(id)
            dead.append(id)
    for id in dead:
        procdct.pop(id, None)
    if len(list(procdct)) > 0:
        root.after(1000, checker) # Run this function every second, but don't block event loop

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
        proc = None
        if len(referer) > 0:
            proc = subprocess.Popen([COMMAND, ARGS, REFERRER.format(referer), SOURCE.format(location)])
        else:
            proc = subprocess.Popen([COMMAND, ARGS, SOURCE.format(location)])
        ref = procs.insert('', 'end', text=COMMAND, values=(location))
        procdct[ref] = proc
        root.after(1000, checker)

def itemClicked(event):
    id = treeview.identify_row(event.y)
    printValue(id)

def itemKeypress(event):
    id = treeview.focus()
    printValue(id)

def procClicked(event):
    id = procs.identify_row(event.y)
    if id in procdct:
        proc = procdct[id]
        proc.kill()
        procs.delete(id)
        procdct.pop(id, None)

def procKeypress(event):
    id = procs.focus()
    if id in procdct:
        proc = procdct[id]
        proc.kill()
        procs.delete(id)
        procdct.pop(id, None)

treeview.bind("<Button-1>", itemClicked)
treeview.bind("<Key-Return>", itemKeypress)

procs.bind("<Button-1>", procClicked)
procs.bind("<Key-Return>", procKeypress)

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
        for val in res["array"]:
            title = list(val)[0]
            item = treeview.insert(id, "end", text=title)
            items[item] = val

treeview.bind("<Button-2>", rightClicked)
treeview.bind("<Button-3>", rightClicked)

def addPlaylist(fnam):
    res = {}
    path = Path(fnam)
    if not path.is_file():
        return res
    with open(fnam, 'r') as inf:
        res = parseM3U(inf)
    nam = fnam
    if res["title"] is not None:
        nam = res["title"]
    root_item = treeview.insert("", "end", text=nam)
    dumpres[fnam] = res
    for val in res["array"]:
        title = list(val)[0]
        item = treeview.insert(root_item, "end", text=title)
        items[item] = val
    return res

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

def search(term):
    res = {}
    for loc in dumpres.keys():
        val = dumpres[loc]
        plname = loc
        if val["title"] is not None:
            plname = val["title"]
        for stream in val["array"]:
            title = list(stream)[0]
            if re.search(term, title):
                if loc not in res:
                    res[loc] = {"title": plname, "array": []}
                res[loc]["array"].append(stream)
    return res

def findConfigureFile():
    path = None
    if 'APPDATA' in os.environ:
        path = Path(os.environ['APPDATA'], 'show_m3u.ini')
    elif 'XDG_CONFIG_HOME' in os.environ:
        path = Path(os.environ['XDG_CONFIG_HOME'], 'show_m3u.ini')
    elif 'HOME' in os.environ:
        path = Path(os.environ['HOME'], '.show_m3urc')
    else:
        return None
    if path.is_file():
        return path
    else:
        return None

def useConfigureFile(fname):
    global COMMAND, REFERRER, ARGS, SOURCE
    config = ConfigParser(allow_no_value=True,delimiters=('=',))
    config.optionxform = str # Preserve case in filenames
    config.read_file(open(fname))
    if 'vars' in config.sections():
        if 'command' in list(config['vars']):
            COMMAND = config['vars']['command']
        if 'referrer' in list(config['vars']):
            REFERRER = config['vars']['referrer']
        if 'args' in list(config['vars']):
            ARGS = config['vars']['args']
        if 'source' in list(config['vars']):
            SOURCE = config['vars']['source']
    if 'files' in config.sections():
        for fn in list(config['files']):
            addPlaylist(fn)

def reloadConfigure():
    global items
    global dumpres
    for item in treeview.get_children():
        treeview.delete(item)
    items = {}
    dumpres = {}
    path = findConfigureFile()
    if path:
        useConfigureFile(path)

def reloadCurrentFiles():
    global items
    global dumpres
    files = dumpres.keys()
    items = {}
    dumpres = {}
    for fnam in files:
        addPlaylist(fnam)

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
        chan = dumpres[loc]
        name = loc
        if chan["title"] is not None:
            name = chan["title"]
        root_item = treeview.insert("", "end", text=name)
        for val in chan["array"]:
            title = list(val)[0]
            item = treeview.insert(root_item, "end", text=title)
            items[item] = val

def doSearch(event):
    global items
    for item in treeview.get_children():
        treeview.delete(item)
    items = {}
    term = searchterm.get()
    if re.match("^\\s+$", term) or (len(term) == 0):
        for loc in dumpres.keys():
            chan = dumpres[loc]
            name = loc
            if chan["title"] is not None:
                name = chan["title"]
            root_item = treeview.insert("", "end", text=name)
            for val in chan["array"]:
                title = list(val)[0]
                item = treeview.insert(root_item, "end", text=title)
                items[item] = val
    else:
        res = search(term)
        for loc in res.keys():
            chan = res[loc]
            name = loc
            if chan["title"] is not None:
                name = chan["title"]
            root_item = treeview.insert("", "end", text=name)
            for val in chan["array"]:
                title = list(val)[0]
                item = treeview.insert(root_item, "end", text=title)
                items[item] = val


searchbutton.bind("<Button-1>", doSearch)
searchterm.bind("<Key-Return>", doSearch)

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
filemenu.add_command(label="Reload Current Playlists", command=reloadCurrentFiles)
filemenu.add_command(label="Reload Configure", command=reloadConfigure)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=root.quit)
confmenu = tk.Menu(menubar, tearoff=0)
confmenu.add_command(label="Player", command=confPlayer)
menubar.add_cascade(label="File", menu=filemenu)
menubar.add_cascade(label="Configure", menu=confmenu)
root.config(menu=menubar)

parser = argparse.ArgumentParser(description='Play M3U File From GUI')

parser.add_argument('-i', '--input', metavar='INFILE', type=str, nargs='+', default='', help='Specify INFILE as M3U input file or files')
parser.add_argument('-l', '--list', metavar='INFILE', type=str, nargs=1, default='', help='Specify INFILE as list of M3U files')
parser.add_argument('-c', '--command', metavar='COMMAND', type=str, nargs=1, default='', help='Specify the program name to use to play the media')
parser.add_argument('-a', '--args', metavar='ARGS', type=str, nargs=1, default='', help='Specify the other arguments needed, as one string')
parser.add_argument('-r', '--referrer', metavar='REFERRER', type=str, nargs=1, default='', help='Specify how to get the player to send the HTTP REFERER header, if needed, as Python format string')
parser.add_argument('-s', '--source', metavar='SOURCE', type=str, nargs=1, default='', help='Specify how to pass the source into the player, as Python format string')
parser.add_argument('-C', '--configure', metavar='CONFIG_FILE', type=str, nargs=1, default='', help='Specify a configure file that can set options and contain a list of M3U files to load. Otherwise, the program looks for show_m3u.ini in XDG_CONFIG_HOME or APPDATA if set in environment, or .show_m3urc in HOME')

args = parser.parse_args()

if len(args.command) > 0:
    COMMAND = args.command[0]
if len(args.args) > 0:
    ARGS = args.args[0]
if len(args.referrer) > 0:
    REFERRER = args.referrer[0]
if len(args.source) > 0:
    SOURCE = args.source[0]

if len(args.input) > 0:
    for fnam in args.input:
        addPlaylist(fnam)
if len(args.list) > 0:
    with open(args.list[0], 'r') as inf:
        for ln in inf:
            addPlaylist(ln.rstrip())
if len(args.configure) > 0:
    useConfigureFile(args.configure[0])
else:
    conf = findConfigureFile()
    if conf:
        useConfigureFile(conf)

checker()
root.mainloop()
