#!/usr/bin/env python
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements. See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership. The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the License for the
# specific language governing permissions and limitations
# under the License.
#

import os
import sys
import numpy as np

import Tkinter as tk
import Tkconstants, tkFileDialog
import ttk

from functools import partial

class Multipos(object):
    def __init__(self,filename=None):
        self.filename = None
        self.lines = []
        self.lx = -1
        self.ly = -1
        self.lz = -1
        self.laz = -1
        self.leaz = -1
        self.ln = -1

        self.read(filename)

    def read(self,filename):
        """Read a prefs file
        """
        if filename is None:
            return

        self.filename = filename
        self.lines = open(os.path.join(directory,filename)).readlines()
        self.get_lxyzn()

        return self.lines

    def get_lxyzn(self,lines=None):
        """Get the line positions of the different sections of interest
        """
        if lines is None:
            lines = self.lines
        else:
            self.lines = lines

        self.lx = -1
        self.ly = -1
        self.lz = -1
        self.laz = -1
        self.leaz = -1
        self.ln = -1

        nlines = len(lines)
        for i in range(nlines):
            line = lines[i]
            if line.startswith("{Multipoint X Locations}"):
                self.lx = i
            elif line.startswith("{Multipoint Y Locations}"):
                self.ly = i
            elif line.startswith("{Multipoint Z Locations}"):
                self.lz = i
            elif line.startswith("{Multipoint String Locations}"):
                self.ln = i
            elif line.startswith("{Multipoint Aux Z Locations}"):
                self.laz = i
            elif line.startswith("{Enable Aux Z}"):
                self.leaz = i

        return self.lx,self.ly,self.lz,self.laz,self.leaz,self.ln

    def get_npos(self,lines=None):
        """Get the number of ROI positions
        """
        if lines is None:
            lines = self.lines
            lx, ly, lz, laz, leaz, ln = \
                self.lx, self.ly, self.lz, self.laz, self.leaz, self.ln
        else:
            self.lines = lines
            lx, ly, lz, laz, leaz, ln = self.get_lxyzn()

        if ln == -1:
            return 0

        line = lines[ln+3]
        n = int(line.split("\t")[0])
        return n

    def get_positions(self,lines=None):
        """Get the ROI positions into an array
        """
        if lines is None:
            lines = self.lines
            lx, ly, lz, laz, leaz, ln = \
                self.lx, self.ly, self.lz, self.laz, self.leaz, self.ln
        else:
            self.lines = lines
            lx, ly, lz, laz, leaz, ln = self.get_lxyzn()

        n = self.get_npos()
        arr = []
        for i in range(n):
            x = float(lines[lx+i+3])
            y = float(lines[ly+i+3])
            z = float(lines[lz+i+3])
            arr.append([x,y,z])

        return np.array(arr)

    def paste_data(self, arr, lines=None):
        """Paste new positions into a file. Old positions will be stripped out
        """
        if lines is None:
            lines = self.lines
            lx, ly, lz, laz, leaz, ln = \
                self.lx, self.ly, self.lz, self.laz, self.leaz, self.ln
        else:
            self.lines = lines
            lx, ly, lz, laz, leaz, ln = self.get_lxyzn()

        nout = arr.shape[0]

        nlines = len(lines)
        new_lines = []

        n = self.get_npos()

        line = "%d%s||\n" % (nout,"\t"*(nout+1))

        #mapping to strings
        xarr = map(str,arr[:,0])
        yarr = map(str,arr[:,1])
        zarr = map(str,arr[:,2])
        if laz == -1:
            new_lines = lines[0:lx+3] + ["\n".join(xarr)+"\n"] + \
                    lines[lx+3+n:ly+3] + ["\n".join(yarr)+"\n"] + \
                    lines[ly+3+n:lz+3] + ["\n".join(zarr)+"\n"] + \
                    lines[lz+3+n:ln+3] + [line] + \
                    lines[ln+4:]
        else:
            azstr = "\n".join(map(str,np.zeros(nout,'f')))+"\n"
            eazstr = "\t".join(map(str,np.ones(nout,'i')))+"||\n"
            new_lines = lines[0:lx+3] + ["\n".join(xarr)+"\n"] + \
                    lines[lx+3+n:ly+3] + ["\n".join(yarr)+"\n"] + \
                    lines[ly+3+n:lz+3] + ["\n".join(zarr)+"\n"] + \
                    lines[lz+3+n:ln+3] + [line] + \
                    lines[ln+4:laz+3] + [azstr] + \
                    lines[laz+3+n:leaz+3] + [eazstr] + \
                    lines[leaz+4:]

        return new_lines

    def clone(self, n, lines=None):
        """Clone gets the ROI positions,
                duplicates them n times and
                pastes the result back into the file lines
        """
        if lines is None:
            lines = self.lines
        else:
            self.lines = lines

        arr = self.get_positions()
        arr = np.vstack([arr]*n)

        return self.paste_data(arr)

