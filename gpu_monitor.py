#! /usr/bin/env python3

import sys
import argparse
import logging as lg
import fileinput as Fi
from pathlib import Path
from time import time

class Output(object) :
  def __init__(self, filename, mode='w') :
    if str(filename) == '-' :
      self.outstream = sys.stdout

    else : 
      self.outstream = Path(filename).open(mode)

    lg.debug('Output: self.outstream set.')

  def __enter__(self) :
    return self.outstream

  def __exit__(self, exc_type, exc_value, traceback) :
    self.outstream.close()

def cli_args() :
  parser = argparse.ArgumentParser(
    description="Parse `nvidia-smi' and write"
    " a line of log for each gpu.",
    formatter_class=(
      argparse.ArgumentDefaultsHelpFormatter
    ),
  )

  parser.add_argument("-v", "--verbose", action="store_true",
                      help="Verbose logging.")
  parser.add_argument("-i", "--input", default='-',
                      metavar='PATH',
                      help="Input Filename")
  parser.add_argument("-o", "--output", default='-',
                      metavar='PATH',
                      help="Output Filename")

  return parser.parse_args()

def main() :
  args = cli_args()
  if args.verbose : lg.getLogger().setLevel(lg.DEBUG)
  lg.debug('Args: %s', args)

  L = [l.rstrip('\n') for l in Fi.input(args.input)]
  lg.debug('L: \n%s', '\n'.join(L))

  data, datum = [], []

  for l in L :
    line_data = [d for d in l.split(' ') if d]

    if len(line_data) < 2 :
      if datum : data.append(datum)
      datum = []
      continue

    lg.debug('line_data: %s', line_data)
    if not line_data[1].endswith('%') :
      lg.debug('not line_data[1].endswith("%%"): %s',
               line_data)

      try : 
        gpu_id = int (line_data[1])
      except :
        continue

      lg.debug('gpu_id: %s', gpu_id)

      datum.extend((time(), gpu_id))
      continue

    lg.debug('line_data[1].endswith("%%"): %s',
             line_data)
    try : 
      fan = float(line_data[1].rstrip('%'))
      temp = float(line_data[2].rstrip('C'))
      pwr = float(line_data[4].rstrip('W'))
      mem = float(line_data[8].rstrip('MiB'))
      gpu_util = float(line_data[12].rstrip('%'))

    except :
      raise

    lg.debug('fan:%s tmp:%s pwr:%s mem:%s gpu:%s',
             fan, temp,pwr,mem,gpu_util)
    datum.extend((fan, temp,pwr,mem,gpu_util))

  data = '\n'.join(
    ' '.join(
      ('%s'% v) for v in d
    ) for d in data
  )
  lg.debug('data: \n%s', data)

  with Output(args.output, 'a') as F :
    F.write(data)
    F.write('\n')

if __name__ == '__main__' :
  lg.basicConfig(level=lg.INFO, format='%(levelname)-8s: %(message)s')

  main()
