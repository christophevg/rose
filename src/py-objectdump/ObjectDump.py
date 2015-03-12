#!/usr/bin/python

# - wrapper around objdump
# - allows for function relocation
# - minimal support for mach-o-x86-64

import sys
import subprocess
import re
import struct
import argparse

# file format mach-o-x86-64

# '0000000000000000 <_a>:'
function = re.compile('^([0-9]{16}) <_([a-zA-Z_]+)>:$')
# '   1:\t48 89 e5             \tmov    %rsp,%rbp'
extract_bytes = re.compile('^ *[0-9a-z]+:\t([0-9a-z]{2}) ?([0-9a-z]{2})? ?([0-9a-z]{2})? ?([0-9a-z]{2})? ?([0-9a-z]{2})?')
# '0000000000000029 BRANCH32          _a'
relocation = re.compile('^([0-9]{16}) BRANCH32 {10}_([a-zA-Z0-9_]+)$')

class ObjectDump():

  def __init__(self):
    self.functions      = {}

  def load(self, filename):
    code_out        = run(["gobjdump", "-d",                filename])
    relocations_out = run(["gobjdump", "-j", ".text", "-r", filename])

    current_function = None

    # load relocations
    relocations = {}
    for line in relocations_out:
      matches = relocation.match(line)
      if matches:
        relocations[int(matches.group(1), 16)] = Relocation(
          link      = matches.group(2),
          size      = 4,
          functions = self.functions
        )

    # parse code
    byte = 0
    for line in code_out:
      # load function
      matches = function.match(line)
      if matches:
        name  = matches.group(2)
        start = int(matches.group(1),16)
        self.functions[name] = Function(name, start)
        current_function = self.functions[name]
      # load byte code, inserting relocations as we encounter them
      matches = extract_bytes.match(line)
      if matches:
        g = 1
        while g <= 5 and matches.group(g):
          skip = 1
          try:
            relocations[byte].offset = byte - current_function.start
            relocations[byte].origin = current_function
            current_function.bytes.append(relocations[byte])
            skip = len(relocations[byte])
          except KeyError:
            current_function.bytes.append(Byte(int(matches.group(g),16)))
          byte += skip
          g += skip
    return self

class Function():
  def __init__(self, name, start):
    self.name  = name
    self.start = start
    self.bytes = []
  def __repr__(self):
    return self.name
  def __str__(self):
    return " ".join(map(str, self.bytes))
  def __len__(self):
    length = 0
    for b in self.bytes: length += len(b)
    return length

class Byte():
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return '{:02x}'.format(self.value)
  def __len__(self):
    return 1

class Relocation():
  def __init__(self, size, link, functions):
    self.size      = size
    self.link      = link
    self.functions = functions
    self.origin    = None;
    self.offset    = None;
  def __str__(self):
    # the relative address takes the _next_ instruction as a reference
    next_instruction = (self.origin.start + self.offset + self.size)
    relative_address = self.functions[self.link].start - next_instruction
    s = struct.pack('<i', relative_address).encode('hex')
    return " ".join([s[i:i+2] for i in range(0, len(s), 2)])
  def __len__(self):
    return self.size

def run(cmd):
  p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
  out, err = p.communicate()
  return out.split("\n");

if __name__ == "__main__":
  parser = argparse.ArgumentParser(
      description="Command-line tool to query and relocate object files.")
  parser.add_argument("files", type=str, nargs="*",
                      help="object files to be loaded.")
  parser.add_argument("-v", "--verbose",
                      help="output info on what's happening",
                      action="store_true")
  parser.add_argument("-l", "--list",
                      help="list all loaded functions",
                      action="store_true")
  parser.add_argument("-n", "--name",
                      help="show name of function (in combination with -f or -l)",
                      action="store_true")
  parser.add_argument("-s", "--size",
                      help="show size of code. in combination with -f or -l for each function",
                      action="store_true")
  parser.add_argument("-p", "--position",
                      help="show position of code (in combination with -f or -l)",
                      action="store_true")
  parser.add_argument("-c", "--code",
                      help="show code. in combination with -f for each function",
                      action="store_true")
  parser.add_argument("-f", "--function",
                      help="show information for this function",
                      action="append")
  parser.add_argument("-r", "--relocate",
                      help="relocate a function. argument format: <name>:<hex-address>",
                      action="append")
  
  args = parser.parse_args()

  o = ObjectDump()

  # load object file(s)
  for file in args.files: o.load(file)

  # perform relocations
  if args.relocate:
    for relocation in args.relocate:
      (name, location) = str.split(relocation, ":")
      o.functions[name].start = int(location, 16)

  # show requested information

  def labeled(label, value):
    return (label +"=" if args.verbose else "") + str(value)

  def show(function):
    out = []

    if args.name:     out.append(labeled("name",     repr(function)))
    if args.size:     out.append(labeled("size",     len(function)))
    if args.position: out.append(labeled("position", function.start))
    if args.code:     out.append(labeled("code",     function))

    if len(out) > 0: print " ".join(out)

  if args.list:
    for name, function in o.functions.iteritems():
      show(function)
  elif args.function:
    for function in args.function:
      show(o.functions[function])
  elif args.size:
    total = 0
    for name, function in o.functions.iteritems():
      total += len(function)
    if args.verbose: sys.stdout.write("total=")
    print total