class TkDialog(tk.Frame):
    def __init__(self, root,directory=''):
        tk.Frame.__init__(self, root)
        self.root = root
        self.root.title("Position cloner v1.0")

        #self.root.wm_iconbitmap('./icon_zeR_icon.ico')

        # options for buttons
        button_opt = {'fill': Tkconstants.BOTH, 'padx': 5, 'pady': 5}
        frame_opt = {'fill': Tkconstants.BOTH, 'padx': 0, 'pady': 0}

        self.var_fnfrom = tk.StringVar(root)
        self.LabeledFn(self,"Input:",self.var_fnfrom,self.AskInput)

        self.var_spin = tk.StringVar(root)
        self.var_spin.set("3")
        self.LabeledSpin(self,"Repeats:",self.var_spin, 1,20)

        self.var_fnto = tk.StringVar(root)
        self.LabeledFn(self,"Output:",self.var_fnto,self.AskOutput)

        tk.Button(self, text='Clone!', command=self.ProcessFile).pack(**button_opt)

        #Status bar
        self.status = tk.StringVar()        
        tk.Label(self, bd=1, relief=tk.SUNKEN, anchor=tk.W, textvariable=self.status, font=('arial',12,'normal')).pack(fill=tk.X)
        self.pack(**frame_opt)

        # defining options for opening a directory
        self.dir_opt1 = options = {}
        options['initialdir'] = directory
        options['initialfile'] = ''
        options['parent'] = root
        options['filetypes'] = [('Point prefs', '.mlt.prefs')]
        options['title'] = 'Select the input file'

        # these options are for the output file dialog
        self.dir_opt2 = options = {}
        options['initialdir'] = directory
        options['initialfile'] = ''
        options['parent'] = root
        options['filetypes'] = [('Point prefs', '.mlt.prefs')]
        options['title'] = 'Select the output file'

    def ProcessFile(self):
        fn = os.path.join(self.dir_opt1['initialdir'],self.var_fnfrom.get())
        fn_out = os.path.join(self.dir_opt2['initialdir'],self.var_fnto.get())

        n = int(self.var_spin.get())

        if os.path.exists(fn) and os.path.isfile(fn) and fn_out != '':
            mp = Multipos()
            mp.read(fn)
            npos = mp.get_npos()
            new_lines = mp.clone(n)

            f = open(fn_out,"w")
            f.writelines(new_lines)
            f.close()

            self.status.set("Found %d position, cloned %d times" % (npos,n))

    def LabeledCombo(self,root,label,tv,values=[]):
        row = tk.Frame(root)
        lab = tk.Label(row, width=8, text=label, anchor='w')
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=tk.LEFT)
        widget = ttk.Combobox(row, textvariable=tv, values=values, exportselection=0, state="readonly")
        widget.pack(side=tk.LEFT, expand=tk.YES, fill=tk.X)

        return widget

    def LabeledSpin(self,root,label,tv,from_=1,to=20):
        row = tk.Frame(root)
        lab = tk.Label(row, width=8, text=label, anchor='w')
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=tk.LEFT)
        widget = tk.Spinbox(row, textvariable=tv, from_=from_, to=to)
        widget.pack(side=tk.LEFT, expand=tk.YES, fill=tk.X)

        return widget

    def LabeledFn(self,root,label,tv,func):
        def ask_dialog(entry):
            fn = tkFileDialog.askopenfilename()

            if fn is not None:
                entry.set(fn)

        if func is None:
            func = ask_dialog

        row = tk.Frame(root)
        lab = tk.Label(row, width=8, text=label, anchor='w')
        ent = tk.Entry(row, textvariable=tv)
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=tk.LEFT)
        ent.pack(side=tk.LEFT, expand=tk.YES, fill=tk.X)
        but = tk.Button(row, text="...", command=partial(func, tv))
        but.pack(side=tk.LEFT)

        return ent

    def AskInput(self, tv):
        """Returns a selected filename."""

        fn = tkFileDialog.askopenfilename(**self.dir_opt1)
        fn = fn.replace("/",os.sep)
        if len(fn) == 0:
            return

        the_dir, fn = os.path.split(fn)
        self.dir_opt1['initialdir'] = the_dir
        self.dir_opt1['initialfile'] = fn

        fn_out = "new_"+fn
        self.dir_opt2['initialdir'] = the_dir
        self.dir_opt2['initialfile'] = fn_out

        self.var_fnfrom.set(fn)
        self.AskOutput(self.var_fnto)

        self.var_fnto.set(fn_out)

    def AskOutput(self, tv):
        """Returns a selected filename."""

        fn = tkFileDialog.asksaveasfilename(**self.dir_opt2)
        fn = fn.replace("/",os.sep)
        if len(fn) == 0:
            return

        the_dir, fn = os.path.split(fn)
        self.dir_opt2['initialdir'] = the_dir
        self.dir_opt2['initialfile'] = fn

    def quit(self):
        self.root.destroy()

def test():
    directory = r"C:\ProgramData\Intelligent Imaging Innovations\SlideBook 6.0\Users\Default User"
    fn = "timelapse.mlt.prefs"

    fn = os.path.join(directory,fn)

    mp = Multipos()
    mp.read(fn)
    new_lines = mp.clone(5)

    fn_out = os.path.join(directory,"new_"+fn)
    f = open(fn_out,"w")
    f.writelines(new_lines)
    f.close()

if __name__ == '__main__':
    nargv = len(sys.argv)
    directory = ""
    if nargv > 1:
        directory = sys.argv[1]
        if not os.path.isdir(directory):
            print "%s not a valid directory..."
            directory = ""
        
    root = tk.Tk()
    tde = TkDialog(root,directory)
    tde.pack()
    root.mainloop()
